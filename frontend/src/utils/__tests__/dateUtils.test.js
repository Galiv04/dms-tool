// frontend/src/utils/__tests__/dateUtils.test.js
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest'
import { 
  formatLocalDateTime, 
  getRelativeTime, 
  formatLocalDate, 
  formatLocalTime 
} from '../dateUtils'

describe('dateUtils', () => {
  beforeEach(() => {
    // Mock della data corrente per test consistenti
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-01-15T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('formatLocalDateTime', () => {
    test('formatta correttamente datetime ISO', () => {
      const isoString = '2024-01-15T10:30:00Z'
      const result = formatLocalDateTime(isoString)
      expect(result).toMatch(/\d{2}\/\d{2}\/\d{4}, \d{2}:\d{2}/)
    })

    test('gestisce input null/undefined', () => {
      expect(formatLocalDateTime(null)).toBe('Data non disponibile')
      expect(formatLocalDateTime(undefined)).toBe('Data non disponibile')
      expect(formatLocalDateTime('')).toBe('Data non disponibile')
    })

    test('gestisce date invalide', () => {
      expect(formatLocalDateTime('invalid-date')).toBe('Data non valida')
    })
  })

  describe('getRelativeTime', () => {
    test('calcola "ora" per differenze < 1 minuto', () => {
      const now = new Date('2024-01-15T12:00:00Z').toISOString()
      expect(getRelativeTime(now)).toBe('Ora')
    })

    test('calcola minuti fa', () => {
      const fiveMinutesAgo = new Date('2024-01-15T11:55:00Z').toISOString()
      expect(getRelativeTime(fiveMinutesAgo)).toBe('5 minuti fa')
    })

    test('calcola ore fa', () => {
      const twoHoursAgo = new Date('2024-01-15T10:00:00Z').toISOString()
      expect(getRelativeTime(twoHoursAgo)).toBe('2 ore fa')
    })

    test('calcola giorni fa', () => {
      const threeDaysAgo = new Date('2024-01-12T12:00:00Z').toISOString()
      expect(getRelativeTime(threeDaysAgo)).toBe('3 giorni fa')
    })

    test('gestisce date future', () => {
      const future = new Date('2024-01-16T12:00:00Z').toISOString()
      expect(getRelativeTime(future)).toBe('In futuro')
    })

    test('gestisce input invalidi', () => {
      expect(getRelativeTime(null)).toBe('Data non disponibile')
      expect(getRelativeTime('invalid')).toBe('Data non valida')
    })
  })

  describe('formatLocalDate', () => {
    test('formatta solo la data', () => {
      const isoString = '2024-01-15T10:30:00Z'
      const result = formatLocalDate(isoString)
      expect(result).toMatch(/\d{2}\/\d{2}\/\d{4}/)
      expect(result).not.toMatch(/:/) // Non deve contenere orario
    })
  })

  describe('formatLocalTime', () => {
    test('formatta solo l\'ora', () => {
      const isoString = '2024-01-15T10:30:00Z'
      const result = formatLocalTime(isoString)
      expect(result).toMatch(/\d{2}:\d{2}/)
      expect(result).not.toMatch(/\d{4}/) // Non deve contenere anno
    })
  })
})
