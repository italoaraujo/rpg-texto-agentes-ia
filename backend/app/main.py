import uuid
import time
from collections import Counter
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
from uuid import UUID

from app.schemas.game import StartGameRequest, ProcessTurnRequest, GameStateResponse
from app.core.crew import run_game_turn
from app.core.telemetry import get_serialized_metrics, rpg_active_sessions_count

def normalize_text_for_comparison(text: str) -> str:
    import unicodedata
    name = str(text).lower().strip()
    name = "".join(
        c for c in unicodedata.normalize("NFD", name)
        if unicodedata.category(c) != "Mn"
    )
    return name

def detect_state_changes(prev: dict, curr: dict, timestamp: float) -> list:
    events = []
    
    # 1. Health change
    prev_health = prev.get("health", 100)
    curr_health = curr.get("health", 100)
    if curr_health != prev_health:
        diff = curr_health - prev_health
        if diff > 0:
            events.append({
                "type": "health_gain",
                "message": f"Curou {diff} de vida",
                "timestamp": timestamp
            })
        else:
            events.append({
                "type": "health_loss",
                "message": f"Sofreu {-diff} de dano",
                "timestamp": timestamp
            })
    
    # 2. Environment change
    prev_env = prev.get("current_environment")
    curr_env = curr.get("current_environment")
    if prev_env and curr_env and normalize_text_for_comparison(prev_env) != normalize_text_for_comparison(curr_env):
        events.append({
            "type": "environment_change",
            "message": f"Mudou de ambiente para {curr_env}",
            "timestamp": timestamp
        })
        
    # 3. Companions
    prev_comp_raw = prev.get("companions", [])
    curr_comp_raw = curr.get("companions", [])
    
    prev_comp = {normalize_text_for_comparison(c): c for c in prev_comp_raw}
    curr_comp = {normalize_text_for_comparison(c): c for c in curr_comp_raw}
    
    # Joined
    for norm_c in curr_comp.keys() - prev_comp.keys():
        c = curr_comp[norm_c]
        events.append({
            "type": "companion_join",
            "message": f"{c} entrou na equipe",
            "timestamp": timestamp
        })
    # Left
    for norm_c in prev_comp.keys() - curr_comp.keys():
        c = prev_comp[norm_c]
        events.append({
            "type": "companion_leave",
            "message": f"{c} saiu da equipe",
            "timestamp": timestamp
        })
        
    # 4. Skills
    prev_skills_raw = prev.get("skills", [])
    curr_skills_raw = curr.get("skills", [])
    
    prev_skills = {normalize_text_for_comparison(s): s for s in prev_skills_raw}
    curr_skills = {normalize_text_for_comparison(s): s for s in curr_skills_raw}
    
    # Learned
    for norm_s in curr_skills.keys() - prev_skills.keys():
        s = curr_skills[norm_s]
        events.append({
            "type": "skill_learn",
            "message": f"Aprendeu habilidade: {s}",
            "timestamp": timestamp
        })
    # Lost
    for norm_s in prev_skills.keys() - curr_skills.keys():
        s = prev_skills[norm_s]
        events.append({
            "type": "skill_loss",
            "message": f"Perdeu habilidade: {s}",
            "timestamp": timestamp
        })
        
    # 5. Items (Inventory)
    prev_inv_raw = prev.get("inventory", [])
    curr_inv_raw = curr.get("inventory", [])
    
    prev_inv = Counter(normalize_text_for_comparison(it) for it in prev_inv_raw)
    curr_inv = Counter(normalize_text_for_comparison(it) for it in curr_inv_raw)
    
    item_display_names = {}
    for it in prev_inv_raw + curr_inv_raw:
        item_display_names[normalize_text_for_comparison(it)] = it
        
    all_items = set(prev_inv.keys()) | set(curr_inv.keys())
    for norm_item in all_items:
        p_count = prev_inv[norm_item]
        c_count = curr_inv[norm_item]
        display_name = item_display_names[norm_item]
        if c_count > p_count:
            diff = c_count - p_count
            events.append({
                "type": "item_obtained",
                "message": f"Obteve: {display_name} (x{diff})" if diff > 1 else f"Obteve: {display_name}",
                "timestamp": timestamp
            })
        elif p_count > c_count:
            diff = p_count - c_count
            events.append({
                "type": "item_used",
                "message": f"Usou/Perdeu: {display_name} (x{diff})" if diff > 1 else f"Usou/Perdeu: {display_name}",
                "timestamp": timestamp
            })
            
    return events

app = FastAPI(
    title="RPG de Texto Baseado em Agentes - API",
    description="Backend para processamento de RPG de texto com LangChain e DeepSeek"
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
rpg_active_sessions_count.set(0)

def get_initial_inventory(character_class: str) -> list:
    """Retorna itens iniciais baseados na classe do personagem."""
    inventories = {
        "Guerreiro": ["Espada de Bronze", "Escudo de Madeira", "Pocao de Cura P", "Pocao de Cura P", "Pocao de Cura P"],
        "Mago": ["Cajado de Aprendiz", "Grimorio do Fogo", "Pocao de Cura P", "Pocao de Cura P", "Pocao de Cura P"],
        "Ladino": ["Adaga Envenenada", "Gazuas de Ladrao", "Pocao de Cura P", "Pocao de Cura P", "Pocao de Cura P"],
        "Clerigo": ["Maca de Ferro", "Simbolo Sagrado", "Pocao de Cura P", "Pocao de Cura P", "Pocao de Cura P"]
    }
    return inventories.get(character_class, ["Graveto", "Pocao de Cura P", "Pocao de Cura P", "Pocao de Cura P"])

def get_initial_skills(character_class: str) -> list:
    """Retorna habilidades iniciais baseadas na classe do personagem."""
    skills = {
        "Guerreiro": ["Golpe Poderoso", "Bloqueio com Escudo"],
        "Mago": ["Bola de Fogo", "Missil Magico"],
        "Ladino": ["Ataque Furtivo", "Furtividade"],
        "Clerigo": ["Cura Divina", "Escudo da Fe"]
    }
    return skills.get(character_class, ["Ataque Basico"])

@app.post("/game/start", response_model=GameStateResponse, status_code=201)
def start_game(request: StartGameRequest):
    game_id = uuid.uuid4()
    
    # Define o estado inicial do jogador
    initial_inventory = get_initial_inventory(request.character_class)
    initial_skills = get_initial_skills(request.character_class)
    
    # Para o turno de introdução, orquestramos a pipeline LangChain interpretando a ação inicial do jogador
    intro_action = f"Explorar a região de {request.starting_environment} e observar o ambiente ao redor."
    
    initial_companions = []
    if request.starting_companion and request.starting_companion != "Nenhum":
        initial_companions = [request.starting_companion]

    try:
        narrative, current_env, suggested_actions, player_state, telemetry = run_game_turn(
            game_id=game_id,
            player_name=request.player_name,
            character_class=request.character_class,
            player_action=intro_action,
            current_health=100,
            current_inventory=initial_inventory,
            current_companions=initial_companions,
            current_skills=initial_skills,
            short_narrative=request.short_narrative,
            suggest_actions=request.suggest_actions,
            current_environment=request.starting_environment
        )
        
        # Mapeamento do estado inicial antes de chamar o turno de introdução
        pre_start_state = {
            "health": 100,
            "current_environment": request.starting_environment,
            "inventory": initial_inventory,
            "companions": initial_companions,
            "skills": initial_skills
        }
        
        # Mapeia o estado resultante
        post_start_state = {
            "health": player_state["health"],
            "current_environment": current_env,
            "inventory": player_state["inventory"],
            "companions": player_state["companions"],
            "skills": player_state["skills"]
        }
        
        # Cria os eventos
        t_now = time.time()
        events = [{
            "type": "game_start",
            "message": "Jornada iniciada!",
            "timestamp": t_now
        }]
        
        # Detecta mudanças ocorridas no turno de introdução
        intro_events = detect_state_changes(pre_start_state, post_start_state, t_now)
        events.extend(intro_events)

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
            "companions": player_state["companions"],
            "skills": player_state["skills"],
            "alive": player_state["alive"],
            "history": [
                {
                    "action": intro_action,
                    "narrative": narrative
                }
            ],
            "events": events
        }
        rpg_active_sessions_count.set(len(games_db))
        
        return GameStateResponse(
            game_id=game_id,
            narrative=narrative,
            current_environment=current_env,
            suggested_actions=suggested_actions,
            player_state=player_state,
            telemetry_metadata=telemetry,
            action_history=events
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
        history = game_state.get("history", [])
        narrative, current_env, suggested_actions, player_state, telemetry = run_game_turn(
            game_id=request.game_id,
            player_name=game_state["player_name"],
            character_class=game_state["character_class"],
            player_action=request.player_action,
            current_health=game_state["health"],
            current_inventory=game_state["inventory"],
            current_companions=game_state.get("companions", ["Eldon"]),
            current_skills=game_state.get("skills", []),
            short_narrative=game_state["short_narrative"],
            suggest_actions=game_state.get("suggest_actions", False),
            current_environment=game_state.get("current_environment", "Masmorra"),
            history=history
        )
        
        # Atualiza o histórico mantendo apenas as últimas 10 mensagens/rodadas
        new_history = list(history)
        new_history.append({
            "action": request.player_action,
            "narrative": narrative
        })
        new_history = new_history[-10:]
        
        # Mapeia o estado antes do turno
        prev_state = {
            "health": game_state["health"],
            "current_environment": game_state["current_environment"],
            "inventory": game_state["inventory"],
            "companions": game_state["companions"],
            "skills": game_state["skills"]
        }
        
        # Mapeia o estado resultante
        post_state = {
            "health": player_state["health"],
            "current_environment": current_env,
            "inventory": player_state["inventory"],
            "companions": player_state["companions"],
            "skills": player_state["skills"]
        }
        
        t_now = time.time()
        turn_events = detect_state_changes(prev_state, post_state, t_now)
        
        # Recupera eventos anteriores e estende com os novos
        events = list(game_state.get("events", []))
        events.extend(turn_events)
        
        # Atualiza a persistência em memória
        games_db[request.game_id].update({
            "health": player_state["health"],
            "inventory": player_state["inventory"],
            "companions": player_state["companions"],
            "skills": player_state["skills"],
            "current_environment": current_env,
            "alive": player_state["alive"],
            "history": new_history,
            "events": events
        })
        
        return GameStateResponse(
            game_id=request.game_id,
            narrative=narrative,
            current_environment=current_env,
            suggested_actions=suggested_actions,
            player_state=player_state,
            telemetry_metadata=telemetry,
            action_history=events
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


