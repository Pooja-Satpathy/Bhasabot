// src/components/FileUpload.jsx
import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, CheckCircle, Loader2, X, AlertCircle } from "lucide-react";
import { uploadPDF } from "../api/client";

const FileUpload = ({ onUploadSuccess, currentFile }) => {
  const [uploadState, setUploadState] = useState("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [fileName, setFileName] = useState(currentFile || "");

  const onDrop = useCallback(async (acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      setUploadState("error");
      setErrorMessage("Only PDF files are accepted. Please try again.");
      return;
    }
    const file = acceptedFiles[0];
    if (!file) return;
    setFileName(file.name);
    setUploadState("uploading");
    setErrorMessage("");
    setUploadProgress(0);
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => Math.min(prev + 10, 85));
    }, 300);
    try {
      const result = await uploadPDF(file);
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadState("success");
      onUploadSuccess({ sessionId: result.session_id, filename: result.filename, chunksStored: result.chunks_stored, message: result.message });
    } catch (error) {
      clearInterval(progressInterval);
      setUploadState("error");
      setErrorMessage(error.message || "Upload failed. Please try again.");
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
    disabled: uploadState === "uploading",
  });

  const handleReset = () => {
    setUploadState("idle");
    setFileName("");
    setUploadProgress(0);
    setErrorMessage("");
  };

  return (
    <div className="w-full">
      {uploadState === "success" ? (
        <div id="upload-success-panel" className="glass rounded-xl p-4 border border-emerald-500/30 bg-emerald-500/5">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                <CheckCircle size={18} className="text-emerald-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-emerald-300">PDF Loaded</p>
                <p className="text-xs text-slate-400 mt-0.5 max-w-[180px] truncate">{fileName}</p>
              </div>
            </div>
            <button id="upload-new-file-btn" onClick={handleReset} className="p-1.5 rounded-lg hover:bg-surface-600 transition-colors text-slate-500 hover:text-slate-300" title="Upload a different file" aria-label="Upload a different file">
              <X size={14} />
            </button>
          </div>
        </div>
      ) : (
        <div
          {...getRootProps()}
          id="pdf-dropzone"
          className={`relative cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition-all duration-300 select-none ${
            isDragActive ? "border-brand-400 bg-brand-600/10 drop-active" : "border-surface-500 hover:border-brand-500/60 hover:bg-surface-700/40"
          } ${uploadState === "uploading" ? "pointer-events-none opacity-80" : ""} ${uploadState === "error" ? "border-red-500/50 bg-red-500/5" : ""}`}
          aria-label="PDF upload dropzone"
        >
          <input {...getInputProps()} id="pdf-file-input" aria-label="Choose PDF file" />
          <div className="flex flex-col items-center gap-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              uploadState === "uploading" ? "bg-brand-600/20" : uploadState === "error" ? "bg-red-500/20" : "bg-brand-600/15"
            }`}>
              {uploadState === "uploading" ? <Loader2 size={22} className="text-brand-400 animate-spin" />
                : uploadState === "error" ? <AlertCircle size={22} className="text-red-400" />
                : isDragActive ? <Upload size={22} className="text-brand-400 animate-bounce" />
                : <FileText size={22} className="text-brand-400" />}
            </div>
            {uploadState === "uploading" ? (
              <div className="space-y-2 w-full">
                <p className="text-sm text-brand-300 font-medium">Processing PDF...</p>
                <div className="w-full bg-surface-600 rounded-full h-1.5">
                  <div className="bg-gradient-to-r from-brand-500 to-purple-500 h-1.5 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                </div>
                <p className="text-xs text-slate-500">Extracting text and generating embeddings...</p>
              </div>
            ) : uploadState === "error" ? (
              <div>
                <p className="text-sm text-red-400 font-medium">Upload Failed</p>
                <p className="text-xs text-slate-500 mt-1">{errorMessage}</p>
                <p className="text-xs text-brand-400 mt-2 font-medium">Click to try again</p>
              </div>
            ) : isDragActive ? (
              <p className="text-sm text-brand-300 font-medium">Drop your PDF here!</p>
            ) : (
              <div>
                <p className="text-sm font-medium text-slate-300">Drag & drop a PDF here</p>
                <p className="text-xs text-slate-500 mt-1">or <span className="text-brand-400 font-medium">click to browse</span></p>
                <p className="text-xs text-slate-600 mt-3">PDF files up to 50MB • Any language</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
