import { Link } from 'react-router'
import Icon from '../components/Icon'
import PageHeader from '../components/PageHeader'
import PriorityBadge from '../components/PriorityBadge'
import { useReports } from '../hooks/useReports'
import { displayId, reportTitle } from '../utils/formatters'

const positions = [
  { left: '24%', top: '12%' },
  { left: '65%', top: '12%' },
  { left: '76%', top: '90%' },
  { left: '32%', top: '90%' },
]
const priorityStyles = { Alta: 'high', Média: 'medium', Baixa: 'low' }

export default function MapPage() {
  const { reports } = useReports()
  const examples = reports
    .filter((report) => report.source === 'fixture')
    .slice(0, positions.length)

  return (
    <>
      <PageHeader
        eyebrow="VISÃO DO TERRITÓRIO"
        title="Mapa de ocorrências"
        description="Esboço do espaço que apresentará os relatos no recorte escolhido para o estudo de caso."
      >
        <span className="outline-pill">Esboço</span>
      </PageHeader>
      <div className="map-layout">
        <section
          className="card map-card"
          aria-label="Prévia ilustrativa do mapa"
        >
          <div className="map-topline">
            <Icon name="pin" size={20} />
            <div>
              <strong>Região a definir</strong>
              <span>
                Posições ilustrativas, sem correspondência geográfica.
              </span>
            </div>
          </div>
          <div className="map-preview">
            <div className="map-green map-green-one" />
            <div className="map-green map-green-two" />
            <div className="map-road map-road-one" />
            <div className="map-road map-road-two" />
            <div className="map-road map-road-three" />
            <div className="map-region-label">
              <Icon name="map" size={34} />
              <strong>Seu território, em perspectiva</strong>
              <span>O mapa da região será incluído nesta área.</span>
            </div>
            {examples.map((report, index) => (
              <Link
                key={report.id}
                to={'/relatos/' + report.id}
                style={positions[index]}
                className={
                  'map-marker ' + priorityStyles[report.analysis.priority]
                }
                aria-label={
                  'Ver ' +
                  displayId(report) +
                  ', prioridade ' +
                  report.analysis.priority.toLowerCase()
                }
              >
                <Icon name="pin" size={24} />
              </Link>
            ))}
          </div>
          <div className="map-legend">
            <strong>Prioridades</strong>
            <PriorityBadge priority="Alta" />
            <PriorityBadge priority="Média" />
            <PriorityBadge priority="Baixa" />
          </div>
        </section>
        <aside className="card map-reports">
          <h2>Relatos de exemplo</h2>
          <p>Clique em um marcador ou consulte os detalhes.</p>
          {examples.map((report) => (
            <Link
              key={report.id}
              className="map-report"
              to={'/relatos/' + report.id}
            >
              <span>
                {displayId(report)}
                <Icon name="arrow" size={17} />
              </span>
              <strong>{reportTitle(report)}</strong>
              <PriorityBadge priority={report.analysis.priority} />
            </Link>
          ))}
        </aside>
      </div>
    </>
  )
}
