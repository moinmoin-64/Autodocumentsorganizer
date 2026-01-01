/**
 * Drag & Drop Upload Handler - TypeScript Version
 */
/**
 * Drag & Drop Upload handler
 */
export class DragDropUpload {
    constructor(dropZoneId, fileInputId, onUploadCallback) {
        this.dropZone = document.getElementById(dropZoneId);
        this.fileInput = document.getElementById(fileInputId);
        this.onUpload = onUploadCallback;
        if (!this.dropZone || !this.fileInput) {
            console.warn(`Drag-drop elements not found: ${dropZoneId}, ${fileInputId}`);
            return;
        }
        this.init();
    }
    /**
     * Initialize drag-drop functionality
     */
    init() {
        // Prevent default drag behaviors
        const events = ['dragenter', 'dragover', 'dragleave', 'drop'];
        events.forEach(eventName => {
            this.dropZone?.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
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
            const files = e.target.files;
            if (files) {
                this.handleFiles(files);
            }
        });
    }
    /**
     * Prevent default drag behaviors
     */
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    /**
     * Highlight drop zone
     */
    highlight() {
        this.dropZone?.classList.add('drag-over');
    }
    /**
     * Remove highlight from drop zone
     */
    unhighlight() {
        this.dropZone?.classList.remove('drag-over');
    }
    /**
     * Handle dropped files
     */
    handleDrop(e) {
        const dt = e.dataTransfer;
        if (!dt)
            return;
        const files = dt.files;
        this.handleFiles(files);
    }
    /**
     * Handle files (convert FileList to File[])
     */
    handleFiles(files) {
        const fileArray = Array.from(files);
        if (fileArray.length > 0) {
            const result = this.onUpload(fileArray);
            if (result instanceof Promise) {
                result.catch(console.error);
            }
        }
    }
}
/**
 * Upload function signature (to be implemented in app)
 */
export async function uploadFile(files) {
    console.log('Files to upload:', files);
    // TODO: Implement actual upload
}
// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initializeDragDrop();
    });
}
else {
    initializeDragDrop();
}
/**
 * Initialize drag-drop upload
 */
function initializeDragDrop() {
    if (typeof uploadFile === 'function') {
        new DragDropUpload('uploadArea', 'fileInput', uploadFile);
    }
}
// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DragDropUpload, uploadFile, initializeDragDrop };
}
//# sourceMappingURL=drag-drop-upload.js.map