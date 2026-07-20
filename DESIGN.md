# Guia de Design Visual e Layout (DESIGN.md)

Este documento descreve as decisões de UI/UX, tokens de design, paleta de cores, tipografia e técnicas estéticas utilizadas na interface do **RPG de Texto Baseado em Agentes**.

---

## 1. Conceito Estético: Dark Space Fantasy & Glassmorphism

A interface foi projetada para evocar a atmosfera de um painel de controle misterioso e futurista fundido com elementos de fantasia medieval clássica. Buscou-se um visual limpo, moderno e imersivo, evitando designs simplistas ou amadores.

### Efeitos de Vidro (Glassmorphism)
Todos os cartões e painéis centrais utilizam o efeito de vidro translúcido sobre um fundo cósmico escuro:
* **Fundo de Painéis**: `rgba(20, 16, 38, 0.7)` (roxo escuro com 70% de opacidade).
* **Desfoque de Fundo**: `backdrop-filter: blur(16px)` para isolar o texto da textura de fundo cósmico.
* **Borda Delicada**: `border: 1px solid rgba(255, 255, 255, 0.08)` para dar profundidade de objeto 3D flutuante.
* **Sombra Suave**: Sombra projetada larga para simular elevação espacial.

---

## 2. Paleta de Cores (Tokens CSS)

A paleta de cores foi curada com base em valores de matiz, saturação e luminosidade (HSL) específicos para garantir contraste, elegância e harmonia visual em Dark Mode:

* `bg-primary` (`#0a0814`): Fundo geral escuro com gradientes radiais roxos e cianos sutis nas extremidades.
* `accent-purple` (`#9d4edd`): Cor de destaque principal (marca).
* `accent-purple-light` (`#c77dff`): Destaques secundários e títulos de IA.
* `accent-gold` (`#ffb703`): Destaque para ações do jogador e alertas de aviso.
* `accent-cyan` (`#00f5d4`): Destaque para dados de telemetria rápida e modelos de IA ativos.
* `accent-red` (`#ff0054`): Dano e perigos fatais.
* `accent-green` (`#38b000`): Indicador de conexão ativa ("Mestre Online") e vida saudável.

---

## 3. Cores Dinâmicas por Ambiente Geográfico (9 Cenários)

O cabeçalho do console de narrativa reage dinamicamente ao ambiente ativo, alterando a cor da sua borda esquerda e o emoji de fundo para refletir o clima do cenário:

| Ambiente | Emoji | Cor da Borda (Hex) | Atmosfera Narrativa |
| :--- | :---: | :--- | :--- |
| **Masmorra** | 💀 | `#ff0054` (Vermelho) | Masmorras da Morte |
| **Floresta** | 🌲 | `#38b000` (Verde) | Sussurros Selvagens |
| **Cidade** | 🏰 | `#00f5d4` (Ciano) | Bastião do Comércio |
| **Deserto** | 🏜️ | `#ffb703` (Dourado) | Terras Secas |
| **Montanha** | 🏔️ | `#adb5bd` (Cinza) | Picos Eternos |
| **Pântano** | 🕸️ | `#9d4edd` (Roxo) | Águas Estagnadas |
| **Oceano** | 🌊 | `#3a86ff` (Azul) | Mar Revolto |
| **Vulcão** | 🌋 | `#ff0054` (Vermelho) | Fúria da Terra |
| **Céu** | ☁️ | `#8ecae6` (Azul Claro) | Firmamento Arcano |

---

## 4. Tipografia Premium

Substituímos as fontes padrão do navegador por fontes modernas importadas diretamente do Google Fonts:
1. **Títulos e Cabeçalhos (Outfit)**: Fonte geométrica, imponente e limpa, ideal para marcas, títulos de cards e identificadores de status.
2. **Texto de Leitura (Inter)**: Fonte sem serifa altamente otimizada para legibilidade de telas e blocos longos de texto literário, reduzindo a fadiga visual.
3. **Métricas e Valores (Fira Code)**: Fonte monoespaçada estilo console do desenvolvedor para dados numéricos de telemetria, tempos de resposta e uso de tokens.

---

## 5. Micro-animações e Elementos de Interação

A interface responde de forma orgânica às interações do usuário, criando uma sensação de vida e responsividade:

* **Cards de Inventário Interativos**: 
  * Passar o mouse (hover) gera uma transição suave que clareia o fundo, altera a borda para roxo neon (`var(--accent-purple-light)`) e aplica um brilho suave (`box-shadow: 0 0 10px rgba(168, 85, 247, 0.12)`).
* **Botões de Ação Rápida**:
  * Ao passar o mouse, ativam brilho roxo neon e aumentam sutilmente o contraste.
* **Barra de Vida Corporal**:
  * A barra transiciona sua cor dinamicamente: verde (saúde >= 70%), amarelo/dourado (saúde >= 30%) e vermelho (perigo abaixo de 30%).
* **Indicador de Digitação (Typing Indicator)**:
  * Três bolhas com animação oscilante de pulso em loop de 1.4s que avisam o jogador quando os agentes do LangChain estão processando o turno no backend.
* **Conexão Ativa**:
  * O crachá "Mestre Online" pisca uma bolha de status verde neon simulando batimentos cardíacos para assegurar que a conexão via WebSocket/Polling com o backend FastAPI está saudável.

---

## 6. Estrutura e Grade do Layout (Duas Colunas)

O console foi distribuído em uma grade responsiva moderna de 12 colunas com layout flex-grow:
1. **Coluna Esquerda (Console - 1fr)**:
   * **Cabeçalho de Localização**: Fixo no topo, comunicando a região e status.
   * **Log Histórico**: Área flexível autogerida com barra de rolagem estilizada transparente que flui para baixo automaticamente à medida que novas narrativas ou ações são adicionadas.
   * **Alternativas Sugeridas**: Botões rápidos de sugestões de ações, que somem em carregamentos.
   * **Barra de Ação Livre**: Campo de texto com botão com gradiente de roxo para rosa, fixado na base do console.
2. **Coluna Direita (Status / Telemetria - 380px)**:
   * **Card do Herói**: Identidade do jogador (nome, classe com ícones contextuais de combate, barra de vida, lista de companheiros ativos, lista de habilidades ativas (⚡) e inventário agrupado).
   * **Card de Telemetria da IA**: Painel técnico exibindo dados de performance do backend (modelo de IA ativo, latência de resposta, fallbacks automáticos e acumulador de tokens consumidos).

---

## 7. Assistente de Criação Passo a Passo (Wizard Flow)

A tela inicial foi dividida em um assistente de 5 etapas para evitar fadiga de decisão e guiar o jogador na ambientação da aventura:
1. **Passo 1 (Nome)**: Entrada textual do nome do personagem com validação de preenchimento.
2. **Passo 2 (Classe)**: Grade interativa de seleção de arquétipo (Guerreiro, Mago, Ladino, Clérigo).
3. **Passo 3 (NPC)**: Escolha de companheiro inicial com backstories dedicados ou opção de começar sozinho.
4. **Passo 4 (Ambiente)**: Seleção do ambiente geográfico de início.
5. **Passo 5 (Configurações)**: Ajustes de opções de jogo, vindo habilitados por padrão ("Narrativa Curta e Dinâmica" e "Sugerir Alternativas de Ação").
* **Barra de Progresso**: Um indicador visual de linha com círculos numerados interativos que se iluminam à medida que o jogador avança. Permite retroceder aos passos passados ao clicar nos círculos.
* **Prevenção de Ghost Clicks**: Desabilitação temporária de 400ms do botão "Adentrar a Masmorra" ao entrar no Passo 5 para evitar double-taps acidentais oriundos do botão "Avançar" do Passo 4.

---

## 8. Responsividade Móvel (Mobile Layout)

A interface se adapta organicamente a dispositivos móveis e tablets usando media queries do CSS:
* **Grids de Coluna Única**: Abaixo de `768px`, a visualização em duas colunas é convertida em uma única coluna vertical. O console de narrativa ganha destaque no topo, enquanto os status e a telemetria rolam para a base da página.
* **Menus Empilhados**: O grid de opções de criação de personagem (2 colunas) se reconfigura para 1 coluna vertical em larguras estreitas para acomodar o toque.
* **Rótulos Curto-Responsivos**: Os nomes das etapas do assistente no celular são abreviados ("Nome", "Classe", "NPC", "Início", "Configs") para evitar encavalamento de textos.
* **Ajuste de Formulário**: Abaixo de `480px`, o input de ação e o botão de envio se empilham verticalmente com 100% de largura para otimizar o espaço do teclado virtual.
