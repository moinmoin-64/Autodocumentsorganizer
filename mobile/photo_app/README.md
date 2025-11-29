# Flutter Photo Manager App - Build & Deploy Guide

## 📱 Überblick

Diese Flutter App ermöglicht das Hochladen und Verwalten von Fotos direkt vom Smartphone mit iOS-ähnlichem Design.

## 🛠️ Installation & Setup

### Voraussetzungen
- Flutter SDK (3.0+): https://flutter.dev/docs/get-started/install
- Android Studio (für Android) oder Xcode (für iOS)
- Git

### 1. Flutter SDK installieren
```bash
# Windows (mit Chocolatey)
choco install flutter

# macOS (mit Homebrew)
brew install flutter

# Oder manuell von flutter.dev herunterladen
```

### 2. Projekt einrichten
```bash
cd mobile/photo_app

# Dependencies installieren
flutter pub get

# Flutter Doctor ausführen
flutter doctor
```

## 🔨 App builden

### Android APK (zum Testen)
```bash
flutter build apk --release

# APK befindet sich in:
# build/app/outputs/flutter-apk/app-release.apk
```

### Android App Bundle (für Play Store)
```bash
flutter build appbundle --release

# AAB befindet sich in:
# build/app/outputs/bundle/release/app-release.aab
```

### iOS App (benötigt macOS + Xcode)
```bash
flutter build ios --release

# Dann in Xcode öffnen und archivieren
open ios/Runner.xcworkspace
```

## 📦 App verteilen

### Option 1: Direkte APK-Installation (Einfachste Methode)

1. **APK builden:**
```bash
flutter build apk --release
```

2. **APK auf Server kopieren:**
```bash
# APK zum öffentlichen Ordner kopieren
cp build/app/outputs/flutter-apk/app-release.apk ../../app/static/download/photo-app.apk
```

3. **QR-Code nutzen:**
- Öffne `http://your-server:5000/photos.html`
- Klicke auf QR-Button (unten links)
- Scanne QR-Code mit Handy
- APK herunterladen und installieren
- ⚠️ Hinweis: "Unbekannte Quellen" in Android-Einstellungen aktivieren

### Option 2: Google Play Store (Professionell)

1. **Google Play Console Account erstellen:**
- https://play.google.com/console
- Einmalige Gebühr: $25

2. **App Bundle hochladen:**
```bash
flutter build appbundle --release
```

3. **In Play Console hochladen:**
- Neue App erstellen
- App Bundle hochladen
- Store Listing ausfüllen
- Veröffentlichen

### Option 3: Apple App Store (für iOS)

1. **Apple Developer Account:**
- https://developer.apple.com
- Jährliche Gebühr: $99

2. **App in Xcode vorbe reiten:**
```bash
flutter build ios --release
open ios/Runner.xcworkspace
```

3. **In App Store Connect hochladen:**
- Product → Archive
- Distribute App → App Store Connect
- Upload

## ⚙️ Konfiguration

### Server-URL ändern
Die App fragt beim ersten Start nach der Server-URL. Alternativ kann die Default-URL im Code gesetzt werden:

In `lib/main.dart`:
```dart
final prefs = await SharedPreferences.getInstance();
final url = prefs.getString('server_url') ?? 'http://192.168.1.100:5000'; // Hier ändern
```

### App-Icon anpassen
```bash
# Icon (mindestens 1024x1024) nach flutter_launcher_icons.yaml kopieren
flutter pub run flutter_launcher_icons:main
```

### App-Name ändern

**Android (`android/app/src/main/AndroidManifest.xml`):**
```xml
<application
    android:label="Photo Manager"  <!-- Hier ändern -->
```

**iOS (`ios/Runner/Info.plist`):**
```xml
<key>CFBundleName</key>
<string>Photo Manager</string>  <!-- Hier ändern -->
```

## 🧪 Testen

### Auf echtem Gerät testen
```bash
# Android
flutter run --release

# iOS (macOS nur)
flutter run --release -d iPhone
```

### Emulator verwenden
```bash
# Android Emulator starten
flutter emulators --launch <emulator_name>

# App starten
flutter run
```

## 🔐 Sicherheit & Best Practices

### SSL/HTTPS verwenden
Für Produktion unbedingt HTTPS nutzen:

1. **Nginx Reverse Proxy einrichten:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
    }
}
```

2. **URL in App ändern:**
```
https://your-domain.com statt http://192.168.1.100:5000
```

### Android-Berechtigungen
Bereits konfiguriert in `android/app/src/main/AndroidManifest.xml`:
- Internet-Zugriff
- Kamera
- Speicher

## 📱 Features

- ✅ **iOS-Style Design** (Photo Grid wie iOS 18)
- ✅ **Foto-Upload** von Kamera oder Galerie
- ✅ **Automatische Organisation** nach Datum (Jahr/Monat/Tag)
- ✅ **Vollbildansicht** mit Zoom & Swipe
- ✅ **Download** auf Gerät
- ✅ **Server-Konfiguration** in App

## 🐛 Troubleshooting

### "Couldn't resolve host"
- Server-URL überprüfen
- Firewall-Einstellungen checken
- Gleiche WiFi-Netzwerk nutzen

### "Permission denied" beim Upload
- Kamera-/Speicher-Berechtigungen in Android-Einstellungen prüfen

### App stürzt ab
```bash
# Logs anzeigen
flutter logs

# oder
adb logcat | grep flutter
```

## 📞 Support

Bei Problemen:
1. `flutter doctor` ausführen
2. Logs prüfen (`flutter logs`)
3. GitHub Issues: [Link zu deinem Repo]

---

**Made with Flutter & ❤️**
