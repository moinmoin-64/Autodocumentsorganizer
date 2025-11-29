import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:photo_view/photo_view.dart';
import 'package:photo_view/photo_view_gallery.dart';
import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  runApp(PhotoManagerApp());
}

class PhotoManagerApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Photo Manager',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        brightness: Brightness.light,
        scaffoldBackgroundColor: Color(0xFFF2F2F7), // iOS Background
        appBarTheme: AppBarTheme(
          backgroundColor: Color(0xFFF2F2F7),
          elevation: 0,
          iconTheme: IconThemeData(color: Color(0xFF007AFF)),
          titleTextStyle: TextStyle(
            color: Colors.black,
            fontSize: 34,
            fontWeight: FontWeight.bold,
            fontFamily: 'SF Pro Display',
          ),
        ),
      ),
      home: SettingsScreen(),
    );
  }
}

// Settings Screen - für Server-URL Konfiguration
class SettingsScreen extends StatefulWidget {
  @override
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _urlController = TextEditingController();
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadServerUrl();
  }

  Future<void> _loadServerUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final url = prefs.getString('server_url') ?? '';
    _urlController.text = url;
    
    if (url.isNotEmpty) {
      // Wenn URL gespeichert, direkt zur Gallery
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => GalleryScreen(serverUrl: url)),
      );
    }
  }

  Future<void> _saveAndContinue() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) {
      _showError('Bitte Server-URL eingeben');
      return;
    }

    setState(() => _isLoading = true);

    try {
      // Test connection
      final response = await http.get(Uri.parse('$url/api/photos'));
      
      if (response.statusCode == 200) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('server_url', url);
        
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => GalleryScreen(serverUrl: url)),
        );
      } else {
        _showError('Server nicht erreichbar');
      }
    } catch (e) {
      _showError('Verbindungsfehler: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showError(String message) {
    showCupertinoDialog(
      context: context,
      builder: (context) => CupertinoAlertDialog(
        title: Text('Fehler'),
        content: Text(message),
        actions: [
          CupertinoDialogAction(
            child: Text('OK'),
            onPressed: () => Navigator.pop(context),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Einstellungen', style: TextStyle(fontWeight: FontWeight.w600)),
      ),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SizedBox(height: 40),
            Text(
              'Server-Adresse',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
            ),
            SizedBox(height: 8),
            CupertinoTextField(
              controller: _urlController,
              placeholder: 'http://192.168.1.100:5000',
              keyboardType: TextInputType.url,
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            SizedBox(height: 24),
            CupertinoButton.filled(
              onPressed: _isLoading ? null : _saveAndContinue,
              child: _isLoading
                  ? CupertinoActivityIndicator(color: Colors.white)
                  : Text('Verbinden'),
            ),
          ],
        ),
      ),
    );
  }
}

// Gallery Screen - iOS-Style Photo Grid
class GalleryScreen extends StatefulWidget {
  final String serverUrl;

  GalleryScreen({required this.serverUrl});

  @override
  _GalleryScreenState createState() => _GalleryScreenState();
}

class _GalleryScreenState extends State<GalleryScreen> {
  List<Photo> _photos = [];
  bool _isLoading = false;
  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _loadPhotos();
  }

  Future<void> _loadPhotos() async {
    setState(() => _isLoading = true);

    try {
      final response = await http.get(
        Uri.parse('${widget.serverUrl}/api/photos?limit=1000'),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _photos = (data['photos'] as List)
              .map((p) => Photo.fromJson(p, widget.serverUrl))
              .toList();
        });
      }
    } catch (e) {
      print('Load error: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _uploadPhoto() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.camera);
    
    if (image == null) return;

    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('${widget.serverUrl}/api/photos/upload'),
      );

      request.files.add(await http.MultipartFile.fromPath('file', image.path));
      request.fields['date'] = DateTime.now().toIso8601String();

      final response = await request.send();

      if (response.statusCode == 201) {
        _loadPhotos(); // Reload
        _showSuccess();
      }
    } catch (e) {
      print('Upload error: $e');
    }
  }

  void _showSuccess() {
    showCupertinoDialog(
      context: context,
      builder: (context) => CupertinoAlertDialog(
        title: Text('Erfolg'),
        content: Text('Foto hochgeladen!'),
        actions: [
          CupertinoDialogAction(
            child: Text('OK'),
            onPressed: () => Navigator.pop(context),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Library', style: TextStyle(fontSize: 34, fontWeight: FontWeight.bold)),
            Text('${_photos.length} Items', style: TextStyle(fontSize: 13, color: Colors.grey)),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.more_horiz),
            onPressed: () {},
          ),
          TextButton(
            onPressed: () {},
            child: Text('Select', style: TextStyle(color: Color(0xFF007AFF))),
          ),
        ],
      ),
      body: _isLoading
          ? Center(child: CupertinoActivityIndicator())
          : GridView.builder(
              padding: EdgeInsets.all(2),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                crossAxisSpacing: 2,
                mainAxisSpacing: 2,
              ),
              itemCount: _photos.length,
              itemBuilder: (context, index) {
                return GestureDetector(
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => PhotoViewScreen(
                          photos: _photos,
                          initialIndex: index,
                          serverUrl: widget.serverUrl,
                        ),
                      ),
                    );
                  },
                  child: Image.network(
                    _photos[index].thumbnailUrl,
                    fit: BoxFit.cover,
                    loadingBuilder: (context, child, progress) {
                      if (progress == null) return child;
                      return Container(
                        color: Colors.grey[200],
                        child: Center(child: CupertinoActivityIndicator()),
                      );
                    },
                  ),
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: _uploadPhoto,
        backgroundColor: Color(0xFF007AFF),
        child: Icon(Icons.camera_alt, color: Colors.white),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
    );
  }
}

// Photo View Screen - Fullscreen with Download
class PhotoViewScreen extends StatefulWidget {
  final List<Photo> photos;
  final int initialIndex;
  final String serverUrl;

  PhotoViewScreen({
    required this.photos,
    required this.initialIndex,
    required this.serverUrl,
  });

  @override
  _PhotoViewScreenState createState() => _PhotoViewScreenState();
}

class _PhotoViewScreenState extends State<PhotoViewScreen> {
  late PageController _pageController;
  late int _currentIndex;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
    _pageController = PageController(initialPage: widget.initialIndex);
  }

  Future<void> _downloadPhoto() async {
    try {
      final photo = widget.photos[_currentIndex];
      final response = await http.get(Uri.parse(photo.fullUrl));
      
      if (response.statusCode == 200) {
        final dir = await getApplicationDocumentsDirectory();
        final file = File('${dir.path}/${photo.filename}');
        await file.writeAsBytes(response.bodyBytes);
        
        showCupertinoDialog(
          context: context,
          builder: (context) => CupertinoAlertDialog(
            title: Text('Gespeichert'),
            content: Text('Foto wurde heruntergeladen'),
            actions: [
              CupertinoDialogAction(
                child: Text('OK'),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
        );
      }
    } catch (e) {
      print('Download error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          PhotoViewGallery.builder(
            pageController: _pageController,
            itemCount: widget.photos.length,
            builder: (context, index) {
              return PhotoViewGalleryPageOptions(
                imageProvider: NetworkImage(widget.photos[index].fullUrl),
                minScale: PhotoViewComputedScale.contained,
                maxScale: PhotoViewComputedScale.covered * 2,
              );
            },
            onPageChanged: (index) {
              setState(() => _currentIndex = index);
            },
          ),
          SafeArea(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // Back Button
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.5),
                      shape: BoxShape.circle,
                    ),
                    child: IconButton(
                      icon: Icon(Icons.arrow_back_ios_new, color: Colors.white),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ),
                  // Download Button
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.5),
                      shape: BoxShape.circle,
                    ),
                    child: IconButton(
                      icon: Icon(Icons.download, color: Colors.white),
                      onPressed: _downloadPhoto,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// Photo Model
class Photo {
  final String filename;
  final String path;
  final String fullUrl;
  final String thumbnailUrl;
  final DateTime date;

  Photo({
    required this.filename,
    required this.path,
    required this.fullUrl,
    required this.thumbnailUrl,
    required this.date,
  });

  factory Photo.fromJson(Map<String, dynamic> json, String serverUrl) {
    return Photo(
      filename: json['filename'],
      path: json['path'],
      fullUrl: '$serverUrl${json['url']}',
      thumbnailUrl: '$serverUrl${json['thumbnail_url']}',
      date: DateTime.parse(json['date']),
    );
  }
}
