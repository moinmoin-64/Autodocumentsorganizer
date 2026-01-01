/**
 * Drag & Drop Upload Handler - TypeScript Version
 */

/**
 * File upload event callback
 */
export type UploadCallback = (files: File[]) => Promise<void> | void;

/**
 * Drag & Drop Upload handler
 */
export class DragDropUpload {
    private dropZone: HTMLElement | null;
    private fileInput: HTMLInputElement | null;
    private onUpload: UploadCallback;

    constructor(dropZoneId: string, fileInputId: string, onUploadCallback: UploadCallback) {
        this.dropZone = document.getElementById(dropZoneId);
        this.fileInput = document.getElementById(fileInputId) as HTMLInputElement;
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
    private init(): void {
        // Prevent default drag behaviors
        const events = ['dragenter', 'dragover', 'dragleave', 'drop'] as const;
        
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
            const files = (e.target as HTMLInputElement).files;
            if (files) {
                this.handleFiles(files);
            }
        });
    }

    /**
     * Prevent default drag behaviors
     */
    private preventDefaults(e: DragEvent): void {
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
export async function uploadFile(files: File[]): Promise<void> {
    console.log('Files to upload:', files);
    // TODO: Implement actual upload
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
        new DragDropUpload('uploadArea', 'fileInput', uploadFile);
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DragDropUpload, uploadFile, initializeDragDrop };
}
