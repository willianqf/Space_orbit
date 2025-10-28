# settings.py
import pygame
pygame.font.init() # Inicializa as fontes aqui

# --- ADICIONE ESTE BLOCO PARA CARREGAR A LOGO ---
LOGO_JOGO = None
try:
    LOGO_JOGO = pygame.image.load("Space_Orbit.png")
    print("Logo carregada com sucesso!") # Mensagem de confirmação
except pygame.error as e:
    print(f"Erro ao carregar a imagem 'Space_Orbit.png': {e}")
    LOGO_JOGO = None # Garante que é None se falhar
# --- FIM DO BLOCO DA LOGO ---


# 1. Configurações da Tela e Mapa
LARGURA_TELA_INICIAL = 800
# 1. Configurações da Tela e Mapa
LARGURA_TELA_INICIAL = 800
ALTURA_TELA_INICIAL = 600
MAP_WIDTH = 8000
MAP_HEIGHT = 8000
MAP_RECT = pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT)

# 2. Constantes do Jogo
MAX_OBSTACULOS = 50
MAX_INIMIGOS = 15
MAX_BOTS = 6 # Valor inicial padrão de bots
MAX_BOTS_LIMITE_SUPERIOR = 10 # Limite máximo configurável
MAX_MOTHERSHIPS = 2 # <-- ADICIONE ESTA LINHA
MAX_VIDAS_COLETAVEIS = 12
SPAWN_DIST_MIN = LARGURA_TELA_INICIAL * 0.8
SPAWN_DIST_MAX = LARGURA_TELA_INICIAL * 1.5
DESPAWN_DIST = LARGURA_TELA_INICIAL * 2.0
MAX_DISTANCIA_TIRO = 1000
TARGET_CLICK_SIZE = 150
MAX_TARGET_LOCK_DISTANCE = 1000
MAX_BOSS_CONGELANTE = 1                   # Limite de spawn
HP_BOSS_CONGELANTE = 400                  # Dobro do Mothership (200 * 2)
PONTOS_BOSS_CONGELANTE = 300              # Triplo do Mothership (100 * 3)
COOLDOWN_TIRO_CONGELANTE = 15000          # 15 segundos
DURACAO_CONGELAMENTO = 3000             # 3 segundos
COOLDOWN_SPAWN_MINION_CONGELANTE = 10000 # 10 segundos
MAX_MINIONS_CONGELANTE = 6                # Máximo de minions ativos
HP_MINION_CONGELANTE = 10
PONTOS_MINION_CONGELANTE = 5              # Recompensa por minion
VELOCIDADE_MINION_CONGELANTE = 4.5        # Velocidade do minion (ajuste se necessário)
COOLDOWN_TIRO_MINION_CONGELANTE = 1500    # Cooldown de tiro do minion

# 3. Constantes da Nave e Upgrades
MAX_NIVEL_ESCUDO = 5
DURACAO_FX_ESCUDO = 150
REDUCAO_DANO_POR_NIVEL = 15
MAX_NIVEL_DANO = 5
MAX_NIVEL_MOTOR = 5
RASTRO_MAX_PARTICULAS = 20
RASTRO_DURACAO = 200
RASTRO_TAMANHO_INICIAL = 4
VIDA_COLETADA_CURA = 1

# 4. Constantes da Loja
CUSTO_BASE_MOTOR = 20
CUSTO_BASE_DANO = 75
CUSTO_BASE_AUXILIAR = 50
CUSTO_BASE_MAX_VIDA = 50
CUSTO_BASE_ESCUDO = 60

# 5. Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
AZUL_NAVE = (0, 150, 255)
PONTA_NAVE = (255, 255, 0)
VERMELHO_TIRO = (255, 50, 50)
CINZA_OBSTACULO = (128, 128, 128)
CORES_ESTRELAS = [(50, 50, 50), (100, 100, 100)]
VERDE_AUXILIAR = (0, 255, 100)
VERDE_VIDA = (0, 255, 0)
VERMELHO_VIDA_FUNDO = (255, 0, 0)
LARANJA_TIRO_INIMIGO = (255, 150, 0)
VERMELHO_PERSEGUIDOR = (200, 0, 0)
ROXO_ATIRADOR_RAPIDO = (150, 0, 200)
AMARELO_BOMBA = (200, 200, 0)
CINZA_LOJA_FUNDO = (20, 20, 20, 200)
CINZA_BOTAO_DESLIGADO = (100, 100, 100)
LARANJA_BOT = (255, 120, 0)
MINIMAP_FUNDO = (50, 50, 50, 150)
CIANO_MOTHERSHIP = (0, 200, 200)
CIANO_MINION = (0, 130, 130)
COR_ESCUDO_FX = (150, 200, 255, 200)
VERDE_TIRO_MAX = (0, 255, 100)
COR_RASTRO_MOTOR = (255, 150, 0) # Laranja
LARANJA_RAPIDO = (255, 100, 0)
AZUL_TIRO_RAPIDO = (0, 100, 200)
ROXO_ATORDOADOR = (100, 0, 100)
ROXO_TIRO_LENTO = (200, 0, 255)
VERMELHO_VIDA_COLETAVEL = (255, 20, 20)
AZUL_CONGELANTE = (0, 100, 255)         # Cor do Boss
AZUL_MINION_CONGELANTE = (100, 150, 255) # Cor do Minion
AZUL_TIRO_CONGELANTE = (150, 200, 255)   # Cor do Projétil
# Cor de overlay de pausa
PRETO_TRANSPARENTE_PAUSA = (0, 0, 0, 180)

# 6. Fontes
FONT_PADRAO = pygame.font.SysFont('Arial', 24)
FONT_TITULO = pygame.font.SysFont('Arial', 32, bold=True)
FONT_HUD = pygame.font.SysFont('Arial', 20)
FONT_TERMINAL = pygame.font.SysFont('Consolas', 22)
FONT_BOTAO_LOJA = pygame.font.SysFont('Arial', 18, bold=True)
FONT_RANKING = pygame.font.SysFont('Arial', 16)
FONT_HUD_DETALHES = pygame.font.SysFont('Arial', 16)

# 7. Outros
NUM_ESTRELAS = 150