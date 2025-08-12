import { useState, useEffect } from 'react';

// Store per toast globale
let toastCount = 0;
const toastSubscribers = new Set();

// Stato globale dei toast
const toastStore = {
  toasts: [],
  subscribe: (callback) => {
    toastSubscribers.add(callback);
    return () => toastSubscribers.delete(callback);
  },
  emit: () => {
    toastSubscribers.forEach(callback => callback());
  },
  addToast: (toastData) => {
    const id = ++toastCount;
    const toast = {
      id,
      ...toastData,
    };
    
    toastStore.toasts = [toast, ...toastStore.toasts].slice(0, 5); // Limita a 5 toast
    toastStore.emit();
    
    // Auto-rimozione dopo timeout
    if (toastData.duration !== Infinity) {
      setTimeout(() => {
        toastStore.removeToast(id);
      }, toastData.duration || 5000);
    }
    
    return id;
  },
  removeToast: (id) => {
    toastStore.toasts = toastStore.toasts.filter(toast => toast.id !== id);
    toastStore.emit();
  },
  updateToast: (id, updates) => {
    toastStore.toasts = toastStore.toasts.map(toast =>
      toast.id === id ? { ...toast, ...updates } : toast
    );
    toastStore.emit();
  }
};

export const useToast = () => {
  const [, forceUpdate] = useState({});
  
  // Re-render quando cambiano i toast
  useEffect(() => {
    return toastStore.subscribe(() => {
      forceUpdate({});
    });
  }, []);
  
  const toast = (props) => {
    const {
      title,
      description,
      variant = 'default',
      duration = 5000,
      ...rest
    } = typeof props === 'string' ? { description: props } : props;
    
    return toastStore.addToast({
      title,
      description,
      variant,
      duration,
      ...rest
    });
  };
  
  return {
    toast,
    toasts: toastStore.toasts,
    dismiss: toastStore.removeToast
  };
};
