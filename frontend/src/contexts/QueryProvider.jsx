// src/contexts/QueryProvider.jsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
// import { useState } from 'react'

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 1 minuto
        gcTime: 10 * 60 * 1000, // 10 minuti (sostituisce cacheTime)
        retry: (failureCount, error) => {
          // Non riprovare su errori 401/403
          if (error?.status === 401 || error?.status === 403) {
            return false
          }
          return failureCount < 3
        },
      },
      mutations: {
        retry: false,
      },
    },
  })
}

let browserQueryClient
function getQueryClient() {
  if (typeof window === 'undefined') {
    // Server: crea sempre un nuovo query client
    return makeQueryClient()
  } else {
    // Browser: crea query client se non esiste
    if (!browserQueryClient) browserQueryClient = makeQueryClient()
    return browserQueryClient
  }
}

export default function QueryProvider({ children }) {
  const queryClient = getQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
