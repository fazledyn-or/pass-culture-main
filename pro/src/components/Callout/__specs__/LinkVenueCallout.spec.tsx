import { screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import React from 'react'

import LinkVenueCallout, {
  LinkVenueCalloutProps,
} from 'components/Callout/LinkVenueCallout'
import { BankAccountEvents } from 'core/FirebaseEvents/constants'
import * as useAnalytics from 'hooks/useAnalytics'
import { defaultGetOffererResponseModel } from 'utils/apiFactories'
import { renderWithProviders } from 'utils/renderWithProviders'

const mockLogEvent = vi.fn()

describe('LinkVenueCallout', () => {
  let props: LinkVenueCalloutProps = {
    titleOnly: false,
  }
  it('should not render LinkVenueCallout without FF', () => {
    renderWithProviders(<LinkVenueCallout {...props} />)

    expect(
      screen.queryByText(/Dernière étape pour vous faire rembourser/)
    ).not.toBeInTheDocument()
    expect(
      screen.queryByText(
        /Afin de percevoir vos remboursements, vous devez rattacher vos lieux/
      )
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('link', {
        name: 'Gérer le rattachement de mes lieux',
      })
    ).not.toBeInTheDocument()
  })

  describe('With FF enabled', () => {
    const storeOverrides = {
      features: {
        list: [
          { isActive: true, nameKey: 'WIP_ENABLE_NEW_BANK_DETAILS_JOURNEY' },
        ],
      },
    }

    it.each([
      {
        ...defaultGetOffererResponseModel,
        hasValidBankAccount: true,
        venuesWithNonFreeOffersWithoutBankAccounts: [],
      },
      {
        ...defaultGetOffererResponseModel,
        id: 2,
        hasValidBankAccount: false,
        venuesWithNonFreeOffersWithoutBankAccounts: [1],
      },
    ])(
      'should not render the add link venue banner if the offerer  hasValidBankAccount = $hasValidBankAccount and venuesWithNonFreeOffersWithoutBankAccounts = $venuesWithNonFreeOffersWithoutBankAccounts',
      ({
        hasValidBankAccount,
        venuesWithNonFreeOffersWithoutBankAccounts,
        ...rest
      }) => {
        props.offerer = {
          ...rest,
          hasValidBankAccount,
          venuesWithNonFreeOffersWithoutBankAccounts,
        }
        renderWithProviders(<LinkVenueCallout {...props} />, {
          storeOverrides,
        })

        expect(
          screen.queryByText(/Dernière étape pour vous faire rembourser/)
        ).not.toBeInTheDocument()
      }
    )

    it('should render LinkVenueCallout', () => {
      props.offerer = {
        ...defaultGetOffererResponseModel,
        hasValidBankAccount: true,
        venuesWithNonFreeOffersWithoutBankAccounts: [1],
      }
      renderWithProviders(<LinkVenueCallout {...props} />, {
        storeOverrides,
      })

      expect(
        screen.getByText(/Dernière étape pour vous faire rembourser/)
      ).toBeInTheDocument()
      expect(
        screen.getByText(
          /Afin de percevoir vos remboursements, vous devez rattacher/
        )
      ).toBeInTheDocument()
      expect(
        screen.getByRole('link', {
          name: 'Gérer le rattachement de mes lieux',
        })
      ).toBeInTheDocument()
    })

    it('should render LinkVenueCallout with singular wording', () => {
      props.titleOnly = false
      props.offerer = {
        ...defaultGetOffererResponseModel,
        hasValidBankAccount: true,
        venuesWithNonFreeOffersWithoutBankAccounts: [1],
      }
      renderWithProviders(<LinkVenueCallout {...props} />, {
        storeOverrides,
      })

      expect(
        screen.getByText(
          /Dernière étape pour vous faire rembourser : rattachez votre lieu/
        )
      ).toBeInTheDocument()
      expect(
        screen.getByText(
          /Afin de percevoir vos remboursements, vous devez rattacher votre lieu/
        )
      ).toBeInTheDocument()
    })

    it('should render LinkVenueCallout with singular plural', () => {
      props = {
        titleOnly: false,
      }
      props.offerer = {
        ...defaultGetOffererResponseModel,
        hasValidBankAccount: true,
        venuesWithNonFreeOffersWithoutBankAccounts: [1, 2],
      }
      renderWithProviders(<LinkVenueCallout {...props} />, {
        storeOverrides,
      })

      expect(
        screen.getByText(
          /Dernière étape pour vous faire rembourser : rattachez vos lieux/
        )
      ).toBeInTheDocument()
      expect(
        screen.getByText(
          /Afin de percevoir vos remboursements, vous devez rattacher vos lieux/
        )
      ).toBeInTheDocument()
    })

    it('should log add venue bank to account', async () => {
      vi.spyOn(useAnalytics, 'default').mockImplementation(() => ({
        logEvent: mockLogEvent,
      }))

      props.offerer = {
        ...defaultGetOffererResponseModel,
        hasValidBankAccount: true,
        venuesWithNonFreeOffersWithoutBankAccounts: [1],
      }

      renderWithProviders(<LinkVenueCallout {...props} />, {
        storeOverrides,
        initialRouterEntries: ['/accueil'],
      })

      await userEvent.click(
        screen.getByRole('link', {
          name: 'Gérer le rattachement de mes lieux',
        })
      )

      expect(mockLogEvent).toHaveBeenCalledWith(
        BankAccountEvents.CLICKED_ADD_VENUE_TO_BANK_ACCOUNT,
        {
          from: '/accueil',
          offererId: 0,
        }
      )
    })
  })
})
