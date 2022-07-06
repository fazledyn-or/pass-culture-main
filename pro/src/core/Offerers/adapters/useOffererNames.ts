import { GET_DATA_ERROR_MESSAGE } from 'core/shared'
import { TOffererName } from 'core/Offerers/types'
import { apiV1 } from 'api/api'
import { useAdapter } from 'hooks'

type TGetOffererNamesAdapter = Adapter<void, TOffererName[], TOffererName[]>

const FAILING_RESPONSE = {
  isOk: false,
  message: GET_DATA_ERROR_MESSAGE,
  payload: [],
}

const getOffererNamesAdapter: TGetOffererNamesAdapter = async () => {
  try {
    const response = await apiV1.getOfferersListOfferersNames()
    return {
      isOk: true,
      message: null,
      payload: response.offerersNames,
    }
  } catch (e) {
    return FAILING_RESPONSE
  }
}

const useGetOffererNames = () =>
  useAdapter<TOffererName[], TOffererName[]>(getOffererNamesAdapter)

export default useGetOffererNames
