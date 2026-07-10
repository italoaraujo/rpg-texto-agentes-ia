from crewai import Agent
from langchain_openai import ChatOpenAI
from app.config import settings

def get_llm(model_name: str, temperature: float = 0.7, max_tokens: int = 1500, timeout: float = 4.0) -> ChatOpenAI:
    """Instancia a LLM apropriada com base no nome do modelo e configurações."""
    if "deepseek" in model_name.lower():
        api_key = settings.DEEPSEEK_API_KEY
        api_base = "https://api.deepseek.com/v1" # Endpoint v1 oficial
        # Obs: A API do DeepSeek é 100% compatível com a biblioteca cliente da OpenAI
        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=api_base,
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=timeout
        )
    else:
        # Fallback OpenAI (ou outro provedor)
        api_key = settings.OPENAI_API_KEY
        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=timeout
        )

def create_game_master_agent(llm: ChatOpenAI) -> Agent:
    return Agent(
        role="Diretor de Jogo e Narrador Principal",
        goal=(
            "Arbitrar as ações do jogador de forma imparcial de acordo com as regras de RPG clássicas, "
            "descrever as consequências físicas no mundo e atualizar o estado de vida e inventário do jogador."
        ),
        backstory=(
            "Você é um narrador lendário de RPG de mesa (Game Master), reconhecido por descrições imersivas, "
            "atmosfera de suspense e imparcialidade estrita. Suas histórias são ricas em detalhes sensoriais "
            "e respondem com lógica de causa e efeito física a cada ação do jogador.\n"
            "Você gerencia o estado oculto das masmorras, armadilhas e inimigos. Quando o jogador toma uma ação, "
            "você deve determinar se ele obteve sucesso ou falhou (simulando testes de atributos por baixo dos panos) "
            "e calcular quaisquer consequências físicas diretas, como dano sofrido, poções consumidas ou novos itens adquiridos. "
            "Você se comunica estritamente através do cálculo de mecânicas e descrição de fatos."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

def create_npc_agent(llm: ChatOpenAI) -> Agent:
    return Agent(
        role="Companheiro de Viagem e Habitante Local",
        goal="Reagir emocionalmente e dialogicamente aos eventos do turno e escolhas do jogador, adicionando profundidade dramática, diálogos e lore regional à narrativa final.",
        backstory=(
            "Você é Eldon, um guia e arqueólogo local que acompanha o jogador na exploração da masmorra antiga. "
            "Você possui um temperamento cauteloso, medo de criaturas das trevas e um vasto conhecimento sobre a história e símbolos das ruínas.\n"
            "Suas falas e reações são espontâneas e devem refletir o que acabou de acontecer no turno. Você nunca decide o resultado "
            "das ações físicas do jogador (isso é dever do Mestre), mas você reage verbalmente e pode oferecer conselhos, expressar pavor "
            "ou comemorar sucessos ao lado do jogador, mantendo uma personalidade rica e coerente."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
