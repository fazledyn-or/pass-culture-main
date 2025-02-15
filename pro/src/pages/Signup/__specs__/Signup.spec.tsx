import { screen } from '@testing-library/react'
import React from 'react'

import { renderWithProviders } from 'utils/renderWithProviders'

import Signup from '../Signup'

vi.mock('apiClient/api', () => ({
  api: {
    getProfile: vi.fn(),
    listFeatures: vi.fn(),
    listOfferersNames: vi.fn(),
    getSirenInfo: vi.fn(),
  },
}))

describe('src | components | pages | Signup', () => {
  let storeOverrides: any
  beforeEach(() => {
    storeOverrides = {
      user: {
        currentUser: null,
      },
      features: {
        list: [{ isActive: true, nameKey: 'ENABLE_PRO_ACCOUNT_CREATION' }],
      },
    }
  })

  it('should render logo and sign-up form', () => {
    renderWithProviders(<Signup />, {
      storeOverrides,
      initialRouterEntries: ['/'], // /inscription
    })

    expect(
      screen.getByRole('heading', { name: /Créer votre compte/ })
    ).toBeInTheDocument()
  })

  it('should render logo and confirmation page', () => {
    renderWithProviders(<Signup />, {
      storeOverrides,
      initialRouterEntries: ['/confirmation'], // /inscription/confirmation
    })

    expect(
      screen.getByText(/Votre compte est en cours de création./)
    ).toBeInTheDocument()
  })

  it('should render maintenance page when signup is unavailable', () => {
    const storeOverrides = {
      features: {
        list: [{ isActive: false, nameKey: 'ENABLE_PRO_ACCOUNT_CREATION' }],
      },
    }

    renderWithProviders(<Signup />, {
      storeOverrides,
      initialRouterEntries: ['/inscription'],
    })

    expect(
      screen.getByRole('heading', { name: /Inscription indisponible/ })
    ).toBeInTheDocument()
  })
})
