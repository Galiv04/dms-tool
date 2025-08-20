import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Check, X, Clock, User, MessageSquare } from 'lucide-react';
import {Tooltip} from '@/components/ui/tooltip';

// eslint-disable-next-line no-unused-vars
const RecipientsList = ({ recipients = [], currentUserEmail, variant }) => {
  if (!recipients.length) return null;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
        return <Check className="h-3 w-3 text-green-600" />;
      case 'rejected':
        return <X className="h-3 w-3 text-red-600" />;
      case 'pending':
        return <Clock className="h-3 w-3 text-yellow-600" />;
      default:
        return <Clock className="h-3 w-3 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'approved':
        return 'Approvato';
      case 'rejected':
        return 'Rifiutato';
      case 'pending':
        return 'In attesa';
      default:
        return 'Sconosciuto';
    }
  };

  const getInitials = (name, email) => {
    if (name) {
      return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    }
    if (email) {
      return email.split('@').slice(0, 2).toUpperCase();
    }
    return 'U';
  };

  const getName = (recipient) => {
    return recipient.recipient_name || 
           recipient.recipient_email?.split('@') || 
           'Sconosciuto';
  };

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-gray-900 flex items-center">
        <User className="h-4 w-4 mr-2" />
        Destinatari ({recipients.length})
      </h4>
      <div className="space-y-2">
        {recipients.map((recipient) => (
          <div
            key={recipient.id}
            className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
              recipient.recipient_email === currentUserEmail 
                ? 'bg-blue-50 border-blue-200' 
                : 'bg-gray-50 border-gray-200'
            }`}
          >
            <div className="flex items-center space-x-3">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="text-xs bg-gray-200 text-gray-700">
                  {getInitials(recipient.recipient_name, recipient.recipient_email)}
                </AvatarFallback>
              </Avatar>
              
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {getName(recipient)}
                  {recipient.recipient_email === currentUserEmail && (
                    <span className="ml-2 text-xs text-blue-600 font-medium">(Tu)</span>
                  )}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {recipient.recipient_email}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {/* 💬 Comment Icon with Tooltip */}
              {recipient.comments && (
                <Tooltip content={recipient.comments} position="left">
                  <div className="p-1.5 rounded-full bg-blue-100 text-blue-600 hover:bg-blue-200 transition-colors">
                    <MessageSquare className="h-3 w-3" />
                  </div>
                </Tooltip>
              )}

              {/* Status Badge */}
              <Badge className={`${getStatusColor(recipient.status)} flex items-center space-x-1`}>
                {getStatusIcon(recipient.status)}
                <span className="text-xs">{getStatusText(recipient.status)}</span>
              </Badge>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecipientsList;
