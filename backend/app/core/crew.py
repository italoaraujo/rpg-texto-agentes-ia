import time
import json
import re
from uuid import UUID
from typing import List, Dict, Any, Tuple
from crewai import Crew, Process
from langchain_community.callbacks import get_openai_callback

from app.config import settings
from app.core.agents import get_llm, create_game_master_agent, create_npc_agent
from app.core.tasks import (
    create_arbitration_task,
    create_npc_reaction_task,
    create_consolidation_task
)
from app.core.telemetry import (
    rpg_player_health,
    rpg_model_switches_total,
    rpg_llm_request_duration_seconds,
    rpg_llm_tokens_consumed_total,
    rpg_crew_task_duration_seconds,
    rpg_active_environment_turns_total,
    rpg_game_turns_total,
    rpg_player_items_consumed_total
)

def clean_json_output(output_str: str) -> Dict[str, Any]:
    """Extrai e limpa a resposta JSON da LLM, tratando marcações markdown."""
    try:
        # Se a saída estiver embrulhada em blocos de código markdown ```json ... ```
        match = re.search(r"```json\s*(.*?)\s*```", output_str, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # Caso contrário, tenta encontrar a abertura e fechamento de chaves
            match_braces = re.search(r"(\{.*?\})", output_str, re.DOTALL)
            json_str = match_braces.group(1) if match_braces else output_str
        
        return json.loads(json_str)
    except Exception as e:
        print(f"[ERROR] Falha ao parsear JSON da narrativa: {e}. String bruta: {output_str}")
        # Fallback de emergência caso a LLM quebre o formato
        return {
            "narrative": output_str,
            "health_change": -5,  # Penalidade pequena por erro crítico
            "items_added": [],
            "items_removed": [],
            "suggested_actions": [],
            "current_environment": "Masmorra"
        }

def normalize_item_name(name: str) -> str:
    import unicodedata
    name = str(name).lower().strip()
    name = "".join(
        c for c in unicodedata.normalize("NFD", name)
        if unicodedata.category(c) != "Mn"
    )
    return name

def parse_item_and_qty(item_str: str) -> Tuple[str, int]:
    import re
    item_str = item_str.strip()
    match = re.match(r"^(\d+)\s+(.+)$", item_str)
    if match:
        qty = int(match.group(1))
        name = match.group(2).strip()
    else:
        qty = 1
        name = item_str

    name_lower = name.lower()
    if "moeda" in name_lower:
        name = "Moeda de Ouro"
    elif "pocao de cura p" in name_lower or "poção de cura p" in name_lower or "pocão de cura p" in name_lower:
        name = "Pocao de Cura P"
    elif "pocao de cura" in name_lower or "poção de cura" in name_lower or "pocão de cura" in name_lower:
        name = "Pocao de Cura P"
        
    return name, qty

def run_game_turn(
    game_id: UUID,
    player_name: str,
    character_class: str,
    player_action: str,
    current_health: int,
    current_inventory: List[str],
    current_companions: List[str],
    current_skills: List[str],
    short_narrative: bool = False,
    suggest_actions: bool = False,
    current_environment: str = "Masmorra"
) -> Tuple[str, str, List[str], Dict[str, Any], Dict[str, Any]]:
    """
    Orquestra o turno usando CrewAI.
    Tenta primeiro usar o DeepSeek. Se demorar mais de 4s ou falhar, alterna para GPT-4o-Mini.
    Retorna (narrativa_final, ambiente_geografico, sugestoes_de_acao, estado_jogador_atualizado, telemetria_metadata).
    """
    active_model = settings.PRIMARY_MODEL
    fallback_triggered = False
    response_time = 0.0
    tokens = {"prompt": 0, "completion": 0, "total": 0}
    crew_output = ""

    start_time = time.time()
    crew_start_time = start_time
    t1_end = None
    t2_end = None

    def t1_callback(output):
        nonlocal t1_end
        t1_end = time.time()
        dur = t1_end - crew_start_time
        rpg_crew_task_duration_seconds.labels(task_name="arbitration").observe(dur)

    def t2_callback(output):
        nonlocal t1_end, t2_end
        t2_end = time.time()
        start = t1_end if t1_end else crew_start_time
        dur = t2_end - start
        rpg_crew_task_duration_seconds.labels(task_name="npc_reaction").observe(dur)

    def t3_callback(output):
        nonlocal t2_end
        t3_end = time.time()
        start = t2_end if t2_end else crew_start_time
        dur = t3_end - start
        rpg_crew_task_duration_seconds.labels(task_name="consolidation").observe(dur)

    try:
        print(f"[INFO] Iniciando turno do jogo {game_id} usando {active_model} (narrativa_curta={short_narrative}, sugerir_acoes={suggest_actions}, ambiente={current_environment})...")
        # 1. Instancia LLM Primária (DeepSeek) com timeout estrito de 4s
        max_tokens = 500 if short_narrative else 1500
        llm = get_llm(
            model_name=settings.PRIMARY_MODEL,
            timeout=settings.DEEPSEEK_TIMEOUT,
            max_tokens=max_tokens
        )
        
        # 2. Cria agentes e tarefas
        active_companion = current_companions[0] if current_companions else None
        gm_agent = create_game_master_agent(llm)
        npc_agent = create_npc_agent(llm, active_companion)
        
        t1 = create_arbitration_task(gm_agent, player_action, current_health, current_inventory, current_companions, current_skills, character_class, short_narrative, current_environment, callback=t1_callback)
        t2 = create_npc_reaction_task(npc_agent, t1, short_narrative, callback=t2_callback)
        t3 = create_consolidation_task(gm_agent, t1, t2, current_skills, short_narrative, suggest_actions, current_environment, callback=t3_callback)
        
        crew = Crew(
            agents=[gm_agent, npc_agent],
            tasks=[t1, t2, t3],
            process=Process.sequential,
            verbose=True
        )
        
        # 3. Executa capturando tokens
        with get_openai_callback() as cb:
            crew_output = crew.kickoff()
            tokens["prompt"] = cb.prompt_tokens
            tokens["completion"] = cb.completion_tokens
            tokens["total"] = cb.total_tokens
            
        # Estimador lógico de fallback se a API do DeepSeek ou o Callback retornar 0
        if tokens["total"] == 0:
            est_prompt = max(800, (len(player_action) + 3000) // 3)
            est_completion = max(100, len(str(crew_output)) // 3)
            tokens["prompt"] = est_prompt
            tokens["completion"] = est_completion
            tokens["total"] = est_prompt + est_completion
        
        response_time = time.time() - start_time
        # Registra a latência feliz do DeepSeek
        rpg_llm_request_duration_seconds.labels(model=settings.PRIMARY_MODEL, status="success").observe(response_time)
        
    except Exception as exc:
        # Se falhou ou deu timeout (> 4s), entra no bloco de fallback
        response_time = time.time() - start_time
        print(f"[WARNING] API Primária ({settings.PRIMARY_MODEL}) falhou ou estourou timeout em {response_time:.2f}s. Erro: {exc}")
        
        # Registra a falha na latência do DeepSeek
        rpg_llm_request_duration_seconds.labels(model=settings.PRIMARY_MODEL, status="failure").observe(response_time)
        
        # Incrementa contador de fallbacks
        reason = "timeout" if response_time >= settings.DEEPSEEK_TIMEOUT else "api_error"
        rpg_model_switches_total.labels(reason=reason, fallback_model=settings.FALLBACK_MODEL).inc()
        
        # Dispara fallback
        fallback_triggered = True
        active_model = settings.FALLBACK_MODEL
        print(f"[INFO] Acionando modelo reserva {active_model}...")
        
        fallback_start_time = time.time()
        crew_start_time = fallback_start_time
        t1_end = None
        t2_end = None
        try:
            # Instancia LLM de fallback com timeout maior
            max_tokens_fallback = 500 if short_narrative else 1500
            llm_fallback = get_llm(
                model_name=settings.FALLBACK_MODEL,
                timeout=settings.FALLBACK_TIMEOUT,
                max_tokens=max_tokens_fallback
            )
            
            active_companion = current_companions[0] if current_companions else None
            gm_agent = create_game_master_agent(llm_fallback)
            npc_agent = create_npc_agent(llm_fallback, active_companion)
            
            t1 = create_arbitration_task(gm_agent, player_action, current_health, current_inventory, current_companions, current_skills, character_class, short_narrative, current_environment, callback=t1_callback)
            t2 = create_npc_reaction_task(npc_agent, t1, short_narrative, callback=t2_callback)
            t3 = create_consolidation_task(gm_agent, t1, t2, current_skills, short_narrative, suggest_actions, current_environment, callback=t3_callback)
            
            crew_fallback = Crew(
                agents=[gm_agent, npc_agent],
                tasks=[t1, t2, t3],
                process=Process.sequential,
                verbose=True
            )
            
            with get_openai_callback() as cb:
                crew_output = crew_fallback.kickoff()
                tokens["prompt"] = cb.prompt_tokens
                tokens["completion"] = cb.completion_tokens
                tokens["total"] = cb.total_tokens
                
            # Estimador lógico de fallback para a chamada de contingência
            if tokens["total"] == 0:
                est_prompt = max(800, (len(player_action) + 3000) // 3)
                est_completion = max(100, len(str(crew_output)) // 3)
                tokens["prompt"] = est_prompt
                tokens["completion"] = est_completion
                tokens["total"] = est_prompt + est_completion
                
            response_time = time.time() - start_time  # tempo total desde o início da requisição
            fallback_duration = time.time() - fallback_start_time
            
            # Registra sucesso da LLM de fallback
            rpg_llm_request_duration_seconds.labels(model=settings.FALLBACK_MODEL, status="success").observe(fallback_duration)
            
        except Exception as fallback_exc:
            print(f"[CRITICAL] API de Fallback também falhou: {fallback_exc}")
            raise fallback_exc
 
    # 4. Registra tokens consumidos no Prometheus
    rpg_llm_tokens_consumed_total.labels(model=active_model, type="prompt").inc(tokens["prompt"])
    rpg_llm_tokens_consumed_total.labels(model=active_model, type="completion").inc(tokens["completion"])
 
    # 5. Processa a resposta estruturada
    resolved_data = clean_json_output(crew_output)
    
    # Extrai o ambiente de destino e valida se ele é suportado
    updated_env = resolved_data.get("current_environment", current_environment)
    if updated_env not in ["Masmorra", "Floresta", "Cidade", "Deserto", "Montanha", "Pantano", "Oceano", "Vulcao", "Ceu"]:
        updated_env = current_environment
    
    # Extrai sugestões de ações alternativas do JSON
    suggested_actions = resolved_data.get("suggested_actions", [])
    if not isinstance(suggested_actions, list):
        suggested_actions = []
    
    # 6. Atualiza o estado lógico do jogador
    health_change = resolved_data.get("health_change", 0)
    new_health = max(0, min(100, current_health + health_change))
    
    # Adição/Remoção de Itens
    updated_inventory = list(current_inventory)
    for it in resolved_data.get("items_added", []):
        name, qty = parse_item_and_qty(it)
        for _ in range(qty):
            updated_inventory.append(name)
            
    for it in resolved_data.get("items_removed", []):
        name, qty = parse_item_and_qty(it)
        for _ in range(qty):
            norm_name = normalize_item_name(name)
            match_item = None
            
            # 1. Tenta correspondência exata normalizada (sem acentos, caixa baixa)
            for inv_item in updated_inventory:
                if normalize_item_name(inv_item) == norm_name:
                    match_item = inv_item
                    break
                    
            # 2. Se não encontrou, tenta correspondência parcial (ex: "pocao de cura" contido em "pocao de cura p")
            if not match_item:
                for inv_item in updated_inventory:
                    norm_inv_item = normalize_item_name(inv_item)
                    if norm_name in norm_inv_item or norm_inv_item in norm_name:
                        match_item = inv_item
                        break
                        
            if match_item:
                updated_inventory.remove(match_item)
                rpg_player_items_consumed_total.labels(item_name=match_item).inc()
            else:
                print(f"[WARNING] Item '{name}' solicitado para remoção não foi encontrado no inventário: {updated_inventory}")
 
    # 7. Atualiza o Gauge de vida no Prometheus
    rpg_player_health.labels(
        game_id=str(game_id),
        player_name=player_name,
        character_class=character_class
    ).set(new_health)

    # 8. Incrementa o contador de turnos e turnos por ambiente
    rpg_game_turns_total.labels(game_id=str(game_id)).inc()
    rpg_active_environment_turns_total.labels(biome=updated_env).inc()
 
    # Extrai a lista de companheiros ativa do retorno JSON
    updated_companions = resolved_data.get("companions", current_companions)
    if not isinstance(updated_companions, list):
        updated_companions = current_companions

    # Extrai a lista de habilidades ativa do retorno JSON
    updated_skills = resolved_data.get("skills", current_skills)
    if not isinstance(updated_skills, list):
        updated_skills = current_skills

    player_state = {
        "health": new_health,
        "max_health": 100,
        "inventory": updated_inventory,
        "companions": updated_companions,
        "skills": updated_skills,
        "alive": new_health > 0
    }
 
    telemetry_metadata = {
        "active_model": active_model,
        "fallback_triggered": fallback_triggered,
        "response_time_seconds": round(response_time, 2),
        "tokens_consumed": tokens
    }
 
    return resolved_data.get("narrative", ""), updated_env, suggested_actions, player_state, telemetry_metadata
