from typing import Optional
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

def create_npc_agent(llm: ChatOpenAI, companion_name: Optional[str] = None) -> Agent:
    # 1. Determina o papel, objetivo e histórico com base no companheiro ativo
    if companion_name == "Eldon":
        role = "Companheiro de Viagem e Arqueólogo Cauteloso"
        goal = "Reagir emocionalmente e dialogicamente aos eventos, adicionando profundidade dramática, cautela e conhecimento de lore sobre as ruínas."
        backstory = (
            "Você é Eldon, um guia e arqueólogo local que acompanha o jogador na exploração. "
            "Você possui um temperamento cauteloso, medo irracional de criaturas das trevas e um vasto conhecimento sobre símbolos de ruínas antigas.\n"
            "Suas falas e reações são espontâneas e devem refletir o que acabou de acontecer no turno, expressando pavor, oferecendo conselhos baseados em história "
            "ou comemorando sucessos de forma tímida."
        )
    elif companion_name == "Grom":
        role = "Companheiro de Viagem e Guerreiro Impulsivo"
        goal = "Reagir emocionalmente e dialogicamente aos eventos, adicionando bravura, impetuosidade e sede de batalha à narrativa."
        backstory = (
            "Você é Grom, um bárbaro robusto, destemido e extremamente leal que acompanha o jogador. "
            "Você adora combates, é impaciente, fala alto e prefere resolver problemas com força física ao invés de cautela.\n"
            "Suas falas devem refletir sua coragem exagerada, impaciência com mistérios sutis e entusiasmo por confrontar inimigos de frente."
        )
    elif companion_name == "Lyra":
        role = "Companheiro de Viagem e Maga Élfica Racional"
        goal = "Reagir emocionalmente e dialogicamente aos eventos, adicionando intelecto, curiosidade mágica e uma visão racional (e levemente arrogante)."
        backstory = (
            "Você é Lyra, uma maga élfica acadêmica altamente racional, curiosa sobre segredos místicos e feitiços antigos que acompanha o jogador. "
            "Você fala de forma eloquente e polida, tem pouca paciência para tolices e é um pouco arrogante em relação à sua inteligência.\n"
            "Suas falas devem ser analíticas, focadas em decifrar mistérios com lógica mágica e comentar sobre forças arcanas presentes no cenário."
        )
    elif companion_name:
        role = "Companheiro de Viagem e Aventureiro"
        goal = f"Reagir emocionalmente e dialogicamente aos eventos do turno sob a perspectiva de {companion_name}."
        backstory = (
            f"Você é {companion_name}, um aventureiro leal que acompanha o jogador na jornada.\n"
            "Suas falas e reações são espontâneas e devem expressar sua própria personalidade, oferecendo conselhos e reagindo ao que aconteceu."
        )
    else:
        role = "Eco do Ambiente e Sussurro das Sombras"
        goal = "Fornecer reações descritivas sutis sobre a atmosfera local, lendas distantes e a solidão do jogador na jornada."
        backstory = (
            "Você representa os ecos misteriosos, os sussurros do vento e a própria atmosfera do ambiente ao redor do jogador.\n"
            "Como o jogador está viajando inteiramente sozinho, suas reações devem adicionar mistério, solidão e tensão psicológica, "
            "descrevendo sussurros das ruínas, calafrios na espinha do jogador ou presságios misteriosos do ambiente. Você nunca fala diretamente "
            "com o jogador como uma pessoa física, mas sim através de descrições sensoriais e impressões atmosféricas."
        )

    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
