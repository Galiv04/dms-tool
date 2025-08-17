// src/components/approvals/ApprovalDetails.jsx
import React from 'react';
import { Separator } from '@/components/ui/separator';
import { Clock, AlertCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

const ApprovalDetails = ({ approval, myRecipient }) => {
  const formatDate = (dateString) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isExpiringSoon = () => {
    if (!approval.due_date) return false;
    const dueDate = new Date(approval.due_date);
    const now = new Date();
    const diffHours = (dueDate - now) / (1000 * 60 * 60);
    return diffHours > 0 && diffHours <= 24;
  };

  return (
    <div className="mb-4">
      {approval.description && (
        <div className="mb-3">
          <p className="text-sm text-gray-700">{approval.description}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        {/* Data di scadenza */}
        {approval.due_date && (
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-gray-400" />
            <div>
              <span className="text-gray-600">Scadenza: </span>
              <span className={isExpiringSoon() ? "text-orange-600 font-medium" : "text-gray-900"}>
                {formatDate(approval.due_date)}
              </span>
              {isExpiringSoon() && (
                <AlertCircle className="inline h-3 w-3 text-orange-600 ml-1" />
              )}
            </div>
          </div>
        )}

        {/* Priorità */}
        {approval.priority && (
          <div className="flex items-center gap-2">
            <span className="text-gray-600">Priorità: </span>
            <Badge 
              variant="outline"
              className={
                approval.priority === 'high' ? 'border-red-200 text-red-800' :
                approval.priority === 'medium' ? 'border-yellow-200 text-yellow-800' :
                'border-green-200 text-green-800'
              }
            >
              {approval.priority === 'high' && '🔴 Alta'}
              {approval.priority === 'medium' && '🟡 Media'}
              {approval.priority === 'low' && '🟢 Bassa'}
            </Badge>
          </div>
        )}

        {/* Mio stato se sono recipient */}
        {myRecipient && (
          <div className="flex items-center gap-2">
            <span className="text-gray-600">Il mio stato: </span>
            <Badge 
              variant="outline"
              className={
                myRecipient.status === 'approved' ? 'border-green-200 text-green-800' :
                myRecipient.status === 'rejected' ? 'border-red-200 text-red-800' :
                'border-yellow-200 text-yellow-800'
              }
            >
              {myRecipient.status === 'pending' && '⏳ Da decidere'}
              {myRecipient.status === 'approved' && '✅ Approvato'}
              {myRecipient.status === 'rejected' && '❌ Rifiutato'}
            </Badge>
          </div>
        )}
      </div>

      <Separator className="mt-4" />
    </div>
  );
};

export default ApprovalDetails;
