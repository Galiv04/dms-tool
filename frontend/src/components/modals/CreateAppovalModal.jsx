import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { CheckIcon, ChevronDownIcon, XIcon, FileIcon, AlertCircleIcon, Loader2, Users, MessageSquare } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useToast } from '@/hooks/useToast';
import apiClient from '@/api/client';

// Schema di validazione Zod
const approvalSchema = z.object({
  title: z.string()
    .min(1, "Il titolo è obbligatorio")
    .max(200, "Il titolo non può superare i 200 caratteri"),
  description: z.string()
    .max(1000, "La descrizione non può superare i 1000 caratteri")
    .optional(),
  document_id: z.string()
    .min(1, "Seleziona un documento"),
  approval_type: z.enum(["all", "any"], {
    required_error: "Seleziona il tipo di approvazione",
  }),
  recipients: z.array(z.object({
    recipient_email: z.string().email("Email non valida"),
    recipient_name: z.string().min(1, "Nome obbligatorio"),
  })).min(1, "Aggiungi almeno un destinatario"),
  requester_comments: z.string()
    .max(500, "I commenti non possono superare i 500 caratteri")
    .optional(),
});

export default function CreateApprovalModal({ isOpen, onClose, onSuccess }) {
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [newRecipient, setNewRecipient] = useState({ email: '', name: '' });
  const [isAddingRecipient, setIsAddingRecipient] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Form setup
  const form = useForm({
    resolver: zodResolver(approvalSchema),
    defaultValues: {
      title: '',
      description: '',
      document_id: '',
      approval_type: 'all',
      recipients: [],
      requester_comments: '',
    },
  });

  const { watch, setValue, getValues, formState: { errors } } = form;
  const watchedValues = watch();

  // Query per ottenere utenti disponibili
  const { data: availableUsers = [] } = useQuery({
    queryKey: ['available-users'],
    queryFn: async () => {
      const response = await apiClient.get('/approvals/users');
      return response.data;
    },
    enabled: isOpen,
  });

  // Query per ottenere documenti dell'utente
  const { data: userDocuments = [], isLoading: loadingDocuments } = useQuery({
    queryKey: ['user-documents-for-approval'],
    queryFn: async () => {
      const response = await apiClient.get('/approvals/documents');
      return response.data;
    },
    enabled: isOpen,
  });

  // Mutation per validazione real-time
  const validateMutation = useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/approvals/validate', data);
      return response.data;
    },
    onSuccess: (data) => {
      setValidationResult(data);
    },
    onError: (error) => {
      console.error('Validation error:', error);
      setValidationResult({ valid: false, errors: ['Errore di validazione'] });
    },
  });

  // Mutation per creare l'approvazione
  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/approvals/', data);
      return response.data;
    },
    onSuccess: (data) => {
      toast({
        title: "Approvazione creata",
        description: `La richiesta "${data.title}" è stata creata con successo.`,
        variant: "success"
      });
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      queryClient.invalidateQueries({ queryKey: ['approval-stats'] });
      onSuccess?.(data);
      handleClose();
    },
    onError: (error) => {
      const errorMessage = error.response?.data?.detail || 'Errore durante la creazione';
      toast({
        title: "Errore",
        description: errorMessage,
        variant: "destructive",
      });
    },
  });

  // Effetto per validazione real-time
  useEffect(() => {
    if (watchedValues.document_id && watchedValues.recipients.length > 0) {
      const delayedValidation = setTimeout(() => {
        validateMutation.mutate(watchedValues);
      }, 500);
      return () => clearTimeout(delayedValidation);
    }
  }, [watchedValues.document_id, watchedValues.recipients, validateMutation]);

  // Handlers
  const handleClose = () => {
    form.reset();
    setSelectedUsers([]);
    setNewRecipient({ email: '', name: '' });
    setIsAddingRecipient(false);
    setValidationResult(null);
    onClose();
  };

  const handleAddRecipient = () => {
    if (newRecipient.email && newRecipient.name) {
      const currentRecipients = getValues('recipients') || [];
      const updatedRecipients = [...currentRecipients, { 
        recipient_email: newRecipient.email,
        recipient_name: newRecipient.name
      }];
      setValue('recipients', updatedRecipients);
      setNewRecipient({ email: '', name: '' });
      setIsAddingRecipient(false);
    }
  };

  const handleRemoveRecipient = (index) => {
    const currentRecipients = getValues('recipients') || [];
    const updatedRecipients = currentRecipients.filter((_, i) => i !== index);
    setValue('recipients', updatedRecipients);
  };

  const handleAddUserAsRecipient = (user) => {
    const currentRecipients = getValues('recipients') || [];
    const exists = currentRecipients.some(r => r.recipient_email === user.email);
    
    if (!exists) {
      const updatedRecipients = [...currentRecipients, {
        recipient_email: user.email,
        recipient_name: user.display_name || user.email,
      }];
      setValue('recipients', updatedRecipients);
      setSelectedUsers([...selectedUsers, user.id]);
    }
  };

  const onSubmit = (data) => {
    createMutation.mutate(data);
  };

  const selectedDocument = userDocuments.find(doc => doc.id === watchedValues.document_id);

return (
  <Dialog open={isOpen} onOpenChange={handleClose}>
    <DialogContent className="w-[95vw] max-w-4xl h-[90vh] flex flex-col p-0 overflow-hidden">
      <DialogHeader className="flex-shrink-0 px-4 py-3 border-b bg-background">
        <DialogTitle className="flex items-center gap-2 text-lg">
          <FileIcon className="h-5 w-5 flex-shrink-0" />
          <span className="truncate">Crea Richiesta di Approvazione</span>
        </DialogTitle>
        <DialogDescription className="text-sm text-muted-foreground">
          Compila i campi qui sotto per creare una nuova richiesta di approvazione.
        </DialogDescription>
      </DialogHeader>

      <div className="flex-1 overflow-y-auto">
        <div className="px-4 py-4">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 max-w-full">
              
              {/* STEP 1: Informazioni Base */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-base font-semibold">
                  <FileIcon className="h-4 w-4 flex-shrink-0" />
                  <span>1. Informazioni Base</span>
                </div>
                
                <div className="space-y-4 pl-6">
                  {/* Titolo */}
                  <FormField
                    control={form.control}
                    name="title"
                    render={({ field }) => (
                      <FormItem className="w-full">
                        <FormLabel className="text-sm font-medium">Titolo della richiesta *</FormLabel>
                        <FormControl>
                          <Input 
                            placeholder="es. Approvazione Contratto Cliente XYZ"
                            className="w-full max-w-full"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Descrizione */}
                  <FormField
                    control={form.control}
                    name="description"
                    render={({ field }) => (
                      <FormItem className="w-full">
                        <FormLabel className="text-sm font-medium">Descrizione</FormLabel>
                        <FormControl>
                          <Textarea 
                            placeholder="Descrizione dettagliata della richiesta..."
                            className="w-full max-w-full min-h-[80px] resize-none"
                            {...field}
                          />
                        </FormControl>
                        <FormDescription className="text-xs text-muted-foreground">
                          Spiega brevemente cosa deve essere approvato
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Documento */}
                  <FormField
                    control={form.control}
                    name="document_id"
                    render={({ field }) => (
                      <FormItem className="w-full">
                        <FormLabel className="text-sm font-medium">Documento da approvare *</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger className="w-full max-w-full">
                              <SelectValue placeholder="Seleziona un documento" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent className="max-w-[90vw]">
                            {loadingDocuments ? (
                              <div className="p-3 text-center">
                                <Loader2 className="h-4 w-4 animate-spin mx-auto mb-2" />
                                <div className="text-sm text-muted-foreground">Caricamento...</div>
                              </div>
                            ) : userDocuments.length === 0 ? (
                              <div className="p-3 text-center text-sm text-muted-foreground">
                                Nessun documento disponibile
                              </div>
                            ) : (
                              userDocuments.map((doc) => (
                                <SelectItem key={doc.id} value={doc.id}>
                                  <div className="flex items-center gap-2 w-full max-w-full">
                                    <FileIcon className="h-4 w-4 flex-shrink-0" />
                                    <div className="flex-1 min-w-0 max-w-full">
                                      <div className="font-medium truncate">
                                        {doc.original_filename || doc.filename}
                                      </div>
                                      <div className="text-xs text-muted-foreground truncate">
                                        {doc.content_type} • {(doc.size / 1024).toFixed(1)} KB
                                      </div>
                                    </div>
                                  </div>
                                </SelectItem>
                              ))
                            )}
                          </SelectContent>
                        </Select>
                        {selectedDocument && (
                          <div className="mt-2 p-2 bg-muted/30 rounded text-xs space-y-1 max-w-full">
                            <div className="truncate"><span className="font-medium">Nome:</span> {selectedDocument.original_filename}</div>
                            <div><span className="font-medium">Tipo:</span> {selectedDocument.content_type}</div>
                            <div><span className="font-medium">Dimensione:</span> {(selectedDocument.size / 1024).toFixed(1)} KB</div>
                          </div>
                        )}
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Tipo di Approvazione */}
                  <FormField
                    control={form.control}
                    name="approval_type"
                    render={({ field }) => (
                      <FormItem className="w-full">
                        <FormLabel className="text-sm font-medium">Tipo di approvazione *</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger className="w-full max-w-full">
                              <SelectValue placeholder="Come devono approvare?" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent className="max-w-[90vw]">
                            <SelectItem value="all">
                              <div className="py-1">
                                <div className="font-medium">🔒 Tutti devono approvare</div>
                                <div className="text-xs text-muted-foreground">
                                  Serve il consenso di tutti i destinatari
                                </div>
                              </div>
                            </SelectItem>
                            <SelectItem value="any">
                              <div className="py-1">
                                <div className="font-medium">⚡ Basta una approvazione</div>
                                <div className="text-xs text-muted-foreground">
                                  Serve il consenso di almeno uno
                                </div>
                              </div>
                            </SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>

              <Separator className="my-6" />

              {/* STEP 2: Destinatari */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-base font-semibold">
                  <Users className="h-4 w-4 flex-shrink-0" />
                  <span>2. Destinatari</span>
                  {watchedValues.recipients?.length > 0 && (
                    <span className="text-sm font-normal text-muted-foreground">
                      ({watchedValues.recipients.length})
                    </span>
                  )}
                </div>

                <div className="space-y-4 pl-6">
                  {/* Lista destinatari */}
                  {watchedValues.recipients?.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm font-medium">Selezionati:</Label>
                      <div className="space-y-2 max-h-32 overflow-y-auto">
                        {watchedValues.recipients.map((recipient, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between p-2 bg-secondary/20 rounded border max-w-full"
                          >
                            <div className="flex-1 min-w-0 mr-2">
                              <div className="font-medium text-sm truncate">
                                {recipient.recipient_name}
                              </div>
                              <div className="text-xs text-muted-foreground truncate">
                                {recipient.recipient_email}
                              </div>
                            </div>
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRemoveRecipient(index)}
                              className="h-6 w-6 p-0 flex-shrink-0 hover:bg-destructive hover:text-destructive-foreground"
                            >
                              <XIcon className="h-3 w-3" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Aggiungi utenti */}
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Aggiungi utenti registrati:</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          type="button"
                          variant="outline"
                          className="w-full max-w-full justify-between"
                        >
                          <span className="truncate">Seleziona utenti...</span>
                          <ChevronDownIcon className="ml-2 h-4 w-4 flex-shrink-0 opacity-50" />
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-[90vw] max-w-md p-0" align="start">
                        <Command>
                          <CommandInput placeholder="Cerca..." />
                          <CommandEmpty>Nessun utente trovato.</CommandEmpty>
                          <CommandGroup className="max-h-48 overflow-y-auto">
                            {availableUsers.map((user) => (
                              <CommandItem
                                key={user.id}
                                onSelect={() => handleAddUserAsRecipient(user)}
                                className="cursor-pointer"
                              >
                                <div className="flex items-center gap-2 w-full min-w-0">
                                  <div className="flex-1 min-w-0">
                                    <div className="font-medium truncate">
                                      {user.display_name || user.email}
                                    </div>
                                    <div className="text-xs text-muted-foreground truncate">
                                      {user.email}
                                    </div>
                                  </div>
                                  {selectedUsers.includes(user.id) && (
                                    <CheckIcon className="h-4 w-4 flex-shrink-0 text-primary" />
                                  )}
                                </div>
                              </CommandItem>
                            ))}
                          </CommandGroup>
                        </Command>
                      </PopoverContent>
                    </Popover>
                  </div>

                  <div className="flex items-center my-3">
                    <div className="flex-1 border-t"></div>
                    <span className="px-2 text-xs text-muted-foreground">oppure</span>
                    <div className="flex-1 border-t"></div>
                  </div>

                  {/* Destinatario esterno */}
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Aggiungi email esterna:</Label>
                    {!isAddingRecipient ? (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setIsAddingRecipient(true)}
                        className="w-full max-w-full"
                      >
                        + Aggiungi destinatario esterno
                      </Button>
                    ) : (
                      <div className="p-3 border rounded bg-muted/10 space-y-3 max-w-full">
                        <div>
                          <Label className="text-xs">Email</Label>
                          <Input
                            placeholder="nome@esempio.com"
                            type="email"
                            value={newRecipient.email}
                            onChange={(e) => setNewRecipient(prev => ({
                              ...prev,
                              email: e.target.value
                            }))}
                            className="mt-1 w-full max-w-full"
                          />
                        </div>
                        <div>
                          <Label className="text-xs">Nome</Label>
                          <Input
                            placeholder="Nome Cognome"
                            value={newRecipient.name}
                            onChange={(e) => setNewRecipient(prev => ({
                              ...prev,
                              name: e.target.value
                            }))}
                            className="mt-1 w-full max-w-full"
                          />
                        </div>
                        <div className="flex gap-2">
                          <Button
                            type="button"
                            onClick={handleAddRecipient}
                            disabled={!newRecipient.email || !newRecipient.name}
                            className="flex-1"
                          >
                            Aggiungi
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            onClick={() => {
                              setIsAddingRecipient(false);
                              setNewRecipient({ email: '', name: '' });
                            }}
                            className="flex-1"
                          >
                            Annulla
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>

                  {errors.recipients && (
                    <Alert variant="destructive">
                      <AlertCircleIcon className="h-4 w-4" />
                      <AlertDescription className="text-sm">
                        {errors.recipients.message}
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              </div>

              <Separator className="my-6" />

              {/* STEP 3: Commenti */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-base font-semibold">
                  <MessageSquare className="h-4 w-4 flex-shrink-0" />
                  <span>3. Commenti (Opzionale)</span>
                </div>

                <div className="pl-6">
                  <FormField
                    control={form.control}
                    name="requester_comments"
                    render={({ field }) => (
                      <FormItem className="w-full">
                        <FormLabel className="text-sm font-medium">Note per i destinatari</FormLabel>
                        <FormControl>
                          <Textarea 
                            placeholder="Note opzionali per i destinatari..."
                            className="w-full max-w-full min-h-[80px] resize-none"
                            {...field}
                          />
                        </FormControl>
                        <FormDescription className="text-xs text-muted-foreground">
                          Incluse nell'email di notifica (max 500 caratteri)
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>

              {/* Validazione */}
              {validationResult && (
                <Alert variant={validationResult.valid ? "default" : "destructive"} className="mx-4">
                  <AlertCircleIcon className="h-4 w-4 flex-shrink-0" />
                  <AlertDescription>
                    {validationResult.valid ? (
                      <div className="space-y-1">
                        <div className="font-medium">✅ Pronto per l'invio!</div>
                        <div className="text-xs space-y-1">
                          <div>📄 {validationResult.document_name}</div>
                          <div>👥 {validationResult.recipient_count} destinatari</div>
                          <div>🔒 {validationResult.approval_type === 'all' ? 'Tutti' : 'Almeno uno'}</div>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div className="font-medium">❌ Completa questi campi:</div>
                        <ul className="text-xs mt-1 space-y-1">
                          {validationResult.errors?.map((error, index) => (
                            <li key={index}>• {error}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
              )}
            </form>
          </Form>
        </div>
      </div>

      <DialogFooter className="flex-shrink-0 px-4 py-3 border-t bg-background">
        <div className="flex gap-2 w-full">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={createMutation.isPending}
            className="flex-1 sm:flex-none"
          >
            Annulla
          </Button>
          <Button
            type="submit"
            disabled={createMutation.isPending || !validationResult?.valid}
            onClick={form.handleSubmit(onSubmit)}
            className="flex-1 sm:flex-none"
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-1" />
                Creando...
              </>
            ) : (
              'Crea Richiesta'
            )}
          </Button>
        </div>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);

}
