import { Link, useLocation, useParams } from 'react-router'
import EmptyState from '../components/EmptyState'
import Icon from '../components/Icon'
import PageHeader from '../components/PageHeader'
import PriorityBadge from '../components/PriorityBadge'
import { useReports } from '../hooks/useReports'
import { displayId, formatDate, reportTitle } from '../utils/formatters'

export default function ReportDetailPage() {
  const { reportId } = useParams()
  const { state } = useLocation()
  const { reports } = useReports()
  const report = reports.find((item) => item.id === reportId)

  if (!report) {
    return (
      <section className="card">
        <EmptyState
          icon="list"
          title="Relato não encontrado"
          description="Os relatos criados nesta demonstração são removidos ao recarregar a página. Você pode consultar os exemplos disponíveis."
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
      {state?.created && report.source === 'session' && (
        <div className="success-notice" role="status">
          <Icon name="check" size={21} />
          <div>
            <strong>Relato de exemplo criado.</strong>
            <p>Ele ficará disponível durante esta sessão de demonstração.</p>
          </div>
        </div>
      )}
      <PageHeader
        eyebrow={displayId(report) + ' · DADOS DE EXEMPLO'}
        title={reportTitle(report)}
        description="Informações do relato e espaço para o resultado da análise."
      />
      <div className="details-layout">
        <section className="card detail-card" aria-labelledby="relato-title">
          <h2 id="relato-title">Sobre o relato</h2>
          <p className="detail-description">{report.description}</p>
          <div className="detail-meta">
            <Icon name="pin" size={20} />
            <div>
              <h3>Localização</h3>
              <p>{report.location.reference}</p>
              <small>Região do estudo a definir</small>
              {report.location.latitude !== null &&
                report.location.longitude !== null && (
                  <p className="coordinates-value">
                    Latitude: {report.location.latitude} · Longitude:{' '}
                    {report.location.longitude}
                  </p>
                )}
            </div>
          </div>
          <div className="detail-meta">
            <Icon name="clock" size={20} />
            <div>
              <h3>Data do exemplo</h3>
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
                  ? 'Apresentação ilustrativa das informações previstas.'
                  : 'Área prevista para os resultados do relato.'}
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
                  <small>
                    Sugestão ilustrativa, sem encaminhamento a um órgão.
                  </small>
                </div>
              </div>
              <p className="analysis-note">
                <Icon name="info" size={17} />
                Estes resultados são exemplos preparados para o protótipo.
              </p>
            </>
          ) : (
            <EmptyState
              icon="sparkles"
              title="Análise ainda não disponível"
              description="Categoria, prioridade, risco e setor sugerido terão espaço aqui. Consulte um relato de exemplo para visualizar essa apresentação."
            >
              <Link className="button secondary" to="/relatos/exemplo-001">
                Ver análise de exemplo
                <Icon name="arrow" size={17} />
              </Link>
            </EmptyState>
          )}
        </section>
      </div>
    </>
  )
}
