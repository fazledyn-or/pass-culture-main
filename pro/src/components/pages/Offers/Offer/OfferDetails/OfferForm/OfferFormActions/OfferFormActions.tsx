import cn from 'classnames'
import React from 'react'
import { Link } from 'react-router-dom'

import {
  Events,
  OFFER_FORM_NAVIGATION_MEDIUM,
} from 'core/FirebaseEvents/constants'
import useAnalytics from 'hooks/useAnalytics'
import { OfferBreadcrumbStep } from 'new_components/OfferBreadcrumb'
import { Button, ButtonLink, SubmitButton } from 'ui-kit'
import { ButtonVariant } from 'ui-kit/Button/types'

import styles from './OfferFormActions.module.scss'

interface IOfferFormActionsProps {
  canSaveDraft: boolean
  cancelUrl: string
  onClickNext: () => void
  onClickSaveDraft: () => void
  isDisabled: boolean
  isSubmitLoading: boolean
  isEdition: boolean
}

const OfferFormActions = ({
  canSaveDraft,
  isDisabled,
  isSubmitLoading,
  isEdition,
  cancelUrl,
  onClickNext,
  onClickSaveDraft,
}: IOfferFormActionsProps) => {
  const { logEvent } = useAnalytics()
  const onCancelClick = () => {
    if (isEdition)
      logEvent?.(Events.CLICKED_OFFER_FORM_NAVIGATION, {
        from: OfferBreadcrumbStep.DETAILS,
        to: OfferBreadcrumbStep.SUMMARY,
        used: OFFER_FORM_NAVIGATION_MEDIUM.STICKY_BUTTONS,
        isEdition: isEdition,
      })
  }

  return (
    <div className={cn(styles['form-actions'])}>
      <ButtonLink
        className={cn(styles['action'], styles['action-cancel'])}
        link={{
          to: cancelUrl,
          isExternal: false,
        }}
        variant={ButtonVariant.SECONDARY}
        onClick={onCancelClick}
      >
        {'Annuler et quitter'}
      </ButtonLink>

      {canSaveDraft && (
        <Button
          className={styles['action']}
          disabled={isDisabled || isSubmitLoading}
          onClick={onClickSaveDraft}
          variant={ButtonVariant.SECONDARY}
        >
          Enregistrer un brouillon
        </Button>
      )}
      <SubmitButton
        disabled={isDisabled}
        isLoading={isSubmitLoading}
        onClick={onClickNext}
      >
        {isEdition ? 'Enregistrer les modifications' : 'Étape suivante'}
      </SubmitButton>
    </div>
  )
}

export default OfferFormActions
