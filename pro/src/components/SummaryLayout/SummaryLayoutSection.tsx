import cn from 'classnames'
import React from 'react'

import fullEditIcon from 'icons/full-edit.svg'
import { ButtonLink, Title } from 'ui-kit'

import style from './SummaryLayout.module.scss'

interface SummaryLayoutSectionProps {
  title: string
  children: React.ReactNode | React.ReactNode[]
  className?: string
  editLink?: string // FIXME(MathildeDuboille - 18/10/22): make this props mandatory when we can modify collective offer during its creation
  'aria-label'?: string
}

const Section = ({
  title,
  children,
  className,
  editLink,
  ...props
}: SummaryLayoutSectionProps): JSX.Element => (
  <div className={cn(style['summary-layout-section'], className)}>
    <div className={style['summary-layout-section-header']}>
      <div className={style['summary-layout-section-header-content']}>
        <Title as="h3" level={3}>
          {title}
        </Title>
        {editLink && (
          <ButtonLink
            link={{
              to: editLink,
              isExternal: false,
              'aria-label': props['aria-label'],
            }}
            className={style['summary-layout-section-header-edit-link']}
            icon={fullEditIcon}
          >
            Modifier
          </ButtonLink>
        )}
      </div>
      <div className={style['summary-layout-section-header-separator']}></div>
    </div>
    {children}
  </div>
)

export default Section
