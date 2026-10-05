const styles = { Alta: 'high', Média: 'medium', Baixa: 'low' }

export default function PriorityBadge({ priority }) {
  return (
    <span className={'priority-badge ' + (styles[priority] || 'pending')}>
      <span className="status-dot" />
      {priority ? 'Prioridade ' + priority.toLowerCase() : 'Sem análise'}
    </span>
  )
}
