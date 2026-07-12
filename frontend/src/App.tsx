import React, { useState, useRef, useEffect } from 'react'
import { 
  Shield, 
  Sword, 
  Sparkles, 
  User, 
  Users,
  Send, 
  Heart, 
  Briefcase, 
  Activity, 
  Cpu, 
  Clock, 
  RotateCcw 
} from 'lucide-react'

// Interfaces conforme OpenAPI
interface PlayerState {
  health: number;
  max_health: number;
  inventory: string[];
  companions: string[];
  skills: string[];
  alive: boolean;
}

interface TokenUsage {
  prompt: number;
  completion: number;
  total: number;
}

interface TelemetryMetadata {
  active_model: string;
  fallback_triggered: boolean;
  response_time_seconds: number;
  tokens_consumed: TokenUsage;
}

interface NarrativeBlock {
  type: 'player' | 'narrative';
  text: string;
}

export default function App() {
  // Estados de Configuração inicial carregados do localStorage se existirem
  const [screen, setScreen] = useState<'setup' | 'playing'>(() => {
    return localStorage.getItem('rpg_game_id') ? 'playing' : 'setup';
  });
  const [playerName, setPlayerName] = useState(() => {
    return localStorage.getItem('rpg_player_name') || '';
  });
  const [characterClass, setCharacterClass] = useState(() => {
    return localStorage.getItem('rpg_character_class') || '';
  });
  const [shortNarrative, setShortNarrative] = useState(() => {
    const saved = localStorage.getItem('rpg_short_narrative');
    return saved !== null ? saved === 'true' : true;
  });
  const [suggestActions, setSuggestActions] = useState(() => {
    const saved = localStorage.getItem('rpg_suggest_actions');
    return saved !== null ? saved === 'true' : true;
  });
  const [startingCompanion, setStartingCompanion] = useState(() => {
    return localStorage.getItem('rpg_starting_companion') || '';
  });
  const [startingEnvironment, setStartingEnvironment] = useState(() => {
    return localStorage.getItem('rpg_starting_environment') || '';
  });
  const [currentEnvironment, setCurrentEnvironment] = useState(() => {
    return localStorage.getItem('rpg_current_environment') || 'Masmorra';
  });
  
  // Estados da Sessão de Jogo
  const [gameId, setGameId] = useState<string | null>(() => {
    return localStorage.getItem('rpg_game_id');
  });
  const [narrativeHistory, setNarrativeHistory] = useState<NarrativeBlock[]>(() => {
    const saved = localStorage.getItem('rpg_narrative_history');
    return saved ? JSON.parse(saved) : [];
  });
  const [suggestedActions, setSuggestedActions] = useState<string[]>(() => {
    const saved = localStorage.getItem('rpg_suggested_actions');
    return saved ? JSON.parse(saved) : [];
  });
  const [playerState, setPlayerState] = useState<PlayerState>(() => {
    const saved = localStorage.getItem('rpg_player_state');
    return saved ? JSON.parse(saved) : {
      health: 100,
      max_health: 100,
      inventory: [],
      companions: [],
      skills: [],
      alive: true
    };
  });
  const [telemetry, setTelemetry] = useState<TelemetryMetadata | null>(() => {
    const saved = localStorage.getItem('rpg_telemetry');
    return saved ? JSON.parse(saved) : null;
  });
  
  // Estado de Controles de UI
  const [loading, setLoading] = useState(false);
  const [actionInput, setActionInput] = useState('');
  const [connectionError, setConnectionError] = useState(false);
  const [setupStep, setSetupStep] = useState(1);
  const [canSubmit, setCanSubmit] = useState(false);
  const [warning, setWarning] = useState<string | null>(null);

  useEffect(() => {
    if (setupStep === 6) {
      setCanSubmit(false);
      const timer = setTimeout(() => {
        setCanSubmit(true);
      }, 400);
      return () => clearTimeout(timer);
    } else {
      setCanSubmit(false);
    }
  }, [setupStep]);
  
  
  const historyEndRef = useRef<HTMLDivElement>(null);
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Salva o estado de jogo no localStorage sempre que alterado para manter a sessão ativa
  useEffect(() => {
    if (gameId) {
      localStorage.setItem('rpg_game_id', gameId);
      localStorage.setItem('rpg_player_name', playerName);
      localStorage.setItem('rpg_character_class', characterClass);
      localStorage.setItem('rpg_player_state', JSON.stringify(playerState));
      localStorage.setItem('rpg_narrative_history', JSON.stringify(narrativeHistory));
      localStorage.setItem('rpg_short_narrative', String(shortNarrative));
      localStorage.setItem('rpg_suggest_actions', String(suggestActions));
      localStorage.setItem('rpg_suggested_actions', JSON.stringify(suggestedActions));
      localStorage.setItem('rpg_starting_environment', startingEnvironment);
      localStorage.setItem('rpg_current_environment', currentEnvironment);
      localStorage.setItem('rpg_starting_companion', startingCompanion);
      if (telemetry) {
        localStorage.setItem('rpg_telemetry', JSON.stringify(telemetry));
      }
    } else {
      localStorage.removeItem('rpg_game_id');
      localStorage.removeItem('rpg_player_name');
      localStorage.removeItem('rpg_character_class');
      localStorage.removeItem('rpg_player_state');
      localStorage.removeItem('rpg_narrative_history');
      localStorage.removeItem('rpg_short_narrative');
      localStorage.removeItem('rpg_suggest_actions');
      localStorage.removeItem('rpg_suggested_actions');
      localStorage.removeItem('rpg_starting_environment');
      localStorage.removeItem('rpg_current_environment');
      localStorage.removeItem('rpg_starting_companion');
      localStorage.removeItem('rpg_telemetry');
    }
  }, [gameId, playerName, characterClass, playerState, narrativeHistory, telemetry, shortNarrative, suggestActions, suggestedActions, startingEnvironment, currentEnvironment, startingCompanion]);

  // Faz scroll automático no console de narrativa
  useEffect(() => {
    historyEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [narrativeHistory, loading]);

  const classes = [
    { name: 'Guerreiro', icon: '⚔️', desc: 'Mestre no combate corpo a corpo.' },
    { name: 'Mago', icon: '🔮', desc: 'Dominador de magias arcanas.' },
    { name: 'Ladino', icon: '🗡️', desc: 'Especialista em furtividade e astúcia.' },
    { name: 'Clerigo', icon: '🛡️', desc: 'Canalizador de cura e poder sagrado.' }
  ];

  const companions_list = [
    { name: 'Eldon', icon: '👤', desc: 'Arqueólogo cauteloso, especialista em símbolos e ruínas antigas.' },
    { name: 'Grom', icon: '🪓', desc: 'Guerreiro bárbaro impulsivo, destemido e focado em força física.' },
    { name: 'Lyra', icon: '🔮', desc: 'Maga élfica racional, focada em decifrar mistérios e forças mágicas.' },
    { name: 'Nenhum', icon: '❌', desc: 'Começar a aventura inteiramente sozinho.' }
  ];

  const environments = [
    { name: 'Masmorra', icon: '💀', desc: 'Ruínas e masmorras escuras.' },
    { name: 'Floresta', icon: '🌲', desc: 'Bosques densos e segredos.' },
    { name: 'Cidade', icon: '🏰', desc: 'Tavernas de pedra e comércio.' },
    { name: 'Deserto', icon: '🏜️', desc: 'Dunas áridas e sol escaldante.' },
    { name: 'Montanha', icon: '🏔️', desc: 'Picos nevados e gargantas.' },
    { name: 'Pantano', icon: '🕸️', desc: 'Pântanos nevoentos e perigos.' },
    { name: 'Oceano', icon: '🌊', desc: 'Mares misteriosos e barcos.' },
    { name: 'Vulcao', icon: '🌋', desc: 'Rios de lava e cavernas quentes.' },
    { name: 'Ceu', icon: '☁️', desc: 'Ilhas flutuantes e ventos fortes.' }
  ];

  const handleNextStep = () => {
    if (setupStep === 1) {
      if (!playerName.trim()) {
        setWarning('Por favor, defina o nome do seu herói antes de prosseguir!');
        return;
      }
    } else if (setupStep === 2) {
      if (!characterClass) {
        setWarning('Por favor, escolha uma classe para o seu herói!');
        return;
      }
    } else if (setupStep === 3) {
      if (!startingCompanion) {
        setWarning('Por favor, escolha um companheiro inicial!');
        return;
      }
    } else if (setupStep === 4) {
      if (!startingEnvironment) {
        setWarning('Por favor, escolha um ambiente de início!');
        return;
      }
    }
    setWarning(null);
    setSetupStep(prev => prev + 1);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (setupStep < 6) {
      handleNextStep();
    } else {
      if (canSubmit) {
        handleStartGame(e);
      }
    }
  };

  // Inicia o jogo no Backend
  const handleStartGame = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!playerName.trim()) return;

    setLoading(true);
    setConnectionError(false);

    try {
      const response = await fetch(`${API_URL}/game/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_name: playerName,
          character_class: characterClass,
          starting_companion: startingCompanion,
          starting_environment: startingEnvironment,
          short_narrative: shortNarrative,
          suggest_actions: suggestActions
        })
      });

      if (!response.ok) throw new Error('Erro de conexão ao iniciar jogo.');

      const data = await response.json();
      
      setGameId(data.game_id);
      setPlayerState(data.player_state);
      setTelemetry(data.telemetry_metadata);
      setSuggestedActions(data.suggested_actions || []);
      setCurrentEnvironment(data.current_environment);
      setNarrativeHistory([
        { type: 'narrative', text: data.narrative }
      ]);
      setScreen('playing');
    } catch (err) {
      console.error(err);
      setConnectionError(true);
    } finally {
      setLoading(false);
    }
  };

  // Envia a ação do jogador no loop de turnos
  const handleSendAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionInput.trim() || !gameId || loading) return;

    const currentAction = actionInput;
    setActionInput('');
    await handleTriggerSuggestedAction(currentAction);
  };

  // Helper para disparar ações de texto (seja por botão ou formulário de input livre)
  const handleTriggerSuggestedAction = async (actionText: string) => {
    if (loading || !gameId || !playerState.alive) return;

    setLoading(true);
    
    // Adiciona a ação no histórico imediatamente
    setNarrativeHistory(prev => [...prev, { type: 'player', text: actionText }]);

    try {
      const response = await fetch(`${API_URL}/game/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_id: gameId,
          player_action: actionText
        })
      });

      if (!response.ok) {
        if (response.status === 400) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || 'Sessão inválida ou expirada.');
        }
        throw new Error('Erro de conexão no turno.');
      }

      const data = await response.json();
      setPlayerState(data.player_state);
      setTelemetry(data.telemetry_metadata);
      setSuggestedActions(data.suggested_actions || []);
      setCurrentEnvironment(data.current_environment);
      setNarrativeHistory(prev => [...prev, { type: 'narrative', text: data.narrative }]);
    } catch (err: any) {
      console.error(err);
      const isSessionError = err.message && (
        err.message.includes('Sessão inválida') || 
        err.message.includes('não encontrada') ||
        err.message.includes('morto')
      );

      if (isSessionError) {
        setNarrativeHistory(prev => [...prev, { 
          type: 'narrative', 
          text: `[SISTEMA]: A sessão do jogo expirou ou o herói morreu (${err.message}). Retornando à tela inicial em breve...` 
        }]);
        setTimeout(() => {
          handleReset();
        }, 3500);
      } else {
        setNarrativeHistory(prev => [...prev, { 
          type: 'narrative', 
          text: "[SISTEMA]: Falha na conexão com os agentes. Verifique se o backend está online e tente novamente." 
        }]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setScreen('setup');
    setGameId(null);
    setNarrativeHistory([]);
    setSuggestedActions([]);
    setCurrentEnvironment('Masmorra');
    setPlayerName('');
    setCharacterClass('');
    setStartingCompanion('');
    setStartingEnvironment('');
    setTelemetry(null);
    setSetupStep(1);
    setShortNarrative(true);
    setSuggestActions(true);
    setWarning(null);
  };

  // Funções utilitárias de UI
  const getHealthClass = (health: number) => {
    if (health >= 70) return 'healthy';
    if (health >= 30) return 'warning';
    return '';
  };

  const getHeroIcon = (charClass: string) => {
    switch (charClass) {
      case 'Guerreiro': return <Sword size={18} />;
      case 'Mago': return <Sparkles size={18} />;
      case 'Ladino': return <User size={18} />;
      case 'Clerigo': return <Shield size={18} />;
      default: return <Sword size={18} />;
    }
  };

  // Agrupa e conta a quantidade de itens no inventário para exibir
  const getGroupedInventory = (inventory: string[]) => {
    const counts: { [key: string]: number } = {};
    inventory.forEach(item => {
      const match = item.trim().match(/^(\d+)\s+(.+)$/);
      let name = item.trim();
      let qty = 1;
      if (match) {
        qty = parseInt(match[1], 10);
        name = match[2].trim();
      }

      const nameLower = name.toLowerCase();
      if (nameLower.includes('moeda')) {
        name = 'Moeda de Ouro';
      } else if (nameLower.includes('pocao de cura p') || nameLower.includes('poção de cura p') || nameLower.includes('pocão de cura p')) {
        name = 'Pocao de Cura P';
      }

      counts[name] = (counts[name] || 0) + qty;
    });

    return Object.entries(counts).map(([name, count]) => {
      let displayName = name;
      if (count > 1) {
        if (name === 'Moeda de Ouro') displayName = 'Moedas de Ouro';
        else if (name === 'Pocao de Cura P') displayName = 'Poções de Cura P';
      }
      return { name: displayName, count };
    });
  };

  if (screen === 'setup') {
    return (
      <div className="app-container">
        <div className="glass-panel setup-screen">
          <h1 className="setup-title">Crônicas dos Agentes</h1>
          <p className="setup-subtitle">Construa sua lenda no RPG de agentes com DeepSeek & CrewAI</p>
          
          {connectionError && (
            <div style={{
              background: 'rgba(255, 0, 84, 0.1)',
              color: 'var(--accent-red)',
              border: '1px solid rgba(255, 0, 84, 0.2)',
              padding: '12px',
              borderRadius: '8px',
              fontSize: '0.9rem',
              marginBottom: '20px',
              textAlign: 'center'
            }}>
              Não foi possível conectar ao backend na porta 8000. Certifique-se de que os contêineres Docker estão ativos.
            </div>
          )}

          <form onSubmit={handleFormSubmit} className="setup-form">
            {/* Indicador Visual do Passo a Passo */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '32px', position: 'relative' }}>
              {[1, 2, 3, 4, 5, 6].map((stepNum) => (
                <div key={stepNum} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1, zIndex: 2 }}>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: setupStep >= stepNum ? 'var(--accent-purple)' : 'rgba(255, 255, 255, 0.05)',
                    border: `2px solid ${setupStep === stepNum ? 'var(--accent-purple-light)' : 'var(--border-color)'}`,
                    color: setupStep >= stepNum ? '#fff' : 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 'bold',
                    fontSize: '0.85rem',
                    boxShadow: setupStep === stepNum ? '0 0 10px rgba(168, 85, 247, 0.3)' : 'none',
                    transition: 'var(--transition-smooth)',
                    cursor: stepNum < setupStep ? 'pointer' : 'default'
                  }}
                  onClick={() => {
                    if (stepNum < setupStep) {
                      setSetupStep(stepNum);
                      setWarning(null);
                    }
                  }}
                  >
                    {stepNum}
                  </div>
                  <span style={{ fontSize: '0.7rem', color: setupStep >= stepNum ? 'var(--text-main)' : 'var(--text-muted)', marginTop: '6px', fontWeight: setupStep === stepNum ? 600 : 400 }}>
                    {stepNum === 1 ? 'Nome' :
                     stepNum === 2 ? 'Classe' :
                     stepNum === 3 ? 'NPC' :
                     stepNum === 4 ? 'Início' :
                     stepNum === 5 ? 'Configs' : 'Revisão'}
                  </span>
                </div>
              ))}
              <div style={{
                position: 'absolute',
                top: '16px',
                left: '8%',
                right: '8%',
                height: '2px',
                background: 'rgba(255, 255, 255, 0.05)',
                zIndex: 1
              }}>
                <div style={{
                  width: `${((setupStep - 1) / 5) * 100}%`,
                  height: '100%',
                  background: 'var(--accent-purple)',
                  transition: 'var(--transition-smooth)'
                }}></div>
              </div>
            </div>

            {/* Conteúdo do Passo Ativo */}
            {setupStep === 1 && (
              <div className="form-group" style={{ animation: 'fadeIn 0.3s ease-out' }}>
                <label className="form-label">Nome do Herói</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="Ex: Arthur, o Destemido"
                  value={playerName}
                  onChange={(e) => {
                    setPlayerName(e.target.value);
                    if (warning) setWarning(null);
                  }}
                  required
                  maxLength={25}
                  disabled={loading}
                  autoFocus
                  style={warning ? { borderColor: 'var(--accent-red)', boxShadow: '0 0 0 2px rgba(255, 0, 84, 0.15)' } : {}}
                />
                {warning && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-red)', fontSize: '0.85rem', marginTop: '6px', animation: 'fadeIn 0.2s ease-out' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '16px', height: '16px', borderRadius: '50%', background: 'rgba(255, 0, 84, 0.15)', fontSize: '0.75rem', fontWeight: 'bold' }}>!</span>
                    <span>Preencha o nome do seu herói</span>
                  </div>
                )}
              </div>
            )}

            {setupStep === 2 && (
              <div className="form-group" style={{ animation: 'fadeIn 0.3s ease-out' }}>
                <label className="form-label">Classe do Herói</label>
                <div className="class-grid">
                  {classes.map((cls) => (
                    <div 
                      key={cls.name}
                      className={`class-option ${characterClass === cls.name ? 'selected' : ''}`}
                      onClick={() => {
                        if (!loading) {
                          setCharacterClass(cls.name);
                          if (warning) setWarning(null);
                        }
                      }}
                      style={warning ? { borderColor: 'rgba(255, 0, 84, 0.3)' } : {}}
                    >
                      <div className="class-icon">{cls.icon}</div>
                      <div className="class-name">{cls.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        {cls.desc}
                      </div>
                    </div>
                  ))}
                </div>
                {warning && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-red)', fontSize: '0.85rem', marginTop: '10px', animation: 'fadeIn 0.2s ease-out' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '16px', height: '16px', borderRadius: '50%', background: 'rgba(255, 0, 84, 0.15)', fontSize: '0.75rem', fontWeight: 'bold' }}>!</span>
                    <span>Selecione a classe do seu herói</span>
                  </div>
                )}
              </div>
            )}

            {setupStep === 3 && (
              <div className="form-group" style={{ animation: 'fadeIn 0.3s ease-out' }}>
                <label className="form-label">Companheiro Inicial (NPC)</label>
                <div className="class-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(135px, 1fr))' }}>
                  {companions_list.map((npc: { name: string; icon: string; desc: string }) => (
                    <div 
                      key={npc.name}
                      className={`class-option ${startingCompanion === npc.name ? 'selected' : ''}`}
                      onClick={() => {
                        if (!loading) {
                          setStartingCompanion(npc.name);
                          if (warning) setWarning(null);
                        }
                      }}
                      style={{ padding: '14px 10px', ...(warning ? { borderColor: 'rgba(255, 0, 84, 0.3)' } : {}) }}
                    >
                      <div className="class-icon" style={{ fontSize: '1.6rem', marginBottom: '6px' }}>{npc.icon}</div>
                      <div className="class-name" style={{ fontSize: '0.85rem' }}>{npc.name === 'Nenhum' ? 'Sem Companheiro' : npc.name}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px', textAlign: 'center', lineHeight: '1.2' }}>
                        {npc.desc}
                      </div>
                    </div>
                  ))}
                </div>
                {warning && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-red)', fontSize: '0.85rem', marginTop: '10px', animation: 'fadeIn 0.2s ease-out' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '16px', height: '16px', borderRadius: '50%', background: 'rgba(255, 0, 84, 0.15)', fontSize: '0.75rem', fontWeight: 'bold' }}>!</span>
                    <span>Selecione seu companheiro inicial</span>
                  </div>
                )}
              </div>
            )}

            {setupStep === 4 && (
              <div className="form-group" style={{ animation: 'fadeIn 0.3s ease-out' }}>
                <label className="form-label">Ambiente de Início</label>
                <div className="class-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))' }}>
                  {environments.map((env) => (
                    <div 
                      key={env.name}
                      className={`class-option ${startingEnvironment === env.name ? 'selected' : ''}`}
                      onClick={() => {
                        if (!loading) {
                          setStartingEnvironment(env.name);
                          if (warning) setWarning(null);
                        }
                      }}
                      style={{ padding: '14px 10px', ...(warning ? { borderColor: 'rgba(255, 0, 84, 0.3)' } : {}) }}
                    >
                      <div className="class-icon" style={{ fontSize: '1.6rem', marginBottom: '6px' }}>{env.icon}</div>
                      <div className="class-name" style={{ fontSize: '0.85rem' }}>{env.name}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px', textAlign: 'center', lineHeight: '1.2' }}>
                        {env.desc}
                      </div>
                    </div>
                  ))}
                </div>
                {warning && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-red)', fontSize: '0.85rem', marginTop: '10px', animation: 'fadeIn 0.2s ease-out' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '16px', height: '16px', borderRadius: '50%', background: 'rgba(255, 0, 84, 0.15)', fontSize: '0.75rem', fontWeight: 'bold' }}>!</span>
                    <span>Selecione o ambiente de início</span>
                  </div>
                )}
              </div>
            )}

            {setupStep === 5 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', animation: 'fadeIn 0.3s ease-out' }}>
                <label className="form-label">Configurações de Partida</label>
                
                {/* Toggle para Narrativa Curta e Dinâmica */}
                <div 
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '16px',
                    borderRadius: '12px',
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-color)',
                    cursor: 'pointer',
                    transition: 'var(--transition-smooth)'
                  }}
                  onClick={() => !loading && setShortNarrative(!shortNarrative)}
                >
                  <input 
                    type="checkbox" 
                    id="shortNarrative" 
                    checked={shortNarrative} 
                    onChange={(e) => setShortNarrative(e.target.checked)}
                    style={{ 
                      width: '18px', 
                      height: '18px', 
                      cursor: 'pointer', 
                      accentColor: 'var(--accent-purple)' 
                    }}
                    disabled={loading}
                  />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', cursor: 'pointer' }}>
                    <label 
                      htmlFor="shortNarrative" 
                      className="form-label" 
                      style={{ margin: 0, cursor: 'pointer', fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-main)' }}
                    >
                      Narrativa Curta e Dinâmica
                    </label>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      A Crew responderá com diálogos e ações físicas mais ágeis e diretas.
                    </span>
                  </div>
                </div>

                {/* Toggle para Sugestão de Alternativas */}
                <div 
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '16px',
                    borderRadius: '12px',
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-color)',
                    cursor: 'pointer',
                    transition: 'var(--transition-smooth)'
                  }}
                  onClick={() => !loading && setSuggestActions(!suggestActions)}
                >
                  <input 
                    type="checkbox" 
                    id="suggestActions" 
                    checked={suggestActions} 
                    onChange={(e) => setSuggestActions(e.target.checked)}
                    style={{ 
                      width: '18px', 
                      height: '18px', 
                      cursor: 'pointer', 
                      accentColor: 'var(--accent-purple)' 
                    }}
                    disabled={loading}
                  />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', cursor: 'pointer' }}>
                    <label 
                      htmlFor="suggestActions" 
                      className="form-label" 
                      style={{ margin: 0, cursor: 'pointer', fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-main)' }}
                    >
                      Sugerir Alternativas de Ação
                    </label>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      O narrador fornecerá de 3 a 5 opções pré-definidas clicáveis a cada turno.
                    </span>
                  </div>
                </div>
              </div>
            )}

            {setupStep === 6 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', animation: 'fadeIn 0.3s ease-out' }}>
                <label className="form-label">Confirmar Escolhas do Herói</label>
                
                <div style={{
                  background: 'rgba(255, 255, 255, 0.01)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '12px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '10px' }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Nome:</span>
                    <span style={{ fontWeight: 600, color: 'var(--accent-purple-light)', fontSize: '0.9rem' }}>{playerName}</span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '10px' }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Classe:</span>
                    <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.9rem' }}>
                      {characterClass === 'Guerreiro' ? '⚔️ Guerreiro' :
                       characterClass === 'Mago' ? '🔮 Mago' :
                       characterClass === 'Ladino' ? '🗡️ Ladino' : '🛡️ Clérigo'}
                    </span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '10px' }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Companheiro Inicial:</span>
                    <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.9rem' }}>
                      {startingCompanion === 'Nenhum' ? 'Sem Companheiro (❌)' : startingCompanion}
                    </span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '10px' }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Ambiente de Início:</span>
                    <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {startingEnvironment === 'Floresta' ? '🌲 Floresta' :
                       startingEnvironment === 'Cidade' ? '🏰 Cidade' :
                       startingEnvironment === 'Deserto' ? '🏜️ Deserto' :
                       startingEnvironment === 'Montanha' ? '🏔️ Montanha' :
                       startingEnvironment === 'Pantano' ? '🕸️ Pântano' :
                       startingEnvironment === 'Oceano' ? '🌊 Oceano' :
                       startingEnvironment === 'Vulcao' ? '🌋 Vulcão' :
                       startingEnvironment === 'Ceu' ? '☁️ Céu' : '💀 Masmorra'}
                    </span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Opções da Narrativa:</span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '6px' }}>
                      <span style={{
                        fontSize: '0.75rem',
                        background: 'rgba(157, 78, 221, 0.08)',
                        color: 'var(--accent-purple-light)',
                        border: '1px solid rgba(157, 78, 221, 0.15)',
                        padding: '4px 8px',
                        borderRadius: '6px'
                      }}>
                        {shortNarrative ? 'Narrativa Curta e Dinâmica' : 'Narrativa Longa'}
                      </span>
                      <span style={{
                        fontSize: '0.75rem',
                        background: 'rgba(0, 245, 212, 0.08)',
                        color: 'var(--accent-cyan)',
                        border: '1px solid rgba(0, 245, 212, 0.15)',
                        padding: '4px 8px',
                        borderRadius: '6px'
                      }}>
                        {suggestActions ? 'Sugestão de Ações' : 'Sem Sugestões'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Botões de Ação do Passo a Passo */}
            <div style={{ display: 'flex', gap: '12px', marginTop: '32px' }}>
              {setupStep > 1 && (
                <button 
                  type="button" 
                  onClick={() => {
                    setSetupStep(prev => prev - 1);
                    setWarning(null);
                  }} 
                  className="start-button" 
                  style={{ background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-color)', color: 'var(--text-main)', flex: 1 }}
                  disabled={loading}
                >
                  Voltar
                </button>
              )}
              {setupStep < 6 ? (
                <button 
                  type="button" 
                  onClick={handleNextStep} 
                  className="start-button"
                  style={{ flex: 2 }}
                >
                  Avançar
                </button>
              ) : (
                <button type="submit" className="start-button" style={{ flex: 2 }} disabled={loading || !playerName.trim() || !canSubmit}>
                  {loading ? (
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
                      <div className="spinner"></div>
                      Invocando a Crew...
                    </div>
                  ) : 'Iniciar Aventura'}
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="glass-panel app-header">
        <div className="brand">
          <span style={{ fontSize: '1.8rem' }}>⚔️</span>
          <div>
            <h1 className="brand-title">Crônicas dos Agentes</h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Mesa RPG orquestrada por IA</p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div className="connection-badge">
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'currentColor' }}></div>
            Mestre Online
          </div>
          <button 
            onClick={handleReset} 
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-main)',
              borderRadius: '8px',
              padding: '6px 12px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.85rem'
            }}
          >
            <RotateCcw size={14} /> Novo Jogo
          </button>
        </div>
      </header>

      {/* Grid Central */}
      <div className="game-grid">
        {/* Coluna do Console (Narrativa) */}
        <main className="glass-panel console-area">
          {/* Banner de Ambiente Geográfico Contextual */}
          <div 
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'rgba(255, 255, 255, 0.01)',
              borderBottom: '1px solid var(--border-color)',
              padding: '16px 24px',
              borderLeft: `4px solid ${
                currentEnvironment === 'Floresta' ? '#38b000' :
                currentEnvironment === 'Cidade' ? '#00f5d4' :
                currentEnvironment === 'Deserto' ? '#ffb703' :
                currentEnvironment === 'Montanha' ? '#adb5bd' :
                currentEnvironment === 'Pantano' ? '#9d4edd' :
                currentEnvironment === 'Oceano' ? '#3a86ff' :
                currentEnvironment === 'Vulcao' ? '#ff0054' :
                currentEnvironment === 'Ceu' ? '#8ecae6' : '#ef4444'
              }`,
              borderRadius: '16px 16px 0 0'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '2rem' }}>
                {currentEnvironment === 'Floresta' ? '🌲' :
                 currentEnvironment === 'Cidade' ? '🏰' :
                 currentEnvironment === 'Deserto' ? '🏜️' :
                 currentEnvironment === 'Montanha' ? '🏔️' :
                 currentEnvironment === 'Pantano' ? '🕸️' :
                 currentEnvironment === 'Oceano' ? '🌊' :
                 currentEnvironment === 'Vulcao' ? '🌋' :
                 currentEnvironment === 'Ceu' ? '☁️' : '💀'}
              </span>
              <div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.08em' }}>
                  Ambiente Atual
                </div>
                <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {currentEnvironment}
                </h3>
              </div>
            </div>
            <span 
              style={{
                fontSize: '0.75rem',
                color: 'var(--text-muted)',
                fontStyle: 'italic',
                background: 'rgba(255,255,255,0.03)',
                padding: '4px 10px',
                borderRadius: '20px',
                border: '1px solid var(--border-color)'
              }}
            >
              {currentEnvironment === 'Floresta' ? 'Sussurros Selvagens' :
               currentEnvironment === 'Cidade' ? 'Bastião do Comércio' :
               currentEnvironment === 'Deserto' ? 'Terras Secas' :
               currentEnvironment === 'Montanha' ? 'Picos Eternos' :
               currentEnvironment === 'Pantano' ? 'Águas Estagnadas' :
               currentEnvironment === 'Oceano' ? 'Mar Revolto' :
               currentEnvironment === 'Vulcao' ? 'Fúria da Terra' :
               currentEnvironment === 'Ceu' ? 'Firmamento Arcano' : 'Masmorras da Morte'}
            </span>
          </div>

          <div className="narrative-history">
            {narrativeHistory.map((block, idx) => (
              <div key={idx} className="narrative-block">
                {block.type === 'player' ? (
                  <div>
                    <div className="player-action-log">
                      <span>👤 {playerName} tenta:</span>
                    </div>
                    <p className="narrative-text" style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>
                      "{block.text}"
                    </p>
                  </div>
                ) : (
                  <div>
                    <div style={{ 
                      fontFamily: 'var(--font-display)', 
                      fontWeight: 600, 
                      color: 'var(--accent-purple-light)',
                      marginBottom: '8px',
                      fontSize: '0.9rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}>
                      <span>📜 Resolvido pela Crew:</span>
                    </div>
                    <p className="narrative-text">{block.text}</p>
                  </div>
                )}
              </div>
            ))}
            
            {loading && (
              <div className="narrative-block">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-purple-light)' }}>
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                  <span style={{ fontSize: '0.9rem', fontStyle: 'italic' }}>
                    O Mestre e Eldon estão decidindo seu destino...
                  </span>
                </div>
              </div>
            )}
            <div ref={historyEndRef} />
          </div>

          {/* Alternativas de Ação Sugeridas */}
          {!loading && playerState.alive && suggestedActions.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px', padding: '0 8px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Opções Rápidas de Ação:
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {suggestedActions.map((action, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleTriggerSuggestedAction(action)}
                    style={{
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid var(--border-color)',
                      color: 'var(--text-main)',
                      borderRadius: '8px',
                      padding: '8px 14px',
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                      textAlign: 'left',
                      transition: 'var(--transition-smooth)'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(168, 85, 247, 0.1)';
                      e.currentTarget.style.borderColor = 'var(--accent-purple-light)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
                      e.currentTarget.style.borderColor = 'var(--border-color)';
                    }}
                  >
                    {idx + 1} - {action}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Form de Ação */}
          <form onSubmit={handleSendAction} className="input-area">
            <input 
              type="text" 
              className="action-input"
              placeholder={playerState.alive ? "Descreva sua ação física ou diálogo aqui..." : "Você caiu em combate. Inicie um novo jogo."}
              value={actionInput}
              onChange={(e) => setActionInput(e.target.value)}
              disabled={loading || !playerState.alive}
              maxLength={150}
              required
            />
            <button type="submit" className="send-button" disabled={loading || !actionInput.trim() || !playerState.alive}>
              {loading ? <div className="spinner"></div> : <><Send size={16} /> Enviar</>}
            </button>
          </form>
        </main>

        {/* Coluna da Direita (Sidebar) */}
        <aside className="sidebar">
          {/* Card de Status */}
          <div className="glass-panel status-card">
            <h2 className="status-title">
              <Heart size={18} style={{ color: 'var(--accent-red)' }} />
              Status do Herói
            </h2>
            
            <div className="player-info">
              <span className="player-name">{playerName}</span>
              <span className="player-class" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                {getHeroIcon(characterClass)}
                {characterClass}
              </span>
            </div>

            {/* Health Gauge */}
            <div className="health-container">
              <div className="health-header">
                <span>Vida Corporal</span>
                <span style={{ fontWeight: 'bold' }}>
                  {playerState.health} / {playerState.max_health} PV
                </span>
              </div>
              <div className="health-bar-bg">
                <div 
                  className={`health-bar-fill ${getHealthClass(playerState.health)}`}
                  style={{ width: `${(playerState.health / playerState.max_health) * 100}%` }}
                ></div>
              </div>
              {!playerState.alive && (
                <div style={{ color: 'var(--accent-red)', fontSize: '0.8rem', marginTop: '6px', fontWeight: 600 }}>
                  💀 FIM DE JOGO
                </div>
              )}
            </div>

            {/* Companheiros da Equipe */}
            <div style={{ marginBottom: '20px' }}>
              <div className="health-header" style={{ marginBottom: '12px' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontWeight: 600 }}>
                  <Users size={16} />
                  Companheiros da Equipe
                </span>
              </div>
              <div className="companions-list" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {playerState.companions && playerState.companions.length > 0 ? (
                  playerState.companions.map((npc: string, idx: number) => (
                    <div 
                      key={idx} 
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        background: 'rgba(255, 255, 255, 0.02)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '10px',
                        padding: '10px 14px',
                        fontSize: '0.88rem',
                        transition: 'var(--transition-smooth)',
                        cursor: 'default'
                      }}
                      onMouseEnter={(e: React.MouseEvent<HTMLDivElement>) => {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                        e.currentTarget.style.borderColor = 'var(--accent-purple-light)';
                        e.currentTarget.style.boxShadow = '0 0 10px rgba(168, 85, 247, 0.12)';
                      }}
                      onMouseLeave={(e: React.MouseEvent<HTMLDivElement>) => {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
                        e.currentTarget.style.borderColor = 'var(--border-color)';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontSize: '1.1rem' }}>👤</span>
                        <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{npc}</span>
                      </div>
                      <span style={{ fontSize: '0.72rem', background: 'rgba(168, 85, 247, 0.15)', color: 'var(--accent-purple-light)', padding: '2px 8px', borderRadius: '12px', fontWeight: 600 }}>NPC</span>
                    </div>
                  ))
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontStyle: 'italic', padding: '10px 14px', border: '1px dashed var(--border-color)', borderRadius: '10px', textAlign: 'center' }}>
                    Nenhum companheiro no grupo.
                  </div>
                )}
              </div>
            </div>

            {/* Habilidades do Herói */}
            <div style={{ marginBottom: '20px' }}>
              <div className="health-header" style={{ marginBottom: '12px' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontWeight: 600 }}>
                  <Sparkles size={16} style={{ color: 'var(--accent-gold)' }} />
                  Habilidades do Herói
                </span>
              </div>
              <div className="skills-list" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {playerState.skills && playerState.skills.length > 0 ? (
                  playerState.skills.map((skill: string, idx: number) => (
                    <div 
                      key={idx} 
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        background: 'rgba(255, 255, 255, 0.02)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '10px',
                        padding: '10px 14px',
                        fontSize: '0.88rem',
                        transition: 'var(--transition-smooth)',
                        cursor: 'default'
                      }}
                      onMouseEnter={(e: React.MouseEvent<HTMLDivElement>) => {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                        e.currentTarget.style.borderColor = 'var(--accent-gold)';
                        e.currentTarget.style.boxShadow = '0 0 10px rgba(245, 158, 11, 0.12)';
                      }}
                      onMouseLeave={(e: React.MouseEvent<HTMLDivElement>) => {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
                        e.currentTarget.style.borderColor = 'var(--border-color)';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontSize: '1.1rem', color: 'var(--accent-gold)' }}>⚡</span>
                        <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{skill}</span>
                      </div>
                      <span style={{ fontSize: '0.72rem', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-gold)', padding: '2px 8px', borderRadius: '12px', fontWeight: 600 }}>Ativa</span>
                    </div>
                  ))
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontStyle: 'italic', padding: '10px 14px', border: '1px dashed var(--border-color)', borderRadius: '10px', textAlign: 'center' }}>
                    Nenhuma habilidade aprendida.
                  </div>
                )}
              </div>
            </div>

            {/* Inventário */}
            <div>
              <div className="health-header" style={{ marginBottom: '12px' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontWeight: 600 }}>
                  <Briefcase size={16} />
                  Inventário de Mochila
                </span>
              </div>
              <div className="inventory-list" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {playerState.inventory.length > 0 ? (
                  getGroupedInventory(playerState.inventory).map((item, idx) => (
                    <div 
                      key={idx} 
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        background: 'rgba(255, 255, 255, 0.02)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '10px',
                        padding: '10px 14px',
                        fontSize: '0.88rem',
                        transition: 'var(--transition-smooth)',
                        cursor: 'default'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                        e.currentTarget.style.borderColor = 'var(--accent-purple-light)';
                        e.currentTarget.style.boxShadow = '0 0 10px rgba(168, 85, 247, 0.12)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)';
                        e.currentTarget.style.borderColor = 'var(--border-color)';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontSize: '1.1rem' }}>
                          {item.name.toLowerCase().includes('pocao') ? '🧪' : 
                           item.name.toLowerCase().includes('espada') || item.name.toLowerCase().includes('adaga') || item.name.toLowerCase().includes('maca') ? '⚔️' :
                           item.name.toLowerCase().includes('escudo') || item.name.toLowerCase().includes('simbolo') ? '🛡️' : 
                           item.name.toLowerCase().includes('cajado') || item.name.toLowerCase().includes('grimorio') ? '🔮' : '📦'}
                        </span>
                        <span style={{ color: 'var(--text-main)', fontWeight: 500 }}>{item.name}</span>
                      </div>
                      <span 
                        style={{
                          background: 'linear-gradient(135deg, var(--accent-purple), var(--accent-pink))',
                          color: '#fff',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '3px 8px',
                          borderRadius: '20px',
                          marginLeft: 'auto',
                          boxShadow: '0 2px 5px rgba(168, 85, 247, 0.3)'
                        }}
                      >
                        x{item.count}
                      </span>
                    </div>
                  ))
                ) : (
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic', paddingLeft: '4px' }}>
                    Sua mochila está vazia.
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Card de Telemetria */}
          <div className="glass-panel telemetry-card">
            <h2 className="status-title">
              <Activity size={18} style={{ color: 'var(--accent-cyan)' }} />
              Métricas da IA
            </h2>

            {telemetry ? (
              <div className="telemetry-grid">
                <div className="telemetry-item">
                  <span className="telemetry-label">Modelo Ativo</span>
                  <span className={`telemetry-value ${telemetry.fallback_triggered ? 'fallback-model' : 'active-model'}`}>
                    {telemetry.active_model}
                  </span>
                </div>

                <div className="telemetry-item">
                  <span className="telemetry-label">Fallback Acionado</span>
                  <span 
                    className="telemetry-value" 
                    style={{ color: telemetry.fallback_triggered ? 'var(--accent-gold)' : 'var(--text-muted)' }}
                  >
                    {telemetry.fallback_triggered ? '⚠️ SIM' : 'NÃO'}
                  </span>
                </div>

                <div className="telemetry-item">
                  <span className="telemetry-label">Tempo de Resposta</span>
                  <span className="telemetry-value" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} />
                    {telemetry.response_time_seconds}s
                  </span>
                </div>

                <div className="telemetry-item" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '8px' }}>
                  <span className="telemetry-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Cpu size={12} />
                    Tokens Faturados (Turno)
                  </span>
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(3, 1fr)', 
                    width: '100%', 
                    gap: '8px', 
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.8rem',
                    textAlign: 'center'
                  }}>
                    <div style={{ background: 'rgba(255,255,255,0.02)', padding: '6px', borderRadius: '4px' }}>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Prompt</div>
                      <div style={{ fontWeight: 600 }}>{telemetry.tokens_consumed.prompt}</div>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.02)', padding: '6px', borderRadius: '4px' }}>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Comp.</div>
                      <div style={{ fontWeight: 600 }}>{telemetry.tokens_consumed.completion}</div>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.02)', padding: '6px', borderRadius: '4px' }}>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Total</div>
                      <div style={{ fontWeight: 600, color: 'var(--accent-purple-light)' }}>
                        {telemetry.tokens_consumed.total}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                Aguardando primeiro turno para coletar telemetria.
              </span>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
