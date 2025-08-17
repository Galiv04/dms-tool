// src/components/approvals/ApprovalActions.jsx
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { Check, X, MessageSquare, Trash2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const ApprovalActions = ({ 
  onDecision, 
  onDelete,
  onConfirmDelete,
  isLoading,
  isCreator = false,
  canDecide = false,
  confirmOpen,
  setConfirmOpen
}) => {
  const [showCommentDialog, setShowCommentDialog] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);
  const [comments, setComments] = useState('');

  const handleAction = (action) => {
    setPendingAction(action);
    setShowCommentDialog(true);
  };

  const confirmDecision = () => {
    const approved = pendingAction === 'approve';
    onDecision && onDecision(approved, comments);
    setShowCommentDialog(false);
    setComments('');
    setPendingAction(null);
  };

  return (
    <>
      <Separator className="mb-4" />
      
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <MessageSquare className="h-4 w-4" />
          <span>
            {isCreator && onDelete && 'Gestisci la tua richiesta'}
            {canDecide && onDecision && 'La tua decisione è richiesta'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Pulsante Delete per Creator */}
          {isCreator && onDelete && (
            <Button
              variant="outline"
              size="sm"
              onClick={onDelete}
              disabled={isLoading}
              className="border-red-200 text-red-700 hover:bg-red-50 hover:border-red-300"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Elimina Richiesta
            </Button>
          )}

          {/* Pulsanti Approva/Rifiuta per Recipient */}
          {canDecide && onDecision && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction('reject')}
                disabled={isLoading}
                className="border-red-200 text-red-700 hover:bg-red-50 hover:border-red-300"
              >
                <X className="h-4 w-4 mr-2" />
                Rifiuta
              </Button>
              
              <Button
                size="sm"
                onClick={() => handleAction('approve')}
                disabled={isLoading}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                <Check className="h-4 w-4 mr-2" />
                Approva
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Dialog Delete */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="text-red-600">
              Elimina Richiesta
            </DialogTitle>
            <DialogDescription>
              Sei sicuro di voler eliminare questa richiesta di approvazione? 
              Questa azione non può essere annullata.
            </DialogDescription>
          </DialogHeader>
          
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setConfirmOpen(false)}
              disabled={isLoading}
            >
              Annulla
            </Button>
            <Button 
              onClick={onConfirmDelete}
              disabled={isLoading}
              className="bg-red-600 hover:bg-red-700"
            >
              {isLoading ? 'Eliminazione...' : 'Elimina'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog per approve/reject con commenti */}
      <Dialog open={showCommentDialog} onOpenChange={setShowCommentDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>
              {pendingAction === 'approve' ? 'Conferma Approvazione' : 'Conferma Rifiuto'}
            </DialogTitle>
            <DialogDescription>
              {pendingAction === 'approve' 
                ? 'Stai per approvare questo documento. Puoi aggiungere un commento opzionale.'
                : 'Stai per rifiutare questo documento. Ti consigliamo di specificare il motivo.'
              }
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <Textarea
              placeholder={
                pendingAction === 'approve'
                  ? "Commento opzionale..."
                  : "Specifica il motivo del rifiuto..."
              }
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              className="min-h-[100px]"
            />
          </div>
          
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowCommentDialog(false)}
              disabled={isLoading}
            >
              Annulla
            </Button>
            <Button 
              onClick={confirmDecision}
              disabled={isLoading}
              className={
                pendingAction === 'approve'
                  ? "bg-green-600 hover:bg-green-700"
                  : "bg-red-600 hover:bg-red-700"
              }
            >
              {isLoading ? 'Invio...' : (pendingAction === 'approve' ? 'Approva' : 'Rifiuta')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ApprovalActions;
