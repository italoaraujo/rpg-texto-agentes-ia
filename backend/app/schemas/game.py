from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class LLMConfig(BaseModel):
    primary_model: str = Field(default="deepseek-chat", example="deepseek-chat")
    fallback_model: str = Field(default="gpt-4o-mini", example="gpt-4o-mini")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1500, ge=1)

class StartGameRequest(BaseModel):
    player_name: str = Field(..., example="Arthur Pendragon")
    character_class: str = Field(..., example="Guerreiro") # Ex: Guerreiro, Mago, Ladino, Clerigo
    starting_environment: str = Field(default="Masmorra", example="Masmorra")
    short_narrative: bool = Field(default=False, example=False)
    suggest_actions: bool = Field(default=False, example=False)
    llm_config: Optional[LLMConfig] = Field(default_factory=LLMConfig)

class ProcessTurnRequest(BaseModel):
    game_id: UUID = Field(..., example="d3b07384-d113-4c22-9b21-4b13a35a74bb")
    player_action: str = Field(..., example="Empunhar minha espada e atacar o Orc à minha frente.")

class PlayerState(BaseModel):
    health: int = Field(..., example=85)
    max_health: int = Field(default=100, example=100)
    inventory: List[str] = Field(default_factory=list, example=["Espada de Bronze", "Pocao de Cura P"])
    alive: bool = Field(default=True)

class TokenUsage(BaseModel):
    prompt: int = Field(default=0, example=1200)
    completion: int = Field(default=0, example=350)
    total: int = Field(default=0, example=1550)

class TelemetryMetadata(BaseModel):
    active_model: str = Field(..., example="deepseek-chat")
    fallback_triggered: bool = Field(default=False)
    response_time_seconds: float = Field(..., example=2.45)
    tokens_consumed: TokenUsage

class GameStateResponse(BaseModel):
    game_id: UUID
    narrative: str = Field(..., example="Você desfere um golpe certeiro no Orc...")
    current_environment: str = Field(default="Masmorra", example="Masmorra")
    suggested_actions: Optional[List[str]] = Field(default=None, example=["Atacar", "Defender", "Fugir"])
    player_state: PlayerState
    telemetry_metadata: TelemetryMetadata

class ErrorResponse(BaseModel):
    error_code: str = Field(..., example="TIMEOUT_FALLBACK_FAILED")
    message: str = Field(..., example="O serviço de IA falhou...")
    details: Optional[str] = Field(None, example="Connection timed out.")
