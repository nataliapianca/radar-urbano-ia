const API_URL = (
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function detailMessage(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length)
    return 'Dados inválidos. Confira os campos e tente novamente.'
  return 'Não foi possível concluir a operação.'
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(API_URL + path, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError(
      'O serviço está indisponível no momento. Verifique sua conexão e tente novamente em instantes.',
      0,
    )
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(detailMessage(body?.detail), response.status)
  }
  return response.json()
}

// Converte o relato da API (campos em português) para o formato usado nas telas.
export function fromApi(relato) {
  const classificacao = relato.classificacao
  return {
    id: relato.id,
    description: relato.texto,
    location: {
      latitude: relato.localizacao.latitude,
      longitude: relato.localizacao.longitude,
      address: relato.localizacao.endereco,
      attribution: relato.localizacao.atribuicao,
    },
    createdAt: relato.criado_em,
    status: relato.status,
    analysis: classificacao
      ? {
          category: classificacao.categoria,
          priority: classificacao.prioridade,
          risk: classificacao.risco_associado,
          suggestedSector: classificacao.setor,
          details: classificacao.informacoes_relevantes,
        }
      : null,
  }
}

export async function listReports(options) {
  const data = await request('/relatos', options)
  return data.relatos.map(fromApi)
}

export async function createReport({
  description,
  latitude,
  longitude,
  address,
  attribution,
}) {
  const relato = await request('/relatos', {
    method: 'POST',
    body: JSON.stringify({
      texto: description,
      localizacao: {
        latitude,
        longitude,
        endereco: address || null,
        atribuicao: attribution || null,
      },
    }),
  })
  return fromApi(relato)
}

export async function searchAddress(address) {
  const data = await request('/localizacoes/buscar', {
    method: 'POST',
    body: JSON.stringify({ endereco: address }),
  })
  return data.resultados
}
