// src/components/approvals/ApprovalCard.jsx
import React from "react";
import { getRelativeTime, formatLocalDateTime } from "../../utils/dateUtils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { CheckCircle, XCircle, Clock, AlertCircle, Ban } from "lucide-react";

const ApprovalCard = ({
  approval,
  onClick,
  showActions = false,
  onApprove,
  onReject,
}) => {
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

    if (!dateString) {
      return 'Data non disponibile';
    }
    
    const result = getRelativeTime(dateString);
    return result;
  };

  const getFullDateTime = (dateString) => {
    if (!dateString) return 'Data non disponibile';
    const result = formatLocalDateTime(dateString);
    return result;
  };

  const getApprovalProgress = () => {
    const total = approval.recipients?.length || 0;
    const approved = approval.recipients?.filter((r) => r.status === "approved").length || 0;
    return {
      approved,
      total,
      percentage: total > 0 ? (approved / total) * 100 : 0,
    };
  };

  const progress = getApprovalProgress();

  return (
    <TooltipProvider>
      <Card 
        className={`cursor-pointer transition-all hover:shadow-md ${
          approval.status === 'expired' ? 'opacity-75' : ''
        }`}
        onClick={() => onClick?.(approval)}
      >
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <CardTitle className="text-lg">
                {approval.title || approval.document?.filename || "Richiesta Approvazione"}
              </CardTitle>
              <CardDescription>
                Richiedente: {approval.requester?.display_name || approval.requester?.email || "Non specificato"}
              </CardDescription>
            </div>
            <Badge variant={getStatusVariant(approval.status)} className="flex items-center gap-1">
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
              <span>Approvazioni: {progress.approved}/{progress.total}</span>
              {approval.approval_type && (
                <span className="text-xs text-muted-foreground">
                  ({approval.approval_type === 'all' ? 'Tutti devono approvare' : 'Basta una approvazione'})
                </span>
              )}
            </div>
            <Progress value={progress.percentage} className="h-2" />
          </div>

          {/* Recipients */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Approvatori ({approval.recipients?.length || 0}):</h4>
            <div className="flex flex-wrap gap-2">
              {approval.recipients?.map((recipient, index) => (
                <div
                  key={recipient.id || index}
                  className="flex items-center gap-2 p-2 rounded-md bg-muted/50 text-xs"
                >
                  <Avatar className="h-6 w-6">
                    <AvatarFallback className="text-xs">
                      {(recipient.recipient_name || recipient.recipient_email || 'U').charAt(0).toUpperCase()}
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
                        <p>Risposto: {getFullDateTime(recipient.responded_at)}</p>
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          {showActions && approval.status === "pending" && (
            <div className="flex gap-2 pt-3 border-t">
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  onApprove?.(approval);
                }}
                disabled={!onApprove}
                size="sm"
                className="flex-1"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Approva
              </Button>
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  onReject?.(approval);
                }}
                disabled={!onReject}
                variant="destructive"
                size="sm"
                className="flex-1"
              >
                <XCircle className="h-4 w-4 mr-2" />
                Rifiuta
              </Button>
            </div>
          )}

          {/* Completion info */}
          {approval.completed_at && (
            <div className="pt-3 border-t text-xs text-muted-foreground text-right">
              Completata: <span className="cursor-help" title={getFullDateTime(approval.completed_at)}>
                {formatDateTime(approval.completed_at)}
              </span>
              {approval.completion_reason && ` (${approval.completion_reason})`}
            </div>
          )}
        </CardContent>
      </Card>
    </TooltipProvider>
  );
};

export default ApprovalCard;
