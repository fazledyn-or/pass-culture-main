import { screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import React from 'react'
import { Route, Routes } from 'react-router-dom'

import { api } from 'apiClient/api'
import {
  GetIndividualOfferResponseModel,
  OfferStatus,
  PatchOfferBodyModel,
  SubcategoryResponseModel,
  WithdrawalTypeEnum,
} from 'apiClient/v1'
import { OFFER_WIZARD_STEP_IDS } from 'components/IndividualOfferNavigation/constants'
import Notification from 'components/Notification/Notification'
import {
  IndividualOfferContext,
  IndividualOfferContextValues,
} from 'context/IndividualOfferContext'
import { CATEGORY_STATUS, OFFER_WIZARD_MODE } from 'core/Offers/constants'
import { IndividualOffer } from 'core/Offers/types'
import { getIndividualOfferPath } from 'core/Offers/utils/getIndividualOfferUrl'
import { AccessiblityEnum } from 'core/shared'
import { IndividualOfferVenueItem } from 'core/Venue/types'
import * as pcapi from 'repository/pcapi/pcapi'
import {
  individualOfferCategoryFactory,
  individualOfferContextFactory,
  individualOfferFactory,
  individualOfferSubCategoryFactory,
  individualOfferVenueItemFactory,
  individualStockFactory,
} from 'utils/individualApiFactories'
import { renderWithProviders } from 'utils/renderWithProviders'

import InformationsScreen, {
  InformationsScreenProps,
} from '../InformationsScreen'

vi.mock('screens/IndividualOffer/Informations/utils', () => {
  return {
    filterCategories: vi.fn(),
  }
})

vi.mock('utils/windowMatchMedia', () => ({
  doesUserPreferReducedMotion: vi.fn(() => true),
}))

vi.mock('repository/pcapi/pcapi', () => ({
  postThumbnail: vi.fn(),
}))

const renderInformationsScreen = (
  props: InformationsScreenProps,
  contextOverride: IndividualOfferContextValues,
  features: { list: { isActive: true; nameKey: string }[] } = { list: [] }
) => {
  const storeOverrides = {
    user: {
      initialized: true,
      currentUser: {
        isAdmin: false,
        email: 'email@example.com',
      },
    },
    features: features,
  }
  const contextValue = individualOfferContextFactory(contextOverride)

  return renderWithProviders(
    <>
      <Routes>
        <Route
          path={getIndividualOfferPath({
            step: OFFER_WIZARD_STEP_IDS.INFORMATIONS,
            mode: OFFER_WIZARD_MODE.EDITION,
          })}
          element={
            <IndividualOfferContext.Provider value={contextValue}>
              <InformationsScreen {...props} />
            </IndividualOfferContext.Provider>
          }
        />
        <Route
          path={getIndividualOfferPath({
            step: OFFER_WIZARD_STEP_IDS.SUMMARY,
            mode: OFFER_WIZARD_MODE.READ_ONLY,
          })}
          element={<div>There is the summary route content</div>}
        />
      </Routes>
      <Notification />
    </>,
    {
      storeOverrides,
      initialRouterEntries: [
        getIndividualOfferPath({
          step: OFFER_WIZARD_STEP_IDS.INFORMATIONS,
          mode: OFFER_WIZARD_MODE.EDITION,
        }),
      ],
    }
  )
}

const scrollIntoViewMock = vi.fn()

describe('screens:IndividualOffer::Informations:edition', () => {
  let props: InformationsScreenProps
  let contextOverride: IndividualOfferContextValues
  let offer: IndividualOffer
  let subCategories: SubcategoryResponseModel[]
  const offererId = 1
  const physicalVenueId = 1
  const virtualVenueId = 2
  const offerId = 12

  beforeEach(() => {
    Element.prototype.scrollIntoView = scrollIntoViewMock
    const categories = [individualOfferCategoryFactory({ id: 'CID' })]
    subCategories = [
      individualOfferSubCategoryFactory({
        id: 'SCID virtual',
        categoryId: 'CID',
        onlineOfflinePlatform: CATEGORY_STATUS.ONLINE,
      }),
      individualOfferSubCategoryFactory({
        id: 'SCID physical',
        categoryId: 'CID',
        onlineOfflinePlatform: CATEGORY_STATUS.OFFLINE,
      }),
    ]

    const venue1: IndividualOfferVenueItem = individualOfferVenueItemFactory()
    const venue2: IndividualOfferVenueItem = individualOfferVenueItemFactory({
      isVirtual: true,
    })

    offer = individualOfferFactory({
      id: offerId,
      author: 'Offer author',
      bookingEmail: 'booking@email.com',
      description: 'Offer description',
      durationMinutes: 140,
      isActive: true,
      isDuo: false,
      isEvent: true,
      isDigital: false,
      accessibility: {
        [AccessiblityEnum.AUDIO]: true,
        [AccessiblityEnum.MENTAL]: true,
        [AccessiblityEnum.MOTOR]: true,
        [AccessiblityEnum.VISUAL]: true,
        [AccessiblityEnum.NONE]: false,
      },
      isNational: false,
      name: 'Offer name',
      musicSubType: '',
      musicType: '',
      offererId: 12,
      offererName: '',
      performer: 'Offer performer',
      ean: '',
      showSubType: '',
      showType: '',
      stageDirector: 'Offer stageDirector',
      speaker: 'Offer speaker',
      subcategoryId: 'SCID physical',
      image: undefined,
      url: 'https://offer.example.com',
      externalTicketOfficeUrl: 'https://external.example.com',
      venueId: 1,
      visa: '',
      withdrawalDetails: 'Offer withdrawalDetails',
      withdrawalDelay: 140,
      withdrawalType: WithdrawalTypeEnum.ON_SITE,
      stocks: [],
      lastProviderName: null,
      lastProvider: null,
      status: OfferStatus.ACTIVE,
    })

    contextOverride = individualOfferContextFactory({
      offerId: offer.id,
      offer: offer,
      venueList: [venue1, venue2],
      offererNames: [{ id: offererId, name: 'Offerer name' }],
      categories,
      subCategories,
    })

    props = {
      venueId: physicalVenueId.toString(),
      offererId: offererId.toString(),
    }

    vi.spyOn(api, 'patchOffer').mockResolvedValue({
      id: offerId,
    } as GetIndividualOfferResponseModel)
    vi.spyOn(api, 'postOffer').mockResolvedValue({
      id: offerId,
    } as GetIndividualOfferResponseModel)
    vi.spyOn(api, 'getOffer').mockResolvedValue(
      {} as GetIndividualOfferResponseModel
    )
    vi.spyOn(api, 'deleteThumbnail').mockResolvedValue()
  })

  it('should submit minimal physical offer and redirect to summary', async () => {
    renderInformationsScreen(props, contextOverride)
    const nameField = screen.getByLabelText('Titre de l’offre')
    await userEvent.clear(nameField)
    await userEvent.type(nameField, 'Le nom de mon offre édité')

    await userEvent.click(
      await screen.findByText('Enregistrer les modifications')
    )

    expect(api.patchOffer).toHaveBeenCalledTimes(1)
    expect(api.patchOffer).toHaveBeenCalledWith(offer.id, {
      audioDisabilityCompliant: true,
      bookingEmail: 'booking@email.com',
      description: 'Offer description',
      durationMinutes: 140,
      externalTicketOfficeUrl: 'https://external.example.com',
      extraData: {
        author: 'Offer author',
        musicSubType: '',
        musicType: '',
        performer: 'Offer performer',
        ean: '',
        showSubType: '',
        showType: '',
        speaker: 'Offer speaker',
        stageDirector: 'Offer stageDirector',
        visa: '',
      },
      isDuo: false,
      isNational: false,
      mentalDisabilityCompliant: true,
      motorDisabilityCompliant: true,
      name: 'Le nom de mon offre édité',
      url: 'https://offer.example.com',
      visualDisabilityCompliant: true,
      withdrawalDetails: 'Offer withdrawalDetails',
      withdrawalDelay: 140,
      withdrawalType: WithdrawalTypeEnum.ON_SITE,
      shouldSendMail: false,
    })
    expect(api.getOffer).toHaveBeenCalledTimes(1)
    expect(
      await screen.findByText('There is the summary route content')
    ).toBeInTheDocument()
    expect(pcapi.postThumbnail).not.toHaveBeenCalled()
    expect(api.postOffer).not.toHaveBeenCalled()
  })

  it('should submit minimal virtual offer and redirect to summary', async () => {
    contextOverride.offer = {
      ...offer,
      venueId: virtualVenueId,
      subcategoryId: 'SCID virtual',
      isEvent: false,
      withdrawalDelay: undefined,
      withdrawalType: null,
    }
    props = {
      venueId: virtualVenueId.toString(),
      offererId: offererId.toString(),
    }

    renderInformationsScreen(props, contextOverride)
    const nameField = screen.getByLabelText('Titre de l’offre')
    await userEvent.clear(nameField)
    await userEvent.type(nameField, 'Le nom de mon offre édité')

    await userEvent.click(
      await screen.findByText('Enregistrer les modifications')
    )

    expect(api.patchOffer).toHaveBeenCalledTimes(1)
    expect(api.patchOffer).toHaveBeenCalledWith(offer.id, {
      audioDisabilityCompliant: true,
      bookingEmail: 'booking@email.com',
      description: 'Offer description',
      durationMinutes: 140,
      externalTicketOfficeUrl: 'https://external.example.com',
      extraData: {
        author: 'Offer author',
        musicSubType: '',
        musicType: '',
        performer: 'Offer performer',
        ean: '',
        showSubType: '',
        showType: '',
        speaker: 'Offer speaker',
        stageDirector: 'Offer stageDirector',
        visa: '',
      },
      isDuo: false,
      isNational: false,
      mentalDisabilityCompliant: true,
      motorDisabilityCompliant: true,
      name: 'Le nom de mon offre édité',
      url: 'https://offer.example.com',
      visualDisabilityCompliant: true,
      withdrawalDetails: 'Offer withdrawalDetails',
      withdrawalDelay: undefined,
      withdrawalType: undefined,
      shouldSendMail: false,
    })
    expect(api.getOffer).toHaveBeenCalledTimes(1)
    expect(
      await screen.findByText('There is the summary route content')
    ).toBeInTheDocument()
    expect(pcapi.postThumbnail).not.toHaveBeenCalled()
    expect(api.postOffer).not.toHaveBeenCalled()
  })

  it('should delete offer image', async () => {
    contextOverride.offer = {
      ...offer,
      image: {
        originalUrl: 'https://image.url',
        url: 'https://image.url',
        credit: 'John Do',
      },
    }
    props = {
      venueId: physicalVenueId.toString(),
      offererId: offererId.toString(),
    }
    renderInformationsScreen(props, contextOverride)
    await screen.findByRole('heading', { name: /Type d’offre/ })
    expect(
      screen.queryByRole('button', { name: /Ajouter une image/ })
    ).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /Supprimer/ }))
    await screen.findByText('Souhaitez-vous vraiment supprimer cette image ?')
    await userEvent.click(screen.getByTestId('confirm-dialog-button-confirm'))
    expect(api.deleteThumbnail).toHaveBeenCalledWith(offer.id)
    expect(
      await screen.findByRole('button', { name: /Ajouter une image/ })
    ).toBeInTheDocument()
  })
  it('should display an error on delete offer image api failure', async () => {
    contextOverride.offer = {
      ...offer,
      image: {
        originalUrl: 'https://image.url',
        url: 'https://image.url',
        credit: 'John Do',
      },
    }
    props = {
      venueId: virtualVenueId.toString(),
      offererId: offererId.toString(),
    }

    renderInformationsScreen(props, contextOverride)
    await screen.findByRole('heading', { name: /Type d’offre/ })
    expect(
      screen.queryByRole('button', { name: /Ajouter une image/ })
    ).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /Supprimer/ }))
    await screen.findByText('Souhaitez-vous vraiment supprimer cette image ?')

    vi.spyOn(api, 'deleteThumbnail').mockRejectedValue(undefined)

    await userEvent.click(screen.getByTestId('confirm-dialog-button-confirm'))
    expect(
      await screen.findByText(
        'Une erreur est survenue lors de la suppression de votre image.',
        { exact: false }
      )
    ).toBeInTheDocument()
    expect(api.deleteThumbnail).toHaveBeenCalledWith(offer.id)

    expect(
      screen.queryByRole('button', { name: /Ajouter une image/ })
    ).not.toBeInTheDocument()
  })

  it('should go back to summary when clicking on "Annuler et quitter"', async () => {
    renderInformationsScreen(props, contextOverride)

    await userEvent.click(screen.getByText('Annuler et quitter'))

    expect(
      screen.getByText('There is the summary route content')
    ).toBeInTheDocument()
  })

  describe('send mail on withdrawal changes', () => {
    let expectedBody: PatchOfferBodyModel
    let features: { list: { isActive: true; nameKey: string }[] }

    beforeEach(() => {
      expectedBody = {
        audioDisabilityCompliant: true,
        bookingEmail: 'booking@email.com',
        description: 'Offer description',
        durationMinutes: 140,
        externalTicketOfficeUrl: 'https://external.example.com',
        extraData: {
          author: 'Offer author',
          musicSubType: '',
          musicType: '',
          performer: 'Offer performer',
          ean: '',
          showSubType: '',
          showType: '',
          speaker: 'Offer speaker',
          stageDirector: 'Offer stageDirector',
          visa: '',
        },
        isDuo: false,
        isNational: false,
        mentalDisabilityCompliant: true,
        motorDisabilityCompliant: true,
        name: 'Le nom de mon offre édité',
        url: 'https://offer.example.com',
        visualDisabilityCompliant: true,
        withdrawalDetails: 'Offer withdrawalDetails',
        withdrawalDelay: undefined,
        withdrawalType: undefined,
        shouldSendMail: false,
      }
    })

    it('should submit when user click onCancel button, but should not send mail', async () => {
      const individualStock = individualStockFactory()
      contextOverride.offer = {
        ...offer,
        venueId: virtualVenueId,
        subcategoryId: 'SCID virtual',
        isEvent: false,
        stocks: [individualStock],
      }
      props = {
        venueId: virtualVenueId.toString(),
        offererId: offererId.toString(),
      }
      expectedBody.withdrawalDelay = 140
      expectedBody.withdrawalType = WithdrawalTypeEnum.ON_SITE

      renderInformationsScreen(props, contextOverride, features)

      const nameField = screen.getByLabelText('Titre de l’offre')
      await userEvent.clear(nameField)
      await userEvent.type(nameField, 'Le nom de mon offre édité')

      const withdrawalDetailsField = screen.getByDisplayValue(
        'Offer withdrawalDetails'
      )
      await userEvent.click(withdrawalDetailsField)
      await userEvent.clear(withdrawalDetailsField)
      await userEvent.type(
        withdrawalDetailsField,
        'Nouvelle information de retrait'
      )
      expectedBody.withdrawalDetails = 'Nouvelle information de retrait'
      await waitFor(() => {
        expect(screen.getByText('Nouvelle information de retrait'))
      })
      const submitButton = await screen.findByText(
        'Enregistrer les modifications'
      )

      await userEvent.click(submitButton)

      expect(
        await screen.findByText(
          'Souhaitez-vous prévenir les bénéficiaires de la modification des modalités de retrait ?'
        )
      ).toBeInTheDocument()

      expect(api.patchOffer).toHaveBeenCalledTimes(0)
      expect(api.getOffer).toHaveBeenCalledTimes(0)
      expect(
        screen.queryByText('There is the summary route content')
      ).not.toBeInTheDocument()

      const cancelSendMailButton = await screen.findByText('Ne pas envoyer')
      await userEvent.click(cancelSendMailButton)

      expect(
        screen.queryByText(
          'Souhaitez-vous prévenir les bénéficiaires de la modification des modalités de retrait ?'
        )
      ).not.toBeInTheDocument()

      expect(api.patchOffer).toHaveBeenCalledTimes(1)
      expect(api.patchOffer).toHaveBeenCalledWith(offer.id, expectedBody)
      expect(api.getOffer).toHaveBeenCalledTimes(1)
      expect(
        await screen.findByText('There is the summary route content')
      ).toBeInTheDocument()
    })

    it('should not submit when user click on close withdrawal dialog button', async () => {
      const individualStock = individualStockFactory()
      contextOverride.offer = {
        ...offer,
        venueId: virtualVenueId,
        subcategoryId: 'SCID virtual',
        isEvent: false,
        stocks: [individualStock],
      }
      props = {
        venueId: virtualVenueId.toString(),
        offererId: offererId.toString(),
      }

      renderInformationsScreen(props, contextOverride, features)

      const nameField = screen.getByLabelText('Titre de l’offre')
      await userEvent.clear(nameField)
      await userEvent.type(nameField, 'Le nom de mon offre édité')

      const withdrawalDetailsField = screen.getByDisplayValue(
        'Offer withdrawalDetails'
      )
      await userEvent.click(withdrawalDetailsField)
      await userEvent.clear(withdrawalDetailsField)
      await userEvent.type(
        withdrawalDetailsField,
        'Nouvelle information de retrait'
      )

      await waitFor(() => {
        expect(screen.getByText('Nouvelle information de retrait'))
      })

      const submitButton = await screen.findByText(
        'Enregistrer les modifications'
      )

      await userEvent.click(submitButton)

      expect(
        await screen.findByText(
          'Souhaitez-vous prévenir les bénéficiaires de la modification des modalités de retrait ?'
        )
      ).toBeInTheDocument()

      const closewithdrawalDialogButton = screen.getByRole('button', {
        name: 'Fermer la modale',
      })
      await userEvent.click(closewithdrawalDialogButton)

      expect(
        screen.queryByText(
          'Souhaitez-vous prévenir les bénéficiaires de la modification des modalités de retrait ?'
        )
      ).not.toBeInTheDocument()

      expect(api.patchOffer).toHaveBeenCalledTimes(0)
      expect(api.getOffer).toHaveBeenCalledTimes(0)
      expect(screen.getByText('Titre de l’offre')).toBeInTheDocument()
    })

    /**
     * In Order:
     *  - No change on widthdrawal and bookingsQuantity
     *  - change but no bookingsQuantity
     *  - No change and no bookingsQuantity
     */
    const shouldNotOpenConditions = [
      {
        modifyWithdrawailDetails: false,
        hasBookingQuantity: true,
      },
      {
        modifyWithdrawailDetails: true,
        hasBookingQuantity: false,
      },
      {
        modifyWithdrawailDetails: false,
        hasBookingQuantity: false,
      },
    ]
    it.each(shouldNotOpenConditions)(
      "should not open widthdrawal send mail modal when user doesn't change withdrawal and stocks has bookingQuantity and submit form",
      async (condition) => {
        const individualStock = individualStockFactory()
        if (!condition.hasBookingQuantity) {
          individualStock.bookingsQuantity = 0
        }
        contextOverride.offer = {
          ...offer,
          venueId: virtualVenueId,
          subcategoryId: 'SCID virtual',
          isEvent: true,
          withdrawalDelay: undefined,
          withdrawalType: null,
          stocks: [individualStock],
        }
        props = {
          venueId: virtualVenueId.toString(),
          offererId: offererId.toString(),
        }
        renderInformationsScreen(props, contextOverride, features)

        const nameField = screen.getByLabelText('Titre de l’offre')
        await userEvent.clear(nameField)
        await userEvent.type(nameField, 'Le nom de mon offre édité')

        if (condition.modifyWithdrawailDetails) {
          const withdrawalDetailsField = screen.getByDisplayValue(
            'Offer withdrawalDetails'
          )
          await userEvent.click(withdrawalDetailsField)
          await userEvent.clear(withdrawalDetailsField)
          await userEvent.type(
            withdrawalDetailsField,
            'Nouvelle information de retrait'
          )
          expectedBody.withdrawalDetails = 'Nouvelle information de retrait'
          await waitFor(() => {
            expect(screen.getByText('Nouvelle information de retrait'))
          })
        }

        const submitButton = await screen.findByText(
          'Enregistrer les modifications'
        )

        await userEvent.click(submitButton)

        expect(
          screen.queryByText(
            'Souhaitez-vous prévenir les bénéficiaires de la modification des modalités de retrait ?'
          )
        ).not.toBeInTheDocument()

        expect(api.patchOffer).toHaveBeenCalledTimes(1)
        expect(api.patchOffer).toHaveBeenCalledWith(offer.id, expectedBody)
        await waitFor(() => {
          expect(api.getOffer).toHaveBeenCalledTimes(1)
        })
        expect(
          await screen.findByText('There is the summary route content')
        ).toBeInTheDocument()
      }
    )

    it('should not open widthdrawal dialog if offer is not active', async () => {
      const individualStock = individualStockFactory()
      contextOverride.offer = {
        ...offer,
        venueId: virtualVenueId,
        subcategoryId: 'SCID virtual',
        isEvent: true,
        withdrawalDelay: undefined,
        withdrawalType: WithdrawalTypeEnum.NO_TICKET,
        stocks: [individualStock],
        isActive: false,
      }

      props = {
        venueId: virtualVenueId.toString(),
        offererId: offererId.toString(),
      }
      renderInformationsScreen(props, contextOverride, features)
      expectedBody.withdrawalDelay = null
      expectedBody.withdrawalType = WithdrawalTypeEnum.NO_TICKET

      const nameField = screen.getByLabelText('Titre de l’offre')
      await userEvent.clear(nameField)
      await userEvent.type(nameField, 'Le nom de mon offre édité')

      const withdrawalDetailsField = screen.getByDisplayValue(
        'Offer withdrawalDetails'
      )
      await userEvent.click(withdrawalDetailsField)
      await userEvent.clear(withdrawalDetailsField)
      await userEvent.type(
        withdrawalDetailsField,
        'Nouvelle information de retrait'
      )
      expectedBody.withdrawalDetails = 'Nouvelle information de retrait'
      await waitFor(() => {
        expect(screen.getByText('Nouvelle information de retrait'))
      })

      const submitButton = await screen.findByText(
        'Enregistrer les modifications'
      )
      await userEvent.click(submitButton)

      expect(
        screen.queryByText(
          'Souhaitez-vous prévenir les bénéficiaires de la modification des modalités de retrait ?'
        )
      ).not.toBeInTheDocument()

      await waitFor(() => {
        expect(api.patchOffer).toHaveBeenCalledTimes(1)
      })
      expect(api.patchOffer).toHaveBeenCalledWith(offer.id, expectedBody)
      expect(
        await screen.findByText('There is the summary route content')
      ).toBeInTheDocument()
    })

    const withdrawalChanges = [
      {
        withdrawalDetails: true,
        withdrawalDelay: false,
        withdrawalType: false,
      },
      {
        withdrawalDetails: false,
        withdrawalDelay: true,
        withdrawalType: false,
      },
      {
        withdrawalDetails: false,
        withdrawalDelay: false,
        withdrawalType: true,
      },
    ]
    it.each(withdrawalChanges)(
      'should open widthdrawal send mail modal when user change withdrawal information and submit',
      async (withdrawalInformations) => {
        const individualStock = individualStockFactory()
        contextOverride.offer = {
          ...offer,
          venueId: virtualVenueId,
          subcategoryId: 'SCID virtual',
          isEvent: false,
          withdrawalType: WithdrawalTypeEnum.ON_SITE,
          withdrawalDelay: 0,
          stocks: [individualStock],
        }
        if (contextOverride.subCategories) {
          contextOverride.subCategories[0].conditionalFields = [
            'withdrawalDelay',
            'withdrawalType',
          ]
        }

        expectedBody.withdrawalDelay = 0
        expectedBody.withdrawalType = WithdrawalTypeEnum.ON_SITE
        expectedBody.shouldSendMail = true

        props = {
          venueId: virtualVenueId.toString(),
          offererId: offererId.toString(),
        }
        renderInformationsScreen(props, contextOverride, features)

        const nameField = screen.getByLabelText('Titre de l’offre')
        await userEvent.clear(nameField)
        await userEvent.type(nameField, 'Le nom de mon offre édité')

        if (withdrawalInformations.withdrawalDetails) {
          const withdrawalDetailsField = screen.getByDisplayValue(
            'Offer withdrawalDetails'
          )
          await userEvent.click(withdrawalDetailsField)
          await userEvent.clear(withdrawalDetailsField)
          await userEvent.type(
            withdrawalDetailsField,
            'Nouvelle information de retrait'
          )
          expectedBody.withdrawalDetails = 'Nouvelle information de retrait'
          await waitFor(() => {
            expect(screen.getByText('Nouvelle information de retrait'))
          })
        }

        if (withdrawalInformations.withdrawalDelay) {
          const withdrawalDelayField =
            await screen.findByLabelText('Heure de retrait')
          await userEvent.selectOptions(withdrawalDelayField, '1 heure')
          expectedBody.withdrawalDelay = 3600
        }

        if (withdrawalInformations.withdrawalType) {
          const withdrawalTypeField = await screen.findByLabelText(
            'Les billets seront envoyés par email'
          )
          await userEvent.click(withdrawalTypeField)
          expectedBody.withdrawalType = WithdrawalTypeEnum.BY_EMAIL
          expectedBody.withdrawalDelay = 60 * 60 * 24
        }

        const submitButton = await screen.findByText(
          'Enregistrer les modifications'
        )

        await userEvent.click(submitButton)

        expect(
          await screen.findByText(
            'Souhaitez-vous prévenir les bénéficiaires de la modification des modalités de retrait ?'
          )
        ).toBeInTheDocument()

        expect(api.patchOffer).toHaveBeenCalledTimes(0)
        expect(api.getOffer).toHaveBeenCalledTimes(0)
        expect(
          screen.queryByText('There is the summary route content')
        ).not.toBeInTheDocument()

        const sendMailButton = await screen.findByText('Envoyer un email')
        await userEvent.click(sendMailButton)

        expect(
          screen.queryByText(
            'Souhaitez-vous prévenir les bénéficiaires de la modification des modalités de retrait ?'
          )
        ).not.toBeInTheDocument()

        expect(api.patchOffer).toHaveBeenCalledTimes(1)
        expect(api.patchOffer).toHaveBeenCalledWith(offer.id, expectedBody)
        expect(api.getOffer).toHaveBeenCalledTimes(1)
        expect(
          await screen.findByText('There is the summary route content')
        ).toBeInTheDocument()
      }
    )
  })
})
