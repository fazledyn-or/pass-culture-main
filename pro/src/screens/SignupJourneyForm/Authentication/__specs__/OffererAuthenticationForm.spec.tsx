import { screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { Form, Formik } from 'formik'
import React from 'react'
import createFetchMock from 'vitest-fetch-mock'

import { apiAdresse } from 'apiClient/adresse'
import {
  Offerer,
  SignupJourneyContext,
  SignupJourneyContextValues,
} from 'context/SignupJourneyContext'
import { DEFAULT_OFFERER_FORM_VALUES } from 'screens/SignupJourneyForm/Offerer/constants'
import { SubmitButton } from 'ui-kit'
import { renderWithProviders } from 'utils/renderWithProviders'

import OffererAuthenticationForm, {
  OffererAuthenticationFormValues,
} from '../OffererAuthenticationForm'
import { validationSchema } from '../validationSchema'

const fetchMock = createFetchMock(vi)
fetchMock.enableMocks()

vi.mock('apiClient/adresse', async () => {
  return {
    ...((await vi.importActual('apiClient/adresse')) ?? {}),
    default: {
      getDataFromAddress: vi.fn(),
    },
  }
})

vi.spyOn(apiAdresse, 'getDataFromAddress').mockResolvedValue([
  {
    address: '12 rue des lilas',
    city: 'Lyon',
    id: '1',
    latitude: 11.1,
    longitude: -11.1,
    label: '12 rue des lilas 69002 Lyon',
    postalCode: '69002',
  },
  {
    address: '12 rue des tournesols',
    city: 'Paris',
    id: '2',
    latitude: 22.2,
    longitude: -2.22,
    label: '12 rue des tournesols 75003 Paris',
    postalCode: '75003',
  },
])

fetchMock.mockResponse(
  JSON.stringify({
    features: [
      {
        properties: {
          name: 'name',
          city: 'city',
          id: 'id',
          label: 'label',
          postcode: 'postcode',
        },
        geometry: {
          coordinates: [0, 0],
        },
      },
    ],
  }),
  { status: 200 }
)

const renderOffererAuthenticationForm = ({
  initialValues,
  onSubmit = vi.fn(),
  contextValue,
}: {
  initialValues: Partial<OffererAuthenticationFormValues>
  onSubmit?: () => void
  contextValue: SignupJourneyContextValues
}) => {
  const storeOverrides = {
    user: {
      initialized: true,
      currentUser: {
        isAdmin: false,
        email: 'email@example.com',
      },
    },
  }

  return renderWithProviders(
    <SignupJourneyContext.Provider value={contextValue}>
      <Formik
        initialValues={initialValues}
        onSubmit={onSubmit}
        validationSchema={validationSchema}
      >
        <Form>
          <OffererAuthenticationForm />
          <SubmitButton isLoading={false}>Submit</SubmitButton>
        </Form>
      </Formik>
    </SignupJourneyContext.Provider>,
    {
      storeOverrides,
      initialRouterEntries: ['/parcours-inscription/identification'],
    }
  )
}

describe('OffererAuthenticationForm', () => {
  let offererAuthenticationFormValues: Offerer
  let contextValue: SignupJourneyContextValues
  let initialValues: Partial<OffererAuthenticationFormValues>

  beforeEach(() => {
    offererAuthenticationFormValues = {
      ...DEFAULT_OFFERER_FORM_VALUES,
      siret: '123 456 789 33333',
      name: 'Test name',
    }
    initialValues = { ...offererAuthenticationFormValues }
    contextValue = {
      activity: null,
      offerer: offererAuthenticationFormValues,
      setActivity: () => {},
      setOfferer: () => {},
    }
  })

  it('should render form', () => {
    renderOffererAuthenticationForm({
      initialValues: initialValues,
      contextValue: contextValue,
    })

    const siretField = screen.getByLabelText('Numéro de SIRET')
    const nameField = screen.getByLabelText('Raison sociale')

    expect(siretField).toBeDisabled()
    expect(siretField).toHaveValue('123 456 789 33333')

    expect(nameField).toBeDisabled()
    expect(nameField).toHaveValue('Test name')

    expect(screen.getByText('Nom public')).toBeInTheDocument()

    expect(
      screen.getByText(
        'À remplir si le nom de votre structure est différent de la raison sociale. C’est ce nom qui sera visible du public.'
      )
    ).toBeInTheDocument()
  })

  it('should not render error on submit when publicName is empty or filled', async () => {
    renderOffererAuthenticationForm({
      initialValues: initialValues,
      contextValue: contextValue,
    })

    const publicNameField = screen.getByLabelText('Nom public', {
      exact: false,
    })
    await userEvent.type(publicNameField, 'Public name')
    expect(publicNameField).toHaveValue('Public name')
  })
})
