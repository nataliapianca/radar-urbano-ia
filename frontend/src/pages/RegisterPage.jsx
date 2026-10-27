import { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import Icon from '../components/Icon'
import PageHeader from '../components/PageHeader'
import { categories, categoryIcons } from '../data/categories'
import { useReports } from '../hooks/useReports'
import { searchAddress } from '../services/api'

const initialForm = {
  description: '',
  address: '',
}

const example = {
  description:
    'Há um poste apagado na rua há três dias. O trecho fica sem luz durante a noite e é utilizado por moradores.',
  address: 'Vitória, Espírito Santo (localização de exemplo)',
}

const exampleLocation = {
  latitude: -20.3155,
  longitude: -40.3128,
  endereco: 'Vitória, Espírito Santo (localização de exemplo)',
  atribuicao: null,
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
  const addressRef = useRef(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [searchingAddress, setSearchingAddress] = useState(false)
  const [addressError, setAddressError] = useState('')
  const [addressOptions, setAddressOptions] = useState([])
  const [selectedLocation, setSelectedLocation] = useState(null)
  const { addReport } = useReports()
  const navigate = useNavigate()

  function updateField(event) {
    if (event.target.name === 'address') {
      setSelectedLocation(null)
      setAddressOptions([])
      setAddressError('')
    }
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }))
  }

  function fillExample() {
    setForm(example)
    setSelectedLocation(exampleLocation)
    setAddressOptions([])
    setAddressError('')
    setErrors({})
    setSubmitError('')
    descriptionRef.current?.focus()
  }

  async function findAddress() {
    const address = form.address.trim()
    if (address.length < 5) {
      setAddressError('Informe rua, número, bairro e cidade para buscar o local.')
      addressRef.current?.focus()
      return
    }
    setSearchingAddress(true)
    setAddressError('')
    setAddressOptions([])
    setSelectedLocation(null)
    try {
      const results = await searchAddress(address)
      if (!results.length) {
        setAddressError(
          'Nenhum local encontrado. Confira o endereço e tente novamente.',
        )
        return
      }
      setAddressOptions(results)
    } catch (error) {
      setAddressError(error.message)
    } finally {
      setSearchingAddress(false)
    }
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
    if (!selectedLocation)
      nextErrors.address = 'Busque e confirme o endereço do problema.'
    setErrors(nextErrors)
    setSubmitError('')
    if (Object.keys(nextErrors).length) {
      if (nextErrors.description) descriptionRef.current?.focus()
      else addressRef.current?.focus()
      return
    }
    setSubmitting(true)
    try {
      const report = await addReport({
        description,
        latitude: selectedLocation.latitude,
        longitude: selectedLocation.longitude,
        address: selectedLocation.endereco,
        attribution: selectedLocation.atribuicao,
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
                Informe o endereço completo. Vamos buscar opções para você
                escolher a correta.
              </p>
              <div className="form-field address-search-field">
                <label htmlFor="endereco">
                  Endereço do problema <span aria-hidden="true">*</span>
                </label>
                <input
                  id="endereco"
                  name="address"
                  ref={addressRef}
                  value={form.address}
                  onChange={updateField}
                  aria-invalid={Boolean(errors.address || addressError)}
                  aria-describedby="endereco-ajuda"
                  placeholder="Rua, número, bairro, cidade e estado"
                  maxLength={300}
                />
                <FieldMessage
                  id="endereco-ajuda"
                  error={errors.address || addressError}
                  hint="Ex.: Rua Exemplo, 123, Centro, Vitória, ES"
                />
                <button
                  className="button secondary address-search-button"
                  type="button"
                  onClick={findAddress}
                  disabled={searchingAddress}
                >
                  <Icon name="map" size={18} />
                  {searchingAddress ? 'Buscando endereço...' : 'Buscar endereço'}
                </button>
                <p className="geocoding-attribution">
                  Geocodificação por{' '}
                  <a
                    href="https://www.geoapify.com/"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Geoapify
                  </a>{' '}
                  .
                </p>
              </div>
              {addressOptions.length > 0 && (
                <div className="address-options" aria-label="Endereços encontrados">
                  <p className="address-options-title">Selecione o local correto:</p>
                  {addressOptions.map((option, index) => (
                    <button
                      className="address-option"
                      key={`${option.latitude}-${option.longitude}-${index}`}
                      type="button"
                      onClick={() => {
                        setSelectedLocation(option)
                        setAddressOptions([])
                        setAddressError('')
                        setForm((current) => ({ ...current, address: option.endereco }))
                      }}
                    >
                      {option.endereco}
                      {option.atribuicao && <small>{option.atribuicao}</small>}
                    </button>
                  ))}
                </div>
              )}
              {selectedLocation && (
                <div className="selected-address" role="status">
                  <strong>Local confirmado</strong>
                  <span>{selectedLocation.endereco}</span>
                  <small>
                    Coordenadas encontradas:{' '}
                    {selectedLocation.latitude.toFixed(5)},{' '}
                    {selectedLocation.longitude.toFixed(5)}
                  </small>
                  {selectedLocation.atribuicao && (
                    <small>{selectedLocation.atribuicao}</small>
                  )}
                </div>
              )}
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
