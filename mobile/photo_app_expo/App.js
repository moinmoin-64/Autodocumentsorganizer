import React, { useState, useEffect } from 'react';
import {
    StyleSheet,
    View,
    Text,
    FlatList,
    Image,
    TouchableOpacity,
    Dimensions,
    SafeAreaView,
    StatusBar,
    Modal,
    ActivityIndicator,
    Alert,
    TextInput
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as FileSystem from 'expo-file-system';
import { BlurView } from 'expo-blur';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');
const COLUMN_COUNT = 3;
const SPACING = 2;
const ITEM_SIZE = (width - (COLUMN_COUNT + 1) * SPACING) / COLUMN_COUNT;

export default function App() {
    const [serverUrl, setServerUrl] = useState('');
    const [showSettings, setShowSettings] = useState(true);

    useEffect(() => {
        loadServerUrl();
    }, []);

    const loadServerUrl = async () => {
        const url = await AsyncStorage.getItem('serverUrl');
        if (url) {
            setServerUrl(url);
            setShowSettings(false);
        }
    };

    if (showSettings) {
        return <SettingsScreen onSave={(url) => {
            setServerUrl(url);
            setShowSettings(false);
        }} />;
    }

    return <GalleryScreen serverUrl={serverUrl} />;
}

// Settings Screen
function SettingsScreen({ onSave }) {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSave = async () => {
        if (!url.trim()) {
            Alert.alert('Fehler', 'Bitte Server-URL eingeben');
            return;
        }

        setLoading(true);
        try {
            const response = await fetch(`${url}/api/photos`);
            if (response.ok) {
                await AsyncStorage.setItem('serverUrl', url);
                onSave(url);
            } else {
                Alert.alert('Fehler', 'Server nicht erreichbar');
            }
        } catch (error) {
            Alert.alert('Fehler', `Verbindung fehlgeschlagen: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <SafeAreaView style={styles.settingsContainer}>
            <StatusBar barStyle="dark-content" />
            <View style={styles.settingsContent}>
                <Text style={styles.settingsTitle}>Einstellungen</Text>
                <Text style={styles.settingsLabel}>Server-Adresse</Text>
                <TextInput
                    style={styles.settingsInput}
                    placeholder="http://192.168.1.100:5000"
                    value={url}
                    onChangeText={setUrl}
                    keyboardType="url"
                    autoCapitalize="none"
                    autoCorrect={false}
                />
                <TouchableOpacity
                    style={styles.settingsButton}
                    onPress={handleSave}
                    disabled={loading}
                >
                    {loading ? (
                        <ActivityIndicator color="#fff" />
                    ) : (
                        <Text style={styles.settingsButtonText}>Verbinden</Text>
                    )}
                </TouchableOpacity>
            </View>
        </SafeAreaView>
    );
}

// Gallery Screen
function GalleryScreen({ serverUrl }) {
    const [photos, setPhotos] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedPhoto, setSelectedPhoto] = useState(null);
    const [cameraPermission, setCameraPermission] = useState(null);

    useEffect(() => {
        loadPhotos();
        requestPermissions();
    }, []);

    const requestPermissions = async () => {
        const { status } = await ImagePicker.requestCameraPermissionsAsync();
        setCameraPermission(status === 'granted');
    };

    const loadPhotos = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${serverUrl}/api/photos?limit=1000`);
            const data = await response.json();
            setPhotos(data.photos || []);
        } catch (error) {
            Alert.alert('Fehler', 'Fotos konnten nicht geladen werden');
        } finally {
            setLoading(false);
        }
    };

    const handleUpload = async () => {
        if (!cameraPermission) {
            Alert.alert('Berechtigung', 'Kamera-Zugriff benötigt');
            return;
        }

        const result = await ImagePicker.launchCameraAsync({
            mediaTypes: ImagePicker.MediaTypeOptions.Images,
            quality: 0.8,
        });

        if (!result.canceled) {
            await uploadPhoto(result.assets[0].uri);
        }
    };

    const uploadPhoto = async (uri) => {
        try {
            const formData = new FormData();
            formData.append('file', {
                uri,
                type: 'image/jpeg',
                name: 'photo.jpg',
            });
            formData.append('date', new Date().toISOString());

            const response = await fetch(`${serverUrl}/api/photos/upload`, {
                method: 'POST',
                body: formData,
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            if (response.ok) {
                Alert.alert('Erfolg', 'Foto hochgeladen!');
                loadPhotos();
            }
        } catch (error) {
            Alert.alert('Fehler', 'Upload fehlgeschlagen');
        }
    };

    const renderPhoto = ({ item, index }) => (
        <TouchableOpacity
            style={styles.photoItem}
            onPress={() => setSelectedPhoto(item)}
        >
            <Image
                source={{ uri: `${serverUrl}${item.thumbnail_url}` }}
                style={styles.photoImage}
            />
        </TouchableOpacity>
    );

    return (
        <SafeAreaView style={styles.container}>
            <StatusBar barStyle="dark-content" />

            {/* Header */}
            <View style={styles.header}>
                <View>
                    <Text style={styles.headerTitle}>Library</Text>
                    <Text style={styles.headerSubtitle}>{photos.length} Items</Text>
                </View>
                <View style={styles.headerActions}>
                    <TouchableOpacity style={styles.headerButton}>
                        <Ionicons name="ellipsis-horizontal" size={24} color="#007AFF" />
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.headerButton}>
                        <Text style={styles.selectButton}>Select</Text>
                    </TouchableOpacity>
                </View>
            </View>

            {/* Photo Grid */}
            {loading ? (
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="large" color="#007AFF" />
                </View>
            ) : (
                <FlatList
                    data={photos}
                    renderItem={renderPhoto}
                    keyExtractor={(item, index) => index.toString()}
                    numColumns={COLUMN_COUNT}
                    contentContainerStyle={styles.grid}
                    showsVerticalScrollIndicator={false}
                />
            )}

            {/* Actions Container */}
            <View style={styles.actionsContainer}>
                {/* Import Button */}
                <TouchableOpacity
                    style={[styles.actionButton, { marginBottom: 16, backgroundColor: '#34C759' }]}
                    onPress={async () => {
                        const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
                        if (status !== 'granted') {
                            Alert.alert('Berechtigung', 'Zugriff auf Fotos benötigt');
                            return;
                        }

                        const result = await ImagePicker.launchImageLibraryAsync({
                            mediaTypes: ImagePicker.MediaTypeOptions.Images,
                            quality: 0.8,
                        });

                        if (!result.canceled) {
                            await uploadPhoto(result.assets[0].uri);
                        }
                    }}
                >
                    <Ionicons name="images" size={28} color="#fff" />
                </TouchableOpacity>

                {/* Camera Button */}
                <TouchableOpacity
                    style={styles.actionButton}
                    onPress={handleUpload}
                >
                    <Ionicons name="camera" size={28} color="#fff" />
                </TouchableOpacity>
            </View>

            {/* Photo Viewer Modal */}
            {selectedPhoto && (
                <PhotoViewer
                    photo={selectedPhoto}
                    serverUrl={serverUrl}
                    onClose={() => setSelectedPhoto(null)}
                />
            )}
        </SafeAreaView>
    );
}

// Photo Viewer (Fullscreen)
function PhotoViewer({ photo, serverUrl, onClose }) {
    const handleDownload = async () => {
        try {
            const fileUri = FileSystem.documentDirectory + photo.filename;
            await FileSystem.downloadAsync(
                `${serverUrl}${photo.url}`,
                fileUri
            );
            Alert.alert('Erfolg', 'Foto gespeichert');
        } catch (error) {
            Alert.alert('Fehler', 'Download fehlgeschlagen');
        }
    };

    return (
        <Modal visible={true} animationType="fade">
            <View style={styles.viewerContainer}>
                <Image
                    source={{ uri: `${serverUrl}${photo.url}` }}
                    style={styles.viewerImage}
                    resizeMode="contain"
                />

                {/* Controls */}
                <BlurView intensity={80} style={styles.viewerControls}>
                    <TouchableOpacity
                        style={styles.viewerButton}
                        onPress={onClose}
                    >
                        <Ionicons name="arrow-back" size={24} color="#fff" />
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={styles.viewerButton}
                        onPress={handleDownload}
                    >
                        <Ionicons name="download" size={24} color="#fff" />
                    </TouchableOpacity>
                </BlurView>
            </View>
        </Modal>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F2F2F7',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        padding: 16,
        backgroundColor: '#F2F2F7',
    },
    headerTitle: {
        fontSize: 34,
        fontWeight: '700',
        color: '#000',
    },
    headerSubtitle: {
        fontSize: 13,
        color: '#8E8E93',
        marginTop: 2,
    },
    headerActions: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    headerButton: {
        marginLeft: 16,
    },
    selectButton: {
        fontSize: 17,
        color: '#007AFF',
    },
    grid: {
        padding: SPACING,
    },
    photoItem: {
        width: ITEM_SIZE,
        height: ITEM_SIZE,
        margin: SPACING / 2,
        backgroundColor: '#E5E5EA',
    },
    photoImage: {
        width: '100%',
        height: '100%',
    },
    actionsContainer: {
        position: 'absolute',
        bottom: 24,
        right: 24,
        alignItems: 'center',
    },
    actionButton: {
        width: 56,
        height: 56,
        borderRadius: 28,
        backgroundColor: '#007AFF',
        justifyContent: 'center',
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 4,
        elevation: 5,
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    viewerContainer: {
        flex: 1,
        backgroundColor: '#000',
    },
    viewerImage: {
        flex: 1,
    },
    viewerControls: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        flexDirection: 'row',
        justifyContent: 'space-between',
        padding: 16,
        paddingTop: 50,
    },
    viewerButton: {
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: 'rgba(0,0,0,0.5)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    settingsContainer: {
        flex: 1,
        backgroundColor: '#F2F2F7',
    },
    settingsContent: {
        padding: 20,
        paddingTop: 60,
    },
    settingsTitle: {
        fontSize: 28,
        fontWeight: '600',
        marginBottom: 32,
    },
    settingsLabel: {
        fontSize: 17,
        fontWeight: '600',
        marginBottom: 8,
    },
    settingsInput: {
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 10,
        fontSize: 16,
        marginBottom: 24,
    },
    settingsButton: {
        backgroundColor: '#007AFF',
        padding: 16,
        borderRadius: 10,
        alignItems: 'center',
    },
    settingsButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
    },
});
