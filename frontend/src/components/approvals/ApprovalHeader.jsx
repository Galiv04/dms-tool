// src/components/approvals/ApprovalHeader.jsx
import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Calendar, FileText, User } from 'lucide-react';

const ApprovalHeader = ({ approval }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800 border-green-200';
      case 'rejected': return 'bg-red-100 text-red-800 border-red-200';
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'expired': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // ✅ NOME CREATOR CORRETTO - Usa approval.requester.display_name o email
  const getCreatorName = () => {
    if (approval.requester?.display_name) return approval.requester.display_name;
    if (approval.requester?.email) {
      const emailPart = approval.requester.email.split('@')[0];
      return emailPart.charAt(0).toUpperCase() + emailPart.slice(1);
    }
    return 'Utente sconosciuto';
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  return (
    <div className="flex items-start justify-between mb-4">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-2">
          <FileText className="h-4 w-4 text-gray-500" />
          <h3 className="text-lg font-semibold text-gray-900">
            {approval.document?.filename || 
             approval.document?.original_filename || 
             approval.title || 
             'Documento senza titolo'}
          </h3>
        </div>
        
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <User className="h-3 w-3" />
            <span>da {getCreatorName()}</span>
          </div>
          
          {approval.created_at && (
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>{formatDate(approval.created_at)}</span>
            </div>
          )}
        </div>
        
        {/* Mostra email se diversa dal display_name */}
        {approval.requester?.email && approval.requester?.display_name && (
          <div className="text-xs text-gray-500 mt-1">
            {approval.requester.email}
          </div>
        )}
      </div>

      <Badge 
        variant="outline" 
        className={getStatusColor(approval.status)}
      >
        {approval.status === 'pending' && '⏳ In attesa'}
        {approval.status === 'approved' && '✅ Approvato'}
        {approval.status === 'rejected' && '❌ Rifiutato'}
        {approval.status === 'expired' && '⏰ Scaduto'}
      </Badge>
    </div>
  );
};

export default ApprovalHeader;
