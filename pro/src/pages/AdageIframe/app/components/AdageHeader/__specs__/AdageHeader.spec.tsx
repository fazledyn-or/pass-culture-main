// @vitest-environment happy-dom
import { screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import React from 'react'
import * as instantSearch from 'react-instantsearch'

import { AdageFrontRoles, AuthenticatedResponse } from 'apiClient/adage'
import { AdageHeaderLink } from 'apiClient/adage/models/AdageHeaderLink'
import { apiAdage } from 'apiClient/api'
import * as useNotification from 'hooks/useNotification'
import { AdageUserContextProvider } from 'pages/AdageIframe/app/providers/AdageUserContext'
import {
  defaultEducationalInstitution,
  defaultUseStatsReturn,
} from 'utils/adageFactories'
import { renderWithProviders } from 'utils/renderWithProviders'

import { AdageHeader } from '../AdageHeader'

interface HeaderLinkProps {
  headerLinkLabel: string
  headerLinkName: AdageHeaderLink
}

const renderAdageHeader = (
  user: AuthenticatedResponse,
  storeOverrides?: any
) => {
  renderWithProviders(
    <AdageUserContextProvider adageUser={user}>
      <AdageHeader />
    </AdageUserContextProvider>,
    { storeOverrides }
  )
}

const isDiscoveryActive = {
  features: {
    list: [
      {
        nameKey: 'WIP_ENABLE_DISCOVERY',
        isActive: true,
      },
    ],
    initialized: true,
  },
}

vi.mock('apiClient/api', () => ({
  apiAdage: {
    logHeaderLinkClick: vi.fn(),
    getEducationalInstitutionWithBudget: vi.fn(),
  },
}))

vi.mock('react-instantsearch', async () => {
  return {
    ...((await vi.importActual('react-instantsearch')) ?? {}),
    useStats: () => {},
  }
})

describe('AdageHeader', () => {
  const notifyError = vi.fn()
  const user = {
    role: AdageFrontRoles.REDACTOR,
    uai: 'uai',
    departmentCode: '30',
    institutionName: 'COLLEGE BELLEVUE',
    institutionCity: 'ALES',
  }

  beforeEach(() => {
    vi.spyOn(useNotification, 'default').mockImplementation(() => ({
      ...vi.importActual('hooks/useNotification'),
      error: notifyError,
    }))
    vi.spyOn(apiAdage, 'getEducationalInstitutionWithBudget').mockResolvedValue(
      defaultEducationalInstitution
    )
    vi.spyOn(instantSearch, 'useStats').mockImplementation(
      () => defaultUseStatsReturn
    )
  })

  it('should render adage header', async () => {
    renderAdageHeader(user)
    await waitFor(() =>
      expect(
        apiAdage.getEducationalInstitutionWithBudget
      ).toHaveBeenCalledTimes(1)
    )

    expect(screen.getByRole('link', { name: 'Rechercher' })).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: 'Pour mon établissement 0' })
    ).toBeInTheDocument()
    expect(
      screen.queryByRole('link', { name: 'Découvrir' })
    ).not.toBeInTheDocument()
    screen.queryByRole('link', { name: /Solde prévisionnel/ })
  })

  it('should render adage header with link for discovery', async () => {
    renderAdageHeader(user, isDiscoveryActive)
    await waitFor(() =>
      expect(
        apiAdage.getEducationalInstitutionWithBudget
      ).toHaveBeenCalledTimes(1)
    )

    expect(screen.getByRole('link', { name: 'Découvrir' })).toBeInTheDocument()
  })

  it('should render the number of hits', async () => {
    vi.spyOn(instantSearch, 'useStats').mockImplementation(() => ({
      ...defaultUseStatsReturn,
      nbHits: 2,
    }))
    renderAdageHeader(user)
    await waitFor(() =>
      expect(screen.getByText('Solde prévisionnel')).toBeInTheDocument()
    )
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('should display the institution budget', async () => {
    renderAdageHeader(user)
    await waitFor(() =>
      expect(screen.getByText('Solde prévisionnel')).toBeInTheDocument()
    )

    expect(screen.getByText('1 000 €')).toBeInTheDocument()
  })

  it('should return an error when the institution budget could not be retrieved', async () => {
    vi.spyOn(
      apiAdage,
      'getEducationalInstitutionWithBudget'
    ).mockRejectedValueOnce({})

    renderAdageHeader(user)
    await waitFor(() =>
      expect(apiAdage.getEducationalInstitutionWithBudget).toHaveBeenCalled()
    )

    expect(notifyError).toHaveBeenNthCalledWith(
      1,
      'Nous avons rencontré un problème lors du chargemement des données'
    )
  })

  const headerLinks: HeaderLinkProps[] = [
    { headerLinkLabel: 'Rechercher', headerLinkName: AdageHeaderLink.SEARCH },
    {
      headerLinkLabel: 'Pour mon établissement 0',
      headerLinkName: AdageHeaderLink.MY_INSTITUTION_OFFERS,
    },
    {
      headerLinkLabel: 'Nouvelle fenêtre Solde prévisionnel',
      headerLinkName: AdageHeaderLink.ADAGE_LINK,
    },
  ]
  it.each(headerLinks)(
    'should log click on header link',
    async (headerLink: HeaderLinkProps) => {
      renderAdageHeader(user)
      await waitFor(() =>
        expect(screen.getByText('Solde prévisionnel')).toBeInTheDocument()
      )

      await userEvent.click(
        screen.getByRole('link', { name: headerLink.headerLinkLabel })
      )
      expect(apiAdage.logHeaderLinkClick).toHaveBeenCalledTimes(1)
      expect(apiAdage.logHeaderLinkClick).toHaveBeenCalledWith({
        iframeFrom: '/',
        header_link_name: headerLink.headerLinkName,
      })
    }
  )
  it('should not display budget when user is readonly ', () => {
    vi.spyOn(apiAdage, 'getEducationalInstitutionWithBudget')

    renderAdageHeader({ ...user, role: AdageFrontRoles.READONLY })

    expect(apiAdage.getEducationalInstitutionWithBudget).not.toHaveBeenCalled()
  })

  it('should not display adage link when user is readonly ', () => {
    vi.spyOn(apiAdage, 'getEducationalInstitutionWithBudget')

    renderAdageHeader({ ...user, role: AdageFrontRoles.READONLY })

    expect(
      screen.queryByRole('link', { name: /Solde prévisionnel/ })
    ).not.toBeInTheDocument()
  })

  it('should not display help download link when user is readonly ', () => {
    vi.spyOn(apiAdage, 'getEducationalInstitutionWithBudget')

    renderAdageHeader({ ...user, role: AdageFrontRoles.READONLY })

    expect(
      screen.queryByRole('link', { name: 'Télécharger l’aide' })
    ).not.toBeInTheDocument()
  })

  it('should display a favorites tab in the header', () => {
    vi.spyOn(apiAdage, 'getEducationalInstitutionWithBudget')

    renderAdageHeader(user)

    expect(
      screen.queryByRole('link', { name: /Mes Favoris/ })
    ).toBeInTheDocument()
  })

  it('should display the user favorite count after the favorite tab name', () => {
    vi.spyOn(apiAdage, 'getEducationalInstitutionWithBudget')

    renderAdageHeader({ ...user, favoritesCount: 10 })

    expect(
      screen.queryByRole('link', { name: /Mes Favoris (10)/ })
    ).toBeInTheDocument()
  })
})
