import { api } from 'apiClient/api'
import { VenueListItemResponseModel } from 'apiClient/v1'
import { AccessiblityEnum, GET_DATA_ERROR_MESSAGE } from 'core/shared'
import { IndividualOfferVenue } from 'core/Venue/types'

type Params = { offererId?: number }
type Payload = IndividualOfferVenue[]
type GetIndividualOfferVenuesAdapter = Adapter<Params, Payload, Payload>

const FAILING_RESPONSE = {
  isOk: false,
  message: GET_DATA_ERROR_MESSAGE,
  payload: [],
}

const getIndividualOfferVenuesAdapter: GetIndividualOfferVenuesAdapter =
  async ({ offererId }) => {
    try {
      const response = await api.getVenues(null, true, offererId)

      const serializeVenue = (
        venue: VenueListItemResponseModel
      ): IndividualOfferVenue => {
        /* istanbul ignore next: DEBT, TO FIX */
        const baseAccessibility = {
          [AccessiblityEnum.VISUAL]: venue.visualDisabilityCompliant || false,
          [AccessiblityEnum.MENTAL]: venue.mentalDisabilityCompliant || false,
          [AccessiblityEnum.AUDIO]: venue.audioDisabilityCompliant || false,
          [AccessiblityEnum.MOTOR]: venue.motorDisabilityCompliant || false,
        }
        return {
          id: venue.id,
          managingOffererId: venue.managingOffererId,
          name: venue.publicName || venue.name,
          isVirtual: venue.isVirtual,
          withdrawalDetails: venue.withdrawalDetails || null,
          accessibility: {
            ...baseAccessibility,
            [AccessiblityEnum.NONE]:
              !Object.values(baseAccessibility).includes(true),
          },
          bookingEmail: venue.bookingEmail || null,
          hasMissingReimbursementPoint: venue.hasMissingReimbursementPoint,
          hasCreatedOffer: venue.hasCreatedOffer,
          venueType: venue.venueTypeCode,
        }
      }

      return {
        isOk: true,
        message: null,
        payload: response.venues.map(serializeVenue),
      }
    } catch (e) {
      return FAILING_RESPONSE
    }
  }

export default getIndividualOfferVenuesAdapter
