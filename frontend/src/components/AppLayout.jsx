import { useEffect, useRef } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router'
import Icon from './Icon'

const navigation = [
  { to: '/', label: 'Registrar relato', icon: 'plus', end: true },
  { to: '/relatos', label: 'Ocorrências', icon: 'list' },
  { to: '/mapa', label: 'Mapa', icon: 'map' },
  { to: '/painel', label: 'Painel', icon: 'grid' },
]

export default function AppLayout() {
  const { pathname } = useLocation()
  const mainRef = useRef(null)

  useEffect(() => {
    window.scrollTo(0, 0)
    mainRef.current?.focus({ preventScroll: true })
    const page = navigation.find((item) =>
      item.end ? pathname === item.to : pathname.startsWith(item.to),
    )
    document.title = (page?.label || 'Página') + ' | Radar Urbano IA'
  }, [pathname])

  return (
    <div className="app">
      <a className="skip-link" href="#conteudo">
        Ir para o conteúdo
      </a>
      <header className="site-header">
        <div className="header-inner">
          <Link
            className="brand"
            to="/"
            aria-label="Radar Urbano IA — registrar relato"
          >
            <span className="brand-mark">
              <Icon name="radar" size={30} />
            </span>
            <span>
              Radar Urbano <span className="brand-ai">IA</span>
              <small>Um olhar atento à cidade</small>
            </span>
          </Link>
          <nav className="main-navigation" aria-label="Navegação principal">
            {navigation.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  'nav-link' + (isActive ? ' active' : '')
                }
              >
                <Icon name={item.icon} size={18} />
                {item.label}
              </NavLink>
            ))}
          </nav>
          <span className="demo-pill">
            <span className="status-dot" />
            Demonstração
          </span>
        </div>
      </header>
      <div className="demo-notice">
        <div className="container">
          <Icon name="info" size={17} />
          <span>Protótipo de navegação com dados de exemplo.</span>
          <span className="study-region">
            <Icon name="pin" size={15} />
            Região a definir
          </span>
        </div>
      </div>
      <main
        id="conteudo"
        ref={mainRef}
        tabIndex={-1}
        className="container main-content"
      >
        <Outlet />
      </main>
      <footer className="site-footer container">
        <span>
          Radar Urbano IA <span className="footer-separator">/</span> Projeto
          Integrador IV
        </span>
        <span>Participação cidadã. Informação para cuidar da cidade.</span>
      </footer>
    </div>
  )
}
