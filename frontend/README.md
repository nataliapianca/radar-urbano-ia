# Radar Urbano IA - Frontend

Interface web do Radar Urbano IA, conectada à API do backend (FastAPI).

## Tecnologias

React, JavaScript/JSX, React Router, Vite, CSS e ESLint. Ambiente de desenvolvimento: Node.js e npm, validado com Node.js 24.19.0.

## Organização do código

Dentro de `frontend`:

- `src/App.jsx`: rotas da aplicação.
- `src/pages/`: telas.
- `src/components/`: componentes compartilhados.
- `src/context/` e `src/hooks/`: estado dos relatos.
- `src/services/api.js`: cliente HTTP da API e conversão dos campos da API para o formato das telas.
- `src/data/`: categorias e prioridades.
- `src/utils/`: funções de apoio.
- `src/App.css` e `src/index.css`: estilos.

## Backend

O frontend consome a API em `POST /relatos` e `GET /relatos` (contrato em `backend/CONTRATO_API.md`). O backend precisa estar em execução (`uvicorn app.main:app --reload`, em `backend/`).

O endereço da API é lido de `VITE_API_URL` (padrão `http://127.0.0.1:8000`). Para mudar, copie `.env.example` para `.env` e edite.

## Execução

Com Node.js e npm instalados e os arquivos desta entrega atualizados, execute no PowerShell, a partir da raiz do projeto:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Abra o endereço Local exibido pelo Vite, normalmente [http://localhost:5173](http://localhost:5173). Para encerrar, use **Ctrl+C**. No macOS/Linux, utilize `npm` no lugar de `npm.cmd`.

## Telas disponíveis

Use o menu para navegar:

- **Registrar relato** (`/`): formulário demonstrativo de descrição e localização.
- **Ocorrências** (`/relatos`): lista com busca e filtros.
- **Detalhes**: botão **Ver relato** na lista, com informações e análise ilustrativa.
- **Mapa** (`/mapa`): esboço com marcadores dos exemplos.
- **Painel** (`/painel`): indicadores demonstrativos.

## Limitações

- A localização é informada por **latitude e longitude obrigatórias**, que é o que a API exige. O campo de endereço/ponto de referência voltará quando o backend o aceitar.
- A classificação (categoria, prioridade, risco e setor) só aparece depois que a IA, ou alguém via `PUT /relatos/{id}/classificacao`, a enviar. Até lá o relato fica como "Recebido", sem análise.
- O backend guarda os dados em memória: reiniciar o servidor apaga os relatos.
- O mapa é um esboço: posiciona os marcadores pelas coordenadas, sem mapa geográfico. O painel calcula os indicadores a partir dos relatos carregados.
- Não há autenticação, envio de fotos ou busca de endereço.
