# Especificação da Telemetria (Prometheus & Grafana)

Este documento especifica a configuração de observabilidade do RPG de texto. Ele descreve as queries **PromQL (Prometheus Query Language)** necessárias para extrair métricas de desempenho da IA e status do jogo, além de fornecer a estrutura JSON base para a criação do dashboard no **Grafana**.

---

## 1. Métricas Customizadas Exportadas pelo Backend

O backend FastAPI irá expor no endpoint `/metrics` as seguintes métricas nativas do Prometheus:

| Nome da Métrica | Tipo | Labels | Descrição |
| :--- | :--- | :--- | :--- |
| `rpg_player_health` | **Gauge** | `game_id`, `player_name`, `character_class` | Nível atual de pontos de vida do jogador. |
| `rpg_model_switches_total` | **Counter** | `reason`, `fallback_model` | Total de vezes que a aplicação alternou de modelo de IA (fallback). |
| `rpg_llm_request_duration_seconds` | **Histogram** | `model`, `status` | Tempo de resposta (latência) da chamada de IA da Crew. |
| `rpg_llm_tokens_consumed_total` | **Counter** | `model`, `type` (`prompt` ou `completion`) | Contagem total de tokens consumidos no processamento. |
| `rpg_crew_task_duration_seconds` | **Histogram** | `task_name` | Duração de execução de cada tarefa individual na CrewAI (arbitration, npc_reaction, consolidation). |
| `rpg_active_environment_turns_total` | **Counter** | `biome` | Contador de turnos passados em cada ambiente. |
| `rpg_game_turns_total` | **Counter** | `game_id` | Contador total de turnos processados por sessão. |
| `rpg_active_sessions_count` | **Gauge** | nenhuma | Quantidade de sessões de jogos ativas simultaneamente. |
| `rpg_player_items_consumed_total` | **Counter** | `item_name` | Contador de itens do inventário consumidos ou removidos. |

---

## 2. Especificação das Consultas (PromQL)

Aqui estão as queries PromQL detalhadas para alimentar cada um dos painéis no dashboard do Grafana:

### A. Latência de Resposta por Turno (Gráfico de Linha)
* **Percentil 95 da latência (p95)**:
  ```promql
  histogram_quantile(0.95, sum(rate(rpg_llm_request_duration_seconds_bucket[5m])) by (le, model))
  ```
* **Latência Média da IA**:
  ```promql
  sum(rate(rpg_llm_request_duration_seconds_sum[5m])) by (model) / sum(rate(rpg_llm_request_duration_seconds_count[5m])) by (model)
  ```

### B. Distribuição de Requisições por Modelo (Gráfico de Pizza/Donut)
* Query PromQL:
  ```promql
  sum(increase(rpg_llm_request_duration_seconds_count[24h])) by (model)
  ```

### C. Vida Atual do Jogador em Tempo Real (Gauge Visual)
* Query PromQL:
  ```promql
  rpg_player_health
  ```

### D. Consumo Acumulado de Tokens (Gráfico de Barras Empilhado)
* Query PromQL:
  ```promql
  sum(increase(rpg_llm_tokens_consumed_total[24h])) by (model, type)
  ```

### E. Custo Estimado da API (LLM Cost) (Painel Stat)
* Query PromQL:
  ```promql
  (sum(increase(rpg_llm_tokens_consumed_total{model="deepseek-chat", type="prompt"}[24h])) * 0.00000014) + (sum(increase(rpg_llm_tokens_consumed_total{model="deepseek-chat", type="completion"}[24h])) * 0.00000028) + (sum(increase(rpg_llm_tokens_consumed_total{model="gpt-4o-mini", type="prompt"}[24h])) * 0.00000015) + (sum(increase(rpg_llm_tokens_consumed_total{model="gpt-4o-mini", type="completion"}[24h])) * 0.00000060)
  ```

### F. Duração Média das Tarefas da Crew (Gráfico de Linha / Time Series)
* Query PromQL:
  ```promql
  sum(rate(rpg_crew_task_duration_seconds_sum[5m])) by (task_name) / sum(rate(rpg_crew_task_duration_seconds_count[5m])) by (task_name)
  ```

### G. Ambientes/Biomas Mais Visitados (Gráfico de Rosca / Donut)
* Query PromQL:
  ```promql
  sum(increase(rpg_active_environment_turns_total[24h])) by (biome)
  ```

### H. Ritmo de Jogo: TPM & Sessões Ativas (Gráfico de Linha / Time Series)
* **Turnos por Minuto (TPM)**:
  ```promql
  sum(rate(rpg_game_turns_total[5m])) * 60
  ```
* **Sessões Ativas**:
  ```promql
  rpg_active_sessions_count
  ```

### I. Itens Consumidos/Removidos do Inventário (Gráfico de Barras)
* Query PromQL:
  ```promql
  sum(rpg_player_items_consumed_total) by (item_name)
  ```

---

## 3. Modelo JSON Estruturado de Painéis (Grafana Schema)

Abaixo está o arquivo JSON completo estruturado com os 9 painéis integrados e organizados por grid.

```json
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": 1,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "id": 1,
      "title": "Latência de Resposta da API por Turno (p95 & Média)",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(rpg_llm_request_duration_seconds_bucket[5m])) by (le, model))",
          "legendFormat": "{{model}} (p95)",
          "refId": "A"
        },
        {
          "expr": "sum(rate(rpg_llm_request_duration_seconds_sum[5m])) by (model) / sum(rate(rpg_llm_request_duration_seconds_count[5m])) by (model)",
          "legendFormat": "{{model}} (Média)",
          "refId": "B"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "custom": {
            "drawStyle": "line",
            "lineInterpolation": "smooth"
          },
          "unit": "s",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": null },
              { "color": "orange", "value": 3.0 },
              { "color": "red", "value": 4.0 }
            ]
          }
        }
      }
    },
    {
      "id": 2,
      "title": "Distribuição de Requisições por Modelo Ativo",
      "type": "piechart",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 0 },
      "targets": [
        {
          "expr": "sum(increase(rpg_llm_request_duration_seconds_count[24h])) by (model)",
          "legendFormat": "{{model}}",
          "instant": true,
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "custom": {
            "hideFrom": { "legend": false, "tooltip": false, "viz": false }
          }
        }
      },
      "options": {
        "pieType": "donut",
        "reduceOptions": {
          "values": false,
          "calcs": ["lastNotNull"]
        }
      }
    },
    {
      "id": 3,
      "title": "Vida Atual do Jogador em Tempo Real",
      "type": "gauge",
      "gridPos": { "h": 8, "w": 6, "x": 0, "y": 8 },
      "targets": [
        {
          "expr": "rpg_player_health",
          "legendFormat": "{{player_name}} (Vida)",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "min": 0,
          "max": 100,
          "unit": "none",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "red", "value": null },
              { "color": "yellow", "value": 30 },
              { "color": "green", "value": 70 }
            ]
          }
        }
      }
    },
    {
      "id": 5,
      "title": "Custo Estimado da API (LLM Cost - 24h)",
      "type": "stat",
      "gridPos": { "h": 8, "w": 6, "x": 6, "y": 8 },
      "targets": [
        {
          "expr": "(sum(increase(rpg_llm_tokens_consumed_total{model=\"deepseek-chat\", type=\"prompt\"}[24h])) * 0.00000014) + (sum(increase(rpg_llm_tokens_consumed_total{model=\"deepseek-chat\", type=\"completion\"}[24h])) * 0.00000028) + (sum(increase(rpg_llm_tokens_consumed_total{model=\"gpt-4o-mini\", type=\"prompt\"}[24h])) * 0.00000015) + (sum(increase(rpg_llm_tokens_consumed_total{model=\"gpt-4o-mini\", type=\"completion\"}[24h])) * 0.00000060)",
          "legendFormat": "Custo total",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "currencyUSD",
          "color": { "mode": "fixed", "fixedColor": "green" }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "textMode": "valueAndName"
      }
    },
    {
      "id": 4,
      "title": "Consumo Acumulado de Tokens (24h)",
      "type": "barchart",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 8 },
      "targets": [
        {
          "expr": "sum(increase(rpg_llm_tokens_consumed_total[24h])) by (model, type)",
          "legendFormat": "{{model}} - {{type}}",
          "instant": true,
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "custom": {
            "stacking": { "mode": "normal", "group": "model" }
          }
        }
      }
    },
    {
      "id": 6,
      "title": "Duração Média das Tarefas da Crew",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 16 },
      "targets": [
        {
          "expr": "sum(rate(rpg_crew_task_duration_seconds_sum[5m])) by (task_name) / sum(rate(rpg_crew_task_duration_seconds_count[5m])) by (task_name)",
          "legendFormat": "{{task_name}}",
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "custom": {
            "drawStyle": "line",
            "lineInterpolation": "smooth"
          },
          "unit": "s"
        }
      }
    },
    {
      "id": 7,
      "title": "Ambientes/Biomas Mais Visitados (Turnos)",
      "type": "piechart",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 16 },
      "targets": [
        {
          "expr": "sum(increase(rpg_active_environment_turns_total[24h])) by (biome)",
          "legendFormat": "{{biome}}",
          "instant": true,
          "refId": "A"
        }
      ],
      "options": {
        "pieType": "donut",
        "reduceOptions": {
          "values": false,
          "calcs": ["lastNotNull"]
        }
      }
    },
    {
      "id": 8,
      "title": "Ritmo de Jogo: TPM & Sessões Ativas",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 24 },
      "targets": [
        {
          "expr": "sum(rate(rpg_game_turns_total[5m])) * 60",
          "legendFormat": "Turnos por Minuto (TPM)",
          "refId": "A"
        },
        {
          "expr": "rpg_active_sessions_count",
          "legendFormat": "Sessões Simultâneas Ativas",
          "refId": "B"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "custom": {
            "drawStyle": "line"
          },
          "unit": "none"
        }
      }
    },
    {
      "id": 9,
      "title": "Itens Consumidos/Removidos do Inventário",
      "type": "barchart",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 24 },
      "targets": [
        {
          "expr": "sum(rpg_player_items_consumed_total) by (item_name)",
          "legendFormat": "{{item_name}}",
          "instant": true,
          "refId": "A"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "short"
        }
      }
    }
  ],
  "schemaVersion": 38,
  "style": "dark",
  "tags": ["rpg", "crewai", "deepseek"],
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "browser",
  "title": "RPG de Texto Baseado em Agentes - Telemetria",
  "uid": "rpg-agentes-telemetria",
  "version": 1
}
```
