import React from 'react';
import { Separator } from '@/components/ui/separator';
import { MessageSquare, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

const CommentsSection = ({ recipients }) => {
  const recipientsWithComments = recipients?.filter(r => r.comments && r.comments.trim()) || [];

  if (!recipientsWithComments.length) return null;

  return (
    <>
      <Separator className="my-4" />
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-gray-900 flex items-center">
          <MessageSquare className="h-4 w-4 mr-2" />
          Commenti ({recipientsWithComments.length})
        </h4>
        
        <div className="space-y-3">
          {recipientsWithComments.map((recipient) => (
            <div key={recipient.id} className="bg-gray-50 rounded-lg p-3 border">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-900">
                    {recipient.recipient_name || recipient.recipient_email?.split('@')[0]}
                  </span>
                  <Badge 
                    className={`flex items-center space-x-1 ${
                      recipient.status === 'approved' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {recipient.status === 'approved' ? (
                      <ThumbsUp className="h-3 w-3" />
                    ) : (
                      <ThumbsDown className="h-3 w-3" />
                    )}
                    <span className="text-xs capitalize">{recipient.status}</span>
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
              <p className="text-sm text-gray-700 italic">
                "{recipient.comments}"
              </p>
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

export default CommentsSection;
