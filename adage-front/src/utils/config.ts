const NODE_ENV = process.env.NODE_ENV || 'development'

export const IS_DEV = NODE_ENV === 'development'
export const IS_PROD = !IS_DEV

export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost'

export const {
  REACT_APP_ALGOLIA_APP_ID: ALGOLIA_APP_ID,
  REACT_APP_ALGOLIA_API_KEY: ALGOLIA_API_KEY,
  REACT_APP_ALGOLIA_OFFERS_INDEX: ALGOLIA_OFFERS_INDEX,
  REACT_APP_ENVIRONMENT_NAME: ENVIRONMENT_NAME,
  REACT_APP_URL_FOR_MAINTENANCE: URL_FOR_MAINTENANCE,
  REACT_APP_SENTRY_SAMPLE_RATE: SENTRY_SAMPLE_RATE,
  REACT_APP_SENTRY_SERVER_URL: SENTRY_SERVER_URL,
  REACT_APP_ASSETS_URL: ASSETS_URL,
  REACT_APP_ENABLE_NEW_OFFER_DESIGN: ENABLE_NEW_OFFER_DESIGN,
} = process.env
