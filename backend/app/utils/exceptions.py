"""
Custom exceptions per l'applicazione DMS
"""

class DMSException(Exception):
    """Base exception per l'applicazione DMS"""
    pass

class ValidationError(DMSException):
    """Errore di validazione dati"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

class NotFoundError(DMSException):
    """Risorsa non trovata"""
    def __init__(self, message: str, resource_type: str = None):
        self.message = message
        self.resource_type = resource_type
        super().__init__(self.message)

class PermissionDeniedError(DMSException):
    """Permessi insufficienti"""
    def __init__(self, message: str, required_permission: str = None):
        self.message = message
        self.required_permission = required_permission
        super().__init__(self.message)

class BusinessLogicError(DMSException):
    """Errore di logica di business"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ExternalServiceError(DMSException):
    """Errore servizio esterno (email, etc.)"""
    def __init__(self, message: str, service_name: str = None):
        self.message = message
        self.service_name = service_name
        super().__init__(self.message)
