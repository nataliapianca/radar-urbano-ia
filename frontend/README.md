# Radar Urbano IA - Frontend

Protótipo: estrutura inicial das telas e navegação, com dados demonstrativos.

## Tecnologias

React, JavaScript/JSX, React Router, Vite, CSS e ESLint. Ambiente de desenvolvimento: Node.js e npm, validado com Node.js 24.19.0.

## Organização do código

Dentro de `frontend`:

- `src/App.jsx`: rotas da aplicação.
- `src/pages/`: telas.
- `src/components/`: componentes compartilhados.
- `src/context/` e `src/hooks/`: estado dos relatos.
- `src/data/`: dados de exemplo.
- `src/utils/`: funções de apoio.
- `src/App.css` e `src/index.css`: estilos.

## Backend

O backend existente utiliza Python e FastAPI. Para esta entrega, não houve alterações nas rotas ou na lógica da API. O protótipo funciona sem iniciar o backend; a integração ficará para outra sprint.

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

## Dados e limitações

Os quatro relatos iniciais e suas análises são fictícios. Novos relatos ficam apenas na memória do navegador, sem análise automática, e são removidos ao recarregar a página.

Esta entrega não contempla integração com API, banco de dados ou IA real, autenticação, cadastro de usuários, envio de fotos ou busca de endereço em mapa geográfico. Mapa e painel são esboços; a região do estudo permanece a definir.
