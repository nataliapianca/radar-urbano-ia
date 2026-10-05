export function formatDate(value) {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(value))
}

export function reportTitle(report) {
  const firstSentence = report.description.split(/[.!?]/)[0].trim()
  return firstSentence.length > 95
    ? firstSentence.slice(0, 95) + '…'
    : firstSentence
}

export function displayId(report) {
  return report.source === 'fixture'
    ? 'EX ' + report.id.split('-').at(-1)
    : 'DEMO ' + report.id.slice(-6).toUpperCase()
}

export function normalizeSearch(value) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}
