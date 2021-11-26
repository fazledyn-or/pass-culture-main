export type IUserVenue = {
  id: string
  name: string
  address: {
    street: string
    city: string
    postalCode: string
  }
}

export type IUserOfferer = {
  id: string
  name: string
  siren: string
  managedVenues: IUserVenue[]
}

export enum ADRESS_TYPE {
  OFFERER_VENUE = 'offererVenue',
  SCHOOL = 'school',
  OTHER = 'other',
}

export type IEducationalCategory = {
  id: string
  label: string
}

export type IEducationalSubCategory = {
  id: string
  categoryId: string
  label: string
}

export type IOfferEducationalFormValues = {
  category: string
  subCategory: string
  title: string
  description: string
  duration: number
  offererId: string
  venueId: string
  eventAddress: {
    addressType: ADRESS_TYPE
    otherAddress: string
    venueId: string
  }
  participants: string[]
  accessibility: string
  phone: string
  email: string
  notifications: boolean
  notificationEmail: string
}
