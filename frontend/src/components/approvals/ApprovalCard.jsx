import React, { useState } from "react";
import { getRelativeTime, formatLocalDateTime } from "../../utils/dateUtils";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Ban,
  Trash2,
  Download,
  MessageSquare,
  Loader2,
} from "lucide-react";
import { useDeleteApproval, useApproveByToken } from "../../hooks/useApprovals";
import { toast } from "sonner";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "../../contexts/AuthContext";
import ConfirmDialog from "../ui/ConfirmDialog"; // 🔧 Nostro componente personalizzato
import { useHandleDownloadDocument } from "../../utils/handleDownloadDocument";

const ApprovalCard = ({
  approval,
  onClick,
  showActions = false,
  showDelete = true,
  onDeleteSuccess,
}) => {
  const { user } = useAuth();

  const [isConfirmOpen, setConfirmOpen] = useState(false); // 🔧 State per modal
  const [showCommentForm, setShowCommentForm] = useState(false);
  const [comments, setComments] = useState("");
  const [pendingDecision, setPendingDecision] = useState(null);

  // ... tutti i tuoi metodi esistenti (getStatusIcon, formatDateTime, ecc.) rimangono uguali ...

  const getStatusIcon = (status) => {
    switch (status) {
      case "pending":
        return <Clock className="h-4 w-4" />;
      case "approved":
        return <CheckCircle className="h-4 w-4" />;
      case "rejected":
        return <XCircle className="h-4 w-4" />;
      case "expired":
        return <AlertCircle className="h-4 w-4" />;
      case "cancelled":
        return <Ban className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getStatusVariant = (status) => {
    switch (status) {
      case "pending":
        return "default";
      case "approved":
        return "success";
      case "rejected":
        return "destructive";
      case "expired":
        return "secondary";
      case "cancelled":
        return "outline";
      default:
        return "default";
    }
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return "Data non disponibile";
    return getRelativeTime(dateString);
  };

  const getFullDateTime = (dateString) => {
    if (!dateString) return "Data non disponibile";
    return formatLocalDateTime(dateString);
  };

  const getApprovalProgress = () => {
    const total = approval.recipients?.length || 0;
    const approved =
      approval.recipients?.filter((r) => r.status === "approved").length || 0;
    return {
      approved,
      total,
      percentage: total > 0 ? (approved / total) * 100 : 0,
    };
  };

  // Mutation decisione come recipient
  const approveMutation = useApproveByToken();

  // Mutation per cancellazione da creator
  const deleteApproval = useDeleteApproval();

  // Trova il recipient corrispondente all'utente loggato
  const myRecipient = approval.recipients?.find(
    (r) => r.recipient_email === user?.email
  );

  // Recipient pending può agire SOLO se la richiesta è pending!
  const canDecide =
    showActions &&
    myRecipient &&
    myRecipient.status === "pending" &&
    approval.status === "pending";

  // Handler per approvazione/rifiuto
  const handleDecision = async (approved) => {
    if (!myRecipient?.approval_token) return;
    setPendingDecision(approved ? "approved" : "rejected");
    approveMutation.mutate(
      {
        token: myRecipient.approval_token,
        approved,
        comments: comments.trim(),
      },
      {
        onSuccess: () => {
          setShowCommentForm(false);
          setComments("");
          setPendingDecision(null);
        },
        onError: () => setPendingDecision(null),
      }
    );
  };

  // 🔧 Handler per aprire conferma eliminazione
  const handleDeleteClick = (e) => {
    e.stopPropagation();

    // // 🔍 DEBUG: Vediamo cosa contiene approval
    // console.log("🔍 DEBUG approval object:", approval);
    // console.log("🔍 DEBUG document info:", {
    //   "approval.document": approval.document,
    //   "approval.document?.original_filename":
    //     approval.document?.original_filename,
    //   "approval.document?.filename": approval.document?.filename,
    // });
    // console.log("🔍 DEBUG recipients info:", {
    //   "approval.recipients": approval.recipients,
    //   "approval.recipients?.length": approval.recipients?.length,
    //   "approval.recipient_count": approval.recipient_count,
    // });

    setConfirmOpen(true);
  };

  // 🔧 Handler per confermare eliminazione
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
      // Non chiudere il modal in caso di errore
    }
  };

  // 🔧 Handler per cancellare eliminazione
  const handleCancelDelete = () => {
    if (!deleteApproval.isPending) {
      setConfirmOpen(false);
    }
  };

  // Verifica se l'utente può eliminare
  // Cerca questa logica nel componente:
  const canDelete =
    showDelete &&
    approval.status === "pending" &&
    user?.id === approval.requester_id;

  console.log("🔍 canDelete logic:", {
    showDelete,
    status: approval.status,
    statusCheck: approval.status === "pending",
    userIdExists: !!user?.id,
    requesterIdExists: !!approval.requester_id,
    idsMatch: user?.id === approval.requester_id,
    finalCanDelete: canDelete,
  });

  const progress = getApprovalProgress();

  const { handleDownload } = useHandleDownloadDocument();

  return (
    <TooltipProvider>
      <Card
        className={`cursor-pointer transition-all hover:shadow-md ${
          approval.status === "expired" ? "opacity-75" : ""
        }`}
        onClick={() => onClick?.(approval)}
      >
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <CardTitle className="text-lg">
                {approval.title ||
                  approval.document?.filename ||
                  "Richiesta Approvazione"}
              </CardTitle>
              <CardDescription>
                Richiedente:{" "}
                {approval.requester?.display_name ||
                  approval.requester?.email ||
                  "Non specificato"}
              </CardDescription>
            </div>
            <Badge
              variant={getStatusVariant(approval.status)}
              className="flex items-center gap-1"
            >
              {getStatusIcon(approval.status)}
              {approval.status.toUpperCase()}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Date Information */}
          <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
            <div>
              <span className="font-medium">Creata: </span>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="cursor-help border-b border-dotted">
                    {formatDateTime(approval.created_at)}
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{getFullDateTime(approval.created_at)}</p>
                </TooltipContent>
              </Tooltip>
            </div>

            {approval.expires_at && (
              <div>
                <span className="font-medium">Scade: </span>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="cursor-help border-b border-dotted">
                      {formatDateTime(approval.expires_at)}
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{getFullDateTime(approval.expires_at)}</p>
                  </TooltipContent>
                </Tooltip>
              </div>
            )}
          </div>

          {/* Description */}
          {approval.description && (
            <div className="p-3 bg-muted rounded-md">
              <p className="text-sm italic">{approval.description}</p>
            </div>
          )}

          {/* Progress */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-sm">
              <span>
                Approvazioni: {progress.approved}/{progress.total}
              </span>
              {approval.approval_type && (
                <span className="text-xs text-muted-foreground">
                  (
                  {approval.approval_type === "all"
                    ? "Tutti devono approvare"
                    : "Basta una approvazione"}
                  )
                </span>
              )}
            </div>
            <Progress value={progress.percentage} className="h-2" />
          </div>

          {/* Recipients */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium">
              Approvatori ({approval.recipients?.length || 0}):
            </h4>
            <div className="flex flex-wrap gap-2">
              {approval.recipients?.map((recipient, index) => (
                <div
                  key={recipient.id || index}
                  className="flex items-center gap-2 p-2 rounded-md bg-muted/50 text-xs"
                >
                  <Avatar className="h-6 w-6">
                    <AvatarFallback className="text-xs">
                      {(
                        recipient.recipient_name ||
                        recipient.recipient_email ||
                        "U"
                      )
                        .charAt(0)
                        .toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <span className="max-w-[100px] truncate">
                    {recipient.recipient_name || recipient.recipient_email}
                  </span>
                  <div className="ml-auto">
                    {getStatusIcon(recipient.status)}
                  </div>
                  {recipient.responded_at && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className="text-xs opacity-60 cursor-help">
                          {formatDateTime(recipient.responded_at)}
                        </span>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>
                          Risposto: {getFullDateTime(recipient.responded_at)}
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Decisione recipient */}
          {canDecide && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
              <h4 className="font-semibold mb-3 flex items-center">
                <MessageSquare className="w-4 h-4 mr-2" />
                La tua decisione richiesta
              </h4>
              {!showCommentForm ? (
                <div className="flex gap-2 pt-3 border-t">
                  <Button
                    onClick={() => {
                      setShowCommentForm(true);
                      setPendingDecision("approved");
                    }}
                    disabled={approveMutation.isPending}
                    size="sm"
                    className="flex-1"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Approva
                  </Button>
                  <Button
                    onClick={() => {
                      setShowCommentForm(true);
                      setPendingDecision("rejected");
                    }}
                    disabled={approveMutation.isPending}
                    variant="destructive"
                    size="sm"
                    className="flex-1"
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Rifiuta
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    {pendingDecision === "approved" ? (
                      <>
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-green-600">Approvazione</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-4 h-4 text-red-600" />
                        <span className="text-red-600">Rifiuto</span>
                      </>
                    )}
                  </div>
                  <Textarea
                    placeholder="Aggiungi commenti opzionali alla tua decisione..."
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    rows={3}
                  />
                  <div className="flex gap-2">
                    <Button
                      onClick={() =>
                        handleDecision(pendingDecision === "approved")
                      }
                      disabled={approveMutation.isPending}
                    >
                      {approveMutation.isPending ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Invio...
                        </>
                      ) : (
                        `Conferma ${pendingDecision === "approved" ? "Approvazione" : "Rifiuto"}`
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowCommentForm(false);
                        setComments("");
                        setPendingDecision(null);
                      }}
                      disabled={approveMutation.isPending}
                    >
                      Annulla
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 🔧 DELETE BUTTON - Con nostro ConfirmDialog */}
          {canDelete && (
            <div className="pt-3 border-t">
              <Button
                variant="outline"
                size="sm"
                onClick={handleDeleteClick}
                className="w-full text-destructive hover:text-destructive hover:bg-destructive/10"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Elimina Richiesta
              </Button>
            </div>
          )}

          {/* Completion info */}
          {approval.completed_at && (
            <div className="pt-3 border-t text-xs text-muted-foreground text-right">
              Completata:{" "}
              <span
                className="cursor-help"
                title={getFullDateTime(approval.completed_at)}
              >
                {formatDateTime(approval.completed_at)}
              </span>
              {approval.completion_reason && ` (${approval.completion_reason})`}
            </div>
          )}

          {approval.document && (
            <div className="my-2 space-y-2">
              <div>
                <strong>Documento:</strong>{" "}
                {approval.document.original_filename}
              </div>
              <Button
                variant="outline"
                onClick={() => handleDownload(approval.document)}
                className="mr-2"
              >
                <Download className="h-4 w-4 mr-1" />
                Scarica
              </Button>
              {approval.document.content_type === "application/pdf" && (
                <div style={{ height: 320, border: "1px solid #eee" }}>
                  <iframe
                    src={`/api/documents/${approval.document.id}/preview`}
                    title="Anteprima documento"
                    width="100%"
                    height="100%"
                    style={{ border: 0 }}
                  />
                </div>
              )}
              {/* Altri tipi di file: usa <img /> per immagini, ecc. */}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 🔧 CONFIRM DIALOG - Nostro componente personalizzato */}
      <ConfirmDialog
        isOpen={isConfirmOpen}
        title="Conferma Eliminazione"
        message={`Sei sicuro di voler eliminare la richiesta di approvazione "${approval.title}"?`}
        details={
          <div>
            <p>
              <strong>Documento:</strong>{" "}
              {approval.document?.original_filename ||
                approval.document?.filename ||
                "N/A"}
            </p>
            <p>
              <strong>Destinatari:</strong>{" "}
              {approval.recipients?.length || approval.recipient_count || 0}
            </p>
            <p>
              <strong>Stato:</strong> {approval.status}
            </p>
            <br />
            <p style={{ color: "#dc2626", fontWeight: "500" }}>
              ⚠️ Questa azione non può essere annullata. Tutti i destinatari non
              potranno più accedere alla richiesta.
            </p>
          </div>
        }
        type="danger"
        confirmText="Elimina Definitivamente"
        cancelText="Annulla"
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        isLoading={deleteApproval.isPending}
      />
    </TooltipProvider>
  );
};

export default ApprovalCard;
