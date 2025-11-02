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
# --- INÍCIO: MODIFICAÇÃO OBSTÁCULOS ---
OBSTACULO_RAIO_MIN = 20
OBSTACULO_RAIO_MAX = 40
OBSTACULO_PONTOS_MIN = 1
OBSTACULO_PONTOS_MAX = 5
# --- FIM: MODIFICAÇÃO OBSTÁCULOS ---
MAX_INIMIGOS = 25 # <-- Atualizado para 25, como você mencionou
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
COOLDOWN_TIRO_CONGELANTE = 10000          # 10 segundos
DURACAO_CONGELAMENTO = 3000             # 3 segundos
COOLDOWN_SPAWN_MINION_CONGELANTE = 10000 # 10 segundos
MAX_MINIONS_CONGELANTE = 6                # Máximo de minions ativos
HP_MINION_CONGELANTE = 10
PONTOS_MINION_CONGELANTE = 5              # Recompensa por minion
# --- INÍCIO DA MODIFICAÇÃO (VELOCIDADE) ---
VELOCIDADE_MINION_CONGELANTE = 25       # Reduzido de 50 para 4.5
# --- FIM DA MODIFICAÇÃO ---
COOLDOWN_TIRO_MINION_CONGELANTE = 600    # Cooldown de tiro do minion
MINION_CONGELANTE_LEASH_RANGE = 1500 # Distância máxima do BOSS que o minion persegue o alvo
MIN_SPAWN_DIST_ENTRE_NAVES_MAE = 800 # Distância mínima entre Motherships/Bosses

# 3. Constantes da Nave e Upgrades
VELOCIDADE_ROTACAO_NAVE = 5
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
MAX_TOTAL_UPGRADES = 12 # Limite total de upgrades que podem ser comprados

# --- INÍCIO: MODIFICAÇÃO DE DIFICULDADE E CUSTOS ---
# Define os limiares de pontos de score necessários para ganhar 1 ponto de upgrade
PONTOS_LIMIARES_PARA_UPGRADE = [100, 250, 500] # Custo: 100, depois 250, depois 500
# Define o score total em que a dificuldade de upgrade muda
PONTOS_SCORE_PARA_MUDAR_LIMIAR = [500, 2000] # Muda para 250 em 500 pts, muda para 500 em 2000 pts
# Define o custo escalonável para as naves auxiliares
CUSTOS_AUXILIARES = [1, 2, 3, 4] # Custo em PONTOS DE UPGRADE (1ª custa 1, 2ª custa 2, etc)
# --- FIM: MODIFICAÇÃO DE DIFICULDADE E CUSTOS ---


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
FONT_NOME_JOGADOR = pygame.font.SysFont('Arial', 16, bold=True) # <-- ADICIONE ESTA LINHA

# 6.5. Constantes de Áudio 
MAX_DISTANCIA_SOM_AUDIVEL = 1200 # Distância máxima (em pixels) que um som pode ser ouvido
PANNING_RANGE_SOM = 800      # A "largura" da sua audição (para calcular esq/dir)
VOLUME_BASE_TIRO_PLAYER = 0.4  # Volume base (será 0.4 no máximo, caindo para 0)
VOLUME_BASE_TIRO_INIMIGO = 0.3 
VOLUME_BASE_EXPLOSAO_BOSS = 0.7 
VOLUME_BASE_EXPLOSAO_NPC = 0.5 
VOLUME_BASE_TIRO_LASER_LONGO = 0.5
VOLUME_BASE_TIRO_CONGELANTE = 0.6 # <--- ADICIONE ESTA LINHA

# --- INÍCIO: GERAÇÃO DE SONS ---
# Esses sons são gerados e definidos em main.py após a inicialização do mixer
SOM_TIRO_PLAYER = None
SOM_TIRO_INIMIGO_SIMPLES = None
SOM_EXPLOSAO_BOSS = None 
SOM_EXPLOSAO_NPC = None 
SOM_TIRO_LASER_LONGO = None
SOM_TIRO_CONGELANTE = None # <--- ADICIONE ESTA LINHA
# --- FIM: GERAÇÃO DE SONS ---


# 7. Outros
NUM_ESTRELAS = 150