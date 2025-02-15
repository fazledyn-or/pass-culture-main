import React from 'react'
import { useNavigate } from 'react-router-dom'

import { AppLayout } from 'app/AppLayout'
import CollectiveOfferLayout from 'components/CollectiveOfferLayout'
import {
  Mode,
  CollectiveOffer,
  isCollectiveOfferTemplate,
} from 'core/OfferEducational'
import { computeURLCollectiveOfferId } from 'core/OfferEducational/utils/computeURLCollectiveOfferId'
import { extractInitialVisibilityValues } from 'core/OfferEducational/utils/extractInitialVisibilityValues'
import { useAdapter } from 'hooks'
import useNotification from 'hooks/useNotification'
import CollectiveOfferVisibilityScreen from 'screens/CollectiveOfferVisibility'
import {
  MandatoryCollectiveOfferFromParamsProps,
  withCollectiveOfferFromParams,
} from 'screens/OfferEducational/useCollectiveOfferFromParams'
import Spinner from 'ui-kit/Spinner/Spinner'

import getEducationalInstitutionsAdapter from './adapters/getEducationalInstitutionsAdapter'
import patchEducationalInstitutionAdapter from './adapters/patchEducationalInstitutionAdapter'

const CollectiveOfferVisibility = ({
  offer,
  reloadCollectiveOffer,
  isTemplate,
}: MandatoryCollectiveOfferFromParamsProps) => {
  const notify = useNotification()
  const navigate = useNavigate()
  const {
    error,
    data: institutionsPayload,
    isLoading,
  } = useAdapter(getEducationalInstitutionsAdapter)

  if (isCollectiveOfferTemplate(offer)) {
    throw new Error(
      'Impossible de mettre à jour la visibilité d’une offre vitrine.'
    )
  }

  const onSuccess = ({
    message,
    payload,
  }: {
    message: string
    payload: CollectiveOffer
  }) => {
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    reloadCollectiveOffer()
    navigate(
      `/offre/${computeURLCollectiveOfferId(
        payload.id,
        false
      )}/collectif/recapitulatif`
    )
    notify.success(message)
  }

  if (isLoading) {
    return <Spinner />
  }

  if (error) {
    return null
  }

  return (
    <AppLayout>
      <CollectiveOfferLayout subTitle={offer.name} isTemplate={isTemplate}>
        <CollectiveOfferVisibilityScreen
          mode={offer.isVisibilityEditable ? Mode.EDITION : Mode.READ_ONLY}
          patchInstitution={patchEducationalInstitutionAdapter}
          initialValues={extractInitialVisibilityValues(
            offer.institution,
            offer.teacher
          )}
          onSuccess={onSuccess}
          institutions={institutionsPayload.institutions}
          isLoadingInstitutions={isLoading}
          offer={offer}
          reloadCollectiveOffer={reloadCollectiveOffer}
        />
      </CollectiveOfferLayout>
    </AppLayout>
  )
}

export default withCollectiveOfferFromParams(CollectiveOfferVisibility)
