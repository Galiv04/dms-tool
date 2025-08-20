import React, { useState } from "react";
import { useApprovals, useApprovalsForMe } from "../hooks/useApprovals";
import { useAuth } from "../contexts/AuthContext";
import ApprovalCard from "../components/approvals/ApprovalCard";
import CreateApprovalModal from "../components/modals/CreateAppovalModal";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Plus, RefreshCw, Loader2, AlertCircle } from "lucide-react";

const ApprovalDashboard = () => {
  const { user } = useAuth();
  const [activeFilter, setActiveFilter] = useState("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  const handleOpenModal = () => {
    setShowCreateModal(true);
  };

  // 📊 Get both my requests and requests for me
  const { 
    data: myRequests = [], 
    isLoading: loadingMyRequests, 
    refetch: refetchMyRequests 
  } = useApprovals({});
  
  const { 
    data: requestsForMe = [], 
    isLoading: loadingForMe, 
    refetch: refetchForMe 
  } = useApprovalsForMe();

  // 🔄 Combine and filter data based on active filter
  const allData = React.useMemo(() => {
    let combined = [];
    
    // Add my created requests
    const myRequestsWithType = myRequests.map(req => ({
      ...req,
      __type: 'created',
      __isCreator: true
    }));
    
    // Add requests where I'm a recipient
    const forMeWithType = requestsForMe.map(req => ({
      ...req,
      __type: 'recipient',
      __isCreator: false
    }));
    
    combined = [...myRequestsWithType, ...forMeWithType];
    
    // Remove duplicates (same request ID)
    const uniqueMap = new Map();
    combined.forEach(item => {
      const existing = uniqueMap.get(item.id);
      if (!existing || (existing.__type === 'recipient' && item.__type === 'created')) {
        // Prioritize 'created' over 'recipient' for same request
        uniqueMap.set(item.id, item);
      }
    });
    
    const uniqueData = Array.from(uniqueMap.values());
    
    // Apply filters
    switch (activeFilter) {
      case 'pending':
        return uniqueData.filter(item => item.status === 'pending');
      case 'approved':
        return uniqueData.filter(item => item.status === 'approved');
      case 'rejected':
        return uniqueData.filter(item => item.status === 'rejected');
      case 'my-pending':
        // Only requests where I'm a recipient and need to decide
        return requestsForMe.filter(item => {
          const myRecipient = item.recipients?.find(r => r.recipient_email === user?.email);
          return myRecipient?.status === 'pending' && item.status === 'pending';
        }).map(req => ({ ...req, __type: 'recipient', __isCreator: false }));
      case 'created':
        return myRequestsWithType;
      default: // 'all'
        return uniqueData;
    }
  }, [myRequests, requestsForMe, activeFilter, user?.email]);

  // 📈 Calculate counts for filter badges
  const filterCounts = React.useMemo(() => {
    const allUnique = new Map();
    [...myRequests, ...requestsForMe].forEach(item => {
      if (!allUnique.has(item.id)) {
        allUnique.set(item.id, item);
      }
    });
    const unique = Array.from(allUnique.values());
    
    const myPendingCount = requestsForMe.filter(item => {
      const myRecipient = item.recipients?.find(r => r.recipient_email === user?.email);
      return myRecipient?.status === 'pending' && item.status === 'pending';
    }).length;
    
    return {
      all: unique.length,
      pending: unique.filter(item => item.status === 'pending').length,
      approved: unique.filter(item => item.status === 'approved').length,
      rejected: unique.filter(item => item.status === 'rejected').length,
      'my-pending': myPendingCount,
      created: myRequests.length
    };
  }, [myRequests, requestsForMe, user?.email]);

  // 🎯 Filter definitions
  const filters = [
    { key: "all", label: "Tutte", count: filterCounts.all },
    { key: "my-pending", label: "Da Approvare", count: filterCounts['my-pending'], color: "bg-orange-100 text-orange-800" },
    { key: "pending", label: "In Attesa", count: filterCounts.pending, color: "bg-yellow-100 text-yellow-800" },
    { key: "approved", label: "Approvate", count: filterCounts.approved, color: "bg-green-100 text-green-800" },
    { key: "rejected", label: "Rifiutate", count: filterCounts.rejected, color: "bg-red-100 text-red-800" },
    { key: "created", label: "Le Mie", count: filterCounts.created, color: "bg-blue-100 text-blue-800" }
  ];

  const isLoading = loadingMyRequests || loadingForMe;

  const handleRefresh = () => {
    refetchMyRequests();
    refetchForMe();
  };

  const handleCreateSuccess = () => {
    refetchMyRequests();
    refetchForMe();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 🎯 Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Approvazioni</h1>
          <p className="text-gray-600 mt-1">
            Gestisci le tue richieste di approvazione e rispondi a quelle ricevute
          </p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Aggiorna
          </Button>
          <Button onClick={handleOpenModal}>
            <Plus className="h-4 w-4 mr-2" />
            Nuova Richiesta
          </Button>
        </div>
      </div>

      {/* 🎛️ Filters */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-lg">Filtri</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {filters.map((filter) => (
              <button
                key={filter.key}
                onClick={() => setActiveFilter(filter.key)}
                className={`inline-flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeFilter === filter.key
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {filter.label}
                <Badge 
                  className={`ml-2 ${filter.color || 'bg-gray-200 text-gray-800'}`}
                  variant="secondary"
                >
                  {filter.count}
                </Badge>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 📋 Results */}
      <div className="space-y-4">
        {allData.length === 0 ? (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {activeFilter === 'all' 
                ? "Nessuna richiesta di approvazione trovata."
                : `Nessuna richiesta trovata per il filtro "${filters.find(f => f.key === activeFilter)?.label}".`
              }
            </AlertDescription>
          </Alert>
        ) : (
          allData.map((approval) => (
            <ApprovalCard
              key={`${approval.id}-${approval.__type}`}
              approval={approval}
              showActions={true}
              variant="default"
            />
          ))
        )}
      </div>

      {/* 🆕 Create Modal */}
      <CreateApprovalModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleCreateSuccess}
      />
    </div>
  );
};

export default ApprovalDashboard;
