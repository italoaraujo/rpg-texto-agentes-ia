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
  * Três bolhas com animação oscilante de pulso em loop de 1.4s que avisam o jogador quando os agentes da CrewAI estão processando o turno no backend.
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
   * **Card do Herói**: Identidade do jogador (nome, classe com ícones contextuais de combate, barra de vida e inventário).
   * **Card de Telemetria da IA**: Painel técnico exibindo dados de performance do backend (modelo de IA ativo, latência de resposta, fallbacks automáticos e acumulador de tokens consumidos).
