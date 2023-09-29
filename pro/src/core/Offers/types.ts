import {
  EducationalInstitutionResponseModel,
  WithdrawalTypeEnum,
  OfferStatus,
  CollectiveOffersBookingResponseModel,
  PriceCategoryResponseModel,
} from 'apiClient/v1'
import { CropParams } from 'components/ImageUploader'
import { CollectiveOfferStatus } from 'core/OfferEducational'
import { AccessibiltyFormValues } from 'core/shared'

import { ALL_STATUS, CATEGORY_STATUS } from './constants'

export type SearchFiltersParams = {
  nameOrIsbn: string
  offererId: string
  venueId: string
  categoryId: string
  status: OfferStatus | CollectiveOfferStatus | typeof ALL_STATUS
  creationMode: string
  collectiveOfferType: string
  periodBeginningDate: string
  periodEndingDate: string
  page?: number
}

export type Offerer = {
  id: number
  name: string
}

export type Venue = {
  name: string
  publicName?: string | null
  offererName: string
  isVirtual: boolean
  departementCode?: string | null
}

export type Stock = {
  beginningDatetime?: Date | null
  remainingQuantity: string | number
  bookingLimitDatetime?: Date | null
  bookingQuantity?: number | null
}

export type Offer = {
  id: number
  status: OfferStatus
  isActive: boolean
  hasBookingLimitDatetimesPassed: boolean
  thumbUrl?: string | null
  isEducational: boolean
  name: string
  isEvent: boolean
  productIsbn?: string | null
  venue: Venue
  stocks: Stock[]
  isPublicApi?: boolean | null
  isEditable: boolean
  isShowcase?: boolean | null
  educationalInstitution?: EducationalInstitutionResponseModel | null
  educationalBooking?: CollectiveOffersBookingResponseModel | null
}

export interface CategorySubtypeItem {
  code: number
  label: string
  children: {
    code: number
    label: string
  }[]
}

export interface OfferCategory {
  id: string
  proLabel: string
  isSelectable: boolean
}

export interface OfferSubCategory {
  id: string
  categoryId: string
  proLabel: string
  isEvent: boolean
  conditionalFields: string[]
  canBeDuo: boolean
  canBeEducational: boolean
  onlineOfflinePlatform: CATEGORY_STATUS
  reimbursementRule: string
  isSelectable: boolean
  canBeWithdrawable: boolean
}

export interface IndividualOfferStock {
  beginningDatetime: string | null
  bookingLimitDatetime: string | null
  bookingsQuantity: number
  dateCreated: Date
  hasActivationCode: boolean
  isEventDeletable: boolean
  isEventExpired: boolean
  isSoftDeleted: boolean
  id: number
  price: number
  priceCategoryId?: number | null
  quantity?: number | null
  remainingQuantity: number | string
  activationCodesExpirationDatetime: Date | null
  activationCodes: string[]
}

export interface IndividualOfferOfferer {
  name: string
  id: number
}

export interface IndividualOfferVenue {
  id: number
  name: string
  publicName: string
  isVirtual: boolean
  address: string
  postalCode: string
  city: string
  offerer: IndividualOfferOfferer
  departmentCode: string
  accessibility: AccessibiltyFormValues
}

// TODO: this should be generated in openapi schema
export interface OfferExtraData {
  author?: string
  musicType?: string
  musicSubType?: string
  performer?: string
  ean?: string
  showType?: string
  showSubType?: string
  speaker?: string
  stageDirector?: string
  visa?: string
}

export interface IndividualOfferVenueProvider {
  name: string
}

export interface OfferCollectiveImage {
  url?: string | null
  credit?: string | null
}

export interface IndividualOfferImage {
  originalUrl: string
  url: string
  credit: string | null
  cropParams?: CropParams
}

export interface IndividualOffer {
  id: number
  author: string
  bookingEmail: string
  description: string
  durationMinutes: number | null
  isActive: boolean
  isActivable: boolean
  isDuo: boolean
  isEvent: boolean
  isDigital: boolean
  accessibility: AccessibiltyFormValues
  isNational: boolean
  name: string
  musicSubType: string
  musicType: string
  offererId: number
  offererName: string
  performer: string
  priceCategories?: PriceCategoryResponseModel[] | null
  ean: string
  showSubType: string
  showType: string
  stageDirector: string
  speaker: string
  subcategoryId: string
  image?: IndividualOfferImage
  url: string
  externalTicketOfficeUrl: string
  venueId: number
  venue: IndividualOfferVenue
  visa: string
  withdrawalDetails: string | null
  withdrawalDelay?: number | null
  withdrawalType: WithdrawalTypeEnum | null
  stocks: IndividualOfferStock[]
  lastProviderName: string | null
  lastProvider: IndividualOfferVenueProvider | null
  status: OfferStatus
  bookingContact?: string | null
}
