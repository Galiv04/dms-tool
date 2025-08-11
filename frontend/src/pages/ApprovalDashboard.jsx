// src/pages/ApprovalDashboard.jsx - ALLINEATO CON BACKEND
import React, { useState } from 'react'
import { useApprovals, useApprovalStats } from '../hooks/useApprovals'
import { useAuth } from '../contexts/AuthContext'
import ApprovalCard from '../components/approvals/ApprovalCard'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Plus, Filter, RefreshCw, Loader2, AlertCircle } from 'lucide-react'

const ApprovalDashboard = () => {
  const { user } = useAuth()
  const [activeFilter, setActiveFilter] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(false)

  // ✅ Sanitizza filtro prima di passarlo
  const sanitizedFilter = React.useMemo(() => {
    if (activeFilter === 'all' || !activeFilter) {
      return {}
    }
    return { status: activeFilter }
  }, [activeFilter])

  // React Query hooks
  const { 
    data: approvals = [], // ✅ Default a array vuoto
    isLoading, 
    error, 
    refetch,
    isFetching 
  } = useApprovals(sanitizedFilter)

  const { data: stats } = useApprovalStats()

  // ✅ Filtri aggiornati con nomi backend
  const filters = [
    { key: 'all', label: 'Tutte', count: stats?.total_requests || 0 },
    { key: 'pending', label: 'In attesa', count: stats?.pending_requests || 0 },
    { key: 'approved', label: 'Approvate', count: stats?.approved_requests || 0 },
    { key: 'rejected', label: 'Rifiutate', count: stats?.rejected_requests || 0 }
  ]

  const handleApprovalClick = (approval) => {
    console.log('Opening approval:', approval)
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Caricamento dashboard approvazioni...</p>
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription className="flex items-center justify-between">
          <span>Errore nel caricamento: {error.message}</span>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            Riprova
          </Button>
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">📋 Dashboard Approvazioni</h1>
          <p className="text-muted-foreground">
            Benvenuto, {user?.display_name}! Gestisci le tue richieste di approvazione.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Button 
            variant="outline" 
            onClick={() => refetch()} 
            disabled={isFetching}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            Aggiorna
          </Button>
          
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Nuova Approvazione
          </Button>
        </div>
      </div>

      {/* ✅ Stats Card con dati backend */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Totali
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_requests || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                In Attesa
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {stats.pending_requests || 0}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Approvate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {stats.approved_requests || 0}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Da Approvare
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {stats.my_pending_approvals || 0}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Filter className="h-4 w-4" />
            <div className="flex gap-2">
              {filters.map((filter) => (
                <Button
                  key={filter.key}
                  variant={activeFilter === filter.key ? "default" : "outline"}
                  size="sm"
                  onClick={() => setActiveFilter(filter.key)}
                  className="gap-2"
                >
                  {filter.label}
                  <Badge variant="secondary" className="ml-1">
                    {filter.count}
                  </Badge>
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* ✅ Lista approvazioni */}
          {!approvals || approvals.length === 0 ? (
            <div className="text-center py-12">
              <div className="rounded-full bg-muted/50 w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <Filter className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">
                {activeFilter === 'all' 
                  ? 'Nessuna approvazione trovata' 
                  : `Nessuna approvazione ${activeFilter}`
                }
              </h3>
              <p className="text-muted-foreground mb-4">
                {activeFilter === 'all'
                  ? 'Crea la tua prima richiesta di approvazione per iniziare.'
                  : `Non ci sono approvazioni con stato "${activeFilter}" al momento.`
                }
              </p>
              {activeFilter === 'all' && (
                <Button onClick={() => setShowCreateModal(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Crea Prima Approvazione
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {approvals.map((approval) => (
                <div key={approval.id} className="border rounded-lg p-4">
                  {/* ✅ Usa dati dal backend schema */}
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-semibold">{approval.title}</h4>
                      <p className="text-sm text-muted-foreground">
                        {approval.description}
                      </p>
                      <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                        <span>ID: {approval.id}</span>
                        <span>Tipo: {approval.approval_type}</span>
                        <span>Stato: {approval.status}</span>
                      </div>
                    </div>
                    <Badge variant={
                      approval.status === 'pending' ? 'destructive' :
                      approval.status === 'approved' ? 'default' : 'secondary'
                    }>
                      {approval.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Modal Placeholder */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Nuova Richiesta Approvazione</CardTitle>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setShowCreateModal(false)}
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <p>Form di creazione approvazione sarà implementato prossimamente...</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default ApprovalDashboard
