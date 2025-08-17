// src/pages/ApprovalDashboard.jsx - ALLINEATO CON BACKEND
import React, { useState } from "react";
import {
  useApprovals,
  useApprovalStats,
  useApprovalsForMe,
} from "../hooks/useApprovals";
import { useAuth } from "../contexts/AuthContext";
import ApprovalCard from "../components/approvals/ApprovalCard";
import CreateApprovalModal from "../components/modals/CreateAppovalModal";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Plus, Filter, RefreshCw, Loader2, AlertCircle } from "lucide-react";

const ApprovalDashboard = () => {
  const { user } = useAuth();
  const [activeFilter, setActiveFilter] = useState("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [tab, setTab] = useState("my-requests");

  // ✅ Sanitizza filtro prima di passarlo
  const sanitizedFilter = React.useMemo(() => {
    if (activeFilter === "all" || !activeFilter) {
      return {};
    }
    return { status: activeFilter };
  }, [activeFilter]);

  // React Query hooks
  const {
    data: approvals = [], // ✅ Default a array vuoto
    isLoading,
    error,
    refetch,
    isFetching,
  } = useApprovals(sanitizedFilter);

  const { data: stats } = useApprovalStats();

  const { data: approvalsForMe = [], isLoading: loadingForMe } =
    useApprovalsForMe();

  // ✅ Filtri aggiornati con nomi backend
  const filters = [
    { key: "all", label: "Tutte", count: stats?.total_requests || 0 },
    { key: "pending", label: "In attesa", count: stats?.pending_requests || 0 },
    {
      key: "approved",
      label: "Approvate",
      count: stats?.approved_requests || 0,
    },
    {
      key: "rejected",
      label: "Rifiutate",
      count: stats?.rejected_requests || 0,
    },
  ];

  // eslint-disable-next-line no-unused-vars
  const handleApprovalClick = (approval) => {
    console.log("Opening approval:", approval);
  };

  const handleCreateSuccess = (approval) => {
    console.log("Approvazione creata con successo:", approval);
    // React Query invaliderà automaticamente le query
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Caricamento dashboard approvazioni...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Errore nel caricamento delle approvazioni: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Dashboard Approvazioni
          </h1>
          <p className="text-muted-foreground">
            Benvenuto, {user?.display_name}! Gestisci le tue richieste di
            approvazione.
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nuova Richiesta
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Totale Richieste
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_requests}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">In Attesa</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">
                {stats.pending_requests}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Approvate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {stats.approved_requests}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Rifiutate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {stats.rejected_requests}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      {/* Tab my-requests and for-me */}
      <div className="flex space-x-2 mb-6">
        <Button
          variant={tab === "my-requests" ? "default" : "outline"}
          onClick={() => setTab("my-requests")}
        >
          Le mie richieste
        </Button>
        <Button
          variant={tab === "for-me" ? "default" : "outline"}
          onClick={() => setTab("for-me")}
        >
          Da approvare
          <span className="ml-2">{approvalsForMe.length}</span>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4" />
          <span className="text-sm font-medium">Filtri:</span>
        </div>
        <div className="flex gap-2">
          {filters.map((filter) => (
            <Button
              key={filter.key}
              variant={activeFilter === filter.key ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveFilter(filter.key)}
              className="flex items-center gap-2"
            >
              {filter.label}
              <Badge variant="secondary" className="ml-1">
                {filter.count}
              </Badge>
            </Button>
          ))}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={refetch}
          disabled={isFetching}
        >
          {isFetching ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          Aggiorna
        </Button>
      </div>

      {/* Le richieste create da te - tab default */}
      {tab === "my-requests" && (
        <>
          <h2 className="mb-4 text-lg font-semibold">
            Le mie richieste di approvazione
          </h2>
          {isLoading ? (
            <Loader2 className="animate-spin" />
          ) : approvals.length === 0 ? (
            <Alert>
              <AlertDescription>
                Nessuna richiesta creata da te
              </AlertDescription>
            </Alert>
          ) : (
            approvals.map((approval) => (
              <ApprovalCard
                key={approval.id}
                approval={approval}
                showActions={true}
              />
            ))
          )}
        </>
      )}

      {/* Le richieste dove sei destinatario */}
      {tab === "for-me" && (
        <>
          <h2 className="mb-4 text-lg font-semibold">
            Richieste dove sei destinatario
          </h2>
          {loadingForMe ? (
            <Loader2 className="animate-spin" />
          ) : approvalsForMe.length === 0 ? (
            <Alert>
              <AlertDescription>
                Nessuna richiesta da approvare
              </AlertDescription>
            </Alert>
          ) : (
            approvalsForMe.map((approval) => (
              <ApprovalCard
                key={approval.id}
                approval={approval}
                showActions={true}
              />
            ))
          )}
        </>
      )}

      {/* Modal Creazione */}
      <CreateApprovalModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleCreateSuccess}
      />
    </div>
  );
};

export default ApprovalDashboard;
