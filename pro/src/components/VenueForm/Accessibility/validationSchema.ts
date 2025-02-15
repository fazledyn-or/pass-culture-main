import * as yup from 'yup'

const isOneTrue = (values: Record<string, boolean>): boolean =>
  Object.values(values).includes(true)

const validationSchema = {
  accessibility: yup.object().when('isVenueVirtual', {
    is: false,
    then: (schema) =>
      schema
        .test({
          name: 'is-one-true',
          message: 'Veuillez sélectionner au moins un critère d’accessibilité',
          test: isOneTrue,
        })
        .shape({
          mental: yup.boolean(),
          audio: yup.boolean(),
          visual: yup.boolean(),
          motor: yup.boolean(),
          none: yup.boolean(),
        }),
  }),
}

export default validationSchema
