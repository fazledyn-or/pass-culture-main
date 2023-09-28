import { screen, waitForElementToBeRemoved } from '@testing-library/react'

import { api } from 'apiClient/api'
import { renderWithProviders } from 'utils/renderWithProviders'

import Reimbursements from '../Reimbursements'

vi.spyOn(api, 'listOfferersNames').mockResolvedValue({
  offerersNames: [
    {
      id: 1,
      name: 'first offerer',
    },
  ],
})

vi.spyOn(api, 'getOfferer').mockResolvedValue({
  address: null,
  apiKey: {
    maxAllowed: 0,
    prefixes: [],
  },
  city: 'city',
  dateCreated: '1010/10/10',
  demarchesSimplifieesApplicationId: null,
  hasAvailablePricingPoints: false,
  hasDigitalVenueAtLeastOneOffer: false,
  hasValidBankAccount: false,
  hasPendingBankAccount: false,
  venuesWithNonFreeOffersWithoutBankAccounts: [],
  isActive: false,
  isValidated: false,
  managedVenues: [],
  name: 'name',
  id: 10,
  postalCode: '123123',
  siren: null,
  dsToken: '',
})

const renderReimbursements = async (storeOverrides: any) => {
  renderWithProviders(<Reimbursements />, {
    storeOverrides,
    initialRouterEntries: ['/remboursements/justificatifs'],
  })
}

describe('Reimbursement page', () => {
  let store: any

  beforeEach(() => {
    store = {
      user: {
        currentUser: {
          isAdmin: false,
          hasSeenProTutorials: true,
        },
        initialized: true,
      },
      features: {
        list: [
          { isActive: false, nameKey: 'WIP_ENABLE_NEW_BANK_DETAILS_JOURNEY' },
        ],
      },
    }
  })

  it('should render reimbursement page with FF WIP_ENABLE_NEW_BANK_DETAILS_JOURNEY off', async () => {
    renderReimbursements(store)

    expect(
      screen.getByText('Justificatifs de remboursement')
    ).toBeInTheDocument()
    expect(screen.getByText('Détails des remboursements')).toBeInTheDocument()
    expect(screen.queryByText('Informations bancaires')).not.toBeInTheDocument()

    expect(
      screen.getByText(
        'Les remboursements s’effectuent tous les 15 jours, rétroactivement suite à la validation d’une contremarque dans le guichet ou à la validation automatique des contremarques d’évènements. Cette page est automatiquement mise à jour à chaque remboursement.'
      )
    ).toBeInTheDocument()
  })

  it('should render reimbursement page with FF WIP_ENABLE_NEW_BANK_DETAILS_JOURNEY enabled', async () => {
    store.features.list[0].isActive = true
    renderReimbursements(store)

    await waitForElementToBeRemoved(() => screen.queryByTestId('spinner'))

    expect(screen.getByText(/Justificatifs/)).toBeInTheDocument()
    expect(screen.getByText(/Détails/)).toBeInTheDocument()
    expect(screen.getByText('Informations bancaires')).toBeInTheDocument()

    expect(
      screen.queryByText(
        'Les remboursements s’effectuent tous les 15 jours, rétroactivement suite à la validation d’une contremarque dans le guichet ou à la validation automatique des contremarques d’évènements. Cette page est automatiquement mise à jour à chaque remboursement.'
      )
    ).not.toBeInTheDocument()
  })
})
