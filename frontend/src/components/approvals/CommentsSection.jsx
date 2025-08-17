// src/components/approvals/CommentsSection.jsx - MIGLIORATO
import React from 'react';
import { Separator } from '@/components/ui/separator';
import { MessageSquare, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

const CommentsSection = ({ recipients }) => {
  const recipientsWithComments = recipients.filter(r => r.comments);
  
  if (!recipientsWithComments.length) return null;

  return (
    <>
      <Separator className="mb-4" />
      
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
          <MessageSquare className="h-4 w-4" />
          Feedback ({recipientsWithComments.length})
        </h4>
        
        <div className="space-y-3">
          {recipientsWithComments.map((recipient, index) => (
            <div 
              key={index} 
              className={`rounded-lg p-4 border-l-4 ${
                recipient.status === 'approved' 
                  ? 'bg-green-50 border-l-green-400 border border-green-200' 
                  : 'bg-red-50 border-l-red-400 border border-red-200'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-900">
                    {recipient.recipient_name || recipient.recipient_email}
                  </span>
                  
                  <Badge 
                    variant="outline"
                    className={
                      recipient.status === 'approved' 
                        ? 'bg-green-100 text-green-800 border-green-200'
                        : 'bg-red-100 text-red-800 border-red-200'
                    }
                  >
                    {recipient.status === 'approved' ? (
                      <><ThumbsUp className="h-3 w-3 mr-1" /> Approvato</>
                    ) : (
                      <><ThumbsDown className="h-3 w-3 mr-1" /> Rifiutato</>
                    )}
                  </Badge>
                </div>
                
                {recipient.responded_at && (
                  <span className="text-xs text-gray-500">
                    {new Date(recipient.responded_at).toLocaleDateString('it-IT', {
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                )}
              </div>
              
              <p className="text-sm text-gray-700 italic">"{recipient.comments}"</p>
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

export default CommentsSection;
