import cx from 'classnames'
import React, { ReactNode } from 'react'

import styles from './Tag.module.scss'

export enum TagVariant {
  SMALL_OUTLINE = 'small-outline',
  LIGHT_GREY = 'light-grey',
  DARK_GREY = 'dark-grey',
  BLACK = 'black',
  PURPLE = 'purple',
  LIGHT_PURPLE = 'light-purple',
  RED = 'red',
  GREEN = 'green',
}

const classByVariant: Record<TagVariant, string> = {
  [TagVariant.SMALL_OUTLINE]: styles['small-outline'],
  [TagVariant.LIGHT_GREY]: styles['light-grey'],
  [TagVariant.DARK_GREY]: styles['dark-grey'],
  [TagVariant.BLACK]: styles['black'],
  [TagVariant.PURPLE]: styles['purple'],
  [TagVariant.LIGHT_PURPLE]: styles['light-purple'],
  [TagVariant.RED]: styles['red'],
  [TagVariant.GREEN]: styles['green'],
}

interface TagProps {
  className?: string
  children: ReactNode
  variant: TagVariant
}

export const Tag = ({
  children,
  className,
  variant,
}: TagProps): JSX.Element => (
  <span className={cx(styles['tag'], classByVariant[variant], className)}>
    {children}
  </span>
)
