import { screen } from '@testing-library/react'
import { addDays } from 'date-fns'
import React from 'react'

import { DMSApplicationstatus } from 'apiClient/v1'
import { defaultCollectiveDmsApplication } from 'utils/collectiveApiFactories'
import { renderWithProviders } from 'utils/renderWithProviders'

import Venue, { VenueProps } from '../Venue'

const renderVenue = (
  props: VenueProps,
  features?: { list: { isActive: true; nameKey: string }[] }
) => {
  const storeOverrides = {
    features: features,
  }
  renderWithProviders(<Venue {...props} />, {
    storeOverrides: { ...storeOverrides },
  })
}

describe('venues', () => {
  let props: VenueProps
  const offererId = 12
  const venueId = 1

  beforeEach(() => {
    props = {
      venueId: venueId,
      isVirtual: false,
      name: 'My venue',
      offererId: offererId,
      dmsInformations: null,
      offererHasBankAccount: false,
      hasNonFreeOffer: false,
      isFirstVenue: false,
    }
  })

  describe('physical venue section', () => {
    it('should display edition venue link', () => {
      props.isVirtual = false

      renderVenue(props)

      expect(
        screen.getByRole('link', { name: 'Éditer le lieu' })
      ).toHaveAttribute(
        'href',
        `/structures/${offererId}/lieux/${venueId}?modification`
      )
    })

    it('should display add bank information when venue does not have a reimbursement point', () => {
      props.hasMissingReimbursementPoint = true
      props.offererHasCreatedOffer = true
      props.venueHasCreatedOffer = true

      renderVenue(props)

      expect(
        screen.getByRole('link', { name: 'Ajouter un RIB' })
      ).toHaveAttribute(
        'href',
        `/structures/${offererId}/lieux/${venueId}?modification#remboursement`
      )
    })

    it('should not display add bank information when for the new bank details journey is enabled', () => {
      props.hasMissingReimbursementPoint = true
      props.offererHasCreatedOffer = true
      props.venueHasCreatedOffer = true

      renderVenue(props, {
        list: [
          { isActive: true, nameKey: 'WIP_ENABLE_NEW_BANK_DETAILS_JOURNEY' },
        ],
      })

      expect(
        screen.queryByRole('link', { name: 'Ajouter un RIB' })
      ).not.toBeInTheDocument()
    })
  })

  it('should not display dms timeline link if venue has no dms application', () => {
    renderVenue({
      ...props,
      hasAdageId: false,
      dmsInformations: null,
    })

    expect(
      screen.queryByRole('link', {
        name: 'Suivre ma demande de référencement ADAGE',
      })
    ).not.toBeInTheDocument()
  })

  it('should display dms timeline link when venue has dms applicaiton and adage id less than 30 days', () => {
    renderVenue({
      ...props,
      hasAdageId: true,
      adageInscriptionDate: addDays(new Date(), -15).toISOString(),
      dmsInformations: {
        ...defaultCollectiveDmsApplication,
        state: DMSApplicationstatus.ACCEPTE,
      },
    })

    expect(
      screen.getByRole('link', {
        name: 'Suivre ma demande de référencement ADAGE',
      })
    ).toHaveAttribute(
      'href',
      `/structures/${offererId}/lieux/${venueId}#venue-collective-data`
    )
  })

  it('should not display dms timeline link if venue has adageId for more than 30days', () => {
    renderVenue({
      ...props,
      hasAdageId: true,
      adageInscriptionDate: addDays(new Date(), -32).toISOString(),
      dmsInformations: {
        ...defaultCollectiveDmsApplication,
        state: DMSApplicationstatus.ACCEPTE,
      },
    })

    expect(
      screen.queryByRole('link', {
        name: 'Suivre ma demande de référencement ADAGE',
      })
    ).not.toBeInTheDocument()
  })

  it('should display dms timeline link if venue has refused application for less than 30days', () => {
    renderVenue({
      ...props,
      dmsInformations: {
        ...defaultCollectiveDmsApplication,
        state: DMSApplicationstatus.REFUSE,
        processingDate: addDays(new Date(), -15).toISOString(),
      },
    })

    expect(
      screen.getByRole('link', {
        name: 'Suivre ma demande de référencement ADAGE',
      })
    ).toBeInTheDocument()
  })

  it('should not display dms timeline link if venue has refused application for more than 30days', () => {
    renderVenue({
      ...props,
      dmsInformations: {
        ...defaultCollectiveDmsApplication,
        state: DMSApplicationstatus.REFUSE,
        processingDate: addDays(new Date(), -31).toISOString(),
      },
    })

    expect(
      screen.queryByRole('link', {
        name: 'Suivre ma demande de référencement ADAGE',
      })
    ).not.toBeInTheDocument()
  })

  it('should display API tag if venue has at least one provider', async () => {
    props.hasProvider = true
    renderVenue(props)

    await screen.findByText('API')
  })
})
