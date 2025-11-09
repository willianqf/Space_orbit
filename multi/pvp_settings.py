# multi/pvp_settings.py
# Configurações específicas do modo PVP (Player vs Player)

import pygame
pygame.font.init()

# --- Configurações do Mapa PVP ---
PVP_MAP_WIDTH = 1500
PVP_MAP_HEIGHT = 1500

# --- Configurações de Jogadores ---
PVP_MAX_JOGADORES = 4
PVP_PONTOS_ATRIBUTOS_INICIAIS = 10

# --- Posições de Spawn (Cantos do Mapa) ---
PVP_SPAWN_POSITIONS = [
    (200, 200),                                      # Canto superior esquerdo
    (PVP_MAP_WIDTH - 200, 200),                      # Canto superior direito
    (200, PVP_MAP_HEIGHT - 200),                     # Canto inferior esquerdo
    (PVP_MAP_WIDTH - 200, PVP_MAP_HEIGHT - 200),    # Canto inferior direito
]

# --- Tempos (em milissegundos) ---
PVP_TEMPO_LOBBY = 30000        # 30 segundos no lobby esperando jogadores
PVP_TEMPO_PARTIDA = 180000     # 3 minutos (180 segundos) de partida

# --- Cores da UI PVP ---
PVP_COR_OVERLAY = (0, 0, 0, 180)           # Fundo dos overlays
PVP_COR_TEXTO_PRINCIPAL = (255, 255, 255)   # Texto principal
PVP_COR_TEXTO_DESTAQUE = (255, 200, 0)      # Texto em destaque (amarelo/dourado)
PVP_COR_CONTAGEM = (255, 50, 50)            # Cor da contagem regressiva (vermelho)
PVP_COR_VENCEDOR = (0, 255, 100)            # Cor do vencedor (verde)

# --- Fontes da UI PVP ---
PVP_FONT_TITULO = pygame.font.SysFont('Arial', 48, bold=True)
PVP_FONT_SUBTITULO = pygame.font.SysFont('Arial', 32)
PVP_FONT_INSTRUCOES = pygame.font.SysFont('Arial', 20)
PVP_FONT_TIMER = pygame.font.SysFont('Arial', 36, bold=True)
PVP_FONT_RANKING = pygame.font.SysFont('Arial', 18, bold=True)

# --- Mensagens da UI ---
PVP_MSG_AGUARDANDO = "Aguardando Jogadores..."
PVP_MSG_INSTRUCOES_LOBBY = "Pressione 'V' para distribuir atributos | ESC para sair"
PVP_MSG_CONTAGEM = "A partida começa em"
PVP_MSG_FIM_TEMPO = "Tempo Esgotado!"
PVP_MSG_VENCEDOR = "Vencedor:"
PVP_MSG_EMPATE = "Empate!"
PVP_MSG_INSTRUCOES_FIM = "Pressione ESC para voltar ao menu"
