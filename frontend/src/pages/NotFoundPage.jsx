import { Link } from 'react-router'
import EmptyState from '../components/EmptyState'

export default function NotFoundPage() {
  return (
    <section className="card">
      <EmptyState
        icon="map"
        title="Página não encontrada"
        description="Use a navegação para registrar um relato ou explorar as ocorrências de exemplo."
      >
        <Link className="button primary" to="/">
          Ir para o registro de relatos
        </Link>
      </EmptyState>
    </section>
  )
}
