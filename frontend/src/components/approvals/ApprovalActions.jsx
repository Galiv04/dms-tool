import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Check, X, MessageSquare, Trash2, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useApprovalAction } from "@/hooks/useApprovals";

const ApprovalActions = ({
  onDelete,
  onConfirmDelete,
  isLoading,
  isCreator = false,
  canDecide = false,
  confirmOpen,
  setConfirmOpen,
  // eslint-disable-next-line no-unused-vars
  approval,
  myRecipient, // 🆕 Passa il recipient corrente per ottenere il token
}) => {
  const [showCommentDialog, setShowCommentDialog] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);
  const [comments, setComments] = useState("");

  console.log("🔍 ApprovalActions render:", { canDecide, myRecipient }); // DEBUG

  // 🆕 Usa l'hook per le azioni di approvazione
  const {
    approve,
    reject,
    loading: approvalLoading,
    status,
    isCompleted,
  } = useApprovalAction(myRecipient?.approval_token);

  // Se già completato, mostra stato
  if (isCompleted) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 border">
        <div className="flex items-center space-x-2">
          {status === "approved" ? (
            <Check className="h-5 w-5 text-green-600" />
          ) : (
            <X className="h-5 w-5 text-red-600" />
          )}
          <span className="font-medium">
            Hai {status === "approved" ? "approvato" : "rifiutato"} questa
            richiesta
          </span>
        </div>
      </div>
    );
  }

  const handleAction = (action) => {
    console.log("🔍 handleAction called:", action); // DEBUG
    setPendingAction(action);
    setShowCommentDialog(true);
  };

  const confirmDecision = async () => {
    console.log("🔍 confirmDecision called:", pendingAction, comments); // DEBUG
    try {
      if (pendingAction === "approve") {
        await approve(comments);
      } else {
        await reject(comments);
      }
      setShowCommentDialog(false);
      setComments("");
      setPendingAction(null);
    } catch (error) {
      console.error("🔍 Decision error:", error); // DEBUG
    }
  };

  return (
    <>
      <Separator className="my-4" />

      <div className="flex space-x-3">
        {canDecide && (
          <>
            <Button
              type="button" // 🔧 IMPORTANTE: Evita submit del form
              onClick={() => handleAction("approve")}
              disabled={approvalLoading}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white"
            >
              {approvalLoading ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Check className="h-4 w-4 mr-2" />
              )}
              Approva
            </Button>

            <Button
              type="button" // 🔧 IMPORTANTE: Evita submit del form
              onClick={() => handleAction("reject")}
              disabled={approvalLoading}
              variant="destructive"
              className="flex-1"
            >
              {approvalLoading ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <X className="h-4 w-4 mr-2" />
              )}
              Rifiuta
            </Button>
          </>
        )}

        {isCreator && (
          <Button
            type="button" // 🔧 IMPORTANTE
            onClick={onDelete}
            disabled={isLoading}
            variant="outline"
            className="border-red-200 text-red-600 hover:bg-red-50"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Elimina
          </Button>
        )}
      </div>

      {/* Dialog per commenti */}
      <Dialog open={showCommentDialog} onOpenChange={setShowCommentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {pendingAction === "approve"
                ? "Approva Richiesta"
                : "Rifiuta Richiesta"}
            </DialogTitle>
            <DialogDescription>
              Aggiungi un commento opzionale alla tua decisione.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <Textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Commenti opzionali..."
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowCommentDialog(false)}
            >
              Annulla
            </Button>
            <Button
              type="button"
              onClick={confirmDecision}
              disabled={approvalLoading}
              className={
                pendingAction === "approve"
                  ? "bg-green-600 hover:bg-green-700"
                  : ""
              }
              variant={pendingAction === "reject" ? "destructive" : "default"}
            >
              {approvalLoading ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : pendingAction === "approve" ? (
                <Check className="h-4 w-4 mr-2" />
              ) : (
                <X className="h-4 w-4 mr-2" />
              )}
              Conferma{" "}
              {pendingAction === "approve" ? "Approvazione" : "Rifiuto"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog di conferma eliminazione */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Conferma Eliminazione</DialogTitle>
            <DialogDescription>
              Sei sicuro di voler eliminare questa richiesta di approvazione?
              Questa azione non può essere annullata.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setConfirmOpen(false)}
            >
              Annulla
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={onConfirmDelete}
            >
              Elimina
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ApprovalActions;
