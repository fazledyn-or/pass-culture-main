import get from 'lodash.get'
import moment from 'moment'
import React, { Component } from 'react'
import { findDOMNode } from 'react-dom'
import { connect } from 'react-redux'

import OccurenceForm from './OccurenceForm'
import OccurenceItem from './OccurenceItem'
import { mergeForm } from '../reducers/form'
import { NEW } from '../utils/config'

class OccurenceManager extends Component {
  constructor () {
    super()
    this.state = {
      isAdding: false
    }
  }

  onAddClick = () => {
    const {
      mergeForm,
      occurences,
    } = this.props

    const lastOccurence = occurences.length > 0 && occurences[occurences.length-1]
    if (lastOccurence) {
      const {
        beginningDatetime,
        endDatetime,
        offer
      } = lastOccurence
      const {
        available,
        groupSize,
        pmrGroupSize,
        price
      } = get(offer, '0', {})
      const date = moment(beginningDatetime).add(1, 'days')
      mergeForm('eventOccurences', NEW,
        {
          available,
          date,
          time: date.format('HH:mm'),
          endTime: moment(endDatetime).add(1, 'days').format('HH:mm'),
          groupSize,
          pmrGroupSize,
          price: typeof price === 'undefined'
            ? 0
            : price
        })
    }

    this.setState({ isAdding: true })
  }


  render() {
    const {
      history,
      location,
      match,
      occasion,
      occurences,
    } = this.props
    const { isAdding } = this.state

    return (
      <div className='occurence-manager'>
        <div className='occurence-table-wrapper'>
          <table className='table is-hoverable occurence-table'>
            <thead>
              <tr>
                <td>Date</td>
                <td>Heure de début</td>
                <td>Heure de fin</td>
                <td>Prix</td>
                <td>Places (total)</td>
                <td>Dont (PMR)</td>
                <td>Supprimer</td>
                <td>Modifier</td>
              </tr>
            </thead>
            <tbody>
              {
                isAdding
                  ? (
                    <OccurenceForm
                      history={history}
                      occasion={occasion}
                      onDeleteClick={e => this.setState({isAdding: false})}
                    />
                  ) : (
                  <tr><td colSpan='10'>
                    <button className='button is-secondary' onClick={this.onAddClick}>
                      + Ajouter un horaire
                    </button>
                  </td></tr>
                )
              }
              {
                occurences && occurences.map(o =>
                  <OccurenceItem
                    key={o.id}
                    isAdding={isAdding}
                    history={history}
                    location={location}
                    match={match}
                    occasion={occasion}
                    occurence={o}
                    occurences={occurences}
                  />
                )
              }
            </tbody>
            {occurences.length > 12 && (
              <thead>
                <tr>
                  <td>Date</td>
                  <td>Heure de début</td>
                  <td>Heure de fin</td>
                  <td>Prix</td>
                  <td>Places (total)</td>
                  <td>Dont PMR</td>
                  <td>Supprimer</td>
                  <td>Modifier</td>
                </tr>
              </thead>
            )}
          </table>
        </div>
      </div>
    )
  }
}

export default connect(null, { mergeForm })(OccurenceManager)
