import { Link } from 'react-router'
import Icon from '../components/Icon'
import PageHeader from '../components/PageHeader'
import PriorityBadge from '../components/PriorityBadge'
import { categories, priorities } from '../data/categories'
import { useReports } from '../hooks/useReports'

export default function DashboardPage() {
  const { reports } = useReports()
  const analyzed = reports.filter((report) => report.analysis)
  const categoryCounts = categories.map((category) => ({
    category,
    count: analyzed.filter((report) => report.analysis.category === category)
      .length,
  }))
  const maxCount = Math.max(1, ...categoryCounts.map((item) => item.count))
  const highCount = analyzed.filter(
    (report) => report.analysis.priority === 'Alta',
  ).length
  const represented = categoryCounts.filter((item) => item.count > 0).length
  const statistics = [
    {
      label: 'Relatos na demonstração',
      value: reports.length,
      icon: 'list',
      hint: 'Exemplos e criações desta sessão',
    },
    {
      label: 'Exemplos com prioridade alta',
      value: highCount,
      icon: 'shield',
      hint: 'Classificações ilustrativas',
    },
    {
      label: 'Categorias representadas',
      value: represented + ' / ' + categories.length,
      icon: 'grid',
      hint: 'Categorias previstas no relatório',
    },
  ]

  return (
    <>
      <PageHeader
        eyebrow="VISÃO ADMINISTRATIVA"
        title="Painel de ocorrências"
        description="Estrutura inicial dos indicadores para acompanhar a distribuição dos relatos. Todos os números se referem à demonstração."
      >
        <span className="outline-pill">Esboço</span>
      </PageHeader>
      <div className="statistics-grid">
        {statistics.map((item) => (
          <section className="card statistic-card" key={item.label}>
            <div>
              <p>{item.label}</p>
              <strong>{item.value}</strong>
              <span>{item.hint}</span>
            </div>
            <span className="category-icon">
              <Icon name={item.icon} size={23} />
            </span>
          </section>
        ))}
      </div>
      <div className="dashboard-layout">
        <section className="card chart-card">
          <div className="section-heading">
            <div>
              <h2>Relatos por categoria</h2>
              <p>Distribuição dos resultados de exemplo.</p>
            </div>
          </div>
          <ul className="category-chart">
            {categoryCounts.map(({ category, count }) => (
              <li key={category}>
                <div>
                  <span>{category}</span>
                  <strong>{count}</strong>
                </div>
                <div className="chart-track" aria-hidden="true">
                  <span style={{ width: (count / maxCount) * 100 + '%' }} />
                </div>
              </li>
            ))}
          </ul>
        </section>
        <section className="card chart-card">
          <div className="section-heading">
            <div>
              <h2>Distribuição de prioridades</h2>
              <p>Exemplos com análise ilustrativa.</p>
            </div>
          </div>
          <div className="priority-totals">
            {priorities.map((priority) => (
              <div key={priority}>
                <PriorityBadge priority={priority} />
                <strong>
                  {
                    analyzed.filter(
                      (report) => report.analysis.priority === priority,
                    ).length
                  }
                </strong>
              </div>
            ))}
          </div>
          <div className="dashboard-note">
            <Icon name="info" size={20} />
            <p>
              {reports.length - analyzed.length}{' '}
              {reports.length - analyzed.length === 1
                ? 'relato de exemplo sem análise.'
                : 'relatos de exemplo sem análise.'}
            </p>
          </div>
          <Link className="text-link" to="/relatos">
            Consultar ocorrências
            <Icon name="arrow" size={17} />
          </Link>
        </section>
      </div>
      <div className="future-panels">
        <section className="card future-panel">
          <span className="section-icon">
            <Icon name="map" size={22} />
          </span>
          <div>
            <h2>Indicadores por região</h2>
            <p>Espaço reservado para o recorte do estudo de caso.</p>
            <span className="outline-pill">Região a definir</span>
          </div>
        </section>
        <section className="card future-panel">
          <span className="section-icon">
            <Icon name="clock" size={22} />
          </span>
          <div>
            <h2>Acompanhamento por situação</h2>
            <p>
              Espaço reservado para as situações das ocorrências, que ainda
              serão definidas.
            </p>
            <span className="outline-pill">Estrutura prevista</span>
          </div>
        </section>
      </div>
    </>
  )
}
