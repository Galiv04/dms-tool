import React from 'react';
import { useToast } from '@/hooks/useToast';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { X, CheckCircle, AlertCircle, XCircle, Info } from 'lucide-react';

const ToastVariants = {
  default: {
    bg: 'bg-background',
    border: 'border-border',
    text: 'text-foreground',
    icon: null
  },
  success: {
    bg: 'bg-green-50',
    border: 'border-green-200',
    text: 'text-green-900',
    icon: CheckCircle
  },
  error: {
    bg: 'bg-red-50',
    border: 'border-red-200', 
    text: 'text-red-900',
    icon: XCircle
  },
  destructive: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-900', 
    icon: XCircle
  },
  warning: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    text: 'text-yellow-900',
    icon: AlertCircle
  },
  info: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    text: 'text-blue-900',
    icon: Info
  }
};

const Toast = ({ toast, onDismiss }) => {
  const variant = ToastVariants[toast.variant] || ToastVariants.default;
  const Icon = variant.icon;

  return (
    <div
      className={`
        relative flex w-full max-w-sm items-center space-x-4 
        overflow-hidden rounded-md border p-4 shadow-lg
        ${variant.bg} ${variant.border} ${variant.text}
        animate-in slide-in-from-right-full duration-300
      `}
    >
      {Icon && <Icon className="h-4 w-4 flex-shrink-0" />}
      
      <div className="flex-1 space-y-1">
        {toast.title && (
          <div className="text-sm font-semibold">{toast.title}</div>
        )}
        {toast.description && (
          <div className="text-sm opacity-90">{toast.description}</div>
        )}
      </div>
      
      <Button
        variant="ghost"
        size="sm" 
        className="h-6 w-6 p-0 hover:bg-black/10"
        onClick={() => onDismiss(toast.id)}
      >
        <X className="h-3 w-3" />
      </Button>
    </div>
  );
};

export const Toaster = () => {
  const { toasts, dismiss } = useToast();

  return (
    <div className="fixed top-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:bottom-0 sm:right-0 sm:top-auto sm:flex-col md:max-w-[420px]">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onDismiss={dismiss} />
      ))}
    </div>
  );
};
