import Icon from './Icon'

export default function EmptyState({
  icon = 'search',
  title,
  description,
  children,
}) {
  return (
    <div className="empty-state">
      <span className="empty-icon">
        <Icon name={icon} size={28} />
      </span>
      <h2>{title}</h2>
      <p>{description}</p>
      {children}
    </div>
  )
}
