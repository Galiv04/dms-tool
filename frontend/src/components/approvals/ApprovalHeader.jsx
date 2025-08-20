import React from "react";
import { Badge } from "@/components/ui/badge";
import { Calendar, FileText, User } from "lucide-react";

const ApprovalHeader = ({ approval }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case "approved":
        return "bg-green-100 text-green-800 border-green-200";
      case "rejected":
        return "bg-red-100 text-red-800 border-red-200";
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "expired":
        return "bg-gray-100 text-gray-800 border-gray-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getCreatorName = () => {
    if (approval.requester?.display_name && approval.requester?.email) {
      const emailPart = approval.requester.email;
      return (
        approval.requester.display_name +
        " - " +
        emailPart.charAt(0).toUpperCase() +
        emailPart.slice(1)
      );
    }
    return "Utente sconosciuto";
  };

  const formatDate = (dateString) => {
    if (!dateString) return "";
    return new Date(dateString).toLocaleDateString("it-IT", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  return (
    <div className="flex justify-between items-start mb-4">
      <div className="flex-1 min-w-0">
        {/* 🎯 TITOLO PRINCIPALE - NON PIÙ FILENAME */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2 leading-tight">
          {approval.title}
        </h3>

        <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
          {/* 👤 RICHIEDENTE - SOLO NOME, NO TITOLO */}
          <div className="flex items-center">
            <User className="h-4 w-4 mr-1" />
            <span>Da: {getCreatorName()}</span>
          </div>

          {/* 📄 DOCUMENTO - NOME FILE SEPARATO */}
          {approval.document && (
            <div className="flex items-center">
              <FileText className="h-4 w-4 mr-1" />
              <span className="truncate max-w-xs">
                {approval.document.original_filename ||
                  approval.document.filename}
              </span>
            </div>
          )}

          {/* 📅 DATA CREAZIONE */}
          <div className="flex items-center">
            <Calendar className="h-4 w-4 mr-1" />
            <span>{formatDate(approval.created_at)}</span>
          </div>
        </div>
      </div>

      {/* 🏷️ STATUS BADGE */}
      <div className="flex items-center space-x-2 ml-4">
        <Badge className={getStatusColor(approval.status)}>
          {approval.status === "pending" && "In Attesa"}
          {approval.status === "approved" && "Approvato"}
          {approval.status === "rejected" && "Rifiutato"}
          {approval.status === "expired" && "Scaduto"}
        </Badge>
      </div>
    </div>
  );
};

export default ApprovalHeader;
