import { connect } from 'react-redux'
import { compose } from 'redux'

import * as pcapi from 'repository/pcapi/pcapi'
import { showNotification } from 'store/reducers/notificationReducer'

import Offers from './Offers'

export const mapStateToProps = state => {
  return {
    getOfferer: pcapi.getOfferer,
  }
}

export const mapDispatchToProps = dispatch => ({
  showInformationNotification: information =>
    dispatch(
      showNotification({
        type: 'information',
        text: information,
      })
    ),
})

export default compose(connect(mapStateToProps, mapDispatchToProps))(Offers)
