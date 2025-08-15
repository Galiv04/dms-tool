// frontend/src/components/approvals/__tests__/ApprovalCard.test.jsx
import { describe, test, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ApprovalCard } from '../../components/approvals/ApprovalCard'

// Mock delle utility
vi.mock('../../utils/dateUtils', () => ({
  getRelativeTime: vi.fn(() => '2 ore fa'),
  formatLocalDateTime: vi.fn(() => '15/01/2024, 10:30')
}))

describe('ApprovalCard', () => {
  const mockApproval = {
    id: 1,
    title: 'Test Approval',
    description: 'Test Description',
    status: 'pending',
    created_at: '2024-01-15T10:30:00Z',
    requester: {
      display_name: 'Mario Rossi'
    },
    document: {
      filename: 'test.pdf'
    }
  }

  test('renderizza correttamente le informazioni base', () => {
    render(<ApprovalCard approval={mockApproval} />)
    
    expect(screen.getByText('Test Approval')).toBeInTheDocument()
    expect(screen.getByText('Test Description')).toBeInTheDocument()
    expect(screen.getByText('Mario Rossi')).toBeInTheDocument()
    expect(screen.getByText('test.pdf')).toBeInTheDocument()
  })

  test('mostra il tempo relativo corretto', () => {
    render(<ApprovalCard approval={mockApproval} />)
    
    expect(screen.getByText('2 ore fa')).toBeInTheDocument()
  })

  test('chiama onClick quando cliccato', () => {
    const mockOnClick = vi.fn()
    render(<ApprovalCard approval={mockApproval} onClick={mockOnClick} />)
    
    fireEvent.click(screen.getByRole('button'))
    expect(mockOnClick).toHaveBeenCalledWith(mockApproval)
  })
})
