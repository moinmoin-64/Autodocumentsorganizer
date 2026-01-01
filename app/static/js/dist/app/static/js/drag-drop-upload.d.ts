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
export declare class DragDropUpload {
    private dropZone;
    private fileInput;
    private onUpload;
    constructor(dropZoneId: string, fileInputId: string, onUploadCallback: UploadCallback);
    /**
     * Initialize drag-drop functionality
     */
    private init;
    /**
     * Prevent default drag behaviors
     */
    private preventDefaults;
    /**
     * Highlight drop zone
     */
    private highlight;
    /**
     * Remove highlight from drop zone
     */
    private unhighlight;
    /**
     * Handle dropped files
     */
    private handleDrop;
    /**
     * Handle files (convert FileList to File[])
     */
    private handleFiles;
}
/**
 * Upload function signature (to be implemented in app)
 */
export declare function uploadFile(files: File[]): Promise<void>;
//# sourceMappingURL=drag-drop-upload.d.ts.map