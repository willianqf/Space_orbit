# main.py
import pygame
import sys
import random
import math
from settings import (MAX_TOTAL_UPGRADES, VOLUME_BASE_EXPLOSAO_BOSS, VOLUME_BASE_EXPLOSAO_NPC, 
                      VOLUME_BASE_TIRO_LASER_LONGO, VOLUME_BASE_TIRO_CONGELANTE,
                      VOLUME_BASE_TIRO_INIMIGO, VOLUME_BASE_TIRO_PLAYER
                      )
# 1. Importações dos Módulos
import settings as s 
import multi.pvp_settings as pvp_s # <-- MODIFICAÇÃO: Importa as configs PVP
from camera import Camera
from projectiles import Projetil, ProjetilInimigo, ProjetilInimigoRapido, ProjetilTeleguiadoLento, ProjetilCongelante, ProjetilTeleguiadoJogador
from entities import Obstaculo, NaveRegeneradora 
from enemies import (InimigoPerseguidor, InimigoAtiradorRapido, InimigoBomba, InimigoMinion,
                     InimigoMothership, InimigoRapido, InimigoTiroRapido, InimigoAtordoador,
                     BossCongelante, MinionCongelante, 
                     set_global_enemy_references)
from effects import Explosao 
from ships import (Player, NaveBot, NaveAuxiliar, Nave, set_global_ship_references, 
                   tocar_som_posicional) 
import ui
from pause_menu import PauseMenu
from settings import VIDA_POR_NIVEL

# --- ETAPA 1: IMPORTAÇÃO DO MÓDULO DE REDE ---
from Redes.network_client import NetworkClient

# --- ETAPA 2: IMPORTAÇÃO DO MÓDULO DE EVENTOS ---
from event_handler import EventHandler

# --- ETAPA 3: IMPORTAÇÃO DO MÓDULO DE LÓGICA ---
from game_logic import GameLogic

# --- ETAPA 4: IMPORTAÇÃO DO MÓDULO DE RENDERIZAÇÃO ---
from renderer import Renderer
# --- FIM: IMPORTAÇÃO ---

# <-- MODIFICAÇÃO: A importação do 'pvp_manager' foi REMOVIDA daqui -->

# 2. Inicialização do Pygame e Tela
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init() 
pygame.mixer.set_num_channels(32)

# --- (GERAÇÃO DE SONS - Sem alterações) ---
try:
    caminho_som_tiro = "sons/tiro.wav" 
    s.SOM_TIRO_PLAYER = pygame.mixer.Sound(caminho_som_tiro)
    print(f"Som '{caminho_som_tiro}' carregado com sucesso!")
    caminho_som_tiro_npc = "sons/tiro_npc.wav" 
    s.SOM_TIRO_INIMIGO_SIMPLES = pygame.mixer.Sound(caminho_som_tiro_npc)
    print(f"Som '{caminho_som_tiro_npc}' carregado com sucesso!")
    caminho_som_explosao_boss = "sons/explosao_boss_inimigo.wav"
    s.SOM_EXPLOSAO_BOSS = pygame.mixer.Sound(caminho_som_explosao_boss)
    print(f"Som '{caminho_som_explosao_boss}' carregado com sucesso!")
    caminho_som_explosao_npc = "sons/explosão_npcs.wav" 
    s.SOM_EXPLOSAO_NPC = pygame.mixer.Sound(caminho_som_explosao_npc)
    print(f"Som '{caminho_som_explosao_npc}' carregado com sucesso!")
    caminho_som_laser_longo = "sons/laser_tiro_longo.wav"
    s.SOM_TIRO_LASER_LONGO = pygame.mixer.Sound(caminho_som_laser_longo)
    print(f"Som '{caminho_som_laser_longo}' carregado com sucesso!")
    caminho_som_congelante = "sons/congelar_tiro.wav"
    s.SOM_TIRO_CONGELANTE = pygame.mixer.Sound(caminho_som_congelante)
    print(f"Som '{caminho_som_congelante}' carregado com sucesso!")
except pygame.error as e:
    print(f"[ERRO] Erro ao carregar um som: {e}")
    s.SOM_TIRO_PLAYER = None; s.SOM_TIRO_INIMIGO_SIMPLES = None
    s.SOM_EXPLOSAO_BOSS = None; s.SOM_EXPLOSAO_NPC = None 
    s.SOM_TIRO_LASER_LONGO = None; s.SOM_TIRO_CONGELANTE = None
except Exception as e:
    print(f"[ERRO] Erro inesperado ao carregar sons: {e}")
    s.SOM_TIRO_PLAYER = None; s.SOM_TIRO_INIMIGO_SIMPLES = None
    s.SOM_EXPLOSAO_BOSS = None; s.SOM_EXPLOSAO_NPC = None 
    s.SOM_TIRO_LASER_LONGO = None; s.SOM_TIRO_CONGELANTE = None
# --- FIM: GERAÇÃO DE SONS ---

LARGURA_TELA = s.LARGURA_TELA_INICIAL
ALTURA_TELA = s.ALTURA_TELA_INICIAL
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.RESIZABLE)
pygame.display.set_caption("Nosso Jogo de Nave Refatorado")
clock = pygame.time.Clock()

try:
    s.LOGO_JOGO = pygame.image.load("Space_Orbit.png")
    s.LOGO_JOGO = s.LOGO_JOGO.convert_alpha()
    print("Logo carregada com sucesso!") 
    print("Testando se esse é o codigo") # SEU PRINT DE TESTE
except pygame.error as e:
    print(f"Erro ao carregar a imagem 'Space_Orbit.png': {e}")
    s.LOGO_JOGO = None 
    
# 3. Variáveis Globais do Jogo
estado_jogo = "MENU" 
dificuldade_jogo_atual = "Normal"

# --- INSTÂNCIA DO CLIENTE DE REDE (Etapa 1) ---
network_client = NetworkClient()

# 4. Criação da Câmera
camera = Camera(LARGURA_TELA, ALTURA_TELA)

# 5. Grupos de Sprites
grupo_projeteis_player = pygame.sprite.Group()
grupo_projeteis_bots = pygame.sprite.Group()
grupo_projeteis_inimigos = pygame.sprite.Group()
grupo_obstaculos = pygame.sprite.Group()
grupo_inimigos = pygame.sprite.Group() 
grupo_motherships = pygame.sprite.Group() 
grupo_boss_congelante = pygame.sprite.Group()
grupo_bots = pygame.sprite.Group()
grupo_player = pygame.sprite.GroupSingle()
grupo_efeitos_visuais = pygame.sprite.Group() 
grupo_explosoes = grupo_efeitos_visuais      

# 6. Criação do Jogador
nave_player = Player(s.MAP_WIDTH // 2, s.MAP_HEIGHT // 2, nome="Jogador")
grupo_player.add(nave_player)

espectador_dummy_alvo = pygame.sprite.Sprite()
espectador_dummy_alvo.posicao = pygame.math.Vector2(s.MAP_WIDTH // 2, s.MAP_HEIGHT // 2)
espectador_dummy_alvo.rect = pygame.Rect(0, 0, 1, 1)

# --- (Rastreadores de estado online - mantidos) ---
online_projectile_ids_last_frame = set()
online_npcs_last_frame = {}
online_players_last_frame = {}

# 7. Define Referências Globais para Módulos
set_global_enemy_references(grupo_explosoes, grupo_inimigos)
set_global_ship_references(grupo_explosoes)

lista_estrelas = []
# 8. Fundo Estrelado (Movido para o Renderer)
for _ in range(s.NUM_ESTRELAS):
    # --- INÍCIO: CORREÇÃO DO BUG (MAPA PRETO) ---
    # As estrelas devem ser geradas no tamanho do MAPA PVE (8000x8000),
    # não no tamanho da TELA (800x600).
    pos_base = pygame.math.Vector2(random.randint(0, s.MAP_WIDTH), random.randint(0, s.MAP_HEIGHT))
    # --- FIM: CORREÇÃO DO BUG ---
    raio = random.randint(1, 2)
    parallax_fator = raio * 0.1
    lista_estrelas.append((pos_base, raio, parallax_fator))
# 9. Funções Auxiliares (Callbacks para os Handlers)

# --- INÍCIO: MODIFICAÇÃO (Novas Funções PVP) ---

def distribuir_atributos_bot(nave, pontos):
    """
    Distribui aleatoriamente os pontos de atributos para os bots.
    (Esta é uma função auxiliar para reiniciar_jogo_pvp)
    """
    opcoes = ["motor", "dano", "max_health", "escudo"]
    for _ in range(pontos):
        upgrade_escolhido = random.choice(opcoes)
        
        # Tenta comprar, se falhar (ex: nível máximo), tenta outro
        if not nave.comprar_upgrade(upgrade_escolhido):
            # Tenta as outras opções em ordem
            for opt in opcoes:
                if nave.comprar_upgrade(opt):
                    break
    
    print(f"[{nave.nome}] Atributos PVP distribuídos.")
    # Reseta a vida para o máximo após os upgrades
    nave.vida_atual = nave.max_vida

def reiniciar_jogo_pvp():
    """ Prepara o lobby do PVP, limpando grupos e spawnando naves no centro. """
    # --- INÍCIO: CORREÇÃO (Declaração Global) ---
    global estado_jogo, nave_player, lista_estrelas, renderer
    # --- FIM: CORREÇÃO ---
    
    # 1. Configura o Mapa para PVP (sobrescreve as constantes de settings)
    s.MAP_WIDTH = pvp_s.MAP_WIDTH
    s.MAP_HEIGHT = pvp_s.MAP_HEIGHT
    s.MAP_RECT = pygame.Rect(0, 0, pvp_s.MAP_WIDTH, pvp_s.MAP_HEIGHT)
    
    # --- INÍCIO: MODIFICAÇÃO (Gera Estrelas para o Mapa PVP) ---
    lista_estrelas.clear()
    for _ in range(s.NUM_ESTRELAS):
        pos_base = pygame.math.Vector2(random.randint(0, pvp_s.MAP_WIDTH), random.randint(0, pvp_s.MAP_HEIGHT))
        raio = random.randint(1, 2)
        parallax_fator = raio * 0.1
        lista_estrelas.append((pos_base, raio, parallax_fator))
    
    # Atualiza a lista no renderer
    renderer.lista_estrelas = lista_estrelas
    print(f"Geradas {s.NUM_ESTRELAS} estrelas para o mapa PVP ({pvp_s.MAP_WIDTH}x{pvp_s.MAP_HEIGHT}).")
    # --- FIM: MODIFICAÇÃO ---
    
    # 2. Reseta o estado global
    game_globals["jogador_esta_vivo_espectador"] = False
    game_globals["alvo_espectador"] = None
    game_globals["alvo_espectador_nome"] = None
    game_globals["spectator_overlay_hidden"] = False
    camera.set_zoom(1.0) 

    print("Iniciando Lobby PVP...")

    # 3. Limpa todos os grupos
    for group in game_groups.values():
        group.empty()

    # 4. Spawna o Jogador Humano
    nave_player.nome = game_globals["nome_jogador_input"].strip() if game_globals["nome_jogador_input"].strip() else "Jogador"
    pos_spawn = pvp_s.SPAWN_LOBBY # Spawna no centro (Lobby)
    
    # Reseta o player
    nave_player.posicao = pygame.math.Vector2(pos_spawn.x, pos_spawn.y)
    nave_player.rect.center = nave_player.posicao
    nave_player.grupo_auxiliares_ativos.empty()
    nave_player.lista_todas_auxiliares = [] 
    for pos in Nave.POSICOES_AUXILIARES:
        nova_aux = NaveAuxiliar(nave_player, pos)
        nave_player.lista_todas_auxiliares.append(nova_aux)
    
    # Reseta status e dá os pontos de atributo
    nave_player.pontos = 0
    nave_player.nivel_motor = 1
    nave_player.nivel_dano = 1
    nave_player.nivel_max_vida = 1
    nave_player.nivel_escudo = 0
    nave_player.nivel_aux = 0 
    nave_player.velocidade_movimento_base = 4 + (nave_player.nivel_motor * 0.5)
    nave_player.max_vida = VIDA_POR_NIVEL[nave_player.nivel_max_vida]
    nave_player.vida_atual = nave_player.max_vida
    nave_player.pontos_upgrade_disponiveis = pvp_s.PONTOS_ATRIBUTOS_INICIAIS # <--- PONTOS!
    nave_player.total_upgrades_feitos = 0
    nave_player._pontos_acumulados_para_upgrade = 0
    nave_player._indice_limiar = 0
    nave_player._limiar_pontos_atual = s.PONTOS_LIMIARES_PARA_UPGRADE[0]
    nave_player.alvo_selecionado = None
    nave_player.posicao_alvo_mouse = None
    nave_player.ultimo_hit_tempo = 0
    nave_player.tempo_fim_lentidao = 0
    nave_player.tempo_fim_congelamento = 0
    nave_player.rastro_particulas = []
    nave_player.parar_regeneracao() 
    nave_player.tempo_spawn_protecao_input = pygame.time.get_ticks() + 200
    
    grupo_player.add(nave_player) # Adiciona ao grupo principal
    
    # 5. Spawna os Bots (para teste)
    for i in range(1, pvp_s.MAX_JOGADORES_PVP):
        # Spawna perto do jogador para o lobby
        pos_bot = pygame.math.Vector2(pos_spawn.x + random.randint(-50, 50), pos_spawn.y + random.randint(-50, 50))
        bot = NaveBot(pos_bot.x, pos_bot.y, "Dificil") # Bots no difícil
        bot.nome = f"BotPVP_{i}"
        
        # Dá os pontos de atributo aos bots
        bot.pontos_upgrade_disponiveis = pvp_s.PONTOS_ATRIBUTOS_INICIAIS
        distribuir_atributos_bot(bot, pvp_s.PONTOS_ATRIBUTOS_INICIAIS)
        
        grupo_bots.add(bot)

    # 6. Adiciona alguns obstáculos
    for _ in range(15):
        x = random.randint(100, pvp_s.MAP_WIDTH - 100)
        y = random.randint(100, pvp_s.MAP_HEIGHT - 100)
        raio = random.randint(s.OBSTACULO_RAIO_MIN, s.OBSTACULO_RAIO_MAX)
        grupo_obstaculos.add(Obstaculo(x, y, raio))
        
    estado_jogo = "PVP_LOBBY"
    game_globals["estado_jogo"] = "PVP_LOBBY"

# --- FIM: Novas Funções (PVP) -
# --- FIM: Novas Funções (PVP) ---


def reiniciar_jogo(pos_spawn=None, dificuldade="Normal"): 
    """ Prepara o jogo PVE, limpando grupos e resetando o jogador. """
    # --- INÍCIO: CORREÇÃO (Declaração Global) ---
    global estado_jogo, nave_player, dificuldade_jogo_atual, lista_estrelas, renderer
    # --- FIM: CORREÇÃO ---
    
    # --- INÍCIO: MODIFICAÇÃO (Restaura Mapa PVE) ---
    s.MAP_WIDTH = pvp_s.PVE_MAP_WIDTH
    s.MAP_HEIGHT = pvp_s.PVE_MAP_HEIGHT
    s.MAP_RECT = pygame.Rect(0, 0, s.MAP_WIDTH, s.MAP_HEIGHT)
    
    # --- INÍCIO: MODIFICAÇÃO (Gera Estrelas para o Mapa PVE) ---
    lista_estrelas.clear()
    for _ in range(s.NUM_ESTRELAS):
        pos_base = pygame.math.Vector2(random.randint(0, s.MAP_WIDTH), random.randint(0, s.MAP_HEIGHT))
        raio = random.randint(1, 2)
        parallax_fator = raio * 0.1
        lista_estrelas.append((pos_base, raio, parallax_fator))
    
    # Atualiza a lista no renderer
    renderer.lista_estrelas = lista_estrelas
    print(f"Geradas {s.NUM_ESTRELAS} estrelas para o mapa PVE ({s.MAP_WIDTH}x{s.MAP_HEIGHT}).")
    # --- FIM: MODIFICAÇÃO ---
    # --- FIM: MODIFICAÇÃO (Restaura Mapa PVE) ---
    
    game_globals["jogador_esta_vivo_espectador"] = False
    game_globals["alvo_espectador"] = None
    game_globals["alvo_espectador_nome"] = None
    game_globals["spectator_overlay_hidden"] = False # <-- ADICIONADO (Reset)
    camera.set_zoom(1.0) 

    print("Reiniciando o Jogo PVE...")
    
    dificuldade_jogo_atual = dificuldade 
    game_globals["dificuldade_selecionada"] = dificuldade 
    print(f"Iniciando jogo na dificuldade: {dificuldade_jogo_atual}")

    if network_client.is_connected():
        nave_player.nome = network_client.get_my_name()
    else:
        nave_player.nome = game_globals["nome_jogador_input"].strip() if game_globals["nome_jogador_input"].strip() else "Jogador"
    
    # Limpa grupos (já limpo em reiniciar_jogo_pvp, mas seguro garantir)
    for group in game_groups.values():
        group.empty()

    spawn_x, spawn_y = 0, 0
    if pos_spawn:
        spawn_x, spawn_y = pos_spawn
        print(f"Spawnando em posição definida pelo servidor: ({spawn_x}, {spawn_y})")
    else:
        print("Spawnando em posição aleatória (Modo Offline)...")
        margem_spawn = 100
        spawn_x = random.randint(margem_spawn, s.MAP_WIDTH - margem_spawn)
        spawn_y = random.randint(margem_spawn, s.MAP_HEIGHT - margem_spawn)
        
    nave_player.posicao = pygame.math.Vector2(spawn_x, spawn_y)
    nave_player.rect.center = nave_player.posicao
    
    nave_player.grupo_auxiliares_ativos.empty()
    nave_player.lista_todas_auxiliares = [] 
    for pos in Nave.POSICOES_AUXILIARES:
        nova_aux = NaveAuxiliar(nave_player, pos)
        nave_player.lista_todas_auxiliares.append(nova_aux)
    nave_player.pontos = 0; nave_player.nivel_motor = 1; nave_player.nivel_dano = 1
    nave_player.nivel_max_vida = 1; nave_player.nivel_escudo = 0; nave_player.nivel_aux = 0 
    nave_player.velocidade_movimento_base = 4 + (nave_player.nivel_motor * 0.5)
    nave_player.max_vida = VIDA_POR_NIVEL[nave_player.nivel_max_vida]
    nave_player.vida_atual = nave_player.max_vida
    nave_player.pontos_upgrade_disponiveis = 0 # <-- PVE começa com 0
    nave_player.total_upgrades_feitos = 0
    nave_player._pontos_acumulados_para_upgrade = 0; nave_player._indice_limiar = 0
    nave_player._limiar_pontos_atual = s.PONTOS_LIMIARES_PARA_UPGRADE[0]
    nave_player.alvo_selecionado = None; nave_player.posicao_alvo_mouse = None
    nave_player.ultimo_hit_tempo = 0; nave_player.tempo_fim_lentidao = 0
    nave_player.tempo_fim_congelamento = 0; nave_player.rastro_particulas = []
    nave_player.parar_regeneracao() 
    nave_player.tempo_spawn_protecao_input = pygame.time.get_ticks() + 200
    
    grupo_player.add(nave_player) # <-- MODIFICAÇÃO: Adiciona o player de volta

    if pos_spawn is None:
        print("Gerando entidades (Obstáculos, Bots)...")
        for _ in range(20): spawnar_obstaculo(nave_player.posicao)
        grupo_bots.empty()
        for _ in range(game_globals["max_bots_atual"]): 
            spawnar_bot(nave_player.posicao, dificuldade_jogo_atual)
    
    estado_jogo = "JOGANDO"

def respawn_player_offline(nave):
    global estado_jogo
    
    # --- INÍCIO: MODIFICAÇÃO (Restaura Mapa PVE) ---
    # Garante que o respawn offline seja sempre no mapa PVE
    s.MAP_WIDTH = pvp_s.PVE_MAP_WIDTH
    s.MAP_HEIGHT = pvp_s.PVE_MAP_HEIGHT
    s.MAP_RECT = pygame.Rect(0, 0, s.MAP_WIDTH, s.MAP_HEIGHT)
    # --- FIM: MODIFICAÇÃO ---
    
    game_globals["jogador_esta_vivo_espectador"] = False
    game_globals["alvo_espectador"] = None
    game_globals["spectator_overlay_hidden"] = False # <-- ADICIONADO (Reset)
    camera.set_zoom(1.0)
    print("Respawnando jogador (Offline)...")
    pos_referencia_bots = [bot.posicao for bot in grupo_bots]
    pos_referencia_inimigos = [inimigo.posicao for inimigo in grupo_inimigos]
    pos_referencias_todas = pos_referencia_bots + pos_referencia_inimigos
    pos_referencia_spawn = pygame.math.Vector2(s.MAP_WIDTH // 2, s.MAP_HEIGHT // 2)
    if pos_referencias_todas: pos_referencia_spawn = random.choice(pos_referencias_todas)
    spawn_x, spawn_y = calcular_posicao_spawn(pos_referencia_spawn)
    nave.posicao = pygame.math.Vector2(spawn_x, spawn_y)
    nave.rect.center = nave.posicao
    print(f"Jogador respawnou em ({int(spawn_x)}, {int(spawn_y)})")
    nave.grupo_auxiliares_ativos.empty()
    nave.lista_todas_auxiliares = [] 
    for pos in Nave.POSICOES_AUXILIARES:
        nova_aux = NaveAuxiliar(nave, pos)
        nave.lista_todas_auxiliares.append(nova_aux)
    nave.pontos = 0; nave.nivel_motor = 1; nave.nivel_dano = 1; nave.nivel_max_vida = 1
    nave.nivel_escudo = 0; nave.nivel_aux = 0 
    nave.velocidade_movimento_base = 4 + (nave.nivel_motor * 0.5)
    nave.max_vida = VIDA_POR_NIVEL[nave.nivel_max_vida] 
    nave.vida_atual = nave.max_vida
    nave.pontos_upgrade_disponiveis = 0; nave.total_upgrades_feitos = 0
    nave._pontos_acumulados_para_upgrade = 0; nave._indice_limiar = 0
    nave._limiar_pontos_atual = s.PONTOS_LIMIARES_PARA_UPGRADE[0]
    nave.alvo_selecionado = None; nave.posicao_alvo_mouse = None
    nave.ultimo_hit_tempo = 0; nave.tempo_fim_lentidao = 0
    nave.tempo_fim_congelamento = 0; nave.rastro_particulas = []
    nave.parar_regeneracao() 
    nave_player.tempo_spawn_protecao_input = pygame.time.get_ticks() + 200
    estado_jogo = "JOGANDO"

def resetar_para_menu():
    global estado_jogo
    
    # --- INÍCIO: MODIFICAÇÃO (Restaura Mapa PVE) ---
    s.MAP_WIDTH = pvp_s.PVE_MAP_WIDTH
    s.MAP_HEIGHT = pvp_s.PVE_MAP_HEIGHT
    s.MAP_RECT = pygame.Rect(0, 0, s.MAP_WIDTH, s.MAP_HEIGHT)
    # --- FIM: MODIFICAÇÃO ---
    
    game_globals["jogador_pediu_para_espectar"] = False
    game_globals["jogador_esta_vivo_espectador"] = False
    game_globals["alvo_espectador"] = None
    game_globals["alvo_espectador_nome"] = None
    camera.set_zoom(1.0)
    print("Voltando ao Menu Principal...")
    nave_player.parar_regeneracao() 
    grupo_bots.empty(); grupo_inimigos.empty(); grupo_motherships.empty()
    grupo_boss_congelante.empty(); grupo_projeteis_bots.empty()
    grupo_projeteis_inimigos.empty(); grupo_projeteis_player.empty() 
    grupo_obstaculos.empty(); grupo_efeitos_visuais.empty() 
    network_client.close()
    estado_jogo = "MENU"

def spawnar_boss_congelante(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia, dist_min_do_jogador=s.SPAWN_DIST_MAX * 1.2)
    novo_boss = BossCongelante(x, y); grupo_inimigos.add(novo_boss); grupo_boss_congelante.add(novo_boss)
def calcular_posicao_spawn(pos_referencia, dist_min_do_jogador=s.SPAWN_DIST_MIN):
    while True:
        x = random.uniform(0, s.MAP_WIDTH); y = random.uniform(0, s.MAP_HEIGHT)
        pos_spawn = pygame.math.Vector2(x, y)
        if pos_referencia.distance_to(pos_spawn) > dist_min_do_jogador: return (x, y) 
def spawnar_inimigo_aleatorio(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia); chance = random.random(); inimigo = None
    if chance < 0.05: inimigo = InimigoBomba(x, y)
    elif chance < 0.10: inimigo = InimigoTiroRapido(x, y)
    elif chance < 0.15: inimigo = InimigoAtordoador(x, y)
    elif chance < 0.35: inimigo = InimigoAtiradorRapido(x, y)
    elif chance < 0.55: inimigo = InimigoRapido(x, y)
    else: inimigo = InimigoPerseguidor(x, y)
    if inimigo: grupo_inimigos.add(inimigo)
def spawnar_bot(pos_referencia, dificuldade="Normal"):
    x, y = calcular_posicao_spawn(pos_referencia); novo_bot = NaveBot(x, y, dificuldade); grupo_bots.add(novo_bot)
def spawnar_mothership(pos_referencia):
    for _ in range(10):
        x, y = calcular_posicao_spawn(pos_referencia); pos_potencial = pygame.math.Vector2(x, y)
        muito_perto = False
        for mothership_existente in grupo_motherships:
            try:
                if pos_potencial.distance_to(mothership_existente.posicao) < s.MIN_SPAWN_DIST_ENTRE_NAVES_MAE:
                    muito_perto = True; break 
            except ValueError: muito_perto = True; break
        if not muito_perto:
            nova_mothership = InimigoMothership(x, y); grupo_inimigos.add(nova_mothership); grupo_motherships.add(nova_mothership); return 
def spawnar_obstaculo(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia); raio = random.randint(s.OBSTACULO_RAIO_MIN, s.OBSTACULO_RAIO_MAX)
    novo_obstaculo = Obstaculo(x, y, raio); grupo_obstaculos.add(novo_obstaculo)
def spawnar_boss_congelante_perto(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia, dist_min_do_jogador=s.SPAWN_DIST_MIN)
    novo_boss = BossCongelante(x, y); grupo_inimigos.add(novo_boss); grupo_boss_congelante.add(novo_boss)

def processar_cheat(comando, nave):
    game_globals["variavel_texto_terminal"] = "" 
    comando_limpo = comando.strip().lower()
    if comando_limpo == "maxpoint": nave.ganhar_pontos(9999)
    elif comando_limpo == "invencivel":
        if isinstance(nave, Player): nave.invencivel = not nave.invencivel
    elif comando_limpo == "maxupgrade":
        if isinstance(nave, Player): nave.pontos_upgrade_disponiveis = MAX_TOTAL_UPGRADES - nave.total_upgrades_feitos
    elif comando_limpo == "spawncongelante": spawnar_boss_congelante_perto(nave_player.posicao)
    else: print(f"[CHEAT] Comando desconhecido: '{comando_limpo}'")

def ciclar_alvo_espectador(game_globals_dict, avancar=True):
    """
    Encontra e define o próximo alvo de espectador (Online ou Offline).
    Usado por 'REQ_SPECTATOR' e pelas teclas Q/E.
    (Esta versão foi corrigida para aceitar o dicionário de estado)
    """
    
    camera.set_zoom(1.0) # Sai do modo zoom ao ciclar
    
    lista_alvos_vivos = []
    lista_nomes_alvos_vivos = [] # for online
    
    if network_client.is_connected():
        game_state = network_client.get_state(); online_players = game_state['players']
        nomes_ordenados = sorted(online_players.keys())
        for nome in nomes_ordenados:
            state = online_players[nome]
            if state.get('hp', 0) > 0:
                lista_alvos_vivos.append({'nome': nome, 'state': state})
                lista_nomes_alvos_vivos.append(nome)
    else: 
        # --- INÍCIO: MODIFICAÇÃO (Ciclar Alvos PVP) ---
        # Se estiver em um estado PVP, os alvos são os bots + player
        if game_globals_dict["estado_jogo"].startswith("PVP_"):
            if nave_player.vida_atual > 0:
                 lista_alvos_vivos.append(nave_player)
            for bot in grupo_bots:
                if bot.vida_atual > 0:
                    lista_alvos_vivos.append(bot)
        # Senão, é PVE
        else:
            if nave_player.vida_atual > 0:
                 lista_alvos_vivos.append(nave_player)
            for bot in grupo_bots:
                if bot.vida_atual > 0:
                    lista_alvos_vivos.append(bot)
        # --- FIM: MODIFICAÇÃO ---

    if not lista_alvos_vivos:
        print("[Espectador] Nenhum alvo vivo para ciclar.")
        # Usa o dicionário passado como argumento
        game_globals_dict["alvo_espectador"] = None; game_globals_dict["alvo_espectador_nome"] = None; return 
    
    current_index = -1
    # Lê o alvo atual do dicionário
    if network_client.is_connected() and game_globals_dict["alvo_espectador_nome"]:
        if game_globals_dict["alvo_espectador_nome"] in lista_nomes_alvos_vivos:
            current_index = lista_nomes_alvos_vivos.index(game_globals_dict["alvo_espectador_nome"])
            
    # --- INÍCIO DA CORREÇÃO (ValueError) ---
    elif not network_client.is_connected() and game_globals_dict["alvo_espectador"]:
        # Procura o OBJETO (alvo_espectador) na LISTA DE OBJETOS (lista_alvos_vivos)
        if game_globals_dict["alvo_espectador"] in lista_alvos_vivos:
            # USA A LISTA DE OBJETOS 'lista_alvos_vivos'
            current_index = lista_alvos_vivos.index(game_globals_dict["alvo_espectador"]) 
    # --- FIM DA CORREÇÃO ---
            
    if avancar: current_index += 1
    else: current_index -= 1
    current_index %= len(lista_alvos_vivos)
    
    # Define o novo alvo no dicionário
    if network_client.is_connected():
        novo_alvo_dict = lista_alvos_vivos[current_index]
        game_globals_dict["alvo_espectador_nome"] = novo_alvo_dict['nome']
        game_globals_dict["alvo_espectador"] = None
        print(f"[Espectador] Seguindo (Online): {game_globals_dict['alvo_espectador_nome']}")
    else:
        novo_alvo_sprite = lista_alvos_vivos[current_index]
        game_globals_dict["alvo_espectador"] = novo_alvo_sprite
        game_globals_dict["alvo_espectador_nome"] = None
        print(f"[Espectador] Seguindo (Offline): {game_globals_dict['alvo_espectador'].nome}")
# 10. Recalcula Posições Iniciais da UI
ui.recalculate_ui_positions(LARGURA_TELA, ALTURA_TELA)

# --- Instância dos Gerenciadores ---
pause_manager = PauseMenu()

# --- INÍCIO: MODIFICAÇÃO (Callback PVP) ---
main_callbacks_eventos = {
    "reiniciar_jogo": reiniciar_jogo, "resetar_para_menu": resetar_para_menu,
    "processar_cheat": processar_cheat, "ciclar_alvo_espectador": ciclar_alvo_espectador,
    "respawn_player_offline": respawn_player_offline,
    "reiniciar_jogo_pvp": reiniciar_jogo_pvp, # <-- ADICIONADO
}
# --- FIM: MODIFICAÇÃO ---

main_callbacks_logica = {
    "spawnar_bot": spawnar_bot, "spawnar_obstaculo": spawnar_obstaculo,
    "spawnar_inimigo_aleatorio": spawnar_inimigo_aleatorio,
    "spawnar_mothership": spawnar_mothership, "spawnar_boss_congelante": spawnar_boss_congelante,
}

event_handler = EventHandler(network_client, camera, pause_manager, main_callbacks_eventos)
game_logic_handler = GameLogic(main_callbacks_logica)
# --- ETAPA 4: Instância do Renderer ---
renderer = Renderer(tela, camera, pause_manager, network_client, lista_estrelas)

# --- Dicionário de Estado Global do Jogo ---
game_globals = {
    "rodando": True, "nome_jogador_input": "", "input_nome_ativo": False,
    "ip_servidor_input": "127.0.0.1", "input_connect_ativo": "none",
    "dificuldade_selecionada": "Normal", "variavel_texto_terminal": "",
    "jogador_pediu_para_espectar": False, "jogador_esta_vivo_espectador": False,
    "alvo_espectador": None, "alvo_espectador_nome": None,
    "espectador_dummy_alvo": espectador_dummy_alvo,
    "spectator_overlay_hidden": False, # <-- ADICIONADO
    "max_bots_atual": s.MAX_BOTS,
    "LARGURA_TELA": LARGURA_TELA, "ALTURA_TELA": ALTURA_TELA,
    "nave_player": nave_player, # <-- Adiciona a nave player ao dicionário
    
    "pvp_disponivel": True, # <-- MODIFICAÇÃO: PVP está disponível
    
    # --- INÍCIO: MODIFICAÇÃO (Estado PVP) ---
    "pvp_lobby_timer_fim": 0,
    "pvp_partida_timer_fim": 0,
    "pvp_vencedor_nome": "Ninguém",
    # --- FIM: MODIFICAÇÃO ---

    # Referências de grupos
    "grupo_efeitos_visuais": grupo_efeitos_visuais, "grupo_inimigos": grupo_inimigos,
    "grupo_bots": grupo_bots, "grupo_obstaculos": grupo_obstaculos,
}

# --- Dicionário de Grupos de Sprites ---
game_groups = {
    "grupo_projeteis_player": grupo_projeteis_player, "grupo_projeteis_bots": grupo_projeteis_bots,
    "grupo_projeteis_inimigos": grupo_projeteis_inimigos, "grupo_obstaculos": grupo_obstaculos,
    "grupo_inimigos": grupo_inimigos, "grupo_motherships": grupo_motherships,
    "grupo_boss_congelante": grupo_boss_congelante, "grupo_bots": grupo_bots,
    "grupo_player": grupo_player, "grupo_efeitos_visuais": grupo_efeitos_visuais,
    "grupo_explosoes": grupo_explosoes,
}


# --- LOOP PRINCIPAL DO JOGO ---
# main.py

# --- LOOP PRINCIPAL DO JOGO ---
while game_globals["rodando"]:
    
    # 1. Configuração do Frame
    agora = pygame.time.get_ticks() 
    is_online = network_client.is_connected()
    
    # --- INÍCIO DA CORREÇÃO: Captura o tamanho ANTIGO ---
    LARGURA_ANTIGA = LARGURA_TELA
    ALTURA_ANTIGA = ALTURA_TELA
    # --- FIM DA CORREÇÃO ---

    # 2. Checagem de Desconexão Inesperada
    if not network_client.listener_thread_running and network_client.connection_status == "CONNECTED":
        if game_globals["jogador_pediu_para_espectar"]:
            print("[Thread de Rede] Desconexão por modo espectador. A entrar em espectador (offline).")
            estado_jogo = "ESPECTADOR"
            nave_player.vida_atual = 0 
            network_client.close() 
            game_globals["jogador_pediu_para_espectar"] = False 
        else:
            print("[AVISO] Thread de rede morreu! Voltando ao Menu.")
            resetar_para_menu(); estado_jogo = "MENU"
    
    # 3. Processar Eventos (Irá atualizar LARGURA_TELA e ALTURA_TELA se houver resize)
    game_state_eventos = game_globals.copy()
    game_state_eventos["estado_jogo"] = estado_jogo
    game_state_eventos["agora"] = agora
    game_state_eventos["is_online"] = is_online
    
    novos_estados = event_handler.processar_eventos(game_state_eventos)
    
    game_globals.update(novos_estados)
    estado_jogo = game_globals["estado_jogo"]
    LARGURA_TELA = game_globals["LARGURA_TELA"]; ALTURA_TELA = game_globals["ALTURA_TELA"]

    if not game_globals["rodando"]: break

    # --- INÍCIO: MODIFICAÇÃO (Estado de transição PVP) ---
    if estado_jogo == "PVP_START":
        print("[MAIN] Estado PVP_START detectado. Iniciando lobby...")
        reiniciar_jogo_pvp() 
        estado_jogo = game_globals["estado_jogo"] # Pega o novo estado ("PVP_LOBBY")
    # --- FIM: MODIFICAÇÃO ---
    
    # --- INÍCIO DA CORREÇÃO: Nova Lógica de Verificação ---
    # Compara o tamanho ANTIGO (antes dos eventos) com o NOVO (depois dos eventos)
    if LARGURA_ANTIGA != LARGURA_TELA or ALTURA_ANTIGA != ALTURA_TELA:
        
        print(f"REDIMENSIONAMENTO DETECTADO! (De {LARGURA_ANTIGA}x{ALTURA_ANTIGA} para {LARGURA_TELA}x{ALTURA_TELA})") # <-- PRINT DE TESTE
        
        # 1. Cria a nova superfície de tela
        tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.RESIZABLE)
        
        # 2. Recalcula a UI (Botões do Menu)
        ui.recalculate_ui_positions(LARGURA_TELA, ALTURA_TELA)
        
        # 3. Redimensiona a Câmera (Mundo do Jogo)
        camera.resize(LARGURA_TELA, ALTURA_TELA)
        
        # 4. Atualiza o Renderer
        renderer.tela = tela 
    # --- FIM DA CORREÇÃO ---
    
    # 4. Lógica de Atualização
    
    # 4a. Atualizar Câmera
    alvo_camera_final = None
    if estado_jogo == "ESPECTADOR":
        target_found = False
        if camera.zoom < 1.0:
            espectador_dummy_alvo.posicao.x = s.MAP_WIDTH / 2; espectador_dummy_alvo.posicao.y = s.MAP_HEIGHT / 2
            alvo_camera_final = espectador_dummy_alvo; target_found = True
        elif is_online and game_globals["alvo_espectador_nome"]:
            game_state_rede = network_client.get_state()
            state = game_state_rede['players'].get(game_globals["alvo_espectador_nome"])
            if state and state.get('hp', 0) > 0:
                espectador_dummy_alvo.posicao = espectador_dummy_alvo.posicao.lerp(pygame.math.Vector2(state['x'], state['y']), 0.5)
                alvo_camera_final = espectador_dummy_alvo; target_found = True
            else: game_globals["alvo_espectador_nome"] = None 
        elif not is_online and game_globals["alvo_espectador"]:
            if game_globals["alvo_espectador"].groups() and game_globals["alvo_espectador"].vida_atual > 0:
                alvo_camera_final = game_globals["alvo_espectador"]; target_found = True
            else: game_globals["alvo_espectador"] = None 
        if not target_found:
            game_globals["alvo_espectador"] = None; game_globals["alvo_espectador_nome"] = None
            teclas = pygame.key.get_pressed()
            velocidade_espectador = 20
            if teclas[pygame.K_w] or teclas[pygame.K_UP]: espectador_dummy_alvo.posicao.y -= velocidade_espectador
            if teclas[pygame.K_s] or teclas[pygame.K_DOWN]: espectador_dummy_alvo.posicao.y += velocidade_espectador
            if teclas[pygame.K_a] or teclas[pygame.K_LEFT]: espectador_dummy_alvo.posicao.x -= velocidade_espectador
            if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]: espectador_dummy_alvo.posicao.x += velocidade_espectador
            meia_largura_tela = LARGURA_TELA / (2 * camera.zoom); meia_altura_tela = ALTURA_TELA / (2 * camera.zoom)
            espectador_dummy_alvo.posicao.x = max(meia_largura_tela, min(espectador_dummy_alvo.posicao.x, s.MAP_WIDTH - meia_largura_tela))
            espectador_dummy_alvo.posicao.y = max(meia_altura_tela, min(espectador_dummy_alvo.posicao.y, s.MAP_HEIGHT - meia_altura_tela))
            alvo_camera_final = espectador_dummy_alvo
    else: 
         if estado_jogo != "PAUSE" and not game_globals["jogador_pediu_para_espectar"]: camera.set_zoom(1.0) 
         alvo_camera_final = nave_player 
    
    # --- INÍCIO: MODIFICAÇÃO (Câmera com Mapa Dinâmico) ---
    # Passa o tamanho ATUAL do mapa (que pode ser 1500 ou 8000) para a câmera
    # (Isso requer uma mudança em camera.py, que faremos no próximo prompt)
    camera.update(alvo_camera_final, s.MAP_WIDTH, s.MAP_HEIGHT)
    # --- FIM: MODIFICAÇÃO ---

    # --- INÍCIO DA MODIFICAÇÃO: Posição do Ouvinte de Áudio ---
    # O ouvinte de áudio é SEMPRE o alvo final da câmera
    posicao_ouvinte_som = alvo_camera_final.posicao
    # --- FIM DA MODIFICAÇÃO ---

    # 4b. Lógica de Jogo (Online/Offline)
    online_players_copy = {}; online_npcs_copy = {}; online_projectiles_copy = []
    
    if estado_jogo not in ["MENU", "GET_NAME", "GET_SERVER_INFO", "MULTIPLAYER_MODE_SELECT"]:
        if is_online:
            game_state_rede = network_client.get_state()
            online_players_copy = game_state_rede['players']
            online_npcs_copy = game_state_rede['npcs']
            online_projectiles_copy = game_state_rede['projectiles']
            MEU_NOME_REDE = network_client.get_my_name()
            my_state = online_players_copy.get(MEU_NOME_REDE)
            
            if my_state:
                nova_pos = pygame.math.Vector2(my_state['x'], my_state['y'])
                if estado_jogo == "JOGANDO" and nave_player.vida_atual > 0: nave_player.posicao = nave_player.posicao.lerp(nova_pos, 0.4)
                nave_player.angulo = my_state['angulo']
                nova_vida = my_state.get('hp', nave_player.vida_atual)
                if (estado_jogo == "ESPECTADOR" or estado_jogo == "PAUSE") and nave_player.vida_atual <= 0 and nova_vida > 0:
                    estado_jogo = "JOGANDO"; nave_player.tempo_spawn_protecao_input = pygame.time.get_ticks() + 200
                    game_globals["jogador_esta_vivo_espectador"] = False; game_globals["jogador_pediu_para_espectar"] = False
                    game_globals["alvo_espectador_nome"] = None; camera.set_zoom(1.0)
                    game_globals["spectator_overlay_hidden"] = False # <-- Reset no respawn
                if nova_vida < nave_player.vida_atual: nave_player.ultimo_hit_tempo = pygame.time.get_ticks()
                is_server_regenerando = my_state.get('esta_regenerando', False)
                if is_server_regenerando and not nave_player.esta_regenerando: nave_player.iniciar_regeneracao(grupo_efeitos_visuais)
                elif not is_server_regenerando and nave_player.esta_regenerando: nave_player.parar_regeneracao()
                nave_player.vida_atual = nova_vida; nave_player.max_vida = my_state.get('max_hp', nave_player.max_vida)
                nave_player.pontos = my_state.get('pontos', nave_player.pontos)
                nave_player.pontos_upgrade_disponiveis = my_state.get('pontos_upgrade_disponiveis', 0)
                nave_player.total_upgrades_feitos = my_state.get('total_upgrades_feitos', 0)
                nave_player.nivel_motor = my_state.get('nivel_motor', 1); nave_player.nivel_dano = my_state.get('nivel_dano', 1)
                nave_player.nivel_max_vida = my_state.get('nivel_max_vida', 1); nave_player.nivel_escudo = my_state.get('nivel_escudo', 0)
                agora_sync = pygame.time.get_ticks()
                if my_state.get('is_lento', False): nave_player.tempo_fim_lentidao = agora_sync + 1000
                if my_state.get('is_congelado', False): nave_player.tempo_fim_congelamento = agora_sync + 1000
                num_aux_servidor = my_state.get('nivel_aux', 0); num_aux_local = len(nave_player.grupo_auxiliares_ativos)
                if num_aux_servidor > num_aux_local:
                    for i in range(num_aux_local, num_aux_servidor):
                        if i < len(nave_player.lista_todas_auxiliares):
                            try:
                                aux = nave_player.lista_todas_auxiliares[i]; offset_rot = aux.offset_pos.rotate(-nave_player.angulo)
                                aux.posicao = nave_player.posicao + offset_rot; aux.rect.center = aux.posicao; aux.angulo = nave_player.angulo
                                nave_player.grupo_auxiliares_ativos.add(aux)
                            except Exception: pass
                elif num_aux_servidor < num_aux_local: nave_player.grupo_auxiliares_ativos.empty()
                nave_player.nivel_aux = num_aux_servidor
                if nave_player.nivel_max_vida > 0 and nave_player.nivel_max_vida < len(VIDA_POR_NIVEL):
                    nave_player.max_vida = VIDA_POR_NIVEL[nave_player.nivel_max_vida]
                else: nave_player.max_vida = my_state.get('max_hp', nave_player.max_vida)
                
                if nave_player.vida_atual <= 0 and estado_jogo == "JOGANDO":
                    if not game_globals["jogador_pediu_para_espectar"]:
                        estado_jogo = "ESPECTADOR"; game_globals["jogador_esta_vivo_espectador"] = False
                        game_globals["alvo_espectador"] = None; game_globals["alvo_espectador_nome"] = None
                        
                        game_globals["spectator_overlay_hidden"] = False # (Correção anterior)
                        
                        espectador_dummy_alvo.posicao = nave_player.posicao.copy()
                        network_client.send("W_UP"); network_client.send("A_UP"); network_client.send("S_UP"); network_client.send("D_UP"); network_client.send("SPACE_UP")
                    else:
                        estado_jogo = "ESPECTADOR"; game_globals["jogador_esta_vivo_espectador"] = True
                        game_globals["alvo_espectador"] = None; game_globals["alvo_espectador_nome"] = None
                        espectador_dummy_alvo.posicao = nave_player.posicao.copy()
            if estado_jogo != "ESPECTADOR": nave_player.rect.center = nave_player.posicao
            
        # --- INÍCIO: MODIFICAÇÃO (Lógica de Alvos PVP) ---
        lista_alvos_naves = []
        if nave_player.vida_atual > 0 and not game_globals["jogador_esta_vivo_espectador"]:
            lista_alvos_naves.append(nave_player)

        # Se for PVP, os alvos são os outros bots/jogadores
        if estado_jogo.startswith("PVP_"):
            lista_alvos_naves.extend([bot for bot in grupo_bots if bot.vida_atual > 0])
            game_globals["lista_alvos_naves"] = lista_alvos_naves
            lista_todos_alvos_para_aux = list(grupo_obstaculos) + lista_alvos_naves
        
        # Senão, é PVE (lógica antiga)
        else:
            lista_alvos_naves.extend([bot for bot in grupo_bots if bot.vida_atual > 0])
            game_globals["lista_alvos_naves"] = lista_alvos_naves 

            if estado_jogo == "JOGANDO" or estado_jogo == "LOJA" or estado_jogo == "TERMINAL":
                 lista_todos_alvos_para_aux = list(grupo_inimigos) + list(grupo_obstaculos) + [nave_player] + list(grupo_bots)
            else:
                lista_todos_alvos_para_aux = list(grupo_inimigos) + list(grupo_obstaculos) + list(grupo_bots)
        # --- FIM: MODIFICAÇÃO ---

        if not is_online:
            
            if estado_jogo not in ["PAUSE"]:
            
                # --- INÍCIO: MODIFICAÇÃO (Chama a lógica PVE ou PVP) ---
                if estado_jogo.startswith("PVP_"):
                    # Roda a lógica de atualização PVP (que criaremos em game_logic.py)
                    novo_estado_jogo = game_logic_handler.update_pvp_logic(game_globals, game_groups, posicao_ouvinte_som)
                    estado_jogo = novo_estado_jogo # Atualiza o estado (ex: se o jogo acabou)
                    game_globals["estado_jogo"] = novo_estado_jogo # Atualiza o global
                
                # Roda a lógica PVE (como era antes)
                elif estado_jogo not in ["PVP_LOBBY", "PVP_COUNTDOWN", "PVP_PLAYING", "PVP_GAME_OVER"]:
                    game_state_logica = game_globals.copy()
                    game_state_logica["estado_jogo"] = estado_jogo
                    game_state_logica["dificuldade_jogo_atual"] = dificuldade_jogo_atual
                    
                    # --- MODIFICAÇÃO: Passa a posição do ouvinte ---
                    novo_estado_jogo = game_logic_handler.update_offline_logic(game_state_logica, game_groups, posicao_ouvinte_som)
                    # --- FIM DA MODIFICAÇÃO ---
                    
                    if novo_estado_jogo == "ESPECTADOR" and estado_jogo != "ESPECTADOR":
                        estado_jogo = "ESPECTADOR"
                        game_globals["jogador_esta_vivo_espectador"] = False
                        game_globals["alvo_espectador"] = None; game_globals["alvo_espectador_nome"] = None
                        
                        game_globals["spectator_overlay_hidden"] = False # (Correção anterior)
                        
                        espectador_dummy_alvo.posicao = nave_player.posicao.copy()
                # --- FIM: MODIFICAÇÃO ---
            
        # --- MODIFICAÇÃO: Passa a posição do ouvinte para os updates dos auxiliares ---
        for bot in grupo_bots: 
            bot.grupo_auxiliares_ativos.update(lista_todos_alvos_para_aux, grupo_projeteis_bots, estado_jogo, nave_player, None, {}, {}, posicao_ouvinte_som)
        if nave_player.vida_atual > 0:
            nave_player.grupo_auxiliares_ativos.update(
                lista_todos_alvos_para_aux, grupo_projeteis_player, estado_jogo, nave_player, 
                network_client.client_socket, online_players_copy, online_npcs_copy, posicao_ouvinte_som     
            )
        # --- FIM DA MODIFICAÇÃO ---
            
        # --- INÍCIO DA CORREÇÃO (BUG DO PAUSE) ---
        # Os efeitos visuais (como explosões) também devem pausar.
        if estado_jogo not in ["PAUSE"]:
            grupo_efeitos_visuais.update() 
        # --- FIM DA CORREÇÃO ---

    # --- INÍCIO: MODIFICAÇÃO (Permite update do player no lobby/countdown) ---
    if estado_jogo in ["JOGANDO", "PVP_LOBBY", "PVP_COUNTDOWN", "PVP_PLAYING"]:
    # --- FIM: MODIFICAÇÃO ---
        if not is_online:
            # --- MODIFICAÇÃO: Passa a posição do ouvinte ---
            nave_player.update(grupo_projeteis_player, camera, None, posicao_ouvinte_som)
            # --- FIM DA MODIFICAÇÃO ---

    # 5. Desenho (Etapa 4)
    online_data = {
        "players": online_players_copy,
        "npcs": online_npcs_copy,
        "projectiles": online_projectiles_copy
    }
    online_trackers = {
        "proj_last_frame": online_projectile_ids_last_frame,
        "npcs_last_frame": online_npcs_last_frame,
        "players_last_frame": online_players_last_frame
    }
    
    # Chamada nova (correta):
    # --- MODIFICAÇÃO: Passa a posição do ouvinte ---
    renderer.draw(estado_jogo, game_globals, game_groups, online_data, 
                  online_trackers, alvo_camera_final, posicao_ouvinte_som)
    # --- FIM DA MODIFICAÇÃO ---


    # 6. Atualização de Trackers (Pós-Desenho)
    if is_online:
        # (online_..._copy foram definidos na seção de lógica)
        online_projectile_ids_last_frame = {p['id'] for p in online_projectiles_copy}
        online_npcs_last_frame = online_npcs_copy
        online_players_last_frame = online_players_copy
    else:
        online_projectile_ids_last_frame.clear()
        online_npcs_last_frame.clear()
        online_players_last_frame.clear()
    
    clock.tick(60)

# 15. Finalização
network_client.close() 
pygame.quit()
sys.exit()