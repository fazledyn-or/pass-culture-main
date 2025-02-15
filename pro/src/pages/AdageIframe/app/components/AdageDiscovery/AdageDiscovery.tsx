import React, { useEffect, useRef, useState } from 'react'

import {
  AdagePlaylistType,
  OfferAddressType,
  StudentLevels,
} from 'apiClient/adage'
import { api, apiAdage } from 'apiClient/api'
import { GET_DATA_ERROR_MESSAGE } from 'core/shared/constants'
import useIsElementVisible from 'hooks/useIsElementVisible'
import useNotification from 'hooks/useNotification'
import fullLinkIcon from 'icons/full-link.svg'
import { Option } from 'pages/AdageIframe/app/types'
import { ButtonLink } from 'ui-kit'
import { ButtonVariant } from 'ui-kit/Button/types'

import styles from './AdageDiscovery.module.scss'
import CardOfferComponent, { CardOfferModel } from './CardOffer/CardOffer'
import CardVenue from './CardVenue/CardVenue'
import Carousel from './Carousel/Carousel'
import circles from './DomainsCard/assets/circles.svg'
import ellipses from './DomainsCard/assets/ellipses.svg'
import pills from './DomainsCard/assets/pills.svg'
import rectangles from './DomainsCard/assets/rectangles.svg'
import squares from './DomainsCard/assets/squares.svg'
import triangles from './DomainsCard/assets/triangles.svg'
import DomainsCard from './DomainsCard/DomainsCard'

export const mockOffer: CardOfferModel = {
  id: 479,
  name: 'Une chouette à la mer',
  description: 'Une offre vraiment chouette',
  subcategoryLabel: 'Cinéma',
  stock: {
    id: 825,
    beginningDatetime: new Date('2022-09-16T00:00:00Z').toISOString(),
    bookingLimitDatetime: new Date('2022-09-16T00:00:00Z').toISOString(),
    isBookable: true,
    price: 140000,
    numberOfTickets: 10,
  },
  venue: {
    id: 1,
    address: '1 boulevard Poissonnière',
    city: 'Paris',
    name: 'Le Petit Rintintin 33',
    postalCode: '75000',
    publicName: 'Le Petit Rintintin 33',
    coordinates: {
      latitude: 48.87004,
      longitude: 2.3785,
    },
    managingOfferer: {
      name: 'Le Petit Rintintin Management',
    },
    distance: 5,
  },
  isSoldOut: false,
  isExpired: false,
  isFavorite: false,
  visualDisabilityCompliant: true,
  mentalDisabilityCompliant: true,
  audioDisabilityCompliant: true,
  motorDisabilityCompliant: true,
  contactEmail: '',
  contactPhone: '',
  domains: [],
  offerVenue: {
    venueId: 1,
    otherAddress: '',
    addressType: OfferAddressType.OFFERER_VENUE,
    distance: 10,
  },
  teacher: {
    firstName: 'Jean',
    lastName: 'Dupont',
  },
  students: [StudentLevels.COLL_GE_4E, StudentLevels.COLL_GE_3E],
  interventionArea: ['75', '92'],
  isTemplate: false,
}

const mockVenue = {
  imageUrl: 'https://picsum.photos/200/300',
  name: 'Le nom administratif du lieu',
  publicName: 'Mon super lieu sur vraiment beaucoup de super lignes',
  distance: 2,
  id: '28',
  city: 'Paris',
}

export const AdageDiscovery = () => {
  const hasSeenAllPlaylist = useRef<boolean>(false)
  const params = new URLSearchParams(location.search)
  const [domainsOptions, setDomainsOptions] = useState<Option<number>[]>([])

  const footerSuggestion = useRef<HTMLDivElement | null>(null)
  const isFooterSuggestionVisible = useIsElementVisible(footerSuggestion)

  const notification = useNotification()
  const adageAuthToken = params.get('token')

  if (isFooterSuggestionVisible && !hasSeenAllPlaylist.current) {
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    apiAdage.logHasSeenAllPlaylist({ iframeFrom: location.pathname })
    hasSeenAllPlaylist.current = true
  }

  useEffect(() => {
    const getAllDomains = async () => {
      try {
        const result = await api.listEducationalDomains()

        return setDomainsOptions(
          result.map(({ id, name }) => ({ value: id, label: name }))
        )
      } catch {
        notification.error(GET_DATA_ERROR_MESSAGE)
      }
    }

    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    getAllDomains()
  }, [])

  function onWholePlaylistSeen(
    playlistId: number,
    playlistType: AdagePlaylistType
  ) {
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    apiAdage.logHasSeenWholePlaylist({
      iframeFrom: location.pathname,
      playlistId,
      playlistType,
    })
  }

  const colorAndMotifOrder = [
    { color: 'orange', src: squares },
    { color: 'purple', src: pills },
    { color: 'pink', src: triangles },
    { color: 'green', src: rectangles },
    { color: 'red', src: ellipses },
    { color: 'blue', src: circles },
  ]

  const trackPlaylistElementClicked = ({
    playlistId,
    playlistType,
    elementId,
  }: {
    playlistId: number
    playlistType: AdagePlaylistType
    elementId: number | null
  }) => {
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    apiAdage.logConsultPlaylistElement({
      iframeFrom: location.pathname,
      playlistId,
      playlistType,
      elementId,
    })
  }

  return (
    <div className={styles['discovery']}>
      <div className={styles['discovery-banner']}>
        <h1 className={styles['discovery-banner-title']}>
          Découvrez <span>la part collective</span> du pass Culture
        </h1>
      </div>

      <div className={styles['discovery-playlists']}>
        <div className={styles['discovery-playlist']}>
          <Carousel
            title={
              <h2 className={styles['section-title']}>
                Les offres publiées récemment
              </h2>
            }
            onLastCarouselElementVisible={() =>
              onWholePlaylistSeen(0, AdagePlaylistType.OFFER)
            }
            elements={[
              <CardOfferComponent
                key="card-offer-1"
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 0, // TODO: change all playlistId with real value
                    playlistType: AdagePlaylistType.OFFER,
                    elementId: 1, // TODO: change elementId with real value
                  })
                }
                offer={{
                  ...mockOffer,
                  id: 1,
                  name: 'Ma super offre',
                  offerVenue: {
                    ...mockOffer.offerVenue,
                    addressType: OfferAddressType.OFFERER_VENUE,
                  },
                  imageUrl: 'https://picsum.photos/201/',
                }}
              />,
              <CardOfferComponent
                key="card-offer-2"
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 0,
                    elementId: 2, // TODO: change elementId with real value
                    playlistType: AdagePlaylistType.OFFER,
                  })
                }
                offer={{
                  ...mockOffer,
                  id: 2,
                  offerVenue: {
                    ...mockOffer.offerVenue,
                    addressType: OfferAddressType.SCHOOL,
                  },
                  imageUrl: 'https://picsum.photos/202/',
                }}
              />,
              <CardOfferComponent
                key="card-offer-3"
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 0,
                    playlistType: AdagePlaylistType.OFFER,
                    elementId: 3, // TODO: change elementId with real value
                  })
                }
                offer={{
                  ...mockOffer,
                  id: 3,
                  offerVenue: {
                    ...mockOffer.offerVenue,
                    addressType: OfferAddressType.OTHER,
                  },
                  imageUrl: 'https://picsum.photos/203/',
                }}
              />,
              <CardOfferComponent
                key="card-offer-4"
                offer={{
                  ...mockOffer,
                  id: 1,
                  name: 'Ma super offre 2',
                  offerVenue: {
                    ...mockOffer.offerVenue,
                    addressType: OfferAddressType.OFFERER_VENUE,
                  },
                  imageUrl: 'https://picsum.photos/201/',
                }}
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 1,
                    playlistType: AdagePlaylistType.DOMAIN,
                    elementId: 4, // TODO: change elementId with real value
                  })
                }
              />,
              <CardOfferComponent
                key="card-offer-5"
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 0,
                    playlistType: AdagePlaylistType.OFFER,
                    elementId: 5, // TODO: change elementId with real value
                  })
                }
                offer={{
                  ...mockOffer,
                  id: 2,
                  offerVenue: {
                    ...mockOffer.offerVenue,
                    addressType: OfferAddressType.SCHOOL,
                  },
                  imageUrl: 'https://picsum.photos/202/',
                }}
              />,
              <CardOfferComponent
                key="card-offer-7"
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 0,
                    playlistType: AdagePlaylistType.OFFER,
                    elementId: 6, // TODO: change elementId with real value
                  })
                }
                offer={{
                  ...mockOffer,
                  id: 3,
                  offerVenue: {
                    ...mockOffer.offerVenue,
                    addressType: OfferAddressType.OTHER,
                  },
                  imageUrl: 'https://picsum.photos/203/',
                }}
              />,
            ]}
          ></Carousel>
        </div>
        <div className={styles['discovery-playlist']}>
          <Carousel
            title={
              <h2 className={styles['section-title']}>
                Explorez les domaines artistiques et culturels
              </h2>
            }
            onLastCarouselElementVisible={() =>
              onWholePlaylistSeen(1, AdagePlaylistType.DOMAIN)
            }
            elements={domainsOptions.map((elm, key) => {
              const colorAndMotif =
                colorAndMotifOrder[key % colorAndMotifOrder.length]

              return (
                <DomainsCard
                  handlePlaylistElementTracking={() =>
                    trackPlaylistElementClicked({
                      playlistId: 1,
                      playlistType: AdagePlaylistType.DOMAIN,
                      elementId: 1, // TODO: change elementId with real value
                    })
                  }
                  key={`domains-${elm.value}`}
                  title={elm.label}
                  color={colorAndMotif.color}
                  src={colorAndMotif.src}
                  href={`/adage-iframe/recherche?token=${adageAuthToken}&domain=${elm.value}`}
                />
              )
            })}
          ></Carousel>
        </div>
        <div className={styles['discovery-playlist']}>
          <Carousel
            title={
              <h2 className={styles['section-title']}>
                Ces interventions peuvent avoir lieu dans votre classe
              </h2>
            }
            onLastCarouselElementVisible={() =>
              onWholePlaylistSeen(2, AdagePlaylistType.OFFER)
            }
            elements={[
              <CardOfferComponent
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 0, // TODO: change all playlistId with real value
                    playlistType: AdagePlaylistType.OFFER,
                    elementId: 1, // TODO: change elementId with real value
                  })
                }
                key={`card-offer-class-1`}
                offer={{
                  ...mockOffer,
                  id: 1,
                  name: 'Ma super offre 3',
                  offerVenue: {
                    ...mockOffer.offerVenue,
                    addressType: OfferAddressType.OFFERER_VENUE,
                  },
                  imageUrl: null,
                }}
              />,
              <CardOfferComponent
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 0,
                    elementId: 2, // TODO: change elementId with real value
                    playlistType: AdagePlaylistType.OFFER,
                  })
                }
                key={`card-offer-class-2`}
                offer={{
                  ...mockOffer,
                  id: 2,
                  offerVenue: {
                    ...mockOffer.offerVenue,
                    addressType: OfferAddressType.SCHOOL,
                  },
                  imageUrl: 'https://picsum.photos/202/',
                }}
              />,
              <CardOfferComponent
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 0,
                    playlistType: AdagePlaylistType.OFFER,
                    elementId: 3, // TODO: change elementId with real value
                  })
                }
                key={`card-offer-class-3`}
                offer={{
                  ...mockOffer,
                  id: 3,
                  offerVenue: {
                    ...mockOffer.offerVenue,
                    addressType: OfferAddressType.OTHER,
                  },
                  imageUrl: 'https://picsum.photos/203/',
                }}
              />,
              <CardOfferComponent
                key={`card-offer-class-4`}
                offer={{
                  ...mockOffer,
                  id: 1,
                  name: 'Ma super offre 4',
                  offerVenue: {
                    ...mockOffer.offerVenue,
                    addressType: OfferAddressType.OFFERER_VENUE,
                  },
                  imageUrl: 'https://picsum.photos/201/',
                }}
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 1,
                    playlistType: AdagePlaylistType.DOMAIN,
                    elementId: 4, // TODO: change elementId with real value
                  })
                }
              />,
              <CardOfferComponent
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 0,
                    playlistType: AdagePlaylistType.OFFER,
                    elementId: 5, // TODO: change elementId with real value
                  })
                }
                key={`card-offer-class-5`}
                offer={{
                  ...mockOffer,
                  id: 2,
                  offerVenue: {
                    ...mockOffer.offerVenue,
                    addressType: OfferAddressType.SCHOOL,
                  },
                  imageUrl: 'https://picsum.photos/202/',
                }}
              />,
              <CardOfferComponent
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 0,
                    playlistType: AdagePlaylistType.OFFER,
                    elementId: 6, // TODO: change elementId with real value
                  })
                }
                key={`card-offer-class-6`}
                offer={{
                  ...mockOffer,
                  id: 3,
                  offerVenue: {
                    ...mockOffer.offerVenue,
                    addressType: OfferAddressType.OTHER,
                  },
                  imageUrl: 'https://picsum.photos/203/',
                }}
              />,
            ]}
          ></Carousel>
        </div>
        <div className={styles['discovery-playlist']}>
          <Carousel
            title={
              <h2 className={styles['section-title']}>
                À moins de 30 minutes à pied de votre établissement
              </h2>
            }
            onLastCarouselElementVisible={() =>
              onWholePlaylistSeen(3, AdagePlaylistType.VENUE)
            }
            elements={[
              <CardVenue
                key="card-venue-1"
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 3,
                    playlistType: AdagePlaylistType.VENUE,
                    elementId: 1, // TODO: change elementId with real value
                  })
                }
                venue={{ ...mockVenue, imageUrl: 'https://picsum.photos/201/' }}
              />,
              <CardVenue
                key="card-venue-1"
                handlePlaylistElementTracking={() =>
                  trackPlaylistElementClicked({
                    playlistId: 3,
                    playlistType: AdagePlaylistType.VENUE,
                    elementId: 1, // TODO: change elementId with real value
                  })
                }
                venue={{
                  ...mockVenue,
                  publicName: 'Mon super 2eme lieu',
                  imageUrl: null,
                }}
              />,
            ]}
          ></Carousel>
        </div>
      </div>
      <div className={styles['discovery-suggestion']}>
        <h2 className={styles['section-title']}>
          Une idée de rubrique ? Soumettez-la nous !
        </h2>
        <ButtonLink
          className={styles['discovery-suggestion-link']}
          variant={ButtonVariant.TERNARYPINK}
          link={{
            to: 'https://passculture.qualtrics.com/jfe/form/SV_6GsfVHSIYQZqdM2',
            isExternal: true,
          }}
          icon={fullLinkIcon}
        >
          Proposer une idée
        </ButtonLink>
      </div>
    </div>
  )
}
