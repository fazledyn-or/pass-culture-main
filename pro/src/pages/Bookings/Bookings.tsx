import React from 'react'
import { useLocation } from 'react-router-dom'

import { AppLayout } from 'app/AppLayout'
import { getVenuesAdapter } from 'core/Bookings/adapters'
import { Audience } from 'core/shared'
import BookingsScreen from 'screens/Bookings'

import {
  getBookingsCSVFileAdapter,
  getBookingsXLSFileAdapter,
  getFilteredBookingsRecapAdapter,
  getUserHasBookingsAdapter,
} from './adapters'

const Bookings = (): JSX.Element => {
  const location = useLocation()

  return (
    <AppLayout>
      <BookingsScreen
        audience={Audience.INDIVIDUAL}
        getBookingsCSVFileAdapter={getBookingsCSVFileAdapter}
        getBookingsXLSFileAdapter={getBookingsXLSFileAdapter}
        getFilteredBookingsRecapAdapter={getFilteredBookingsRecapAdapter}
        getUserHasBookingsAdapter={getUserHasBookingsAdapter}
        getVenuesAdapter={getVenuesAdapter}
        locationState={location.state}
      />
    </AppLayout>
  )
}

export default Bookings
