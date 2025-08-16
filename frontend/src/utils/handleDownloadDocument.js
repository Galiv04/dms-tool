import { useDownloadDocument } from "../hooks/useDocuments";

// Custom hook per scaricare un documento ovunque nel progetto
export const useHandleDownloadDocument = () => {
  const downloadMutation = useDownloadDocument();

  // Questa funzione riceve sempre l'oggetto documento (con id, filename, original_filename, ecc)
  const handleDownload = (document) => {
    if (!document?.id) return;
    const filename = document.original_filename || document.filename || "documento";
    downloadMutation.mutate({
      documentId: document.id,
      filename
    });
  };

  return { handleDownload, downloadMutation };
};
