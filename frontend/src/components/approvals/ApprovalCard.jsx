// src/components/approvals/ApprovalCard.jsx
import React from 'react'
import { formatDistanceToNow } from 'date-fns'
import { it } from 'date-fns/locale'
// import './ApprovalCard.css'

const ApprovalCard = ({ approval, onClick, showActions = false, onApprove, onReject }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return '⏳'
      case 'approved': return '✅'
      case 'rejected': return '❌'
      case 'expired': return '⏰'
      case 'cancelled': return '🚫'
      default: return '❓'
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return '#ff9800'
      case 'approved': return '#4caf50'
      case 'rejected': return '#f44336'
      case 'expired': return '#9e9e9e'
      case 'cancelled': return '#607d8b'
      default: return '#757575'
    }
  }

  const formatDateTime = (dateString) => {
    return formatDistanceToNow(new Date(dateString), { 
      addSuffix: true, 
      locale: it 
    })
  }

  const getApprovalProgress = () => {
    const total = approval.recipients?.length || 0
    const approved = approval.recipients?.filter(r => r.status === 'approved').length || 0
    return { approved, total, percentage: total > 0 ? (approved / total) * 100 : 0 }
  }

  const progress = getApprovalProgress()

  return (
    <div 
      className={`approval-card ${approval.status}`}
      onClick={() => onClick?.(approval)}
    >
      <div className="approval-header">
        <div className="approval-title">
          <h3>{approval.document_title}</h3>
          <span 
            className="approval-status"
            style={{ backgroundColor: getStatusColor(approval.status) }}
          >
            {getStatusIcon(approval.status)} {approval.status.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="approval-meta">
        <div className="approval-info">
          <p><strong>Richiedente:</strong> {approval.requester?.display_name || approval.requester?.email}</p>
          <p><strong>Creata:</strong> {formatDateTime(approval.created_at)}</p>
          {approval.expires_at && (
            <p><strong>Scade:</strong> {formatDateTime(approval.expires_at)}</p>
          )}
        </div>

        <div className="approval-progress">
          <div className="progress-info">
            <span>Approvazioni: {progress.approved}/{progress.total}</span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${progress.percentage}%` }}
            />
          </div>
        </div>
      </div>

      {approval.description && (
        <div className="approval-description">
          <p>{approval.description}</p>
        </div>
      )}

      <div className="approval-recipients">
        <h4>Approvatori ({approval.recipients?.length || 0}):</h4>
        <div className="recipients-list">
          {approval.recipients?.map((recipient, index) => (
            <div key={index} className={`recipient-item ${recipient.status}`}>
              <span className="recipient-name">
                {recipient.user?.display_name || recipient.email}
              </span>
              <span className="recipient-status">
                {getStatusIcon(recipient.status)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {showActions && approval.status === 'pending' && (
        <div className="approval-actions">
          <button 
            onClick={(e) => {
              e.stopPropagation()
              onApprove?.(approval)
            }}
            className="approve-btn"
          >
            ✅ Approva
          </button>
          <button 
            onClick={(e) => {
              e.stopPropagation()
              onReject?.(approval)
            }}
            className="reject-btn"
          >
            ❌ Rifiuta
          </button>
        </div>
      )}
    </div>
  )
}

export default ApprovalCard
