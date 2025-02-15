import { VenueResponse } from 'apiClient/adage'
import { OfferAddressType } from 'apiClient/v1'
import { Facets, Option } from 'pages/AdageIframe/app/types'
import { inferCategoryLabelsFromSubcategories } from 'utils/collectiveCategories'

import { studentsForData } from './OffersSearch/OfferFilters/studentsOptions'
import { SearchFormValues } from './OffersSearch/OffersSearch'

export const ADAGE_FILTERS_DEFAULT_VALUES: SearchFormValues = {
  domains: [],
  students: [],
  departments: [],
  academies: [],
  categories: [],
  eventAddressType: OfferAddressType.OTHER,
  geolocRadius: 50,
  formats: [],
  venue: null,
}

export const adageFiltersToFacetFilters = ({
  domains,
  uai,
  students,
  eventAddressType,
  departments,
  academies,
  categories,
  formats,
  venue,
}: {
  domains: string[]
  uai?: string[] | null
  students: string[]
  departments: string[]
  academies: string[]
  eventAddressType: string
  categories: string[][]
  formats: string[]
  venue: VenueResponse | null
}) => {
  const updatedFilters: Facets = []
  const filtersKeys: string[] = []

  const filteredDomains: string[] = domains.map(
    (domain) => `offer.domains:${domain}`
  )

  const filteredStudents: string[] = students.map(
    (student) => `offer.students:${student}`
  )

  const filteredFormats: string[] = formats.map((format) => `formats:${format}`)

  let filteredDepartments: string[] = []
  if (eventAddressType == OfferAddressType.SCHOOL) {
    filteredDepartments = departments.flatMap((department) => [
      `offer.schoolInterventionArea:${department}`,
    ])
  } else {
    filteredDepartments = departments.flatMap((department) => [
      `venue.departmentCode:${department}`,
      `offer.interventionArea:${department}`,
    ])
  }

  const filteredAcademies: string[] = academies.map(
    (academy) => `venue.academy:${academy}`
  )

  switch (eventAddressType) {
    case 'school':
      filtersKeys.push('eventAddressType')
      updatedFilters.push([`offer.eventAddressType:school`])
      break
    case 'offererVenue':
      filtersKeys.push('eventAddressType')
      updatedFilters.push([
        `offer.eventAddressType:offererVenue`,
        `offer.eventAddressType:other`,
      ])
      break
    default:
      break
  }

  const filteredCategories: string[] = categories.flatMap((categoryValue) =>
    categoryValue.map((subcategoryId) => `offer.subcategoryId:${subcategoryId}`)
  )

  const filteredVenues = venue
    ? [
        `venue.id:${venue.id}`,
        ...venue.relative.map((venueId) => `venue.id:${venueId}`),
      ]
    : []

  if (filteredStudents.length > 0) {
    filtersKeys.push('students')
    updatedFilters.push(filteredStudents)
  }

  if (filteredDomains.length > 0) {
    filtersKeys.push('domains')
    updatedFilters.push(filteredDomains)
  }

  if (filteredDepartments.length > 0) {
    filtersKeys.push('departments')
    updatedFilters.push(filteredDepartments)
  }

  if (filteredAcademies.length > 0) {
    filtersKeys.push('academies')
    updatedFilters.push(filteredAcademies)
  }

  if (filteredCategories.length > 0) {
    filtersKeys.push('categories')
    updatedFilters.push(filteredCategories)
  }

  if (filteredFormats.length > 0) {
    filtersKeys.push('formats')
    updatedFilters.push(filteredFormats)
  }

  if (uai) {
    if (!uai.includes('all')) {
      filtersKeys.push('uaiCode')
    }
    updatedFilters.push(
      uai.map((uaiCode) => `offer.educationalInstitutionUAICode:${uaiCode}`)
    )
  }

  if (filteredVenues.length > 0) {
    filtersKeys.push('venue')
    updatedFilters.push(filteredVenues)
  }

  return {
    queryFilters: updatedFilters,
    filtersKeys: filtersKeys,
  }
}

export const serializeFiltersForData = (
  filters: SearchFormValues,
  currentSearch: string | null,
  categoriesOptions: Option<string[]>[],
  domainsOptions: Option<number>[],
  isFormatEnable: boolean
) => {
  return {
    ...filters,
    query: currentSearch,
    categories: inferCategoryLabelsFromSubcategories(
      filters.categories,
      categoriesOptions
    ),
    domains: filters.domains.map(
      (domainId) =>
        domainsOptions.find((option) => option.value === Number(domainId))
          ?.label
    ),
    students: filters.students.map(
      (student) =>
        studentsForData.find((s) => s.label === student)?.valueForData
    ),
    formats: isFormatEnable ? filters.formats : undefined,
    venue: filters.venue
      ? [filters.venue.id, ...filters.venue.relative.map((venueId) => venueId)]
      : undefined,
  }
}
