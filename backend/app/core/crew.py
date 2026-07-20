import time
import json
import re
from uuid import UUID
from typing import List, Dict, Any, Tuple, Optional

from langchain_community.callbacks import get_openai_callback
from langchain_openai import ChatOpenAI

from app.config import settings
from app.core.agents import get_llm
from app.core.tasks import (
    create_arbitration_messages,
    create_npc_reaction_messages,
    create_consolidation_messages
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
    """Extrai e limpa a resposta JSON da LLM, tratando marcações markdown de forma altamente resiliente."""
    try:
        match = re.search(r"```json\s*(.*?)\s*```", output_str, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            match_braces = re.search(r"(\{.*?\})", output_str, re.DOTALL)
            json_str = match_braces.group(1) if match_braces else output_str
        
        return json.loads(json_str)
    except Exception as e:
        print(f"[ERROR] Falha ao parsear JSON da narrativa: {e}. String bruta: {output_str}")
        
        narrative = ""
        match_narrative = re.search(r'"narrative"\s*:\s*"((?:[^"\\]|\\.)*)"', output_str, re.DOTALL)
        if match_narrative:
            narrative = match_narrative.group(1).replace('\\"', '"').replace('\\n', '\n')
        else:
            if "{" in output_str or '"narrative"' in output_str:
                narrative = "Ocorreu um tremor místico e a visão se dissipou... (Erro na formatação da narrativa)."
            else:
                narrative = output_str

        health_change = 0
        match_health = re.search(r'"health_change"\s*:\s*(-?\d+)', output_str)
        if match_health:
            health_change = int(match_health.group(1))

        current_env = "Masmorra"
        match_env = re.search(r'"current_environment"\s*:\s*"([^"]+)"', output_str)
        if match_env:
            current_env = match_env.group(1)

        return {
            "narrative": narrative,
            "health_change": health_change,
            "items_added": [],
            "items_removed": [],
            "suggested_actions": [],
            "current_environment": current_env
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


def execute_langchain_pipeline(
    llm: ChatOpenAI,
    player_action: str,
    current_health: int,
    current_inventory: List[str],
    current_companions: List[str],
    current_skills: List[str],
    character_class: str,
    short_narrative: bool,
    suggest_actions: bool,
    current_environment: str,
    history: Optional[List[Dict[str, str]]]
) -> str:
    """Executa a sequência de 3 passos do LangChain (Arbitragem -> Reação NPC -> Consolidação JSON)."""
    active_companion = current_companions[0] if current_companions else None

    # Tarefa 1: Arbitragem Físico-Mecânica (Game Master)
    t1_start = time.time()
    messages1 = create_arbitration_messages(
        player_action=player_action,
        health=current_health,
        inventory=current_inventory,
        companions=current_companions,
        skills=current_skills,
        class_name=character_class,
        short_narrative=short_narrative,
        current_environment=current_environment,
        history=history
    )
    res1 = llm.invoke(messages1)
    arbitration_output = res1.content if hasattr(res1, "content") else str(res1)
    dur1 = time.time() - t1_start
    rpg_crew_task_duration_seconds.labels(task_name="arbitration").observe(dur1)

    # Tarefa 2: Reação do NPC ou Eco do Ambiente
    t2_start = time.time()
    messages2 = create_npc_reaction_messages(
        arbitration_output=arbitration_output,
        companion_name=active_companion,
        short_narrative=short_narrative
    )
    res2 = llm.invoke(messages2)
    npc_output = res2.content if hasattr(res2, "content") else str(res2)
    dur2 = time.time() - t2_start
    rpg_crew_task_duration_seconds.labels(task_name="npc_reaction").observe(dur2)

    # Tarefa 3: Consolidação e Formatação JSON (Game Master)
    t3_start = time.time()
    messages3 = create_consolidation_messages(
        arbitration_output=arbitration_output,
        npc_reaction_output=npc_output,
        skills=current_skills,
        short_narrative=short_narrative,
        suggest_actions=suggest_actions,
        current_environment=current_environment
    )
    res3 = llm.invoke(messages3)
    consolidation_output = res3.content if hasattr(res3, "content") else str(res3)
    dur3 = time.time() - t3_start
    rpg_crew_task_duration_seconds.labels(task_name="consolidation").observe(dur3)

    return consolidation_output


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
    current_environment: str = "Masmorra",
    history: List[Dict[str, str]] = None
) -> Tuple[str, str, List[str], Dict[str, Any], Dict[str, Any]]:
    """
    Orquestra o turno usando LangChain.
    Tenta primeiro usar o DeepSeek. Se demorar mais de 4s ou falhar, alterna para GPT-4o-Mini.
    Retorna (narrativa_final, ambiente_geografico, sugestoes_de_acao, estado_jogador_atualizado, telemetria_metadata).
    """
    active_model = settings.PRIMARY_MODEL
    fallback_triggered = False
    response_time = 0.0
    tokens = {"prompt": 0, "completion": 0, "total": 0}
    pipeline_output = ""

    start_time = time.time()

    try:
        print(f"[INFO] Iniciando turno do jogo {game_id} via LangChain usando {active_model} (narrativa_curta={short_narrative}, sugerir_acoes={suggest_actions}, ambiente={current_environment})...")
        max_tokens = 1500 if short_narrative else 2500
        llm = get_llm(
            model_name=settings.PRIMARY_MODEL,
            timeout=settings.DEEPSEEK_TIMEOUT,
            max_tokens=max_tokens
        )
        
        with get_openai_callback() as cb:
            pipeline_output = execute_langchain_pipeline(
                llm=llm,
                player_action=player_action,
                current_health=current_health,
                current_inventory=current_inventory,
                current_companions=current_companions,
                current_skills=current_skills,
                character_class=character_class,
                short_narrative=short_narrative,
                suggest_actions=suggest_actions,
                current_environment=current_environment,
                history=history
            )
            tokens["prompt"] = cb.prompt_tokens
            tokens["completion"] = cb.completion_tokens
            tokens["total"] = cb.total_tokens
            
        if tokens["total"] == 0:
            est_prompt = max(800, (len(player_action) + 3000) // 3)
            est_completion = max(100, len(str(pipeline_output)) // 3)
            tokens["prompt"] = est_prompt
            tokens["completion"] = est_completion
            tokens["total"] = est_prompt + est_completion
        
        response_time = time.time() - start_time
        rpg_llm_request_duration_seconds.labels(model=settings.PRIMARY_MODEL, status="success").observe(response_time)
        
    except Exception as exc:
        response_time = time.time() - start_time
        print(f"[WARNING] API Primária ({settings.PRIMARY_MODEL}) falhou ou estourou timeout em {response_time:.2f}s. Erro: {exc}")
        
        rpg_llm_request_duration_seconds.labels(model=settings.PRIMARY_MODEL, status="failure").observe(response_time)
        
        reason = "timeout" if response_time >= settings.DEEPSEEK_TIMEOUT else "api_error"
        rpg_model_switches_total.labels(reason=reason, fallback_model=settings.FALLBACK_MODEL).inc()
        
        fallback_triggered = True
        active_model = settings.FALLBACK_MODEL
        print(f"[INFO] Acionando modelo reserva {active_model} via LangChain...")
        
        fallback_start_time = time.time()
        try:
            max_tokens_fallback = 1500 if short_narrative else 2500
            llm_fallback = get_llm(
                model_name=settings.FALLBACK_MODEL,
                timeout=settings.FALLBACK_TIMEOUT,
                max_tokens=max_tokens_fallback
            )
            
            with get_openai_callback() as cb:
                pipeline_output = execute_langchain_pipeline(
                    llm=llm_fallback,
                    player_action=player_action,
                    current_health=current_health,
                    current_inventory=current_inventory,
                    current_companions=current_companions,
                    current_skills=current_skills,
                    character_class=character_class,
                    short_narrative=short_narrative,
                    suggest_actions=suggest_actions,
                    current_environment=current_environment,
                    history=history
                )
                tokens["prompt"] = cb.prompt_tokens
                tokens["completion"] = cb.completion_tokens
                tokens["total"] = cb.total_tokens
                
            if tokens["total"] == 0:
                est_prompt = max(800, (len(player_action) + 3000) // 3)
                est_completion = max(100, len(str(pipeline_output)) // 3)
                tokens["prompt"] = est_prompt
                tokens["completion"] = est_completion
                tokens["total"] = est_prompt + est_completion
                
            response_time = time.time() - start_time
            fallback_duration = time.time() - fallback_start_time
            
            rpg_llm_request_duration_seconds.labels(model=settings.FALLBACK_MODEL, status="success").observe(fallback_duration)
            
        except Exception as fallback_exc:
            print(f"[CRITICAL] API de Fallback também falhou: {fallback_exc}")
            raise fallback_exc

    # Registra tokens consumidos no Prometheus
    rpg_llm_tokens_consumed_total.labels(model=active_model, type="prompt").inc(tokens["prompt"])
    rpg_llm_tokens_consumed_total.labels(model=active_model, type="completion").inc(tokens["completion"])

    # Processa a resposta estruturada JSON
    resolved_data = clean_json_output(pipeline_output)
    
    updated_env = resolved_data.get("current_environment", current_environment)
    if updated_env not in ["Masmorra", "Floresta", "Cidade", "Deserto", "Montanha", "Pantano", "Oceano", "Vulcao", "Ceu"]:
        updated_env = current_environment
    
    suggested_actions = resolved_data.get("suggested_actions", [])
    if not isinstance(suggested_actions, list):
        suggested_actions = []
    
    # Atualiza o estado lógico do jogador
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
            
            for inv_item in updated_inventory:
                if normalize_item_name(inv_item) == norm_name:
                    match_item = inv_item
                    break
                    
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

    # Atualiza métricas Prometheus
    rpg_player_health.labels(
        game_id=str(game_id),
        player_name=player_name,
        character_class=character_class
    ).set(new_health)

    rpg_game_turns_total.labels(game_id=str(game_id)).inc()
    rpg_active_environment_turns_total.labels(biome=updated_env).inc()

    updated_companions = resolved_data.get("companions", current_companions)
    if not isinstance(updated_companions, list):
        updated_companions = current_companions

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
