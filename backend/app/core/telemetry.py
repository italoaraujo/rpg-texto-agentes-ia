from prometheus_client import Gauge, Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

# Usamos um registro global para evitar problemas de re-registro em recarregamentos
REGISTRY = CollectorRegistry()

# 1. Gauge para Vida do Jogador em Tempo Real
rpg_player_health = Gauge(
    "rpg_player_health",
    "Vida atual do jogador de RPG em tempo real",
    labelnames=["game_id", "player_name", "character_class"],
    registry=REGISTRY
)

# 2. Counter para Alternância de Modelos (Fallback)
rpg_model_switches_total = Counter(
    "rpg_model_switches_total",
    "Contador de alternâncias/fallbacks de modelo de IA",
    labelnames=["reason", "fallback_model"],
    registry=REGISTRY
)

# 3. Histogram para Latência da API de LLM por turno
rpg_llm_request_duration_seconds = Histogram(
    "rpg_llm_request_duration_seconds",
    "Latência de resposta da API de LLM por turno",
    labelnames=["model", "status"],
    buckets=(0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 8.0, 12.0, float("inf")),
    registry=REGISTRY
)

# 4. Counter para Consumo Acumulado de Tokens
rpg_llm_tokens_consumed_total = Counter(
    "rpg_llm_tokens_consumed_total",
    "Consumo acumulado de Tokens da API de LLM",
    labelnames=["model", "type"], # type: prompt ou completion
    registry=REGISTRY
)

# 5. Histogram para Duração das Tarefas da Crew
rpg_crew_task_duration_seconds = Histogram(
    "rpg_crew_task_duration_seconds",
    "Duração de execução de cada tarefa individual na CrewAI",
    labelnames=["task_name"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, float("inf")),
    registry=REGISTRY
)

# 6. Counter para Ambientes/Biomas Visitados
rpg_active_environment_turns_total = Counter(
    "rpg_active_environment_turns_total",
    "Contador de turnos passados em cada ambiente",
    labelnames=["biome"],
    registry=REGISTRY
)

# 7. Counter para Turnos do Jogo
rpg_game_turns_total = Counter(
    "rpg_game_turns_total",
    "Contador total de turnos processados por sessão",
    labelnames=["game_id"],
    registry=REGISTRY
)

# 8. Gauge para Quantidade de Jogos Simultâneos Ativos
rpg_active_sessions_count = Gauge(
    "rpg_active_sessions_count",
    "Quantidade de sessões de jogos ativas simultaneamente",
    registry=REGISTRY
)

# 9. Counter para Itens Consumidos/Removidos
rpg_player_items_consumed_total = Counter(
    "rpg_player_items_consumed_total",
    "Contador de itens do inventário consumidos ou removidos",
    labelnames=["item_name"],
    registry=REGISTRY
)

def get_serialized_metrics() -> bytes:
    """Retorna todas as métricas no formato do Prometheus."""
    return generate_latest(REGISTRY)
