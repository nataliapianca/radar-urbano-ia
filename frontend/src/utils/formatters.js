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
  return '#' + report.id.slice(0, 8).toUpperCase()
}

export function formatCoordinates(location) {
  if (location.address) return location.address
  return (
    'Lat. ' +
    location.latitude.toFixed(5) +
    ' · Long. ' +
    location.longitude.toFixed(5)
  )
}

export function normalizeSearch(value) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}
