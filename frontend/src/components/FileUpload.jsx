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
  const [duplicateFile, setDuplicateFile] = useState(null);
  const [duplicateSession, setDuplicateSession] = useState(null);

  const selectSession = useCallback((result) => {
    setFileName(result.filename);
    setUploadProgress(100);
    setUploadState("success");
    setDuplicateFile(null);
    setDuplicateSession(null);
    onUploadSuccess({
      sessionId: result.session_id,
      filename: result.filename,
      chunksStored: result.chunks_stored,
      documentVersion: result.document_version,
      message: result.message,
    });
  }, [onUploadSuccess]);

  const processFile = useCallback(async (file, forceReprocess = false) => {
    setFileName(file.name);
    setUploadState("uploading");
    setErrorMessage("");
    setUploadProgress(0);

    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => Math.min(prev + 10, 85));
    }, 300);

    try {
      const result = await uploadPDF(file, { forceReprocess });
      clearInterval(progressInterval);

      if (result.duplicate && !forceReprocess) {
        setUploadProgress(0);
        setUploadState("duplicate");
        setDuplicateFile(file);
        setDuplicateSession(result);
        return;
      }

      selectSession(result);
    } catch (error) {
      clearInterval(progressInterval);
      setUploadState("error");
      setErrorMessage(error.message || "Upload failed. Please try again.");
    }
  }, [selectSession]);

  const onDrop = useCallback(async (acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      setUploadState("error");
      setErrorMessage("Only PDF files are accepted. Please try again.");
      return;
    }
    const file = acceptedFiles[0];
    if (file) await processFile(file);
  }, [processFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
    disabled: uploadState === "uploading" || uploadState === "duplicate",
  });

  const handleReset = () => {
    setUploadState("idle");
    setFileName("");
    setUploadProgress(0);
    setErrorMessage("");
    setDuplicateFile(null);
    setDuplicateSession(null);
  };

  const handleUseExisting = () => {
    if (duplicateSession) selectSession(duplicateSession);
  };

  const handleReprocess = () => {
    if (duplicateFile) processFile(duplicateFile, true);
  };

  return (
    <div className="w-full">
      {uploadState === "duplicate" ? (
        <div className="glass rounded-xl p-4 border border-amber-500/30 bg-amber-500/5">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-500/20 flex items-center justify-center flex-shrink-0">
              <AlertCircle size={18} className="text-amber-400" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-amber-300">PDF already indexed</p>
              <p className="text-xs text-slate-500 mt-1 truncate" title={fileName}>{fileName}</p>
              <p className="text-xs text-slate-500 mt-2">
                {duplicateSession?.message || "Use the existing index to avoid processing it again."}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-4">
            <button
              type="button"
              onClick={handleUseExisting}
              className="rounded-lg px-3 py-2 text-xs font-medium bg-brand-500 text-white hover:bg-brand-600 transition-colors"
            >
              Use existing
            </button>
            <button
              type="button"
              onClick={handleReprocess}
              className="rounded-lg px-3 py-2 text-xs font-medium border border-surface-500 text-slate-400 hover:text-slate-200 hover:bg-surface-700 transition-colors"
            >
              Process again
            </button>
          </div>
          <button
            type="button"
            onClick={handleReset}
            className="w-full mt-2 py-1 text-xs text-slate-600 hover:text-slate-400 transition-colors"
          >
            Cancel
          </button>
        </div>
      ) : uploadState === "success" ? (
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
