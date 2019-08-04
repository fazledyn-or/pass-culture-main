import getRemovedDetailsUrl from '../getRemovedDetailsUrl'

describe('src | helpers | getRemovedDetailsUrl', () => {
  describe('when we have no details url', () => {
    it('should return undefined', () => {
      // given
      const location = {
        pathname: '/foo/bar',
        search: '?fifi',
      }
      const match = {
        params: {
          details: undefined,
        },
      }

      // when
      const result = getRemovedDetailsUrl(location, match)

      //then
      expect(result).toBeUndefined()
    })
  })

  describe('when we have details on url', () => {
    it('should remove the details', () => {
      // given
      const location = {
        pathname: '/foo/details/bar',
        search: '?fifi',
      }
      const match = {
        params: {
          details: 'details',
        },
      }

      // when
      const removedDetailsUrl = getRemovedDetailsUrl(location, match)

      //then
      expect(removedDetailsUrl).toBe('/foo?fifi')
    })
  })
})
