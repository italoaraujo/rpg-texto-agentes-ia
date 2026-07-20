from typing import List, Dict, Optional
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from app.core.agents import get_game_master_system_prompt, get_npc_system_prompt

def create_arbitration_messages(
    player_action: str,
    health: int,
    inventory: List[str],
    companions: List[str],
    skills: List[str],
    class_name: str,
    short_narrative: bool = False,
    current_environment: str = "Masmorra",
    history: Optional[List[Dict[str, str]]] = None
) -> List[BaseMessage]:
    """Cria a lista de mensagens LangChain para a Tarefa 1: Arbitragem Físico-Mecânica (Game Master)."""
    system_prompt = get_game_master_system_prompt()
    
    style_instruction = ""
    if short_narrative:
        style_instruction = "\nATENÇÃO: Escreva um resultado físico curto, rápido e direto ao ponto em apenas 1 parágrafo conciso."

    history_instruction = ""
    if history:
        history_instruction = "Histórico das últimas mensagens/rodadas da sessão atual (use para lembrar acontecimentos anteriores e manter coerência narrativa):\n"
        for i, turn in enumerate(history, 1):
            history_instruction += f"Turno {i}:\n"
            history_instruction += f"  Jogador: \"{turn.get('action', '')}\"\n"
            history_instruction += f"  Narrador (Mestre): \"{turn.get('narrative', '')}\"\n"
        history_instruction += "\n"

    user_message = (
        f"{history_instruction}"
        f"Analise e resolva a ação do jogador: \"{player_action}\".\n"
        f"Considere os dados atuais do jogador e cenário:\n"
        f"- Ambiente Geográfico Ativo: {current_environment}\n"
        f"- Classe: {class_name}\n"
        f"- Vida Atual: {health}/100\n"
        f"- Inventário Atual: {inventory}\n"
        f"- Companheiros na Equipe (NPCs): {companions}\n"
        f"- Habilidades Ativas do Herói: {skills}\n\n"
        "Determine o resultado físico desta ação de forma lógica e imparcial, de acordo com o ambiente em que ele se encontra.\n"
        "Dificuldade baseada na classe: Ajuste a chance de sucesso baseado na classe do jogador (ex: Guerreiros são excelentes em força física/combate; Magos em testes arcanos, leitura de runas e intelecto).\n"
        "Morte do jogador: Se o jogador sofrer dano suficiente para fazer a vida atual ficar igual ou menor que 0, narre a sua derrota física ou morte definitiva.\n"
        "Se a narrativa ou a ação indicar que um companheiro entrou ou saiu do grupo, descreva esse acontecimento físico.\n"
        "Se o jogador se expôs a perigo, determine se ele sofreu dano e o valor exato (ex: 15 de dano).\n"
        "Se ele usou um item de cura do inventário (como 'Pocao de Cura P'), processe o consumo removendo-o e aplicando a cura (+30 de vida).\n"
        "Se encontrou algum item no cenário, adicione-o.\n"
        "Se a ação ou acontecimento indicar que o jogador aprendeu uma nova habilidade (treinamento, leitura de grimório/runas, etc.) ou esqueceu/perdeu uma habilidade (maldição, choque mental, etc.), descreva esse acontecimento físico.\n"
        "Escreva o resultado físico ocorrido de forma factual (ex: 'Você tenta abrir a porta...')."
        f"{style_instruction}"
    )

    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]

def create_npc_reaction_messages(
    arbitration_output: str,
    companion_name: Optional[str] = None,
    short_narrative: bool = False
) -> List[BaseMessage]:
    """Cria a lista de mensagens LangChain para a Tarefa 2: Reação do NPC ou Eco do Ambiente."""
    system_prompt = get_npc_system_prompt(companion_name)
    
    style_instruction = ""
    if short_narrative:
        style_instruction = "\nATENÇÃO: Mantenha a fala ou reação extremamente curta (máximo de 1 a 2 frases dinâmicas)."

    if companion_name:
        user_message = (
            "Leia a resolução física da ação do jogador gerada a seguir:\n"
            f"--- ARBITRAGEM DO MESTRE ---\n{arbitration_output}\n--- FIM DA ARBITRAGEM ---\n\n"
            f"Como o NPC companheiro {companion_name}, reaja a este acontecimento em primeira pessoa, fornecendo um diálogo curto "
            "ou reação expressiva. Sua reação deve refletir estritamente sua própria personalidade e histórico.\n"
            "Não resolva ações físicas, apenas expresse sua voz e sentimentos."
            f"{style_instruction}"
        )
    else:
        user_message = (
            "Leia a resolução física da ação do jogador gerada a seguir:\n"
            f"--- ARBITRAGEM DO MESTRE ---\n{arbitration_output}\n--- FIM DA ARBITRAGEM ---\n\n"
            "Como o Eco do Ambiente e Sussurro das Sombras, forneça descrições atmosféricas, calafrios ou sussurros "
            "do vento que reflitam a solidão absoluta do jogador e a tensão psicológica do local.\n"
            "Não fale diretamente com o jogador como uma pessoa física, apenas descreva as sensações do ambiente."
            f"{style_instruction}"
        )

    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]

def create_consolidation_messages(
    arbitration_output: str,
    npc_reaction_output: str,
    skills: List[str],
    short_narrative: bool = False,
    suggest_actions: bool = False,
    current_environment: str = "Masmorra"
) -> List[BaseMessage]:
    """Cria a lista de mensagens LangChain para a Tarefa 3: Consolidação e Formatação JSON (Game Master)."""
    system_prompt = get_game_master_system_prompt()
    
    style_instruction = ""
    if short_narrative:
        style_instruction = "\nATENÇÃO: Consolide em uma narrativa muito curta, limpa, objetiva e dinâmica de no máximo 1 ou 2 parágrafos pequenos."

    if suggest_actions:
        actions_instruction = (
            "\nATENÇÃO ADICIONAL: Você DEVE incluir no JSON final uma chave de nome 'suggested_actions' contendo uma "
            "lista (array de strings) de 3 a 5 alternativas de ações lógicas e contextuais que o jogador pode escolher no próximo turno "
            "(ex: ['Atacar com minha espada', 'Gritar por ajuda', 'Tentar fugir pelo corredor', 'Usar uma Pocao de Cura P']). "
            "Cada sugestão deve ser curta, direta, escrita a partir da perspectiva do herói (ex: 'Examinar o altar', 'Atacar o Orc')."
        )
    else:
        actions_instruction = "\nATENÇÃO ADICIONAL: Defina a chave 'suggested_actions' como uma lista vazia [] no JSON final."

    environment_instruction = (
        "\nATENÇÃO DE MUDANÇA DE CENÁRIO: Avalie se a resolução física descrita na Tarefa 1 resultou em uma mudança lógica de ambiente "
        f"em relação ao cenário atual ('{current_environment}'). Por exemplo, se o jogador estava na 'Floresta' e desceu uma escada de ruínas, "
        "o ambiente muda para 'Masmorra'. Se subiu uma corda de escalada em uma montanha em direção a uma ilha voadora, muda para 'Ceu'. "
        "Se entrou em um barco e navegou, muda para 'Oceano'. O novo ambiente determinado DEVE ser estritamente uma dessas 9 strings: "
        "'Masmorra', 'Floresta', 'Cidade', 'Deserto', 'Montanha', 'Pantano', 'Oceano', 'Vulcao', 'Ceu'. "
        "Se o jogador permanecer no mesmo ambiente ou não houver transição explícita, retorne exatamente o valor anterior: '{current_environment}'. "
        "Retorne esse ambiente determinado obrigatoriamente na chave 'current_environment' do JSON."
    )

    user_message = (
        "Consolide a narrativa física (Tarefa 1) e o diálogo do NPC (Tarefa 2) em um texto narrativo único, "
        "literário, imersivo e coeso para o jogador.\n\n"
        f"--- TAREFA 1 (ARBITRAGEM FÍSICA) ---\n{arbitration_output}\n\n"
        f"--- TAREFA 2 (REAÇÃO/DIÁLOGO DO NPC) ---\n{npc_reaction_output}\n\n"
        f"Considere que as habilidades iniciais do jogador no começo deste turno são: {skills}.\n"
        "Morte do jogador: Se a vida final do jogador chegar a 0 (ou menos) após a alteração física da Tarefa 1, a narrativa de consolidação deve decretar a sua morte/derrota física imediata e a chave 'suggested_actions' no JSON deve vir obrigatoriamente vazia [].\n"
        "Além disso, retorne o estado atualizado final do jogador formatado estritamente como um JSON válido (sem textos de introdução ou conclusão fora do bloco JSON) contendo as seguintes chaves:\n"
        "- 'narrative': A história unificada e polida contendo o texto literário.\n"
        "- 'current_environment': O ambiente final atualizado ('Masmorra', 'Floresta', 'Cidade', 'Deserto', 'Montanha', 'Pantano', 'Oceano', 'Vulcao' ou 'Ceu').\n"
        "- 'health_change': O valor numérico líquido de alteração de vida do jogador neste turno (positivo para cura, negativo para dano, 0 para nada).\n"
        "- 'items_added': Lista de itens adicionados neste turno.\n"
        "- 'items_removed': Lista de itens removidos ou consumidos neste turno.\n"
        "- 'suggested_actions': Uma lista de 3 a 5 strings sugerindo ações opcionais para o próximo turno (ou [] se desativado ou se o jogador morreu).\n"
        "- 'companions': Uma lista contendo os nomes (strings) de todos os companheiros (NPCs) que estão ativamente na equipe ao final do turno (ex: ['Eldon'] ou ['Eldon', 'Grom'] se um novo companheiro se juntou, ou [] se Eldon tiver saído).\n"
        f"- 'skills': Uma lista contendo os nomes (strings) de todas as habilidades ativas do personagem ao final do turno (ex: {skills} ou {skills} mais novas habilidades aprendidas, ou sem as habilidades perdidas). Você deve preservar exatamente a grafia e nomes das habilidades iniciais do turno {skills} a menos que a narrativa descreva explicitamente a perda ou aprendizado de alguma habilidade.\n\n"
        "Garanta que a resposta contenha o bloco JSON limpo para fácil extração sintática."
        f"{style_instruction}"
        f"{actions_instruction}"
        f"{environment_instruction}"
    )

    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
