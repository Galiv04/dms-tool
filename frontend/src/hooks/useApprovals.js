import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

// ✅ API functions ALLINEATE con il backend
const approvalsApi = {
  // ✅ Endpoint corretto: /approvals/ (non /approval/requests)
  getApprovals: async (filters = {}) => {
    const params = new URLSearchParams()
    
    // ✅ Backend usa "status_filter" non "status"
    if (filters.status && filters.status !== 'all') {
      params.append('status_filter', filters.status)
    }
    
    // ✅ Aggiungi paginazione (backend supporta limit/offset)
    params.append('limit', '50')
    params.append('offset', '0')
    
    const queryString = params.toString()
    const url = `/approvals${queryString ? '?' + queryString : ''}`
    
    try {
      const response = await apiClient.get(url)
      // ✅ Backend ritorna array diretto, non { data: [...] }
      return response.data
    } catch (error) {
      if (error.response?.status === 404) {
        console.warn('Approvals endpoint not found')
        return []
      }
      throw error
    }
  },

  // ✅ Crea nuova richiesta approvazione
  createApproval: async (approvalData) => {
    const response = await apiClient.post('/approvals/', approvalData)
    return response.data
  },

  // ✅ Dettagli singola approvazione
  getApproval: async (approvalId) => {
    const response = await apiClient.get(`/approvals/${approvalId}`)
    return response.data
  },

  // ✅ Approvazione tramite token (per link email)
  approveByToken: async ({ token, approved, comments }) => {
    const response = await apiClient.post(`/approvals/decide/${token}`, {
      decision: approved ? 'approved' : 'rejected',
      comments: comments || ''
    })
    return response.data
  },

  // ✅ Cancella richiesta approvazione
  cancelApproval: async ({ requestId, reason }) => {
    const response = await apiClient.post(`/approvals/${requestId}/cancel`, {
      reason: reason || ''
    })
    return response.data
  },

  // ✅ Statistiche dashboard
  getApprovalStats: async () => {
    const response = await apiClient.get('/approvals/dashboard/stats')
    return response.data
  },

  // ✅ Approvazioni pending per email (dashboard pubblico)
  getPendingForEmail: async (email) => {
    const response = await apiClient.get(`/approvals/dashboard/pending?email=${email}`)
    return response.data
  },

  // ✅ Info token (per preview)
  getTokenInfo: async (token) => {
    const response = await apiClient.get(`/approvals/token/${token}/info`)
    return response.data
  },

  // ✅ Audit trail
  getAuditTrail: async (requestId) => {
    const response = await apiClient.get(`/approvals/audit/${requestId}`)
    return response.data
  },

  deleteApproval: async (approvalId) => {
    const response = await apiClient.delete(`/approvals/${approvalId}`)
    return response.data
  },
}

// Hook per lista approvazioni con filtri
export const useApprovals = (filters = {}) => {
  // ✅ Sanitizza filtri per evitare "undefined"
  const sanitizedFilters = React.useMemo(() => {
    const result = {}
    if (filters.status && filters.status !== 'all' && filters.status !== 'undefined') {
      result.status = filters.status
    }
    return result
  }, [filters])

  return useQuery({
    queryKey: ['approvals', sanitizedFilters],
    queryFn: () => approvalsApi.getApprovals(sanitizedFilters),
    staleTime: 30 * 1000,
    retry: 3,
  })
}

// Hook per statistiche
export const useApprovalStats = () => {
  return useQuery({
    queryKey: ['approval-stats'],
    queryFn: () => approvalsApi.getApprovalStats(),
    staleTime: 2 * 60 * 1000,
  })
}

// Hook per creare approvazione
export const useCreateApproval = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (approvalData) => approvalsApi.createApproval(approvalData),
    onSuccess: () => {
      queryClient.invalidateQueries(['approvals'])
      queryClient.invalidateQueries(['approval-stats'])
      queryClient.invalidateQueries(['documents'])
    },
    onError: (error) => {
      console.error('Create approval failed:', error)
    }
  })
}

export function useApproveByToken() {
  return useMutation(
    async ({ token, approved, comments }) => {
      await apiClient.post(`/approvals/decide/${token}`, {
        decision: approved ? "approved" : "rejected",
        comments,
      });
    }
  );
}


// Hook per cancellazione
export const useCancelApproval = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ requestId, reason }) => 
      approvalsApi.cancelApproval({ requestId, reason }),
    onSuccess: () => {
      queryClient.invalidateQueries(['approvals'])
      queryClient.invalidateQueries(['approval-stats'])
    },
    onError: (error) => {
      console.error('Cancel approval failed:', error)
    }
  })
}

// Hook per singola approvazione
export const useApproval = (approvalId) => {
  return useQuery({
    queryKey: ['approvals', approvalId],
    queryFn: () => approvalsApi.getApproval(approvalId),
    enabled: !!approvalId,
    staleTime: 30 * 1000,
  })
}

// Hook per info token
export const useTokenInfo = (token) => {
  return useQuery({
    queryKey: ['approval-token', token],
    queryFn: () => approvalsApi.getTokenInfo(token),
    enabled: !!token,
    retry: false, // Non riprovare su token invalidi
  })
}

// Hook per audit trail
export const useAuditTrail = (requestId) => {
  return useQuery({
    queryKey: ['approval-audit', requestId],
    queryFn: () => approvalsApi.getAuditTrail(requestId),
    enabled: !!requestId,
    staleTime: 60 * 1000,
  })
}

// ✅ Hook per eliminazione approvazione
export const useDeleteApproval = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (approvalId) => approvalsApi.deleteApproval(approvalId),
    onSuccess: () => {
      // Invalida tutte le query correlate
      queryClient.invalidateQueries({ queryKey: ['approvals'] })
      queryClient.invalidateQueries({ queryKey: ['approval-stats'] })
    },
    onError: (error) => {
      console.error('Delete approval failed:', error)
    }
  })
}

// Hook per approvazioni dove sei destinatario
export const useApprovalsForMe = (options = {}) => {
  return useQuery({
    // Key coerente con le altre query
    queryKey: ['approvals', 'for-me'],

    // Funzione asincrona coerente con le altre
    queryFn: async () => {
      try {
        const response = await apiClient.get('/approvals/for-me');
        // Se il backend ritorna direttamente un array, nessun .data.data
        return response.data;
      } catch (error) {
        if (error.response?.status === 404) {
          console.warn('Approvals (for-me) endpoint not found');
          return [];
        }
        throw error;
      }
    },

    // Opzioni React Query personalizzabili (fallback, staleTime, etc.)
    staleTime: 30 * 1000,
    retry: 2,
    ...options,
  });
};

