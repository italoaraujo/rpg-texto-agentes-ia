# language: pt
Funcionalidade: Fluxos do Turno de RPG, Atualização de Vida e Resiliência de IA
  Como um jogador do RPG de texto baseado em agentes,
  Eu quero realizar ações e receber respostas ricas da Crew de agentes,
  Para que o jogo avance e se comporte de forma consistente, resiliente e transparente.

  Contexto:
    Dado que a sessão de jogo foi iniciada com sucesso
    E o jogador é da classe "Guerreiro" com 100 de vida máxima
    E a API primária de IA está configurada como "deepseek-chat"
    E a API reserva de IA está configurada como "gpt-4o-mini"

  Cenário: Turno normal feliz com processamento via API do DeepSeek
    Dado que o jogador está com 100 pontos de vida
    E a conexão com a API do DeepSeek está saudável e respondendo com latência abaixo de 4 segundos
    Quando o jogador envia a ação "Tentar abrir a porta de ferro com um chute"
    Então o motor do jogo deve orquestrar a ação usando a CrewAI com a API do DeepSeek
    E o orquestrador deve receber a narrativa descrevendo o resultado do chute
    E o status do jogo deve retornar que o modelo ativo usado foi "deepseek-chat"
    E a flag de fallback disparado deve ser "falsa"
    E a latência da requisição da IA deve ser coletada sob a métrica "rpg_llm_request_duration_seconds"
    E o consumo acumulado de tokens sob o modelo "deepseek-chat" deve ser incrementado em "rpg_llm_tokens_consumed_total"

  Cenário: Redução de vida do jogador após sofrer dano na narrativa
    Dado que o jogador possui 100 pontos de vida
    E o inventário contém o item "Espada de Bronze"
    Quando a CrewAI determina na narrativa que o jogador sofreu uma emboscada e levou "15" de dano
    Então o estado de vida do jogador deve ser reduzido para "85"
    E a métrica "rpg_player_health" no Prometheus deve ser atualizada para "85" em tempo real
    E o Gauge visual de vida no Frontend deve renderizar o valor "85" de "100" (85%)
    E o inventário do jogador deve continuar contendo o item "Espada de Bronze"

  Cenário: Recuperação de vida do jogador ao consumir item de cura do inventário
    Dado que o jogador possui 50 pontos de vida
    E o inventário contém os itens "Espada de Bronze", "Pocao de Cura P"
    Quando o jogador envia a ação "Beber a Pocao de Cura P do meu inventario"
    Então a CrewAI deve processar o uso da poção, curando "30" pontos de vida do jogador
    E o estado de vida do jogador deve ser atualizado para "80"
    E a métrica "rpg_player_health" deve ser atualizada para "80" no Prometheus
    E o item "Pocao de Cura P" deve ser removido do inventário retornado
    E o Gauge visual de vida no Frontend deve renderizar o valor "80" de "100" (80%)

  Cenário: Falha de conexão/Timeout na API do DeepSeek e fallback automático de infraestrutura
    Dado que a conexão com a API do DeepSeek está instável ou falhando
    Ou o tempo de resposta da API do DeepSeek excedeu o limite de "4.0" segundos
    Quando o jogador envia a ação "Entrar silenciosamente na sala do tesouro"
    Então a CrewAI deve interromper a requisição principal do DeepSeek
    E o orquestrador de backend deve alternar automaticamente a execução para o modelo reserva "gpt-4o-mini"
    E o contador de falhas de modelo "rpg_model_switches_total" deve ser incrementado em "1" com o rótulo "reason='timeout'" ou "reason='api_error'"
    E o estado de jogo retornado ao jogador deve conter a narrativa gerada com sucesso pela IA reserva
    E as informações de telemetria no JSON de resposta devem indicar:
      | active_model         | gpt-4o-mini |
      | fallback_triggered   | true        |
    E a latência da requisição da IA deve ser registrada na métrica correspondente sob o modelo "gpt-4o-mini"
