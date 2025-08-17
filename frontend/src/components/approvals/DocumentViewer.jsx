// src/components/approvals/DocumentViewer.jsx
import React from "react";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { useHandleDownloadDocument } from "@/utils/handleDownloadDocument";
import DocumentBlobPreview from "@/components/approvals/DocumentBlobPreview";

const DocumentViewer = ({
  approval,
  showForRecipient = false,
  currentUserEmail,
}) => {
  const { handleDownload } = useHandleDownloadDocument();

  const isRecipient = approval.recipients?.some(
    (r) => r.recipient_email === currentUserEmail
  );

  if (!approval.document || !showForRecipient || !isRecipient) {
    return null;
  }

  return (
    <div className="my-4 space-y-3 p-4 bg-gray-50 rounded-lg border">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-900">
            Documento allegato:
          </p>
          <p className="text-sm text-gray-600">
            {approval.document.original_filename || approval.document.filename}
          </p>
        </div>

        <Button
          variant="outline"
          onClick={() => handleDownload(approval.document)}
          className="shrink-0"
        >
          <Download className="h-4 w-4 mr-2" />
          Scarica
        </Button>
      </div>

      <DocumentBlobPreview
        document={approval.document}
        showPreview={approval.document?.content_type === "application/pdf"}
      />
    </div>
  );
};

export default DocumentViewer;
