// src/components/approvals/ApprovalCard.jsx
import React, { useState } from "react";
import { Card } from "@/components/ui/card";
import ApprovalHeader from "./ApprovalHeader";
import ApprovalDetails from "./ApprovalDetails";
import RecipientsList from "./RecipientsList";
import ApprovalActions from "./ApprovalActions";
import CommentsSection from "./CommentsSection";
import DocumentViewer from "./DocumentViewer"; // 🆕 NUOVO IMPORT
import { useApproveByToken, useDeleteApproval } from "@/hooks/useApprovals";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";

const ApprovalCard = ({
  approval,
  showActions = false,
  variant = "default",
}) => {
  const { user } = useAuth();
  const approveMutation = useApproveByToken();
  const deleteApproval = useDeleteApproval();
  const [confirmOpen, setConfirmOpen] = useState(false);

  // Trova il recipient corrente
  const myRecipient = approval.recipients?.find(
    (r) => r.recipient_email === user?.email
  );

  const isCreator =
    user?.email === approval.requester?.email ||
    user?.id === approval.requester?.id ||
    user?.id === approval.requester_id;

  const canDecideAsRecipient =
    showActions &&
    myRecipient &&
    myRecipient.status === "pending" &&
    approval.status === "pending";

  const canDeleteAsCreator =
    showActions && isCreator && approval.status === "pending";

  const handleDecision = (approved, comments = "") => {
    if (!myRecipient?.approval_token) return;

    approveMutation.mutate({
      token: myRecipient.approval_token,
      approved,
      comments,
    });
  };

  const handleConfirmDelete = async () => {
    try {
      await deleteApproval.mutateAsync(approval.id);
      toast.success(`Richiesta "${approval.title}" eliminata con successo`);
      setConfirmOpen(false);
    } catch (error) {
      console.error("Delete error:", error);
      toast.error(
        error.response?.data?.detail ||
          error.message ||
          "Errore durante l'eliminazione"
      );
    }
  };

  console.log("🔍 Debug myRecipient:", myRecipient);
  console.log("🔍 Debug myRecipient token:", myRecipient?.approval_token);

  return (
    <Card className="w-full mb-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="p-6">
        <ApprovalHeader approval={approval} variant={variant} />

        <ApprovalDetails approval={approval} myRecipient={myRecipient} />

        <RecipientsList
          recipients={approval.recipients}
          currentUserEmail={user?.email}
          variant={variant}
        />

        {/* 🆕 DOCUMENTO VIEWER - Solo per recipients */}
        <DocumentViewer
          approval={approval}
          showForRecipient={!isCreator}
          currentUserEmail={user?.email}
        />

        {approval.recipients?.some((r) => r.comments) && (
          <CommentsSection recipients={approval.recipients} />
        )}

        {(canDecideAsRecipient || canDeleteAsCreator) && (
          <ApprovalActions
            onDecision={handleDecision}
            onDelete={() => setConfirmOpen(true)}
            onConfirmDelete={handleConfirmDelete}
            isLoading={approveMutation.isLoading || deleteApproval.isLoading}
            isCreator={isCreator && showActions}
            canDecide={canDecideAsRecipient}
            approval={approval}
            myRecipient={myRecipient} // 🆕 AGGIUNGI QUESTA PROP
            confirmOpen={confirmOpen}
            setConfirmOpen={setConfirmOpen}
          />
        )}
      </div>
    </Card>
  );
};

export default ApprovalCard;
