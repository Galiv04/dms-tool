// frontend/src/utils/dateUtils.js
/**
 * Utility per gestione datetime con timezone - Versione produzione
 */

/**
 * Funzione helper per parsare date che possono essere naive o aware
 */
const parseDateTime = (isoString) => {
  if (!isoString) return null;
  
  // console.log("🔧 parseDateTime input:", isoString);
  
  // Se la string non ha timezone info, assumila come UTC
  if (isoString.includes('T') && 
      !isoString.includes('Z') && 
      !isoString.includes('+') && 
      !isoString.includes('-', 19)) {
    // Aggiungi 'Z' per indicare che è UTC
    const utcString = isoString + 'Z';
    // console.log("🔧 Converted to UTC:", utcString);
    return new Date(utcString);
  }
  
  // Ha già timezone info, usa normalmente
  // console.log("🔧 Using as-is (has timezone)");
  return new Date(isoString);
};

/**
 * Formatta una data ISO in formato locale italiano
 * @param {string} isoString - Data in formato ISO (es: "2024-01-15T10:30:00Z")
 * @returns {string} Data formattata (es: "15/01/2024, 11:30")
 */
export const formatLocalDateTime = (isoString) => {
  if (!isoString) return 'Data non disponibile';
  
  try {
    const date = parseDateTime(isoString);
    if (!date || isNaN(date.getTime())) {
      return 'Data non valida';
    }
    
    return new Intl.DateTimeFormat('it-IT', {
      year: 'numeric',
      month: '2-digit', 
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    }).format(date);
  } catch (error) {
    console.error('Errore nel formatare la data:', error);
    return 'Data non valida';
  }
};

/**
 * Restituisce tempo relativo (es: "2 ore fa", "3 giorni fa")
 * @param {string} isoString - Data in formato ISO
 * @returns {string} Tempo relativo
 */
export const getRelativeTime = (isoString) => {
  if (!isoString) return 'Data non disponibile';
  
  try {
    const date = parseDateTime(isoString);
    if (!date || isNaN(date.getTime())) {
      return 'Data non valida';
    }
    
    const now = new Date();
    const diffMs = now - date;
    
    // console.log("🔧 getRelativeTime - date:", date);
    // console.log("🔧 getRelativeTime - now:", now);
    // console.log("🔧 getRelativeTime - diffMs:", diffMs);
    
    // Converti millisecondi in unità più leggibili
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    // Gestisci date future (negative)
    if (diffMs < 0) {
      return 'In futuro';
    }
    
    // Determina l'unità più appropriata
    if (diffSeconds < 30) {
      return 'Ora';
    } else if (diffMinutes < 1) {
      return 'Meno di un minuto fa';
    } else if (diffMinutes < 60) {
      return `${diffMinutes} ${diffMinutes === 1 ? 'minuto' : 'minuti'} fa`;
    } else if (diffHours < 24) {
      return `${diffHours} ${diffHours === 1 ? 'ora' : 'ore'} fa`;
    } else if (diffDays < 30) {
      return `${diffDays} ${diffDays === 1 ? 'giorno' : 'giorni'} fa`;
    } else {
      // Per date più vecchie, mostra la data completa
      return formatLocalDateTime(isoString);
    }
  } catch (error) {
    console.error('Errore nel calcolare il tempo relativo:', error);
    return 'Data non valida';
  }
};

/**
 * Formatta solo la data (senza ora)
 * @param {string} isoString - Data in formato ISO
 * @returns {string} Data formattata (es: "15/01/2024")
 */
export const formatLocalDate = (isoString) => {
  if (!isoString) return 'Data non disponibile';
  
  try {
    const date = parseDateTime(isoString);
    if (!date || isNaN(date.getTime())) {
      return 'Data non valida';
    }
    
    return new Intl.DateTimeFormat('it-IT', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    }).format(date);
  } catch (error) {
    console.error('Errore nel formatare la data:', error);
    return 'Data non valida';
  }
};

/**
 * Formatta solo l'ora (senza data)
 * @param {string} isoString - Data in formato ISO  
 * @returns {string} Ora formattata (es: "11:30")
 */
export const formatLocalTime = (isoString) => {
  if (!isoString) return 'Ora non disponibile';
  
  try {
    const date = parseDateTime(isoString);
    if (!date || isNaN(date.getTime())) {
      return 'Ora non valida';
    }
    
    return new Intl.DateTimeFormat('it-IT', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    }).format(date);
  } catch (error) {
    console.error('Errore nel formatare l\'ora:', error);
    return 'Ora non valida';
  }
};

/**
 * Determina l'urgenza di una scadenza
 * @param {string} isoString - Data di scadenza in formato ISO
 * @returns {string|null} 'expired', 'urgent', 'warning', 'normal', o null
 */
export const getExpiryUrgency = (isoString) => {
  if (!isoString) return null;
  
  try {
    const expiryDate = parseDateTime(isoString);
    if (!expiryDate || isNaN(expiryDate.getTime())) {
      return null;
    }
    
    const now = new Date();
    const hoursUntilExpiry = (expiryDate - now) / (1000 * 60 * 60);
    
    if (hoursUntilExpiry < 0) return 'expired';
    if (hoursUntilExpiry < 24) return 'urgent';
    if (hoursUntilExpiry < 72) return 'warning';
    return 'normal';
  } catch (error) {
    console.error('Errore nel calcolare l\'urgenza:', error);
    return null;
  }
};

/**
 * Converte un datetime in timestamp Unix (secondi)
 * @param {string} isoString - Data in formato ISO
 * @returns {number|null} Timestamp Unix o null se errore
 */
export const toUnixTimestamp = (isoString) => {
  if (!isoString) return null;
  
  try {
    const date = parseDateTime(isoString);
    return date ? Math.floor(date.getTime() / 1000) : null;
  } catch (error) {
    console.error('Errore nella conversione timestamp:', error);
    return null;
  }
};

/**
 * Converte un timestamp Unix in data locale
 * @param {number} timestamp - Timestamp Unix (secondi)
 * @returns {string} Data formattata locale
 */
export const fromUnixTimestamp = (timestamp) => {
  if (!timestamp || typeof timestamp !== 'number') {
    return 'Data non disponibile';
  }
  
  try {
    const date = new Date(timestamp * 1000);
    return formatLocalDateTime(date.toISOString());
  } catch (error) {
    console.error('Errore nella conversione da timestamp:', error);
    return 'Data non valida';
  }
};

/**
 * Verifica se una data è nel futuro
 * @param {string} isoString - Data in formato ISO
 * @returns {boolean} True se la data è nel futuro
 */
export const isFuture = (isoString) => {
  if (!isoString) return false;
  
  try {
    const date = parseDateTime(isoString);
    if (!date || isNaN(date.getTime())) {
      return false;
    }
    
    return date > new Date();
  } catch (error) {
    console.error('Errore nel verificare data futura:', error);
    return false;
  }
};

/**
 * Verifica se una data è nel passato
 * @param {string} isoString - Data in formato ISO
 * @returns {boolean} True se la data è nel passato
 */
export const isPast = (isoString) => {
  if (!isoString) return false;
  
  try {
    const date = parseDateTime(isoString);
    if (!date || isNaN(date.getTime())) {
      return false;
    }
    
    return date < new Date();
  } catch (error) {
    console.error('Errore nel verificare data passata:', error);
    return false;
  }
};

// Export per compatibilità con versioni precedenti
export default {
  formatLocalDateTime,
  getRelativeTime,
  formatLocalDate,
  formatLocalTime,
  getExpiryUrgency,
  toUnixTimestamp,
  fromUnixTimestamp,
  isFuture,
  isPast
};
