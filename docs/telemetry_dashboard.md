# Especificação da Telemetria (Prometheus & Grafana)

Este documento especifica a configuração de observabilidade do RPG de texto. Ele descreve as queries **PromQL (Prometheus Query Language)** necessárias para extrair métricas de desempenho da IA e status do jogo, além de fornecer a estrutura JSON base para a criação do dashboard no **Grafana**.

---

## 1. Métricas Customizadas Exportadas pelo Backend

O backend FastAPI irá expor no endpoint `/metrics` as seguintes métricas nativas do Prometheus:

| Nome da Métrica | Tipo | Labels | Descrição |
| :--- | :--- | :--- | :--- |
| `rpg_player_health` | **Gauge** | `game_id`, `player_name`, `class` | Nível atual de pontos de vida do jogador. |
| `rpg_model_switches_total` | **Counter** | `reason`, `fallback_model` | Total de vezes que a aplicação alternou de modelo de IA (fallback). |
| `rpg_llm_request_duration_seconds` | **Histogram** | `model`, `status` | Tempo de resposta (latência) da chamada de IA da Crew. |
| `rpg_llm_tokens_consumed_total` | **Counter** | `model`, `type` (`prompt` ou `completion`) | Contagem total de tokens consumidos no processamento. |

---

## 2. Especificação das Consultas (PromQL)

Aqui estão as queries PromQL detalhadas para alimentar cada um dos quatro painéis solicitados no dashboard do Grafana:

### A. Painel 1: Latência de Resposta por Turno (Gráfico de Linha)
* **Objetivo**: Monitorar a latência da API do DeepSeek em tempo real, visualizando picos e desvios, incluindo o comportamento após o acionamento de fallbacks.
* **Tipo de Visualização**: Gráfico de Linha (Time Series).
* **Queries PromQL**:
  * **Percentil 95 da latência (p95)**:
    ```promql
    histogram_quantile(0.95, sum(rate(rpg_llm_request_duration_seconds_bucket[5m])) by (le, model))
    ```
  * **Latência Média da IA**:
    ```promql
    sum(rate(rpg_llm_request_duration_seconds_sum[5m])) by (model) / sum(rate(rpg_llm_request_duration_seconds_count[5m])) by (model)
    ```
* **Configurações visuais recomendadas**:
  * Unidade: Segundos (`s`).
  * Mapeamento de cor: Vermelho para latências acima de `4.0s` (limite crítico de timeout do DeepSeek).

### B. Painel 2: Distribuição de Requisições por Modelo (Gráfico de Pizza/Donut)
* **Objetivo**: Visualizar a proporção de requisições que estão rodando na LLM Primária (DeepSeek) versus o modelo reserva (Fallback), evidenciando a taxa de sucesso da infraestrutura primária.
* **Tipo de Visualização**: Gráfico de Pizza ou Donut (Pie Chart).
* **Query PromQL**:
  ```promql
  sum(increase(rpg_llm_request_duration_seconds_count[24h])) by (model)
  ```
* **Configurações visuais recomendadas**:
  * Exibir valores absolutos e porcentagens na legenda.
  * Mapeamento de cor estável: `deepseek-chat` = Azul Marinho; `gpt-4o-mini` = Verde/Laranja.

### C. Painel 3: Vida Atual do Jogador em Tempo Real (Gauge Visual)
* **Objetivo**: Renderizar o medidor de saúde física do personagem selecionado na tela de telemetria.
* **Tipo de Visualização**: Gauge (Medidor circular/barra de preenchimento).
* **Query PromQL**:
  ```promql
  rpg_player_health
  ```
  *(Nota: Se houver mais de um jogo ativo, o Grafana renderizará múltiplos Gauges na tela identificando cada jogador).*
* **Configurações visuais recomendadas**:
  * Limites (Thresholds):
    * `0` a `29` -> Vermelho (Vida Crítica)
    * `30` a `69` -> Amarelo (Cuidado)
    * `70` a `100` -> Verde (Saudável)
  * Valor Máximo: `100`

### D. Painel 4: Consumo Acumulado de Tokens (Gráfico de Barras)
* **Objetivo**: Demonstrar de forma empilhada o volume de tokens enviados (prompt) e recebidos (completion), faturados pela API do DeepSeek e do modelo reserva.
* **Tipo de Visualização**: Gráfico de Barras Empilhado (Bar Chart / Bar Gauge).
* **Query PromQL**:
  ```promql
  sum(increase(rpg_llm_tokens_consumed_total[24h])) by (model, type)
  ```
* **Configurações visuais recomendadas**:
  * Exibição empilhada por tipo (`prompt` na base da barra e `completion` no topo).
  * Unidade: Tokens (Short format).

---

## 3. Modelo JSON Estruturado de Painéis (Grafana Schema)

Abaixo está o trecho em formato JSON estruturado contendo a definição da estrutura dos painéis do Grafana compatível com a API do Grafana v9.x/v10.x. Este JSON pode ser injetado diretamente na propriedade `panels` do dashboard.

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
      "gridPos": { "h": 8, "w": 8, "x": 0, "y": 8 },
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
      "id": 4,
      "title": "Consumo Acumulado de Tokens (24h)",
      "type": "barchart",
      "gridPos": { "h": 8, "w": 16, "x": 8, "y": 8 },
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
