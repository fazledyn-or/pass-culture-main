import React, { useCallback } from 'react'

import { IShouldBlockNavigationReturnValue } from './RouteLeavingGuard/RouteLeavingGuard'
import { ReactComponent as InfoIcon } from './assets/info.svg'
import RouteLeavingGuard from './RouteLeavingGuard'
import { Title } from 'ui-kit'
import styles from './RouteLeavingGuardOfferCreation.module.scss'
import { useLocation } from 'react-router-dom'

export interface RouteLeavingGuardOfferCreationProps {
  when?: boolean
  isCollectiveFlow?: boolean
}

const RouteLeavingGuardOfferCreation = ({
  when = true,
  isCollectiveFlow = false,
}: RouteLeavingGuardOfferCreationProps): JSX.Element => {
  const location = useLocation()

  const shouldBlockNavigation = useCallback(
    (nextLocation: Location): IShouldBlockNavigationReturnValue => {
      let redirectPath = null
      const offerCreationPath = isCollectiveFlow
        ? '/offre/creation/collectif'
        : '/offre/creation/individuel'
      const stocksPathRegex = isCollectiveFlow
        ? /\/offre\/((T-){0,1}[A-Z0-9]+)\/collectif\/stocks/g
        : /\/offre\/([A-Z0-9]+)\/individuel\/stocks/g

      const visibilityPathRegex =
        /\/offre\/((T-){0,1}[A-Z0-9]+)\/collectif\/visibilite/g

      const confirmationPathRegex = isCollectiveFlow
        ? /\/offre\/((T-){0,1}[A-Z0-9]+)\/collectif\/confirmation/g
        : /\/offre\/([A-Z0-9]+)\/individuel\/confirmation/g

      // going from stock to offer
      if (
        location.pathname.match(stocksPathRegex) &&
        nextLocation.pathname.startsWith(offerCreationPath)
      ) {
        redirectPath = '/offres'
        return { redirectPath, shouldBlock: true }
      }
      // going from confirmation to stock
      if (location.pathname.match(confirmationPathRegex)) {
        if (nextLocation.pathname.match(stocksPathRegex)) {
          redirectPath = '/offres'
        }
        return { redirectPath, shouldBlock: false }
      }
      // going to stocks
      // or to visibility
      // or to confirmation
      // or from collective to individual or reverse
      if (
        nextLocation.pathname.match(stocksPathRegex) ||
        nextLocation.pathname.match(visibilityPathRegex) ||
        nextLocation.pathname.match(confirmationPathRegex) ||
        (location.pathname.startsWith(offerCreationPath) &&
          nextLocation.pathname.startsWith(offerCreationPath))
      ) {
        return { shouldBlock: false }
      }
      return { shouldBlock: true }
    },
    [location, isCollectiveFlow]
  )
  return (
    <RouteLeavingGuard
      extraClassNames={styles['exit-offer-creation-dialog']}
      labelledBy="LEAVING_OFFER_CREATION_LABEL_ID"
      shouldBlockNavigation={shouldBlockNavigation}
      when={when}
    >
      <>
        <InfoIcon className={styles['route-leaving-guard-icon']} />
        <Title level={3}>Voulez-vous quitter la création d’offre ?</Title>
        <p>
          Votre offre ne sera pas sauvegardée et toutes les informations seront
          perdues.
        </p>
      </>
    </RouteLeavingGuard>
  )
}

export default RouteLeavingGuardOfferCreation
