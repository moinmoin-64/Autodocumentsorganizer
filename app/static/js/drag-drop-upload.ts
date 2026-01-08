/**
 * Drag & Drop Upload Handler - TypeScript Version mit Advanced Features
 */

/**
 * Upload Progress Callback
 */
export type ProgressCallback = (progress: {
    loaded: number;
    total: number;
    percentage: number;
    filename: string;
}) => void;

/**
 * Upload Response Type
 */
export interface UploadResponse {
    success: boolean;
    message: string;
    files: Array<{
        filename: string;
        size: number;
        url: string;
    }>;
    errors?: Array<{
        filename: string;
        error: string;
    }>;
}

/**
 * File upload event callback
 */
export type UploadCallback = (files: File[]) => Promise<void> | void;

/**
 * Upload Configuration
 */
export interface UploadConfig {
    endpoint?: string;
    maxFileSize?: number;  // In MB
    allowedTypes?: string[];
    maxFiles?: number;
    retryAttempts?: number;
    timeout?: number;  // In ms
}

/**
 * Drag & Drop Upload handler with advanced features
 */
export class DragDropUpload {
    private dropZone: HTMLElement | null;
    private fileInput: HTMLInputElement | null;
    private onUpload: UploadCallback;
    private progressCallback?: ProgressCallback;
    private config: Required<UploadConfig>;
    private uploadQueue: File[] = [];
    private isUploading: boolean = false;

    constructor(
        dropZoneId: string,
        fileInputId: string,
        onUploadCallback: UploadCallback,
        config?: UploadConfig,
        progressCallback?: ProgressCallback
    ) {
        this.dropZone = document.getElementById(dropZoneId);
        this.fileInput = document.getElementById(fileInputId) as HTMLInputElement;
        this.onUpload = onUploadCallback;
        this.progressCallback = progressCallback;

        // Default config
        this.config = {
            endpoint: '/api/upload',
            maxFileSize: 50,  // 50 MB
            allowedTypes: ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.doc', '.docx'],
            maxFiles: 20,
            retryAttempts: 3,
            timeout: 30000,
            ...config
        };

        if (!this.dropZone || !this.fileInput) {
            console.warn(`Drag-drop elements not found: ${dropZoneId}, ${fileInputId}`);
            return;
        }

        this.init();
    }

    /**
     * Initialize drag-drop functionality
     */
    private init(): void {
        // Prevent default drag behaviors
        const events = ['dragenter', 'dragover', 'dragleave', 'drop'] as const;
        
        events.forEach(eventName => {
            this.dropZone?.addEventListener(eventName, (e) => this.preventDefaults(e), false);
            document.body.addEventListener(eventName, (e) => this.preventDefaults(e), false);
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone?.addEventListener(eventName, () => this.highlight(), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone?.addEventListener(eventName, () => this.unhighlight(), false);
        });

        // Handle dropped files
        this.dropZone?.addEventListener('drop', (e) => this.handleDrop(e), false);

        // Handle click to upload
        this.dropZone?.addEventListener('click', () => this.fileInput?.click());
        this.fileInput?.addEventListener('change', (e) => {
            const files = (e.target as HTMLInputElement).files;
            if (files) {
                this.handleFiles(files);
            }
        });
    }

    /**
     * Prevent default drag behaviors
     */
    private preventDefaults(e: Event): void {
        e.preventDefault();
        e.stopPropagation();
    }

    /**
     * Highlight drop zone
     */
    private highlight(): void {
        this.dropZone?.classList.add('drag-over');
    }

    /**
     * Remove highlight from drop zone
     */
    private unhighlight(): void {
        this.dropZone?.classList.remove('drag-over');
    }

    /**
     * Handle dropped files
     */
    private handleDrop(e: DragEvent): void {
        const dt = e.dataTransfer;
        if (!dt) return;

        const files = dt.files;
        this.handleFiles(files);
    }

    /**
     * Handle files (convert FileList to File[])
     */
    private handleFiles(files: FileList): void {
        const fileArray = Array.from(files);
        const validFiles = fileArray.filter(file => this.validateFile(file));
        
        if (validFiles.length === 0) {
            console.error('Keine validen Dateien zum Upload');
            return;
        }

        // Queue files for upload
        this.uploadQueue.push(...validFiles);
        
        // Start upload process
        this.processUploadQueue();
    }

    /**
     * Validate file before upload
     */
    private validateFile(file: File): boolean {
        // Check file size
        const fileSizeMB = file.size / (1024 * 1024);
        if (fileSizeMB > this.config.maxFileSize) {
            this.showError(`${file.name} ist zu groß (Max: ${this.config.maxFileSize}MB)`);
            return false;
        }

        // Check file type
        const extension = '.' + file.name.split('.').pop()?.toLowerCase();
        if (!this.config.allowedTypes.includes(extension)) {
            this.showError(`${file.name} hat nicht unterstützten Dateityp`);
            return false;
        }

        return true;
    }

    /**
     * Process upload queue sequentially
     */
    private async processUploadQueue(): Promise<void> {
        if (this.isUploading || this.uploadQueue.length === 0) {
            return;
        }

        this.isUploading = true;

        while (this.uploadQueue.length > 0) {
            const file = this.uploadQueue.shift();
            if (file) {
                await this.uploadFileWithRetry(file, 0);
            }
        }

        this.isUploading = false;
    }

    /**
     * Upload file with retry logic
     */
    private async uploadFileWithRetry(file: File, attemptNumber: number): Promise<void> {
        try {
            await this.uploadFile(file);
        } catch (error) {
            if (attemptNumber < this.config.retryAttempts) {
                console.warn(`Retry ${attemptNumber + 1}/${this.config.retryAttempts} for ${file.name}`);
                await new Promise(resolve => setTimeout(resolve, 1000 * (attemptNumber + 1)));
                await this.uploadFileWithRetry(file, attemptNumber + 1);
            } else {
                this.showError(`Fehler beim Upload von ${file.name}: ${error}`);
            }
        }
    }

    /**
     * Upload single file to backend
     */
    private uploadFile(file: File): Promise<void> {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);

            const xhr = new XMLHttpRequest();

            // Progress tracking
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const progress = {
                        loaded: e.loaded,
                        total: e.total,
                        percentage: Math.round((e.loaded / e.total) * 100),
                        filename: file.name
                    };
                    
                    if (this.progressCallback) {
                        this.progressCallback(progress);
                    }
                    
                    this.updateProgressUI(progress);
                }
            });

            // Error handling
            xhr.addEventListener('error', () => {
                reject(new Error('Network error'));
            });

            xhr.addEventListener('abort', () => {
                reject(new Error('Upload aborted'));
            });

            // Timeout
            xhr.timeout = this.config.timeout;
            xhr.addEventListener('timeout', () => {
                reject(new Error('Upload timeout'));
            });

            // Complete
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response: UploadResponse = JSON.parse(xhr.responseText);
                        if (response.success) {
                            this.showSuccess(`${file.name} erfolgreich hochgeladen`);
                            resolve();
                        } else {
                            reject(new Error(response.message || 'Upload failed'));
                        }
                    } catch (e) {
                        reject(new Error('Invalid server response'));
                    }
                } else {
                    reject(new Error(`Server error: ${xhr.statusText}`));
                }
            });

            // Send request
            xhr.open('POST', this.config.endpoint, true);
            xhr.send(formData);
        });
    }

    /**
     * Update progress UI
     */
    private updateProgressUI(progress: {
        loaded: number;
        total: number;
        percentage: number;
        filename: string;
    }): void {
        const progressBar = document.getElementById('uploadProgress');
        if (progressBar) {
            const progressElement = progressBar as HTMLProgressElement;
            progressElement.value = progress.percentage;
        }

        const statusElement = document.getElementById('uploadStatus');
        if (statusElement) {
            statusElement.textContent = `${progress.filename}: ${progress.percentage}%`;
        }
    }

    /**
     * Show success message
     */
    private showSuccess(message: string): void {
        const alert = this.createAlert(message, 'success');
        this.showAlert(alert);
    }

    /**
     * Show error message
     */
    private showError(message: string): void {
        const alert = this.createAlert(message, 'error');
        this.showAlert(alert);
    }

    /**
     * Create alert element
     */
    private createAlert(message: string, type: 'success' | 'error'): HTMLDivElement {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        return alert;
    }

    /**
     * Show alert message
     */
    private showAlert(alert: HTMLDivElement): void {
        const container = this.dropZone?.parentElement;
        if (container) {
            container.insertBefore(alert, this.dropZone);
            setTimeout(() => alert.remove(), 5000);
        }
    }

    /**
     * Get upload status
     */
    public getStatus(): {
        isUploading: boolean;
        queueSize: number;
    } {
        return {
            isUploading: this.isUploading,
            queueSize: this.uploadQueue.length
        };
    }
}

/**
 * Upload function
 */
export async function uploadFile(files: File[]): Promise<void> {
    console.log('Files to upload:', files);
    // Wird in main app integriert
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initializeDragDrop();
    });
} else {
    initializeDragDrop();
}

/**
 * Initialize drag-drop upload
 */
function initializeDragDrop(): void {
    if (typeof uploadFile === 'function') {
        new DragDropUpload(
            'uploadArea',
            'fileInput',
            uploadFile,
            {
                endpoint: '/api/upload',
                maxFileSize: 100,
                maxFiles: 20,
                retryAttempts: 3
            }
        );
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DragDropUpload, uploadFile, initializeDragDrop, UploadConfig, UploadResponse };
}
