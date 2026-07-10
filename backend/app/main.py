import uuid
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from uuid import UUID

from app.schemas.game import StartGameRequest, ProcessTurnRequest, GameStateResponse
from app.core.crew import run_game_turn
from app.core.telemetry import get_serialized_metrics

app = FastAPI(
    title="RPG de Texto Baseado em Agentes - API",
    description="Backend para processamento de RPG de texto com CrewAI e DeepSeek"
)

# Configuração do Middleware CORS para permitir conexão com o Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite tudo em desenvolvimento. Pode ser restrito para o container do frontend.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Banco de dados em memória simples para as sessões de jogo ativas
games_db: Dict[UUID, Dict[str, Any]] = {}

def get_initial_inventory(character_class: str) -> list:
    """Retorna itens iniciais baseados na classe do personagem."""
    inventories = {
        "Guerreiro": ["Espada de Bronze", "Escudo de Madeira", "Pocao de Cura P", "Pocao de Cura P", "Pocao de Cura P"],
        "Mago": ["Cajado de Aprendiz", "Grimorio do Fogo", "Pocao de Cura P", "Pocao de Cura P", "Pocao de Cura P"],
        "Ladino": ["Adaga Envenenada", "Gazuas de Ladrao", "Pocao de Cura P", "Pocao de Cura P", "Pocao de Cura P"],
        "Clerigo": ["Maca de Ferro", "Simbolo Sagrado", "Pocao de Cura P", "Pocao de Cura P", "Pocao de Cura P"]
    }
    return inventories.get(character_class, ["Graveto", "Pocao de Cura P", "Pocao de Cura P", "Pocao de Cura P"])

@app.post("/game/start", response_model=GameStateResponse, status_code=201)
def start_game(request: StartGameRequest):
    game_id = uuid.uuid4()
    
    # Define o estado inicial do jogador
    initial_inventory = get_initial_inventory(request.character_class)
    
    # Para o turno de introdução, orquestramos a Crew interpretando a ação inicial do jogador
    intro_action = f"Explorar a região de {request.starting_environment} e observar o ambiente ao redor."
    
    try:
        narrative, current_env, suggested_actions, player_state, telemetry = run_game_turn(
            game_id=game_id,
            player_name=request.player_name,
            character_class=request.character_class,
            player_action=intro_action,
            current_health=100,
            current_inventory=initial_inventory,
            short_narrative=request.short_narrative,
            suggest_actions=request.suggest_actions,
            current_environment=request.starting_environment
        )
        
        # Salva o estado atualizado no banco em memória
        games_db[game_id] = {
            "player_name": request.player_name,
            "character_class": request.character_class,
            "starting_environment": request.starting_environment,
            "current_environment": current_env,
            "short_narrative": request.short_narrative,
            "suggest_actions": request.suggest_actions,
            "health": player_state["health"],
            "inventory": player_state["inventory"],
            "alive": player_state["alive"]
        }
        
        return GameStateResponse(
            game_id=game_id,
            narrative=narrative,
            current_environment=current_env,
            suggested_actions=suggested_actions,
            player_state=player_state,
            telemetry_metadata=telemetry
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao iniciar a orquestração do jogo: {str(e)}"
        )

@app.post("/game/turn", response_model=GameStateResponse)
def process_turn(request: ProcessTurnRequest):
    if request.game_id not in games_db:
        raise HTTPException(
            status_code=400,
            detail="Sessão de jogo inválida ou não encontrada."
        )
        
    game_state = games_db[request.game_id]
    
    if not game_state["alive"]:
        raise HTTPException(
            status_code=400,
            detail="O personagem está morto. Inicie uma nova sessão."
        )
        
    try:
        narrative, current_env, suggested_actions, player_state, telemetry = run_game_turn(
            game_id=request.game_id,
            player_name=game_state["player_name"],
            character_class=game_state["character_class"],
            player_action=request.player_action,
            current_health=game_state["health"],
            current_inventory=game_state["inventory"],
            short_narrative=game_state["short_narrative"],
            suggest_actions=game_state.get("suggest_actions", False),
            current_environment=game_state.get("current_environment", "Masmorra")
        )
        
        # Atualiza a persistência em memória
        games_db[request.game_id].update({
            "health": player_state["health"],
            "inventory": player_state["inventory"],
            "current_environment": current_env,
            "alive": player_state["alive"]
        })
        
        return GameStateResponse(
            game_id=request.game_id,
            narrative=narrative,
            current_environment=current_env,
            suggested_actions=suggested_actions,
            player_state=player_state,
            telemetry_metadata=telemetry
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no processamento do turno: {str(e)}"
        )

@app.get("/metrics")
def metrics():
    """Retorna as métricas expostas para o Prometheus."""
    return Response(
        content=get_serialized_metrics(),
        media_type="text/plain; version=0.0.4"
    )
