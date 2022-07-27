import Icon from 'components/layout/Icon'
import { NavLink } from 'react-router-dom'
import React from 'react'
import cn from 'classnames'
import styles from './GoBackLink.module.scss'

interface GoBackLinkProps {
  to: string
  title: string
}

const GoBackLink = ({ to, title }: GoBackLinkProps): JSX.Element => (
  <NavLink className={cn(styles['go-back-button'])} to={to}>
    <Icon svg="ico-back" className={styles['go-back-icon']} />
    {title}
  </NavLink>
)

export default GoBackLink
