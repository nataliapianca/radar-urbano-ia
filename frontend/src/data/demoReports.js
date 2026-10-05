// Dados fictícios para os esboços. Este objeto não define o contrato da API.
export const demoReports = [
  {
    id: 'exemplo-001',
    description:
      'Buraco na via dificulta a passagem de veículos. A abertura fica próxima a uma faixa de pedestres e obriga os motoristas a desviar.',
    location: {
      reference: 'Próximo a uma faixa de pedestres (exemplo)',
      latitude: null,
      longitude: null,
    },
    createdAt: '2026-10-04T10:30:00-03:00',
    source: 'fixture',
    analysis: {
      category: 'Infraestrutura',
      priority: 'Alta',
      risk: 'Possibilidade de acidentes e danos aos veículos.',
      suggestedSector: 'Setor de obras e manutenção viária',
    },
  },
  {
    id: 'exemplo-002',
    description:
      'Poste de iluminação apagado na passagem de pedestres. O trecho fica sem luz durante a noite e é utilizado por moradores.',
    location: {
      reference: 'Passagem de pedestres perto de uma praça (exemplo)',
      latitude: null,
      longitude: null,
    },
    createdAt: '2026-10-04T09:15:00-03:00',
    source: 'fixture',
    analysis: {
      category: 'Iluminação',
      priority: 'Alta',
      risk: 'Baixa visibilidade e insegurança para quem circula à noite.',
      suggestedSector: 'Setor de iluminação pública',
    },
  },
  {
    id: 'exemplo-003',
    description:
      'Acúmulo de resíduos na calçada. O material ocupa parte da passagem e está próximo a um ponto de descarte.',
    location: {
      reference: 'Calçada próxima a um ponto de descarte (exemplo)',
      latitude: null,
      longitude: null,
    },
    createdAt: '2026-10-03T14:00:00-03:00',
    source: 'fixture',
    analysis: {
      category: 'Limpeza Urbana',
      priority: 'Média',
      risk: 'Obstrução da passagem e possível atração de animais.',
      suggestedSector: 'Setor de limpeza urbana',
    },
  },
  {
    id: 'exemplo-004',
    description:
      'Galhos caídos em uma área verde. Os galhos estão fora do caminho principal, mas precisam ser recolhidos.',
    location: {
      reference: 'Área verde de uma praça (exemplo)',
      latitude: null,
      longitude: null,
    },
    createdAt: '2026-10-02T16:20:00-03:00',
    source: 'fixture',
    analysis: {
      category: 'Meio Ambiente',
      priority: 'Baixa',
      risk: 'Dificuldade de uso de parte da área verde.',
      suggestedSector: 'Setor de manutenção de áreas verdes',
    },
  },
]
