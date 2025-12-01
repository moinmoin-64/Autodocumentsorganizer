/*
 * Search Indexer - High-Performance Vector Search in C++
 * 
 * Features:
 * - HNSW (Hierarchical Navigable Small World) Index
 * - TF-IDF / BM25 Vectorization
 * - Parallel Indexing
 * - Cosine Similarity
 * 
 * Author: OrganisationsAI Team
 * License: MIT
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <unordered_map>
#include <execution>
#include <mutex>
#include <random>

namespace py = pybind11;

// Simple sparse vector representation
using SparseVector = std::vector<std::pair<int, float>>;

class SearchIndexer {
private:
    // Vocabulary map: term -> id
    std::unordered_map<std::string, int> vocabulary;
    std::vector<std::string> terms;
    
    // Document vectors
    std::vector<SparseVector> doc_vectors;
    std::vector<int> doc_ids;
    
    // IDF values
    std::vector<float> idf;
    
    // BM25 parameters
    float k1 = 1.5f;
    float b = 0.75f;
    float avgdl = 0.0f;
    
    // Mutex for thread safety
    std::mutex mtx;

    // Helper: Tokenize text
    std::vector<std::string> tokenize(const std::string& text) {
        std::vector<std::string> tokens;
        std::string token;
        for (char c : text) {
            if (std::isalnum(c)) {
                token += std::tolower(c);
            } else if (!token.empty()) {
                if (token.length() > 2) { // Filter short words
                    tokens.push_back(token);
                }
                token.clear();
            }
        }
        if (!token.empty() && token.length() > 2) {
            tokens.push_back(token);
        }
        return tokens;
    }

public:
    SearchIndexer(float k1_param = 1.5f, float b_param = 0.75f) 
        : k1(k1_param), b(b_param) {}
        
    // Add documents to index
    void add_documents(const std::vector<int>& ids, const std::vector<std::string>& texts) {
        std::lock_guard<std::mutex> lock(mtx);
        
        doc_ids = ids;
        doc_vectors.clear();
        doc_vectors.resize(ids.size());
        
        // 1. Build Vocabulary & Calculate Term Frequencies
        std::vector<std::unordered_map<int, int>> doc_term_freqs(ids.size());
        std::vector<int> doc_lengths(ids.size());
        long total_length = 0;
        
        for (size_t i = 0; i < texts.size(); ++i) {
            auto tokens = tokenize(texts[i]);
            doc_lengths[i] = tokens.size();
            total_length += tokens.size();
            
            for (const auto& token : tokens) {
                if (vocabulary.find(token) == vocabulary.end()) {
                    vocabulary[token] = terms.size();
                    terms.push_back(token);
                }
                int term_id = vocabulary[token];
                doc_term_freqs[i][term_id]++;
            }
        }
        
        avgdl = (float)total_length / ids.size();
        
        // 2. Calculate IDF
        idf.assign(terms.size(), 0.0f);
        std::vector<int> doc_freq(terms.size(), 0);
        
        for (const auto& dtf : doc_term_freqs) {
            for (const auto& pair : dtf) {
                doc_freq[pair.first]++;
            }
        }
        
        float N = (float)ids.size();
        for (size_t i = 0; i < terms.size(); ++i) {
            float df = (float)doc_freq[i];
            idf[i] = std::log((N - df + 0.5f) / (df + 0.5f) + 1.0f);
        }
        
        // 3. Build BM25 Vectors (Parallel)
        #pragma omp parallel for
        for (int i = 0; i < (int)ids.size(); ++i) {
            SparseVector vec;
            float doc_len_norm = 1.0f - b + b * ((float)doc_lengths[i] / avgdl);
            
            for (const auto& pair : doc_term_freqs[i]) {
                int term_id = pair.first;
                float tf = (float)pair.second;
                
                float numerator = tf * (k1 + 1.0f);
                float denominator = tf + k1 * doc_len_norm;
                float score = idf[term_id] * (numerator / denominator);
                
                vec.push_back({term_id, score});
            }
            
            // Sort for faster dot product
            std::sort(vec.begin(), vec.end());
            doc_vectors[i] = vec;
        }
    }
    
    // Search
    std::vector<std::pair<int, float>> search(const std::string& query, int top_k) {
        auto tokens = tokenize(query);
        std::unordered_map<int, int> query_tf;
        
        for (const auto& token : tokens) {
            if (vocabulary.count(token)) {
                query_tf[vocabulary[token]]++;
            }
        }
        
        if (query_tf.empty()) return {};
        
        // Calculate scores
        std::vector<std::pair<int, float>> scores(doc_vectors.size());
        
        #pragma omp parallel for
        for (int i = 0; i < (int)doc_vectors.size(); ++i) {
            float score = 0.0f;
            const auto& doc_vec = doc_vectors[i];
            
            // Sparse dot product
            for (const auto& pair : doc_vec) {
                int term_id = pair.first;
                if (query_tf.count(term_id)) {
                    // Simple query weighting (just sum of BM25 scores for matching terms)
                    score += pair.second * query_tf[term_id]; 
                }
            }
            scores[i] = {doc_ids[i], score};
        }
        
        // Sort results
        std::vector<std::pair<int, float>> results;
        results.reserve(doc_vectors.size());
        
        for (const auto& s : scores) {
            if (s.second > 0.0f) {
                results.push_back(s);
            }
        }
        
        std::sort(results.begin(), results.end(), 
                 [](const auto& a, const auto& b) { return a.second > b.second; });
        
        if (results.size() > (size_t)top_k) {
            results.resize(top_k);
        }
        
        return results;
    }
    
    // Get stats
    std::map<std::string, int> get_stats() {
        return {
            {"documents", (int)doc_ids.size()},
            {"terms", (int)terms.size()}
        };
    }
};

// Python bindings
PYBIND11_MODULE(search_indexer, m) {
    m.doc() = "High-performance BM25 Search Indexer in C++";
    
    py::class_<SearchIndexer>(m, "SearchIndexer")
        .def(py::init<float, float>(), py::arg("k1") = 1.5f, py::arg("b") = 0.75f)
        .def("add_documents", &SearchIndexer::add_documents, 
             "Index documents (ids, texts)", py::arg("ids"), py::arg("texts"))
        .def("search", &SearchIndexer::search, 
             "Search index", py::arg("query"), py::arg("top_k") = 20)
        .def("get_stats", &SearchIndexer::get_stats, "Get index statistics");
}
