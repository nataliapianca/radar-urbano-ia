import { useState } from 'react'
import { Link } from 'react-router'
import EmptyState from '../components/EmptyState'
import Icon from '../components/Icon'
import PageHeader from '../components/PageHeader'
import ReportCard from '../components/ReportCard'
import { categories, priorities } from '../data/categories'
import { useReports } from '../hooks/useReports'
import {
  displayId,
  formatCoordinates,
  normalizeSearch,
} from '../utils/formatters'

export default function ReportsPage() {
  const { reports, loading, error, reload } = useReports()
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [priority, setPriority] = useState('')
  const filtered = reports.filter((report) => {
    const text = normalizeSearch(
      [
        report.description,
        formatCoordinates(report.location),
        report.status,
        report.analysis?.category || '',
        displayId(report),
      ].join(' '),
    )
    return (
      text.includes(normalizeSearch(search.trim())) &&
      (!category || report.analysis?.category === category) &&
      (!priority || report.analysis?.priority === priority)
    )
  })

  function clearFilters() {
    setSearch('')
    setCategory('')
    setPriority('')
  }

  return (
    <>
      <PageHeader
        eyebrow="ACOMPANHAMENTO"
        title="Ocorrências"
        description="Consulte os relatos registrados e acompanhe como as informações são organizadas para cuidar da cidade."
      >
        <Link className="button primary" to="/">
          <Icon name="plus" size={18} />
          Registrar relato
        </Link>
      </PageHeader>
      {loading || error ? (
        <section className="card">
          <EmptyState
            icon={error ? 'info' : 'list'}
            title={error ? 'Não foi possível carregar os relatos' : 'Carregando relatos…'}
            description={error || 'Buscando as ocorrências registradas no servidor.'}
          >
            {error && (
              <button className="button secondary" type="button" onClick={reload}>
                Tentar novamente
              </button>
            )}
          </EmptyState>
        </section>
      ) : (
        <>
      <section className="card filter-card" aria-label="Filtrar ocorrências">
        <div className="filter-search">
          <label htmlFor="busca">Buscar relato</label>
          <div className="input-with-icon">
            <Icon name="search" size={18} />
            <input
              id="busca"
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Descrição, coordenadas ou identificação"
            />
          </div>
        </div>
        <div>
          <label htmlFor="categoria">Categoria</label>
          <select
            id="categoria"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value="">Todas as categorias</option>
            {categories.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="prioridade">Prioridade</label>
          <select
            id="prioridade"
            value={priority}
            onChange={(event) => setPriority(event.target.value)}
          >
            <option value="">Todas as prioridades</option>
            {priorities.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
      </section>
      <div className="results-heading">
        <p role="status" aria-live="polite">
          <strong>{filtered.length}</strong>{' '}
          {filtered.length === 1 ? 'relato encontrado' : 'relatos encontrados'}
          
        </p>
        {(search || category || priority) && (
          <button className="text-button" type="button" onClick={clearFilters}>
            Limpar filtros
          </button>
        )}
      </div>
      {filtered.length ? (
        <div className="reports-grid">
          {filtered.map((report) => (
            <ReportCard key={report.id} report={report} />
          ))}
        </div>
      ) : (
        <section className="card">
          <EmptyState
            title="Nenhum relato encontrado"
            description="Tente outra busca, remova os filtros ou registre um novo relato."
          >
            <button
              className="button secondary"
              type="button"
              onClick={clearFilters}
            >
              Limpar filtros
            </button>
          </EmptyState>
        </section>
      )}
        </>
      )}
    </>
  )
}
