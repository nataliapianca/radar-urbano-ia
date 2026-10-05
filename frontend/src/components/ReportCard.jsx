import { Link } from 'react-router'
import { categoryIcons } from '../data/categories'
import { displayId, formatDate, reportTitle } from '../utils/formatters'
import Icon from './Icon'
import PriorityBadge from './PriorityBadge'

export default function ReportCard({ report }) {
  return (
    <article className="card report-card">
      <div className="report-card-top">
        <span className="category-icon">
          <Icon
            name={categoryIcons[report.analysis?.category] || 'list'}
            size={23}
          />
        </span>
        <PriorityBadge priority={report.analysis?.priority} />
      </div>
      <p className="report-category">
        {report.analysis?.category || 'Categoria a definir'}
        <span>{displayId(report)}</span>
      </p>
      <h2>
        <Link to={'/relatos/' + report.id}>{reportTitle(report)}</Link>
      </h2>
      <p className="report-description">{report.description}</p>
      <p className="report-location">
        <Icon name="pin" size={16} />
        {report.location.reference}
      </p>
      <div className="report-card-bottom">
        <time dateTime={report.createdAt}>{formatDate(report.createdAt)}</time>
        <Link className="text-link" to={'/relatos/' + report.id}>
          Ver relato
          <Icon name="arrow" size={17} />
        </Link>
      </div>
    </article>
  )
}
