// src/components/DocumentUpload.jsx
import React, { useState, useRef } from "react";
import { useUploadDocument } from "../hooks/useDocuments";
import { validateFile } from "../api/documents";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Upload, File, CheckCircle, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const DocumentUpload = ({ onUploadSuccess, onUploadError }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState("");
  const fileInputRef = useRef(null);

  // React Query mutation per upload
  const uploadMutation = useUploadDocument();

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
    e.target.value = "";
  };

  // src/components/DocumentUpload.jsx - AGGIORNA QUESTA PARTE
  const handleFileUpload = async (file) => {
    const validation = validateFile(file);
    if (!validation.valid) {
      setUploadStatus(`Errore: ${validation.error}`);
      if (onUploadError) {
        onUploadError(validation.error);
      }
      return;
    }

    // ✅ DEBUG: Verifica file nel frontend
    console.log("🔍 Frontend sending file:");
    console.log("  - name:", file.name);
    console.log("  - type:", file.type);
    console.log("  - size:", file.size);

    setUploadProgress(0);
    setUploadStatus(`Caricando ${file.name}...`);

    uploadMutation.mutate(
      {
        file,
        onProgress: (progress) => {
          setUploadProgress(progress);
          setUploadStatus(`Caricando ${file.name}... ${progress}%`);
        },
      },
      {
        onSuccess: (result) => {
          // ✅ DEBUG: Verifica response dal backend
          console.log("📥 Backend response:", result);

          // ✅ USA SEMPRE il filename dalla response del backend
          const backendFilename =
            result?.document?.filename || result?.filename;
          const displayName = backendFilename || file.name || "documento";

          console.log("📝 Using filename:", displayName);

          setUploadStatus(`✅ ${displayName} caricato con successo!`);
          setUploadProgress(100);

          if (onUploadSuccess) {
            // ✅ Passa la response completa, non solo il file
            onUploadSuccess(result?.document || result);
          }

          setTimeout(() => {
            setUploadStatus("");
            setUploadProgress(0);
          }, 3000);
        },
        onError: (error) => {
          console.error("💥 Upload error:", error);
          const errorMessage =
            error.response?.data?.detail ||
            error.message ||
            "Errore durante l'upload";
          setUploadStatus(`❌ Errore: ${errorMessage}`);
          setUploadProgress(0);

          if (onUploadError) {
            onUploadError(errorMessage);
          }

          setTimeout(() => {
            setUploadStatus("");
          }, 5000);
        },
      }
    );
  };

  const openFileSelector = () => {
    fileInputRef.current?.click();
  };

  const isUploading = uploadMutation.isPending;

  return (
    <div className="space-y-4">
      <Card
        className={cn(
          "border-2 border-dashed transition-all duration-200 cursor-pointer",
          isDragOver
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50",
          isUploading && "cursor-not-allowed opacity-60"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={!isUploading ? openFileSelector : undefined}
      >
        <CardContent className="flex flex-col items-center justify-center py-12 px-6 text-center">
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            className="hidden"
            accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.gif"
            disabled={isUploading}
          />

          {!isUploading ? (
            <>
              <div className="rounded-full bg-primary/10 p-4 mb-4">
                <Upload className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">
                Trascina i file qui o clicca per selezionare
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                PDF, DOC, TXT, Immagini - Massimo 50MB
              </p>
              <Button variant="outline" size="sm">
                <File className="mr-2 h-4 w-4" />
                Seleziona File
              </Button>
            </>
          ) : (
            <>
              <div className="rounded-full bg-blue-50 p-4 mb-4">
                <Upload className="h-8 w-8 text-blue-600 animate-pulse" />
              </div>
              <h3 className="text-lg font-semibold mb-4">
                Caricamento in corso...
              </h3>
              <div className="w-full max-w-xs">
                <Progress value={uploadProgress} className="h-2" />
                <p className="text-sm text-muted-foreground mt-2">
                  {uploadProgress}%
                </p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Status Messages */}
      {uploadStatus && (
        <Alert
          variant={
            uploadMutation.isError
              ? "destructive"
              : uploadMutation.isSuccess
                ? "default"
                : "default"
          }
          className={
            uploadMutation.isSuccess
              ? "border-green-200 bg-green-50"
              : uploadMutation.isError
                ? "border-red-200 bg-red-50"
                : "border-blue-200 bg-blue-50"
          }
        >
          <div className="flex items-center gap-2">
            {uploadMutation.isSuccess && (
              <CheckCircle className="h-4 w-4 text-green-600" />
            )}
            {uploadMutation.isError && (
              <XCircle className="h-4 w-4 text-red-600" />
            )}
            <AlertDescription
              className={
                uploadMutation.isSuccess
                  ? "text-green-800"
                  : uploadMutation.isError
                    ? "text-red-800"
                    : "text-blue-800"
              }
            >
              {uploadStatus}
            </AlertDescription>
          </div>
        </Alert>
      )}
    </div>
  );
};

export default DocumentUpload;
