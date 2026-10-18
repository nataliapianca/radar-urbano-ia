import { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import Icon from '../components/Icon'
import PageHeader from '../components/PageHeader'
import { categories, categoryIcons } from '../data/categories'
import { useReports } from '../hooks/useReports'

const initialForm = {
  description: '',
  latitude: '',
  longitude: '',
}

const example = {
  description:
    'Há um poste apagado na rua há três dias. O trecho fica sem luz durante a noite e é utilizado por moradores.',
  latitude: '-20.3155',
  longitude: '-40.3128',
}

function invalidCoordinate(value, limit) {
  const text = value.trim()
  const number = Number(text)
  return text === '' || !Number.isFinite(number) || Math.abs(number) > limit
}

function FieldMessage({ id, error, hint }) {
  return (
    <p
      id={id}
      className={error ? 'field-message error-message' : 'field-message'}
    >
      {error || hint}
    </p>
  )
}

export default function RegisterPage() {
  const [form, setForm] = useState(initialForm)
  const [errors, setErrors] = useState({})
  const descriptionRef = useRef(null)
  const latitudeRef = useRef(null)
  const longitudeRef = useRef(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const { addReport } = useReports()
  const navigate = useNavigate()

  function updateField(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }))
  }

  function fillExample() {
    setForm(example)
    setErrors({})
    setSubmitError('')
    descriptionRef.current?.focus()
  }

  async function submit(event) {
    event.preventDefault()
    if (submitting) return
    const nextErrors = {}
    const description = form.description.trim()
    if (description.length < 10)
      nextErrors.description = 'Descreva o problema com pelo menos 10 caracteres.'
    else if (description.length > 5000)
      nextErrors.description = 'A descrição deve ter no máximo 5000 caracteres.'
    if (invalidCoordinate(form.latitude, 90))
      nextErrors.latitude = 'Informe uma latitude entre -90 e 90.'
    if (invalidCoordinate(form.longitude, 180))
      nextErrors.longitude = 'Informe uma longitude entre -180 e 180.'
    setErrors(nextErrors)
    setSubmitError('')
    if (Object.keys(nextErrors).length) {
      if (nextErrors.description) descriptionRef.current?.focus()
      else if (nextErrors.latitude) latitudeRef.current?.focus()
      else longitudeRef.current?.focus()
      return
    }
    setSubmitting(true)
    try {
      const report = await addReport({
        description,
        latitude: Number(form.latitude),
        longitude: Number(form.longitude),
      })
      navigate('/relatos/' + report.id, { state: { created: true } })
    } catch (error) {
      setSubmitError(error.message)
      setSubmitting(false)
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="PARTICIPAÇÃO CIDADÃ"
        title="Relate um problema urbano"
        description="Um buraco na rua, uma luz apagada, um espaço que precisa de cuidado. Seu olhar ajuda a entender o que acontece na cidade."
      />
      <div className="registration-layout">
        <section className="card form-card" aria-labelledby="form-title">
          <div className="section-heading">
            <span className="section-icon">
              <Icon name="plus" size={22} />
            </span>
            <div>
              <h2 id="form-title">Novo relato</h2>
              <p>Conte o que você encontrou e onde aconteceu.</p>
            </div>
          </div>
          <form noValidate onSubmit={submit}>
            {(Object.keys(errors).length > 0 || submitError) && (
              <p className="form-alert" role="alert">
                {submitError || 'Confira os campos destacados para continuar.'}
              </p>
            )}
            <div className="form-field">
              <div className="field-label-row">
                <label htmlFor="descricao">
                  O que está acontecendo? <span aria-hidden="true">*</span>
                </label>
                <button
                  type="button"
                  className="text-button"
                  onClick={fillExample}
                >
                  Usar exemplo
                </button>
              </div>
              <textarea
                id="descricao"
                name="description"
                ref={descriptionRef}
                value={form.description}
                onChange={updateField}
                required
                aria-invalid={Boolean(errors.description)}
                aria-describedby="descricao-ajuda"
                placeholder="Descreva o problema, a situação do local e como isso afeta quem passa por ali."
                rows={6}
              />
              <FieldMessage
                id="descricao-ajuda"
                error={errors.description}
                hint="Uma descrição clara facilita a compreensão do problema."
              />
            </div>
            <div className="coordinates-panel">
              <p className="coordinates-title">
                <Icon name="map" size={18} />
                Onde está o problema? <span aria-hidden="true">*</span>
              </p>
              <p className="field-message">
                Informe a latitude e a longitude do local.
              </p>
              <div className="field-grid">
                <div className="form-field">
                  <label htmlFor="latitude">
                    Latitude <span aria-hidden="true">*</span>
                  </label>
                  <input
                    id="latitude"
                    name="latitude"
                    type="number"
                    step="any"
                    min="-90"
                    max="90"
                    ref={latitudeRef}
                    required
                    value={form.latitude}
                    onChange={updateField}
                    aria-invalid={Boolean(errors.latitude)}
                    aria-describedby="latitude-ajuda"
                    placeholder="Entre -90 e 90"
                  />
                  <FieldMessage
                    id="latitude-ajuda"
                    error={errors.latitude}
                    hint="Coordenada em graus decimais."
                  />
                </div>
                <div className="form-field">
                  <label htmlFor="longitude">
                    Longitude <span aria-hidden="true">*</span>
                  </label>
                  <input
                    id="longitude"
                    name="longitude"
                    type="number"
                    step="any"
                    min="-180"
                    max="180"
                    ref={longitudeRef}
                    required
                    value={form.longitude}
                    onChange={updateField}
                    aria-invalid={Boolean(errors.longitude)}
                    aria-describedby="longitude-ajuda"
                    placeholder="Entre -180 e 180"
                  />
                  <FieldMessage
                    id="longitude-ajuda"
                    error={errors.longitude}
                    hint="Coordenada em graus decimais."
                  />
                </div>
              </div>
            </div>
            <div className="form-submit">
              <p>
                <Icon name="info" size={17} />O relato será enviado ao
                servidor e poderá ser consultado em Ocorrências.
              </p>
              <button
                className="button primary"
                type="submit"
                disabled={submitting}
              >
                {submitting ? 'Enviando…' : 'Enviar relato'}
                <Icon name="arrow" size={18} />
              </button>
            </div>
          </form>
        </section>
        <aside className="registration-aside">
          <section className="card guide-card">
            <p className="eyebrow">DO RELATO À INFORMAÇÃO</p>
            <h2>Uma cidade melhor começa com participação.</h2>
            <ol className="guide-steps">
              <li>
                <span>1</span>
                <div>
                  <h3>Descreva a situação</h3>
                  <p>Conte o que precisa de atenção.</p>
                </div>
              </li>
              <li>
                <span>2</span>
                <div>
                  <h3>Indique o local</h3>
                  <p>Ajude a situar o problema na cidade.</p>
                </div>
              </li>
              <li>
                <span>3</span>
                <div>
                  <h3>Consulte a análise</h3>
                  <p>
                    A proposta prevê categoria, prioridade, risco e setor
                    sugerido.
                  </p>
                </div>
              </li>
            </ol>
            <Link className="text-link" to="/relatos">
              Ver ocorrências registradas
              <Icon name="arrow" size={17} />
            </Link>
          </section>
          <section className="category-guide">
            <h2>Um olhar para diferentes problemas</h2>
            <div className="category-chips">
              {categories.map((category) => (
                <span key={category}>
                  <Icon name={categoryIcons[category]} size={16} />
                  {category}
                </span>
              ))}
            </div>
            <p>As categorias serão apresentadas como resultado da análise.</p>
          </section>
        </aside>
      </div>
    </>
  )
}
