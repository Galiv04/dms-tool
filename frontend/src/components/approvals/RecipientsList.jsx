// src/components/approvals/RecipientsList.jsx
import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Check, X, Clock, User } from 'lucide-react';

// eslint-disable-next-line no-unused-vars
const RecipientsList = ({ recipients = [], currentUserEmail, variant }) => {
  if (!recipients.length) return null;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved': return <Check className="h-3 w-3 text-green-600" />;
      case 'rejected': return <X className="h-3 w-3 text-red-600" />;
      case 'pending': return <Clock className="h-3 w-3 text-yellow-600" />;
      default: return <User className="h-3 w-3 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'border-green-200 text-green-800 bg-green-50';
      case 'rejected': return 'border-red-200 text-red-800 bg-red-50';
      case 'pending': return 'border-yellow-200 text-yellow-800 bg-yellow-50';
      default: return 'border-gray-200 text-gray-800 bg-gray-50';
    }
  };

  const getInitials = (email, name) => {
    if (name) {
      return name.split(' ').map(n => n[0]).join('').toUpperCase();
    }
    return email.split('@').slice(0, 2).toUpperCase();
  };

  return (
    <div className="mb-4">
      <h4 className="text-sm font-medium text-gray-700 mb-3">
        Approvatori ({recipients.length})
      </h4>
      
      <div className="space-y-2">
        {recipients.map((recipient, index) => (
          <div 
            key={index}
            className={`flex items-center justify-between p-3 rounded-lg border ${
              recipient.recipient_email === currentUserEmail 
                ? 'border-blue-200 bg-blue-50' 
                : 'border-gray-200 bg-gray-50'
            }`}
          >
            <div className="flex items-center gap-3">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="text-xs">
                  {getInitials(recipient.recipient_email, recipient.recipient_name)}
                </AvatarFallback>
              </Avatar>
              
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900">
                    {recipient.recipient_name || recipient.recipient_email}
                  </span>
                  {recipient.recipient_email === currentUserEmail && (
                    <Badge variant="outline" className="text-xs border-blue-200 text-blue-800">
                      Tu
                    </Badge>
                  )}
                </div>
                {recipient.recipient_name && (
                  <span className="text-xs text-gray-500">
                    {recipient.recipient_email}
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Badge 
                variant="outline" 
                className={`text-xs ${getStatusColor(recipient.status)}`}
              >
                <span className="flex items-center gap-1">
                  {getStatusIcon(recipient.status)}
                  {recipient.status === 'pending' && 'In attesa'}
                  {recipient.status === 'approved' && 'Approvato'}
                  {recipient.status === 'rejected' && 'Rifiutato'}
                </span>
              </Badge>
              
              {recipient.responded_at && (
                <span className="text-xs text-gray-400">
                  {new Date(recipient.responded_at).toLocaleDateString('it-IT')}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecipientsList;
