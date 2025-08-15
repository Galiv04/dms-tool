// src/components/ui/ConfirmDialog.jsx
import React from 'react';

const ConfirmDialog = ({ 
  isOpen, 
  title, 
  message, 
  details,
  onCancel, 
  onConfirm, 
  confirmText = 'Conferma',
  cancelText = 'Annulla',
  type = 'default', // 'default', 'danger', 'warning'
  isLoading = false
}) => {
  if (!isOpen) return null;

  const getStyles = () => {
    const baseStyles = {
      overlay: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 9999,
        padding: '20px'
      },
      dialog: {
        backgroundColor: 'white',
        borderRadius: '8px',
        maxWidth: '500px',
        width: '100%',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)',
        overflow: 'hidden',
        animation: 'fadeInScale 0.2s ease-out'
      },
      header: {
        padding: '24px 24px 16px',
        borderBottom: '1px solid #e5e5e5'
      },
      content: {
        padding: '16px 24px'
      },
      footer: {
        padding: '16px 24px',
        backgroundColor: '#f8f9fa',
        display: 'flex',
        justifyContent: 'flex-end',
        gap: '12px',
        borderTop: '1px solid #e5e5e5'
      },
      button: {
        padding: '8px 16px',
        borderRadius: '6px',
        border: 'none',
        fontWeight: '500',
        cursor: 'pointer',
        fontSize: '14px',
        transition: 'all 0.2s'
      },
      cancelButton: {
        backgroundColor: '#f1f3f4',
        color: '#5f6368',
        border: '1px solid #dadce0'
      },
      confirmButton: {
        backgroundColor: type === 'danger' ? '#dc2626' : '#3b82f6',
        color: 'white'
      }
    };

    return baseStyles;
  };

  const styles = getStyles();

  // Previeni chiusura durante loading
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget && !isLoading) {
      onCancel();
    }
  };

  return (
    <>
      {/* CSS Animation */}
      <style>{`
        @keyframes fadeInScale {
          from {
            opacity: 0;
            transform: scale(0.9) translateY(-10px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
        
        .confirm-dialog-overlay {
          backdrop-filter: blur(2px);
        }
      `}</style>
      
      <div 
        style={styles.overlay}
        className="confirm-dialog-overlay"
        onClick={handleOverlayClick}
      >
        <div style={styles.dialog} role="dialog" aria-modal="true">
          {/* Header */}
          <div style={styles.header}>
            <h2 style={{ 
              margin: 0, 
              fontSize: '18px', 
              fontWeight: '600',
              color: type === 'danger' ? '#dc2626' : '#1f2937',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              {type === 'danger' && <span style={{ fontSize: '20px' }}>⚠️</span>}
              {type === 'warning' && <span style={{ fontSize: '20px' }}>⚡</span>}
              {title}
            </h2>
          </div>

          {/* Content */}
          <div style={styles.content}>
            <p style={{ 
              margin: '0 0 16px 0', 
              color: '#4b5563', 
              lineHeight: '1.5',
              fontSize: '15px'
            }}>
              {message}
            </p>

            {/* Details (opzionale) */}
            {details && (
              <div style={{
                backgroundColor: '#f9fafb',
                padding: '12px',
                borderRadius: '6px',
                border: '1px solid #e5e7eb',
                fontSize: '14px',
                color: '#6b7280'
              }}>
                {typeof details === 'string' ? (
                  <p style={{ margin: 0 }}>{details}</p>
                ) : (
                  details
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div style={styles.footer}>
            <button
              type="button"
              onClick={onCancel}
              disabled={isLoading}
              style={{
                ...styles.button,
                ...styles.cancelButton,
                opacity: isLoading ? 0.6 : 1,
                cursor: isLoading ? 'not-allowed' : 'pointer'
              }}
            >
              {cancelText}
            </button>
            
            <button
              type="button"
              onClick={onConfirm}
              disabled={isLoading}
              style={{
                ...styles.button,
                ...styles.confirmButton,
                opacity: isLoading ? 0.8 : 1,
                cursor: isLoading ? 'not-allowed' : 'pointer',
                minWidth: '100px'
              }}
            >
              {isLoading ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ 
                    width: '14px', 
                    height: '14px', 
                    border: '2px solid #ffffff40',
                    borderTop: '2px solid #ffffff',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></span>
                  Eliminando...
                </span>
              ) : (
                confirmText
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Spinner animation */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
};

export default ConfirmDialog;
