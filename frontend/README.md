# Radar Urbano IA - Frontend

Interface web do Radar Urbano IA. As telas estão conectadas à API do backend (FastAPI): os relatos são enviados e consultados no servidor, sem dados de demonstração.

## Tecnologias

React, JavaScript/JSX, React Router, Vite, CSS e ESLint. Ambiente de desenvolvimento: Node.js e npm, validado com Node.js 24.19.0.

## Organização do código

Dentro de `frontend`:

- `src/App.jsx`: rotas da aplicação.
- `src/pages/`: telas.
- `src/components/`: componentes compartilhados.
- `src/context/` e `src/hooks/`: estado dos relatos (`ReportsProvider`, `useReports`), carregado da API.
- `src/services/api.js`: cliente HTTP da API e conversão dos campos da API para o formato das telas.
- `src/data/`: categorias e prioridades.
- `src/utils/`: funções de apoio (datas, identificação, coordenadas e busca).
- `src/App.css` e `src/index.css`: estilos.

## Integração com a API

O frontend usa duas rotas, descritas em `backend/CONTRATO_API.md`:

| Ação na tela | Rota |
|---|---|
| Carregar as ocorrências (todas as telas) | `GET /relatos` |
| Enviar um relato | `POST /relatos` |

O detalhe de um relato é localizado na lista já carregada.

A API usa nomes de campo em português, e as telas usam nomes em inglês. A conversão fica em um único lugar, a função `fromApi` de `src/services/api.js`:

| API | Telas |
|---|---|
| `texto` | `description` |
| `localizacao.latitude` / `longitude` | `location.latitude` / `longitude` |
| `criado_em` | `createdAt` |
| `status` | `status` |
| `classificacao.categoria` | `analysis.category` |
| `classificacao.prioridade` | `analysis.priority` |
| `classificacao.risco_associado` | `analysis.risk` |
| `classificacao.setor` | `analysis.suggestedSector` |
| `classificacao.informacoes_relevantes` | `analysis.details` |

Quando o relato ainda não foi classificado, `classificacao` é `null` e `analysis` fica `null`. As telas mostram "Sem análise".

### Endereço da API

O endereço é lido da variável `VITE_API_URL` (padrão `http://127.0.0.1:8000`). Para mudar, copie `.env.example` para `.env` e edite o valor. O backend libera por padrão o CORS de `http://localhost:5173` e `http://127.0.0.1:5173`.

## Execução

É preciso executar o backend e o frontend, cada um em um terminal.

**Backend** (a partir da pasta `backend`, com o ambiente virtual criado e as dependências instaladas conforme o README da raiz):

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

A API fica em [http://127.0.0.1:8000](http://127.0.0.1:8000) e a documentação interativa em [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

**Frontend** (a partir da pasta `frontend`):

```powershell
npm.cmd ci
npm.cmd run dev
```

Abra o endereço Local exibido pelo Vite, normalmente [http://localhost:5173](http://localhost:5173). Para encerrar, use **Ctrl+C**. No macOS/Linux, utilize `npm` no lugar de `npm.cmd`.

Outros scripts: `npm.cmd run lint` e `npm.cmd run build`.

## Telas disponíveis

Use o menu para navegar:

- **Registrar relato** (`/`): formulário com a descrição e a localização. Todos os campos são obrigatórios: descrição (de 10 a 5000 caracteres), latitude (de -90 a 90) e longitude (de -180 a 180). O botão **Usar exemplo** preenche um relato de teste. Após o envio, abre o detalhe do relato criado.
- **Ocorrências** (`/relatos`): lista dos relatos registrados, do mais recente para o mais antigo, com busca por texto e filtros por categoria e prioridade.
- **Detalhes** (`/relatos/:reportId`): botão **Ver relato** na lista. Mostra a descrição, as coordenadas, a data, a situação do relato (`Recebido`, `Classificado`...) e, quando existir, o resultado da análise.
- **Mapa** (`/mapa`): esboço que posiciona os marcadores de acordo com as coordenadas dos relatos, sem mapa geográfico.
- **Painel** (`/painel`): indicadores calculados a partir dos relatos carregados (total, prioridade alta, categorias e distribuição por prioridade).

As telas que dependem da API mostram um aviso de carregamento e, se o serviço estiver indisponível, uma mensagem com o botão **Tentar novamente**.

## Como testar a análise

Nenhum componente envia classificação ainda, então os relatos novos aparecem como `Recebido` e sem análise. Para ver a análise nas telas, classifique um relato manualmente:

1. Registre um relato e copie o identificador completo da URL do detalhe (parte depois de `/relatos/`).
2. Em [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), abra `PUT /relatos/{relato_id}/classificacao`, clique em **Try it out**, cole o identificador e envie, por exemplo:

```json
{
  "categoria": "Iluminação",
  "prioridade": "Alta",
  "setor": "Iluminação Pública",
  "risco_associado": "Baixa visibilidade durante a noite.",
  "informacoes_relevantes": ["Poste apagado"]
}
```

3. Recarregue as telas. A categoria e a prioridade aparecem em Ocorrências, Detalhes, Mapa e Painel.

## Limitações

- A localização é informada por **latitude e longitude obrigatórias**, que é o que a API exige hoje. O campo de endereço ou ponto de referência foi retirado do formulário e voltará quando o backend o aceitar.
- A classificação (categoria, prioridade, risco e setor) depende da integração com a IA, que ainda não envia resultados ao backend.
- O backend ainda não usa banco de dados: guarda os relatos em memória, e reiniciar o servidor apaga todos eles.
- O mapa é um esboço, sem mapa geográfico, e a região do estudo de caso continua a definir.
- Ainda não há autenticação, envio de fotos, busca de endereço, nem atualização da situação do relato (`Em andamento` e `Resolvido`).
