# RPG de Texto Baseado em Agentes com LangChain, DeepSeek e Telemetria

Este repositório contém a arquitetura técnica, especificações de contrato de API, comportamento BDD e configurações de infraestrutura para o projeto do RPG de texto baseado em agentes de inteligência artificial.

Seguindo a metodologia **Spec-Driven Development (Desenvolvimento Orientado a Especificações)**, toda a camada documental e de contratos foi definida antes de qualquer escrita de código de aplicação, garantindo robustez e alinhamento tecnológico.

---

## 1. Tecnologias Utilizadas na Arquitetura

* **Backend**: FastAPI (Python 3.11+) - Rápido, assíncrono e integrado nativamente com Pydantic para validação do OpenAPI.
* **Orquestração de Agentes**: LangChain (LCEL / Runnable Sequences) - Utilizado para gerenciar a pipeline de tarefas sequenciais de agentes com papéis focados (Game Master e NPC).
* **Inteligência Artificial (LLM)**: API Oficial do DeepSeek (`deepseek-chat`) como engine principal e GPT-4o-Mini como fallback automático contra lentidão ou falhas.
* **Telemetria**: Prometheus (coleta de métricas e medição de latência/tokens) e Grafana (visualização do dashboard).
* **Frontend**: React (TypeScript / Vite) - Painel interativo para digitação de ações, renderização de narrativa literária e Gauge visual da vida do jogador em tempo real.

---

## 2. Estrutura e Árvore do Projeto (Modular e Limpa)

Abaixo está a arquitetura de arquivos sugerida para a implementação do projeto, separando as responsabilidades de backend, frontend, infraestrutura de monitoramento e especificações contratuais:

```text
rpg-agentes/
├── backend/                    # Código Python / FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # Ponto de entrada FastAPI, middlewares e rota /metrics
│   │   ├── config.py           # Configurações de envs (DeepSeek/OpenAI keys) e fallback timeouts
│   │   ├── database.py         # Conexão com DB/Redis para persistência de estado do jogador
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # Agrupador de endpoints
│   │   │   └── endpoints/
│   │   │       ├── __init__.py
│   │   │       ├── game.py      # Implementação de POST /game/start e POST /game/turn
│   │   │       └── admin.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── agents.py       # Definição dos prompts e personas dos Agentes (Game Master, NPC)
│   │   │   ├── tasks.py        # Definição dos ChatPromptTemplates do LangChain (Arbitragem, Diálogo, Consolidação)
│   │   │   ├── crew.py         # Orquestrador da pipeline LangChain contendo a lógica de tratamento de fallback de LLM
│   │   │   └── telemetry.py    # Instanciação do Prometheus Client (Gauges, Counters e Histograms)
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── game.py         # Modelos Pydantic baseados na especificação OpenAPI.yaml (Request/Response)
│   │       └── telemetry.py
│   ├── tests/                  # Testes unitários, de integração e BDD
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_game.py
│   │   └── features/           # Testes comportamentais em Gherkin
│   │       ├── steps/
│   │       │   └── game_steps.py # Cola do BDD integrando chamadas HTTP mockadas/reais
│   │       └── behavior.feature  # Cópia ou link simbólico do arquivo central de BDD
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # Código do Cliente React / TypeScript
│   ├── src/
│   │   ├── assets/             # Assets estáticos, fontes e imagens geradas
│   │   ├── components/         # Componentes visuais modulares
│   │   │   ├── GameScreen.tsx  # Tela principal do console do RPG
│   │   │   ├── HealthBar.tsx   # Gauge visual de vida baseado no estado do jogador
│   │   │   ├── Inventory.tsx   # Painel com a listagem dinâmica de itens do jogador
│   │   │   └── ConsoleLog.tsx  # Área de logs e narrativa com micro-animações de máquina de escrever
│   │   ├── services/
│   │   │   └── api.ts          # Chamadas de API (Axios/Fetch) mapeadas para os endpoints FastAPI
│   │   ├── hooks/              # Custom hooks do React
│   │   ├── App.tsx
│   │   ├── index.css           # Estilos base, sistema de Grid e variáveis CSS modernas
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── docs/                       # Documentos contratuais de Especificação (Spec-Driven)
│   ├── openapi.yaml            # Especificação OpenAPI 3.0 para a API do Backend
│   ├── behavior.feature        # Cenários de teste BDD Gherkin (Dado/Quando/Então)
│   ├── langchain_architecture.md # Estruturação detalhada dos agentes e pipeline do LangChain com DeepSeek
│   └── telemetry_dashboard.md  # Queries PromQL e modelo JSON do painel Grafana
│
├── prometheus.yml              # Arquivo de configuração do Prometheus scrape target
├── docker-compose.yml          # Orquestração local de contêineres (App + Telemetria)
└── README.md                   # Este guia arquitetural
```

---

## 3. Descrição dos Arquivos de Especificação Gerados

Os seguintes artefatos já estão disponíveis no diretório `./docs` e na raiz para consulta e orientação do desenvolvimento:

1. **openapi.yaml**:
   Contrato estrito de rotas. Define esquemas robustos para `/game/start`, `/game/turn` e o formato raw de `/metrics` para que o Frontend React e o Backend FastAPI tenham alinhamento total de tipos desde o início.
2. **behavior.feature**:
   Especificação de cenários de teste de comportamento cobrindo turnos felizes, variação de pontos de vida por danos e uso de poções, e o fluxo crítico de resiliência e fallback caso o DeepSeek falhe ou demore mais de 4 segundos.
3. **langchain_architecture.md**:
   Explicação textual de como a pipeline LangChain é estruturada, incluindo o perfil dos dois papéis principais (Mestre e NPC), as três tarefas executadas em série (Arbitragem, Diálogo, Consolidação) e como a memória de turnos recentes é injetada nas requisições da LLM.
4. **telemetry_dashboard.md**:
   Mapeamento PromQL completo e arquivo JSON do painel Grafana contendo as visualizações de latência do DeepSeek, pizza de distribuição por modelo (DeepSeek vs Fallback), Gauge de saúde do jogador ativo e gráfico de barras empilhadas para consumo de tokens.
5. **prometheus.yml**:
   Arquivo pronto para inicializar o Prometheus raspando o backend local na porta `8000` a cada 5 segundos para telemetria de alta frequência do jogo.

---

## 4. Configuração e Inicialização do Ambiente (Docker)

O ambiente completo do projeto é conteinerizado e gerenciado através do arquivo `docker-compose.yml` na raiz do projeto. Isso garante que o backend FastAPI, o frontend React, o Prometheus e o Grafana rodem de forma isolada e integrada sob a mesma rede virtual bridge (`rpg-network`).

### Requisitos Prévios
* **Docker** e **Docker Compose** instalados na máquina do desenvolvedor.
* Um arquivo `.env` na raiz do projeto contendo as chaves de API necessárias:
  ```env
  DEEPSEEK_API_KEY=sua_chave_aqui
  OPENAI_API_KEY=sua_chave_aqui
  ```

### Portas Mapeadas do Ambiente
* **Backend FastAPI**: `http://localhost:8000` (Endpoints `/game/*` e `/metrics`)
* **Frontend React (Vite)**: `http://localhost:5173`
* **Prometheus**: `http://localhost:9090` (Visualização direta de métricas e targets)
* **Grafana**: `http://localhost:3001` (Dashboard com credenciais padrão `admin` / `admin`)

### Como Inicializar o Ambiente
Para subir todos os contêineres e inicializar a coleta de telemetria, execute o comando:
```bash
docker compose up --build -d
```

Para monitorar os logs dos serviços:
```bash
docker compose logs -f
```

Para desligar o ambiente e limpar os recursos:
```bash
docker compose down
```

---

## 5. Funcionalidades de Gameplay Avançadas Desenvolvidas

Para oferecer uma experiência de RPG de texto de ponta, implementamos as seguintes mecânicas avançadas:

1. **Seleção de Ambientes e Transições Geográficas Dinâmicas**:
   * O jogador pode escolher começar a aventura em um dos **9 ambientes** diferentes na tela de criação de personagem (`Masmorra`, `Floresta`, `Cidade`, `Deserto`, `Montanha`, `Pântano`, `Oceano`, `Vulcão`, `Céu`).
   * A IA do LangChain é contextualizada com o ambiente ativo em cada turno. Se a ação descrita pelo jogador indicar um deslocamento lógico (ex: entrar em cavernas arcanas em uma floresta), a IA realiza dinamicamente a transição física do ambiente, atualizando o banner e os efeitos de luz no frontend.
2. **Alternativas de Ação (Sugestões da IA)**:
   * Switch opcional na criação do personagem para que o Mestre (Game Master) forneça de 3 a 5 alternativas rápidas de ação clicáveis e contextuais para o próximo turno. O jogador pode optar por clicar em um botão ou ignorá-los e descrever sua ação livremente na caixa de entrada.
3. **Narrativa Curta e Dinâmica**:
   * Switch opcional para forçar a pipeline LangChain a gerar respostas e diálogos mais compactos, ágeis e diretos, economizando tempo de leitura e tokens.
4. **Inventário Agrupado com Quantidades e Pluralização Dinâmica**:
   * O backend extrai quantidades de textos como `"15 Moedas de Ouro"` e gerencia o inventário armazenando os itens individualmente na mochila do jogador.
   * O frontend agrupa itens idênticos com multiplicadores e aplica a pluralização correta de exibição (ex: `"Moeda de Ouro"` para 1 unidade e `"Moedas de Ouro"` para mais de 1). Consumos parciais deduzem a quantidade exata do inventário do jogador.
5. **Banner de Ambiente Contextual**:
   * O console de jogo exibe um banner dinâmico correspondente ao ambiente ativo. A borda esquerda e os efeitos de brilho do console adaptam suas cores de acordo com a atmosfera do local (ex: verde para a Floresta, ciano para a Cidade, dourado para o Deserto, vermelho para o Vulcão, etc.).
6. **Seleção de Companheiro NPC Dinâmico**:
   * O jogador pode selecionar o NPC inicial da equipe (`Eldon`, `Grom`, `Lyra` ou viajar sozinho). O motor do jogo resolve a backstory e o papel do agente de forma dinâmica. Se optar por ir sozinho, o NPC assume a persona "Sussurro das Sombras" reagindo de forma abstrata à solidão e tensão psicológica do herói.
7. **Sistema de Habilidades Dinâmicas**:
   * O jogador inicia com habilidades correspondentes ao arquétipo de sua classe (ex: Mago começa com `Bola de Fogo` e `Míssil Mágico`). Durante a jornada narrativa, novas habilidades podem ser aprendidas de tomos ou pergaminhos, ou perdidas devido a maldições e esquecimento, atualizando o HUD lateral em tempo real.
8. **Assistente Passo a Passo (Wizard Setup)**:
   * A criação do herói é dividida em 5 passos animados com indicador de progresso interativo. Inclui proteção de debounce de 400ms na última tela de configurações para neutralizar cliques rápidos fantasmas e impedir envios de formulário incorretos via tecla `Enter`.
9. **Responsividade Móvel Nativa (Mobile UI/UX)**:
   * Interface otimizada via CSS Media Queries para smartphones e tablets. Os painéis de narrativa e HUD lateral se adaptam para colunas verticais integradas, reduzindo rótulos e redimensionando campos de inputs de forma natural.

---

## 6. Importação Automática do Dashboard no Grafana

O repositório inclui um script Python automatizado para importar o painel pronto com todas as métricas customizadas instrumentadas (latência, pizza de fallbacks de LLM, Gauge de vida corporal do jogador e gráfico de consumo de tokens).

Com o ambiente Docker ativo, execute na raiz do projeto:
```bash
python3 import_dashboard.py
```

O script criará a fonte de dados `Prometheus` (conectando ao container correspondente) e importará o painel exibindo o link de acesso direto do dashboard.
