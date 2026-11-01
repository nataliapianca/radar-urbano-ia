import { Link, useLocation, useParams } from 'react-router'
import EmptyState from '../components/EmptyState'
import Icon from '../components/Icon'
import PageHeader from '../components/PageHeader'
import PriorityBadge from '../components/PriorityBadge'
import { useReports } from '../hooks/useReports'
import {
  displayId,
  formatCoordinates,
  formatDate,
  reportTitle,
} from '../utils/formatters'

export default function ReportDetailPage() {
  const { reportId } = useParams()
  const { state } = useLocation()
  const { reports, loading, error, reload } = useReports()
  const report = reports.find((item) => item.id === reportId)

  if (loading || error) {
    return (
      <section className="card">
        <EmptyState
          icon={error ? 'info' : 'list'}
          title={
            error ? 'Não foi possível carregar o relato' : 'Carregando relato…'
          }
          description={error || 'Buscando as informações no servidor.'}
        >
          {error && (
            <button className="button secondary" type="button" onClick={reload}>
              Tentar novamente
            </button>
          )}
        </EmptyState>
      </section>
    )
  }

  if (!report) {
    return (
      <section className="card">
        <EmptyState
          icon="list"
          title="Relato não encontrado"
          description="Não há um relato registrado com este identificador. Você pode consultar as ocorrências disponíveis."
        >
          <Link className="button primary" to="/relatos">
            Ver ocorrências
          </Link>
        </EmptyState>
      </section>
    )
  }

  return (
    <>
      <Link className="back-link" to="/relatos">
        <Icon name="back" size={17} />
        Voltar para ocorrências
      </Link>
      {state?.created && (
        <div className="success-notice" role="status">
          <Icon name="check" size={21} />
          <div>
            <strong>Relato enviado.</strong>
            <p>Ele foi registrado e aguarda a análise.</p>
          </div>
        </div>
      )}
      <PageHeader
        eyebrow={displayId(report) + ' · ' + report.status.toUpperCase()}
        title={reportTitle(report)}
        description="Informações do relato e resultado da análise."
      />
      <div className="details-layout">
        <section className="card detail-card" aria-labelledby="relato-title">
          <h2 id="relato-title">Sobre o relato</h2>
          <p className="detail-description">{report.description}</p>
          <div className="detail-meta">
            <Icon name="pin" size={20} />
            <div>
              <h3>Localização</h3>
              <p className="coordinates-value">
                {formatCoordinates(report.location)}
              </p>
              <small>
                Lat. {report.location.latitude.toFixed(5)} · Long.{' '}
                {report.location.longitude.toFixed(5)}
              </small>
              {report.location.attribution && (
                <small>{report.location.attribution}</small>
              )}
            </div>
          </div>
          <div className="detail-meta">
            <Icon name="clock" size={20} />
            <div>
              <h3>Data do registro</h3>
              <time dateTime={report.createdAt}>
                {formatDate(report.createdAt)}
              </time>
            </div>
          </div>
        </section>
        <section className="card analysis-card" aria-labelledby="analise-title">
          <div className="analysis-heading">
            <span className="section-icon">
              <Icon name="sparkles" size={22} />
            </span>
            <div>
              <h2 id="analise-title">Resultado da análise</h2>
              <p>
                {report.analysis
                  ? 'Classificação registrada para este relato.'
                  : 'Situação: ' + report.status + '.'}
              </p>
            </div>
          </div>
          {report.analysis ? (
            <>
              <div className="analysis-summary">
                <div>
                  <span className="detail-label">Categoria</span>
                  <strong>{report.analysis.category}</strong>
                </div>
                <div>
                  <span className="detail-label">Prioridade</span>
                  <PriorityBadge priority={report.analysis.priority} />
                </div>
              </div>
              <div className="analysis-item">
                <Icon name="shield" size={20} />
                <div>
                  <h3>Risco associado</h3>
                  <p>{report.analysis.risk}</p>
                </div>
              </div>
              <div className="analysis-item">
                <Icon name="building" size={20} />
                <div>
                  <h3>Setor responsável sugerido</h3>
                  <p>{report.analysis.suggestedSector}</p>
                  <small>Sugestão, sem encaminhamento a um órgão.</small>
                </div>
              </div>
              {report.analysis.details.length > 0 && (
                <div className="analysis-item">
                  <Icon name="list" size={20} />
                  <div>
                    <h3>Informações relevantes</h3>
                    <ul>
                      {report.analysis.details.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </>
          ) : (
            <EmptyState
              icon="sparkles"
              title="Análise ainda não disponível"
              description="Categoria, prioridade, risco e setor sugerido aparecerão aqui quando o relato for classificado."
            />
          )}
        </section>
      </div>
    </>
  )
}
