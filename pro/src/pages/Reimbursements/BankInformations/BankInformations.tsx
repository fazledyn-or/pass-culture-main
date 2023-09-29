import React, { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { api } from 'apiClient/api'
import { GetOffererBankAccountsResponseModel } from 'apiClient/v1'
import { useReimbursementContext } from 'context/ReimbursementContext/ReimbursementContext'
import { SelectOption } from 'custom_types/form'
import useNotification from 'hooks/useNotification'
import fullLinkIcon from 'icons/full-link.svg'
import fullMoreIcon from 'icons/full-more.svg'
import strokeMoneyIcon from 'icons/stroke-repayment.svg'
import { Button, ButtonLink } from 'ui-kit'
import { ButtonVariant } from 'ui-kit/Button/types'
import SelectInput from 'ui-kit/form/Select/SelectInput'
import Spinner from 'ui-kit/Spinner/Spinner'
import { SvgIcon } from 'ui-kit/SvgIcon/SvgIcon'
import { sortByLabel } from 'utils/strings'

import styles from './BankInformations.module.scss'

const BankInformations = (): JSX.Element => {
  const notify = useNotification()

  const { offerers, selectedOfferer, setSelectedOfferer } =
    useReimbursementContext()

  const [isOffererBankAccountsLoading, setIsOffererBankAccountsLoading] =
    useState<boolean>(false)
  const [, setSelectedOffererBankAccounts] =
    useState<GetOffererBankAccountsResponseModel | null>(null)
  const [searchParams, setSearchParams] = useSearchParams()
  const [isOffererLoading, setIsOffererLoading] = useState<boolean>(false)

  const { structure: offererId } = Object.fromEntries(searchParams)

  const [offererOptions, setOffererOptions] = useState<SelectOption[]>([])
  const selectedOffererId = selectedOfferer?.id.toString() ?? ''

  const updateOfferer = async (newOffererId: string) => {
    if (newOffererId === '') {
      setSelectedOfferer(null)
    } else {
      setIsOffererLoading(true)
      const offerer = await api.getOfferer(Number(newOffererId))
      setSelectedOfferer(offerer)
      setIsOffererLoading(false)
    }
  }

  useEffect(() => {
    if (offererId && offerers && offerers?.length > 0) {
      updateOfferer(offererId)
    }
    if (searchParams.has('structure')) {
      searchParams.delete('structure')
      setSearchParams(searchParams)
    }
  }, [])

  useEffect(() => {
    if (offerers && offerers.length > 1) {
      const initialOffererOptions = sortByLabel(
        offerers.map(item => ({
          value: item['id'].toString(),
          label: item['name'],
        }))
      )
      setOffererOptions([
        {
          label: 'Sélectionnez une structure',
          value: '',
        },
        ...initialOffererOptions,
      ])
    }
  }, [offerers])

  useEffect(() => {
    const getSelectedOffererBankAccounts = async (
      selectedOffererId: number
    ) => {
      setIsOffererBankAccountsLoading(true)
      try {
        const offererBankAccounts =
          await api.getOffererBankAccountsAndAttachedVenues(selectedOffererId)
        setSelectedOffererBankAccounts(offererBankAccounts)
      } catch (error) {
        notify.error(
          'Impossible de récupérer les informations relatives à vos comptes bancaires.'
        )
      } finally {
        setIsOffererBankAccountsLoading(false)
      }
    }

    selectedOfferer && getSelectedOffererBankAccounts(selectedOfferer.id)
  }, [selectedOfferer])

  if (isOffererBankAccountsLoading || isOffererLoading) {
    return <Spinner />
  }

  return (
    <>
      <div className="header">
        <h2 className="header-title">Informations bancaires</h2>
      </div>
      <div className={styles['information']}>
        {!selectedOfferer?.hasValidBankAccount &&
          !selectedOfferer?.hasPendingBankAccount &&
          'Ajoutez au moins un compte bancaire pour percevoir vos remboursements.'}

        {(selectedOfferer?.hasValidBankAccount ||
          selectedOfferer?.hasPendingBankAccount) &&
          "Vous pouvez ajouter plusieurs comptes bancaires afin de percevoir les remboursements de vos offres. Chaque compte bancaire fera l'objet d'un remboursement et d'un justificatif de remboursement distincts."}

        <ButtonLink
          link={{
            to: '', // TODO: le liens manque
            isExternal: true,
            target: '_blank',
          }}
          icon={fullLinkIcon}
          className={styles['information-link-button']}
        >
          En savoir plus
        </ButtonLink>
      </div>
      {offerers && offerers.length > 1 && (
        <div className={styles['select-offerer-section']}>
          <div className={styles['select-offerer-input']}>
            <div className={styles['select-offerer-input-label']}>
              <label htmlFor="selected-offerer">Structure</label>
            </div>
            <SelectInput
              onChange={e => updateOfferer(e.target.value)}
              id="selected-offerer"
              data-testid="select-input-offerer"
              name="offererId"
              options={offererOptions}
              value={selectedOffererId}
            />
          </div>
          {selectedOffererId === '' && (
            <div className={styles['no-offerer-selected']}>
              <SvgIcon
                src={strokeMoneyIcon}
                alt={''}
                width="88"
                className={styles['repayment-icon']}
              />
              <span className={styles['no-offerer-selected-text']}>
                Sélectionnez une structure pour faire apparaitre tous les
                comptes bancaires associés
              </span>
            </div>
          )}
        </div>
      )}
      {!(offerers && offerers?.length > 1 && selectedOffererId === '') && (
        <Button
          icon={fullMoreIcon}
          className={styles['add-bank-account-button']}
          variant={
            selectedOfferer &&
            selectedOfferer?.venuesWithNonFreeOffersWithoutBankAccounts.length >
              0
              ? ButtonVariant.SECONDARY
              : ButtonVariant.PRIMARY
          }
        >
          Ajouter un compte bancaire
        </Button>
      )}
    </>
  )
}

export default BankInformations
