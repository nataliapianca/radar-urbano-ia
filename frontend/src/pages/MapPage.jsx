import { Link } from 'react-router'
import Icon from '../components/Icon'
import PageHeader from '../components/PageHeader'
import PriorityBadge from '../components/PriorityBadge'
import { useReports } from '../hooks/useReports'
import { displayId, reportTitle } from '../utils/formatters'

const priorityStyles = { Alta: 'high', Média: 'medium', Baixa: 'low' }
const MAX_MARKERS = 30

// Posiciona os marcadores pela caixa delimitadora dos relatos (mapa ilustrativo).
function markerPositions(list) {
  const lats = list.map((report) => report.location.latitude)
  const lons = list.map((report) => report.location.longitude)
  const minLat = Math.min(...lats)
  const maxLat = Math.max(...lats)
  const minLon = Math.min(...lons)
  const maxLon = Math.max(...lons)
  const scale = (value, min, max) =>
    max === min ? 50 : 12 + ((value - min) / (max - min)) * 76
  return list.map((report) => ({
    left: scale(report.location.longitude, minLon, maxLon) + '%',
    top: 100 - scale(report.location.latitude, minLat, maxLat) + '%',
  }))
}

export default function MapPage() {
  const { reports } = useReports()
  const shown = reports.slice(0, MAX_MARKERS)
  const positions = shown.length ? markerPositions(shown) : []

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
                Posições relativas às coordenadas dos relatos, sem mapa geográfico.
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
            {shown.map((report, index) => (
              <Link
                key={report.id}
                to={'/relatos/' + report.id}
                style={positions[index]}
                className={
                  'map-marker ' +
                  (priorityStyles[report.analysis?.priority] || 'pending')
                }
                aria-label={
                  'Ver ' +
                  displayId(report) +
                  (report.analysis
                    ? ', prioridade ' + report.analysis.priority.toLowerCase()
                    : ', sem análise')
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
          <h2>Relatos registrados</h2>
          <p>
            {shown.length
              ? 'Clique em um marcador ou consulte os detalhes.'
              : 'Nenhum relato registrado ainda.'}
          </p>
          {shown.map((report) => (
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
              <PriorityBadge priority={report.analysis?.priority} />
            </Link>
          ))}
        </aside>
      </div>
    </>
  )
}
