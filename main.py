# main.py
import pygame
import sys
import random
import math
import socket
import threading 
from settings import (MAX_TOTAL_UPGRADES, VOLUME_BASE_EXPLOSAO_BOSS, VOLUME_BASE_EXPLOSAO_NPC, 
                      VOLUME_BASE_TIRO_LASER_LONGO, VOLUME_BASE_TIRO_CONGELANTE)
# 1. Importações dos Módulos
import settings as s 
from camera import Camera
from projectiles import Projetil, ProjetilInimigo, ProjetilInimigoRapido, ProjetilTeleguiadoLento
from entities import Obstaculo, VidaColetavel

from projectiles import Projetil, ProjetilInimigo, ProjetilInimigoRapido, ProjetilTeleguiadoLento, ProjetilCongelante 

# Importa as classes de inimigos
from enemies import (InimigoPerseguidor, InimigoAtiradorRapido, InimigoBomba, InimigoMinion,
                     InimigoMothership, InimigoRapido, InimigoTiroRapido, InimigoAtordoador,
                     BossCongelante, MinionCongelante, 
                     set_global_enemy_references)
# Importa as classes de naves
from ships import (Player, NaveBot, NaveAuxiliar, Nave, set_global_ship_references, 
                   tocar_som_posicional) 
# Importa as funções e Rects da UI
import ui

# 2. Inicialização do Pygame e Tela
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init() 
pygame.mixer.set_num_channels(32)

# --- INÍCIO: GERAÇÃO DE SONS ---
# (O código de carregamento de sons permanece o mesmo)
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
    if not s.SOM_TIRO_PLAYER: s.SOM_TIRO_PLAYER = None
    if not s.SOM_TIRO_INIMIGO_SIMPLES: s.SOM_TIRO_INIMIGO_SIMPLES = None
    if not s.SOM_EXPLOSAO_BOSS: s.SOM_EXPLOSAO_BOSS = None 
    if not s.SOM_EXPLOSAO_NPC: s.SOM_EXPLOSAO_NPC = None 
    if not s.SOM_TIRO_LASER_LONGO: s.SOM_TIRO_LASER_LONGO = None
    if not s.SOM_TIRO_CONGELANTE: s.SOM_TIRO_CONGELANTE = None
except Exception as e:
    print(f"[ERRO] Erro inesperado ao carregar sons: {e}")
    s.SOM_TIRO_PLAYER = None
    s.SOM_TIRO_INIMIGO_SIMPLES = None
    s.SOM_EXPLOSAO_BOSS = None 
    s.SOM_EXPLOSAO_NPC = None 
    s.SOM_TIRO_LASER_LONGO = None 
    s.SOM_TIRO_CONGELANTE = None
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
except pygame.error as e:
    print(f"Erro ao carregar a imagem 'Space_Orbit.png': {e}")
    s.LOGO_JOGO = None 
# 3. Variáveis Globais do Jogo
estado_jogo = "MENU" 
variavel_texto_terminal = ""
rodando = True
max_bots_atual = s.MAX_BOTS 

# --- Variáveis de Nome e Rede ---
nome_jogador_input = "" 
input_nome_ativo = False
LIMITE_MAX_NOME = 16 

ip_servidor_input = "127.0.0.1" 
input_connect_ativo = "none" 
LIMITE_MAX_IP = 24 

client_socket = None 

# --- INÍCIO DA MODIFICAÇÃO (Estado de Rede Global) ---
listener_thread_running = False 
listener_thread_object = None # Variável que guarda a thread

MEU_NOME_REDE = "" # O nosso nome confirmado pelo servidor

# Dicionário para guardar o estado dos jogadores
online_players_states = {}
# Lista para guardar os projéteis
online_projectiles = [] 
# Dicionário para guardar os NPCs
online_npcs = {} # Formato: { "npc_id_1": {"x": 0, "y": 0, "angulo": 0, "tipo": "..."} }

network_state_lock = threading.Lock() 
network_buffer = "" 
# --- FIM DA MODIFICAÇÃO ---

# 4. Criação da Câmera
camera = Camera(LARGURA_TELA, ALTURA_TELA)

# 5. Grupos de Sprites
# (Usados apenas para o modo OFFLINE e efeitos visuais locais)
grupo_projeteis_player = pygame.sprite.Group()
grupo_projeteis_bots = pygame.sprite.Group()
grupo_projeteis_inimigos = pygame.sprite.Group()
grupo_obstaculos = pygame.sprite.Group()
grupo_vidas_coletaveis = pygame.sprite.Group()
grupo_inimigos = pygame.sprite.Group() 
grupo_motherships = pygame.sprite.Group() 
grupo_boss_congelante = pygame.sprite.Group()
grupo_bots = pygame.sprite.Group()
grupo_explosoes = pygame.sprite.Group()
grupo_player = pygame.sprite.GroupSingle()

# 6. Criação do Jogador
nave_player = Player(s.MAP_WIDTH // 2, s.MAP_HEIGHT // 2, nome=nome_jogador_input)
grupo_player.add(nave_player)

# 7. Define Referências Globais para Módulos
set_global_enemy_references(grupo_explosoes, grupo_inimigos)
set_global_ship_references(grupo_explosoes)

# 8. Fundo Estrelado
lista_estrelas = []
for _ in range(s.NUM_ESTRELAS):
    pos_base = pygame.math.Vector2(random.randint(0, LARGURA_TELA), random.randint(0, ALTURA_TELA))
    raio = random.randint(1, 2)
    parallax_fator = raio * 0.1
    lista_estrelas.append((pos_base, raio, parallax_fator))

# 9. Funções Auxiliares (Spawners, Cheats, Reiniciar)

# --- INÍCIO DA MODIFICAÇÃO (Funções de Rede Atualizadas) ---
def network_listener_thread(sock):
    """
    Corre numa thread separada. Escuta por dados do servidor
    e atualiza os estados globais (jogadores, projéteis e NPCs).
    """
    global listener_thread_running, network_buffer, estado_jogo
    global online_players_states, online_projectiles, online_npcs
    
    print("[Thread de Rede] Iniciada.")
    listener_thread_running = True
    network_buffer = "" 
    
    while listener_thread_running:
        try:
            data = sock.recv(4096)
            if not data:
                if listener_thread_running: 
                    print("[Thread de Rede] Conexão perdida (recv vazio).")
                break 
                
            network_buffer += data.decode('utf-8')
            
            while '\n' in network_buffer:
                message, network_buffer = network_buffer.split('\n', 1)
                
                # --- Processa a nova mensagem STATE|...|PROJ|...|NPC|... ---
                if message.startswith("STATE|"):
                    
                    # 1. Divide a mensagem
                    parts = message.split('|')
                    if len(parts) < 6 or parts[0] != 'STATE' or parts[2] != 'PROJ' or parts[4] != 'NPC':
                        print(f"[Thread de Rede] Recebeu mensagem 'STATE' mal formatada: {message}")
                        continue
                    
                    payload_players = parts[1]
                    payload_proj = parts[3]
                    payload_npcs = parts[5]
                    
                    # --- 2. Processa os Jogadores ---
                    new_player_states = {}
                    player_data_list = payload_players.split(';')
                    
                    for player_data in player_data_list:
                        if not player_data: continue 
                        
                        parts_player = player_data.split(':')
                        if len(parts_player) == 4:
                            try:
                                nome = parts_player[0]
                                new_player_states[nome] = {
                                    'x': float(parts_player[1]),
                                    'y': float(parts_player[2]),
                                    'angulo': float(parts_player[3])
                                }
                            except ValueError:
                                pass # Ignora dados mal formatados
                        
                    # --- 3. Processa os Projéteis ---
                    new_projectiles_list = []
                    proj_data_list = payload_proj.split(';')
                    
                    for proj_data in proj_data_list:
                        if not proj_data: continue
                        
                        parts_proj = proj_data.split(':')
                        if len(parts_proj) == 3: # X:Y:TIPO
                            try:
                                new_projectiles_list.append(
                                    (float(parts_proj[0]), float(parts_proj[1]), parts_proj[2])
                                )
                            except ValueError:
                                pass # Ignora dados mal formatados

                    # --- 4. Processa os NPCs ---
                    new_npc_states = {}
                    npc_data_list = payload_npcs.split(';')
                    
                    for npc_data in npc_data_list:
                        if not npc_data: continue
                        
                        # Formato: ID:TIPO:X:Y:ANGULO
                        parts_npc = npc_data.split(':')
                        if len(parts_npc) == 5:
                            try:
                                npc_id = parts_npc[0]
                                new_npc_states[npc_id] = {
                                    'tipo': parts_npc[1],
                                    'x': float(parts_npc[2]),
                                    'y': float(parts_npc[3]),
                                    'angulo': float(parts_npc[4])
                                }
                            except ValueError:
                                pass # Ignora dados mal formatados

                    # --- 5. Atualiza os dicionários globais de forma segura ---
                    with network_state_lock:
                        online_players_states.clear()
                        online_players_states.update(new_player_states)
                        
                        online_projectiles.clear()
                        online_projectiles.extend(new_projectiles_list)
                        
                        online_npcs.clear()
                        online_npcs.update(new_npc_states)
            
        except socket.timeout:
            continue 
        except (socket.error, ConnectionResetError, BrokenPipeError) as e:
            if listener_thread_running: 
                print(f"[Thread de Rede] Erro de socket: {e}")
            break 
        except Exception as e:
            if listener_thread_running:
                print(f"[Thread de Rede] Erro inesperado na thread: {e}")
            break

    # Fim da thread
    print("[Thread de Rede] Encerrada.")
    listener_thread_running = False
    if estado_jogo != "MENU":
         print("[Thread de Rede] A regressar ao Menu Principal.")
         estado_jogo = "MENU"


def tentar_conectar(ip, porta, nome):
    """ Tenta conectar ao servidor, enviar o nome e iniciar a thread de escuta. """
    global client_socket, estado_jogo, nome_jogador_input, listener_thread_object, MEU_NOME_REDE
    
    nome_final = nome.strip() if nome.strip() else "Jogador"
    nome_jogador_input = nome_final 
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5.0) 
        
        print(f"Tentando conectar a {ip}:{porta}...")
        client_socket.connect((ip, porta))
        
        print("Conexão estabelecida. Enviando nome...")
        client_socket.send(nome_final.encode('utf-8'))
        
        print("Aguardando resposta de spawn do servidor...")
        data = client_socket.recv(2048) 
        resposta_servidor = data.decode('utf-8')
        
        # Lê o novo formato "BEMVINDO|NOME_FINAL|X|Y"
        if resposta_servidor.startswith("BEMVINDO|"):
            parts = resposta_servidor.split('|')
            
            if len(parts) == 4: # BEMVINDO, NOME_FINAL, X, Y
                try:
                    MEU_NOME_REDE = parts[1] # Guarda o nosso nome (pode ter sido alterado)
                    spawn_x = int(parts[2])
                    spawn_y = int(parts[3])
                    
                    print(f"Servidor aceitou! Nome: '{MEU_NOME_REDE}'. Spawn: ({spawn_x}, {spawn_y}).")
                    
                    client_socket.settimeout(None) 
                    listener_thread_object = threading.Thread(target=network_listener_thread, args=(client_socket,), daemon=True)
                    listener_thread_object.start()

                    reiniciar_jogo(pos_spawn=(spawn_x, spawn_y))
                    
                    estado_jogo = "JOGANDO" 
                    return True
                
                except ValueError:
                    print(f"[ERRO DE REDE] Servidor enviou dados de spawn inválidos: {resposta_servidor}")
            else:
                print(f"[ERRO DE REDE] Resposta mal formatada do servidor: {resposta_servidor}")
        else:
            print(f"[ERRO DE REDE] Resposta inesperada do servidor: {resposta_servidor}")
        
        # Se falhar
        client_socket.close()
        client_socket = None
        estado_jogo = "MENU"
        return False
        
    except socket.timeout:
        print(f"[ERRO DE REDE] Tempo de conexão esgotado (timeout) ao tentar conectar a {ip}:{porta}.")
        if client_socket: client_socket.close()
        client_socket = None
        estado_jogo = "MENU"
        return False
    except socket.error as e:
        print(f"[ERRO DE REDE] Não foi possível conectar a {ip}:{porta}. Erro: {e}")
        if client_socket: client_socket.close()
        client_socket = None
        estado_jogo = "MENU" 
        return False

def enviar_input_servidor(input_data):
    """ Envia uma string de input para o servidor, se conectado. """
    global listener_thread_running, estado_jogo
    if client_socket and listener_thread_running:
        try:
            client_socket.sendall((input_data + '\n').encode('utf-8'))
        except (socket.error, BrokenPipeError) as e:
            print(f"[ERRO DE REDE] Falha ao enviar input '{input_data}'. Conexão pode estar fechada. Erro: {e}")
    elif not listener_thread_running and estado_jogo == "JOGANDO":
        print("[AVISO] Tentou enviar input, mas a thread de rede não está a correr. A voltar ao menu.")
        estado_jogo = "MENU"

def fechar_conexao():
    """ Função auxiliar para fechar o socket e parar a thread de escuta. """
    global client_socket, listener_thread_running, listener_thread_object, MEU_NOME_REDE
    
    if listener_thread_running:
        print("Parando a thread de escuta...")
        listener_thread_running = False 
    
    if client_socket:
        print("Fechando conexão de rede...")
        try:
            client_socket.shutdown(socket.SHUT_RDWR) 
            client_socket.close()
        except socket.error:
            pass 
        client_socket = None
    
    if listener_thread_object:
        listener_thread_object.join(timeout=1.0) 
        if listener_thread_object.is_alive():
            print("[AVISO] A thread de escuta não parou.")
        listener_thread_object = None
        
    # Limpa os dados de rede
    MEU_NOME_REDE = ""
    with network_state_lock:
        online_players_states.clear()
        online_projectiles.clear()
        online_npcs.clear() # <-- ADICIONADO

# --- FIM DA MODIFICAÇÃO (Funções de Rede) ---


def reiniciar_jogo(pos_spawn=None): 
    """ Prepara o jogo, limpando grupos e resetando o jogador. """
    global estado_jogo, nave_player, max_bots_atual

    print("Reiniciando o Jogo...")

    if client_socket and MEU_NOME_REDE:
        nave_player.nome = MEU_NOME_REDE
    else:
        nave_player.nome = nome_jogador_input.strip() if nome_jogador_input.strip() else "Jogador"

    # Limpa grupos
    grupo_obstaculos.empty() 
    grupo_vidas_coletaveis.empty() 
    grupo_inimigos.empty() 
    grupo_motherships.empty() 
    grupo_boss_congelante.empty() 
    grupo_bots.empty() 
    grupo_projeteis_player.empty() 
    grupo_projeteis_bots.empty() 
    grupo_projeteis_inimigos.empty() 
    grupo_explosoes.empty() 

    spawn_x, spawn_y = 0, 0
    if pos_spawn:
        # Usa a posição de spawn fornecida (pelo servidor)
        spawn_x, spawn_y = pos_spawn
        print(f"Spawnando em posição definida pelo servidor: ({spawn_x}, {spawn_y})")
        
        # Atualiza o estado local
        with network_state_lock:
            online_players_states.clear()
            online_projectiles.clear()
            online_npcs.clear() # <-- ADICIONADO
            online_players_states[MEU_NOME_REDE] = {
                'x': spawn_x, 'y': spawn_y, 'angulo': 0
            }
    else:
        # Modo Offline: Escolhe posição aleatória
        print("Spawnando em posição aleatória (Modo Offline)...")
        margem_spawn = 100
        spawn_x = random.randint(margem_spawn, s.MAP_WIDTH - margem_spawn)
        spawn_y = random.randint(margem_spawn, s.MAP_HEIGHT - margem_spawn)
        
    nave_player.posicao = pygame.math.Vector2(spawn_x, spawn_y)
    nave_player.rect.center = nave_player.posicao
    
    # Reseta jogador
    nave_player.grupo_auxiliares_ativos.empty()
    nave_player.lista_todas_auxiliares = [] 
    for pos in Nave.POSICOES_AUXILIARES:
        nova_aux = NaveAuxiliar(nave_player, pos)
        nave_player.lista_todas_auxiliares.append(nova_aux)
    nave_player.pontos = 0
    nave_player.nivel_motor = 1
    nave_player.nivel_dano = 1
    nave_player.nivel_max_vida = 1
    nave_player.nivel_escudo = 0
    nave_player.velocidade_movimento_base = 4 + nave_player.nivel_motor
    nave_player.max_vida = 4 + nave_player.nivel_max_vida
    nave_player.vida_atual = nave_player.max_vida
    nave_player.pontos_upgrade_disponiveis = 0
    nave_player.total_upgrades_feitos = 0
    nave_player._pontos_acumulados_para_upgrade = 0
    nave_player._indice_limiar = 0
    nave_player._limiar_pontos_atual = nave_player._limiares[0]
    nave_player.alvo_selecionado = None
    nave_player.posicao_alvo_mouse = None
    nave_player.ultimo_hit_tempo = 0
    nave_player.tempo_fim_lentidao = 0
    nave_player.rastro_particulas = []

    # Apenas spawna entidades no modo offline
    if pos_spawn is None:
        print("Gerando entidades (Obstáculos, Vidas, Bots)...")
        for _ in range(20): spawnar_obstaculo(nave_player.posicao)
        for _ in range(5): spawnar_vida(nave_player.posicao)
        grupo_bots.empty()
        for _ in range(max_bots_atual): spawnar_bot(nave_player.posicao)
    else:
        print("Modo Online. Aguardando dados do servidor para spawnar entidades.")
    
    estado_jogo = "JOGANDO"

def resetar_para_menu():
    """ Reseta o jogo de volta ao menu, fechando conexões. """
    global estado_jogo
    
    print("Voltando ao Menu Principal...")
    
    # Limpa todos os grupos (offline)
    grupo_bots.empty()
    grupo_inimigos.empty()
    grupo_motherships.empty()
    grupo_boss_congelante.empty() 
    grupo_projeteis_bots.empty()
    grupo_projeteis_inimigos.empty()
    grupo_projeteis_player.empty() 
    grupo_obstaculos.empty() 
    grupo_vidas_coletaveis.empty()
    
    # FECHA O SOCKET E LIMPA A VARIÁVEL
    fechar_conexao()
    
    estado_jogo = "MENU"

# (O resto das funções de spawn, cheat, etc. permanecem as mesmas)
def spawnar_boss_congelante(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia, dist_min_do_jogador=s.SPAWN_DIST_MAX * 1.2)
    novo_boss = BossCongelante(x, y)
    grupo_inimigos.add(novo_boss)
    grupo_boss_congelante.add(novo_boss)
    print(f"!!! Boss Congelante spawnou em ({int(x)}, {int(y)}) !!!")
def calcular_posicao_spawn(pos_referencia, dist_min_do_jogador=s.SPAWN_DIST_MIN):
    while True:
        x = random.uniform(0, s.MAP_WIDTH)
        y = random.uniform(0, s.MAP_HEIGHT)
        pos_spawn = pygame.math.Vector2(x, y)
        if pos_referencia.distance_to(pos_spawn) > dist_min_do_jogador:
            return (x, y) 
def spawnar_inimigo_aleatorio(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia)
    chance = random.random()
    inimigo = None
    if chance < 0.05: inimigo = InimigoBomba(x, y)
    elif chance < 0.10: inimigo = InimigoTiroRapido(x, y)
    elif chance < 0.15: inimigo = InimigoAtordoador(x, y)
    elif chance < 0.35: inimigo = InimigoAtiradorRapido(x, y)
    elif chance < 0.55: inimigo = InimigoRapido(x, y)
    else: inimigo = InimigoPerseguidor(x, y)
    if inimigo:
        grupo_inimigos.add(inimigo)
def spawnar_bot(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia)
    novo_bot = NaveBot(x, y)
    grupo_bots.add(novo_bot)
def spawnar_mothership(pos_referencia):
    max_tentativas = 10 
    for _ in range(max_tentativas):
        x, y = calcular_posicao_spawn(pos_referencia)
        pos_potencial = pygame.math.Vector2(x, y)
        muito_perto = False
        for mothership_existente in grupo_motherships:
            try:
                if pos_potencial.distance_to(mothership_existente.posicao) < s.MIN_SPAWN_DIST_ENTRE_NAVES_MAE:
                    muito_perto = True
                    break 
            except ValueError:
                muito_perto = True 
                break
        if not muito_perto:
            nova_mothership = InimigoMothership(x, y)
            grupo_inimigos.add(nova_mothership)
            grupo_motherships.add(nova_mothership)
            print(f"!!! Mothership spawnou em ({int(x)}, {int(y)}) !!!") 
            return 
    print("[AVISO] Não foi possível encontrar uma posição segura para spawnar a Mothership após várias tentativas.")
def spawnar_vida(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia)
    nova_vida = VidaColetavel(x, y)
    grupo_vidas_coletaveis.add(nova_vida)
def spawnar_obstaculo(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia)
    raio = random.randint(s.OBSTACULO_RAIO_MIN, s.OBSTACULO_RAIO_MAX)
    novo_obstaculo = Obstaculo(x, y, raio)
    grupo_obstaculos.add(novo_obstaculo)
def spawnar_boss_congelante_perto(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia, dist_min_do_jogador=s.SPAWN_DIST_MIN)
    novo_boss = BossCongelante(x, y)
    grupo_inimigos.add(novo_boss)
    grupo_boss_congelante.add(novo_boss)
    print(f"[CHEAT] Boss Congelante spawnou perto em ({int(x)}, {int(y)})")
def processar_cheat(comando, nave):
    global variavel_texto_terminal
    comando_limpo = comando.strip().lower()
    if comando_limpo == "maxpoint":
        nave.ganhar_pontos(9999)
        print("[CHEAT] +9999 pontos adicionados!")
    elif comando_limpo == "invencivel":
        if isinstance(nave, Player):
            nave.invencivel = not nave.invencivel
            estado_str = "ATIVADA" if nave.invencivel else "DESATIVADA"
            print(f"[CHEAT] Invencibilidade {estado_str}!")
        else:
             print("[CHEAT] Comando 'invencivel' só funciona para o Jogador.")
    elif comando_limpo == "maxupgrade":
        if isinstance(nave, Player):
             nave.pontos_upgrade_disponiveis = MAX_TOTAL_UPGRADES - nave.total_upgrades_feitos
             print(f"[CHEAT] +{nave.pontos_upgrade_disponiveis} Pontos de Upgrade adicionados!")
        else:
             print("[CHEAT] Comando 'maxupgrade' só funciona para o Jogador.")
    elif comando_limpo == "spawncongelante":
        spawnar_boss_congelante_perto(nave_player.posicao)
        print("[CHEAT] Tentando spawnar Boss Congelante perto do jogador.")
    else:
        print(f"[CHEAT] Comando desconhecido: '{comando_limpo}'")
    variavel_texto_terminal = ""

# 10. Recalcula Posições Iniciais da UI (após inicializar Pygame)
ui.recalculate_ui_positions(LARGURA_TELA, ALTURA_TELA)

# --- LOOP PRINCIPAL DO JOGO ---
while rodando:
    # 11. Tratamento de Eventos
    
    if estado_jogo == "JOGANDO" and client_socket:
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[2]: # Botão direito está seguro
            mouse_pos_tela = pygame.mouse.get_pos()
            camera_world_topleft = (-camera.camera_rect.left, -camera.camera_rect.top)
            mouse_pos_mundo = pygame.math.Vector2(mouse_pos_tela[0] + camera_world_topleft[0],
                                                  mouse_pos_tela[1] + camera_world_topleft[1])
            enviar_input_servidor(f"CLICK_MOVE|{int(mouse_pos_mundo.x)}|{int(mouse_pos_mundo.y)}")
            
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False
        elif event.type == pygame.VIDEORESIZE:
            LARGURA_TELA = event.w
            ALTURA_TELA = event.h
            tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.RESIZABLE)
            ui.recalculate_ui_positions(LARGURA_TELA, ALTURA_TELA)
            camera.resize(LARGURA_TELA, ALTURA_TELA)
            print(f"Tela redimensionada para: {LARGURA_TELA}x{ALTURA_TELA}")

        # --- Eventos por Estado ---
        if estado_jogo == "MENU":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                
                if ui.RECT_BOTAO_JOGAR_OFF.collidepoint(mouse_pos):
                    estado_jogo = "GET_NAME"
                    input_nome_ativo = True 
                elif ui.RECT_BOTAO_MULTIPLAYER.collidepoint(mouse_pos):
                    estado_jogo = "GET_SERVER_INFO"
                    input_connect_ativo = "nome" 
                elif ui.RECT_BOTAO_SAIR.collidepoint(mouse_pos):
                    rodando = False

        elif estado_jogo == "GET_NAME":
            if event.type == pygame.KEYDOWN:
                if input_nome_ativo:
                    if event.key == pygame.K_RETURN:
                        reiniciar_jogo() # Modo Offline
                        estado_jogo = "JOGANDO"
                    elif event.key == pygame.K_BACKSPACE:
                        nome_jogador_input = nome_jogador_input[:-1]
                    else:
                        if len(nome_jogador_input) < LIMITE_MAX_NOME and event.unicode.isprintable():
                            nome_jogador_input += event.unicode
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                
                if ui.RECT_LOGIN_BOTAO.collidepoint(mouse_pos):
                    reiniciar_jogo() # Modo Offline
                    estado_jogo = "JOGANDO"
                elif ui.RECT_LOGIN_INPUT.collidepoint(mouse_pos):
                    input_nome_ativo = True
                else:
                    input_nome_ativo = False
        
        elif estado_jogo == "GET_SERVER_INFO":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    input_connect_ativo = "ip" if input_connect_ativo == "nome" else "nome"
                
                elif event.key == pygame.K_RETURN:
                    if input_connect_ativo == "nome":
                        input_connect_ativo = "ip"
                    elif input_connect_ativo == "ip":
                        input_connect_ativo = "none"
                        tentar_conectar(ip_servidor_input, 5555, nome_jogador_input)
                        
                elif input_connect_ativo == "nome":
                    if event.key == pygame.K_BACKSPACE:
                        nome_jogador_input = nome_jogador_input[:-1]
                    elif len(nome_jogador_input) < LIMITE_MAX_NOME and event.unicode.isprintable():
                        nome_jogador_input += event.unicode
                        
                elif input_connect_ativo == "ip":
                    if event.key == pygame.K_BACKSPACE:
                        ip_servidor_input = ip_servidor_input[:-1]
                    elif len(ip_servidor_input) < LIMITE_MAX_IP and event.unicode.isprintable():
                        ip_servidor_input += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                
                if ui.RECT_CONNECT_BOTAO.collidepoint(mouse_pos):
                    input_connect_ativo = "none"
                    tentar_conectar(ip_servidor_input, 5555, nome_jogador_input)
                
                elif ui.RECT_CONNECT_NOME.collidepoint(mouse_pos):
                    input_connect_ativo = "nome"
                elif ui.RECT_CONNECT_IP.collidepoint(mouse_pos):
                    input_connect_ativo = "ip"
                else:
                    input_connect_ativo = "none"
        
        elif estado_jogo == "JOGANDO":
            if event.type == pygame.KEYDOWN:
                # Eventos de Menu
                if event.key == pygame.K_v: estado_jogo = "LOJA"; print("Abrindo loja...")
                elif event.key == pygame.K_QUOTE: estado_jogo = "TERMINAL"; variavel_texto_terminal = ""; print("Abrindo terminal de cheats...")
                elif event.key == pygame.K_ESCAPE: estado_jogo = "PAUSE"; print("Jogo Pausado.")

                # Eventos de Jogo (Online)
                elif client_socket:
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        enviar_input_servidor("W_DOWN")
                    elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        enviar_input_servidor("A_DOWN")
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        enviar_input_servidor("S_DOWN")
                    elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        enviar_input_servidor("D_DOWN")
                    elif event.key == pygame.K_SPACE:
                        enviar_input_servidor("SPACE_DOWN")
            
            elif event.type == pygame.KEYUP:
                # Eventos de Jogo (Online)
                if client_socket:
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        enviar_input_servidor("W_UP")
                    elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        enviar_input_servidor("A_UP")
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        enviar_input_servidor("S_UP")
                    elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        enviar_input_servidor("D_UP")
                    elif event.key == pygame.K_SPACE:
                        enviar_input_servidor("SPACE_UP")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos_tela = pygame.mouse.get_pos()
                
                if event.button == 1: # Esquerdo (Target Lock)
                    if ui.RECT_BOTAO_UPGRADE_HUD.collidepoint(mouse_pos_tela):
                         estado_jogo = "LOJA"; print("Abrindo loja via clique no botão HUD...")
                    else: # Clique no mapa (Target Lock)
                        camera_world_topleft = (-camera.camera_rect.left, -camera.camera_rect.top)
                        mouse_pos_mundo = pygame.math.Vector2(mouse_pos_tela[0] + camera_world_topleft[0],
                                                              mouse_pos_tela[1] + camera_world_topleft[1])
                        if client_socket:
                            enviar_input_servidor(f"CLICK_TARGET|{int(mouse_pos_mundo.x)}|{int(mouse_pos_mundo.y)}")
                        else:
                            # Lógica offline normal
                            alvo_clicado = None
                            todos_alvos_clicaveis = list(grupo_inimigos) + list(grupo_bots) + list(grupo_obstaculos)
                            for alvo in todos_alvos_clicaveis:
                                target_click_rect = pygame.Rect(0, 0, s.TARGET_CLICK_SIZE, s.TARGET_CLICK_SIZE)
                                target_click_rect.center = alvo.posicao
                                if target_click_rect.collidepoint(mouse_pos_mundo):
                                    alvo_clicado = alvo
                                    break
                            nave_player.alvo_selecionado = alvo_clicado
                
        elif estado_jogo == "PAUSE":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: estado_jogo = "JOGANDO"; print("Jogo Retomado.")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                
                if ui.RECT_BOTAO_VOLTAR_MENU.collidepoint(mouse_pos):
                    resetar_para_menu()
                    
                if ui.RECT_BOTAO_BOT_MENOS.collidepoint(mouse_pos):
                    if max_bots_atual > 0:
                        max_bots_atual -= 1
                        print(f"Máximo de Bots reduzido para: {max_bots_atual}")
                        if len(grupo_bots) > max_bots_atual:
                             try:
                                 bot_para_remover = random.choice(grupo_bots.sprites())
                                 bot_para_remover.kill()
                                 print(f"Bot {bot_para_remover.nome} removido.")
                             except IndexError:
                                 pass
                elif ui.RECT_BOTAO_BOT_MAIS.collidepoint(mouse_pos):
                    if max_bots_atual < s.MAX_BOTS_LIMITE_SUPERIOR:
                        max_bots_atual += 1
                        print(f"Máximo de Bots aumentado para: {max_bots_atual}")

        elif estado_jogo == "LOJA":
            # ... (código do estado LOJA permanece o mesmo) ...
            if event.type == pygame.KEYDOWN and event.key == pygame.K_v: estado_jogo = "JOGANDO"; print("Fechando loja...")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if ui.RECT_BOTAO_MOTOR.collidepoint(mouse_pos): nave_player.comprar_upgrade("motor")
                elif ui.RECT_BOTAO_DANO.collidepoint(mouse_pos): nave_player.comprar_upgrade("dano")
                elif ui.RECT_BOTAO_AUX.collidepoint(mouse_pos): nave_player.comprar_upgrade("auxiliar")
                elif ui.RECT_BOTAO_MAX_HP.collidepoint(mouse_pos): nave_player.comprar_upgrade("max_health")
                elif ui.RECT_BOTAO_ESCUDO.collidepoint(mouse_pos): nave_player.comprar_upgrade("escudo")

        elif estado_jogo == "TERMINAL":
            # ... (código do estado TERMINAL permanece o mesmo) ...
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    processar_cheat(variavel_texto_terminal, nave_player)
                    estado_jogo = "JOGANDO"
                elif event.key == pygame.K_BACKSPACE: variavel_texto_terminal = variavel_texto_terminal[:-1]
                elif event.key == pygame.K_QUOTE: estado_jogo = "JOGANDO"; print("Fechando terminal.")
                else:
                    if len(variavel_texto_terminal) < 50: variavel_texto_terminal += event.unicode

        elif estado_jogo == "GAME_OVER":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if ui.RECT_BOTAO_REINICIAR.collidepoint(mouse_pos):
                    if client_socket:
                        resetar_para_menu()
                    else:
                        reiniciar_jogo() # Modo offline, reinicia


    # 12. Lógica de Atualização
    if estado_jogo not in ["MENU", "PAUSE", "GET_NAME", "GET_SERVER_INFO"]:
        camera.update(nave_player)

        # Define listas de alvos (apenas para auxiliares)
        lista_todos_alvos_para_aux = list(grupo_inimigos) + list(grupo_obstaculos) + [nave_player] + list(grupo_bots)

        # --- LÓGICA DE JOGO OFFLINE ---
        if client_socket is None: 
            lista_alvos_naves = [nave_player] + list(grupo_bots)
            grupo_bots.update(nave_player, grupo_projeteis_bots, grupo_bots, grupo_inimigos, grupo_obstaculos)
            grupo_inimigos.update(lista_alvos_naves, grupo_projeteis_inimigos, s.DESPAWN_DIST)
            
            grupo_projeteis_player.update()
            grupo_projeteis_bots.update()
            grupo_projeteis_inimigos.update()
            
            # Spawns locais
            if len(grupo_vidas_coletaveis) < s.MAX_VIDAS_COLETAVEIS: spawnar_vida(nave_player.posicao)
            if len(grupo_obstaculos) < s.MAX_OBSTACULOS: spawnar_obstaculo(nave_player.posicao)
            contagem_inimigos_normais = sum(1 for inimigo in grupo_inimigos if not isinstance(inimigo, (InimigoMinion, InimigoMothership)))
            if contagem_inimigos_normais < s.MAX_INIMIGOS: spawnar_inimigo_aleatorio(nave_player.posicao)
            if len(grupo_motherships) < s.MAX_MOTHERSHIPS: spawnar_mothership(nave_player.posicao)
            if estado_jogo == "JOGANDO" and len(grupo_bots) < max_bots_atual: spawnar_bot(nave_player.posicao)
            if len(grupo_boss_congelante) < s.MAX_BOSS_CONGELANTE: spawnar_boss_congelante(nave_player.posicao)
            
            # Colisões locais
            colisoes = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_obstaculos, True, True)
            for _, obst_list in colisoes.items():
                for obst in obst_list: 
                    nave_player.ganhar_pontos(obst.pontos_por_morte)
            colisoes = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_inimigos, True, False)
            for _, inim_list in colisoes.items():
                for inimigo in inim_list:
                    morreu = inimigo.foi_atingido(nave_player.nivel_dano)
                    if morreu:
                        nave_player.ganhar_pontos(inimigo.pontos_por_morte);
                        if isinstance(inimigo, (InimigoMothership, BossCongelante)):
                            if isinstance(inimigo, InimigoMothership): inimigo.grupo_minions.empty()
                            if tocar_som_posicional and s.SOM_EXPLOSAO_BOSS:
                                tocar_som_posicional(s.SOM_EXPLOSAO_BOSS, inimigo.posicao, nave_player.posicao, VOLUME_BASE_EXPLOSAO_BOSS)
                        else:
                            if tocar_som_posicional and s.SOM_EXPLOSAO_NPC:
                                tocar_som_posicional(s.SOM_EXPLOSAO_NPC, inimigo.posicao, nave_player.posicao, VOLUME_BASE_EXPLOSAO_NPC)
            colisoes = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_bots, True, False)
            for proj, bot_list in colisoes.items():
                for bot in bot_list:
                    bot.foi_atingido(nave_player.nivel_dano, estado_jogo, proj.posicao)
            colisoes = pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_obstaculos, True, True)
            for proj, obst_list in colisoes.items():
                bot_que_acertou = None
                for bot_ in grupo_bots:
                    if bot_.posicao.distance_to(proj.posicao) < bot_.distancia_scan:
                        bot_que_acertou = bot_
                        break
                if bot_que_acertou:
                    for obst in obst_list:
                        bot_que_acertou.ganhar_pontos(obst.pontos_por_morte)
            colisoes = pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_inimigos, True, False)
            for proj, inim_list in colisoes.items():
                bot_que_acertou = None; dano_bot = 1
                for bot_ in grupo_bots:
                    if bot_.posicao.distance_to(proj.posicao) < bot_.distancia_scan: bot_que_acertou = bot_; dano_bot = bot_.nivel_dano; break
                if bot_que_acertou:
                    for inimigo in inim_list:
                        morreu = inimigo.foi_atingido(dano_bot)
                        if morreu:
                            bot_que_acertou.ganhar_pontos(inimigo.pontos_por_morte);
                            if isinstance(inimigo, (InimigoMothership, BossCongelante)):
                                if isinstance(inimigo, InimigoMothership): inimigo.grupo_minions.empty()
                                if tocar_som_posicional and s.SOM_EXPLOSAO_BOSS:
                                    tocar_som_posicional(s.SOM_EXPLOSAO_BOSS, inimigo.posicao, nave_player.posicao, VOLUME_BASE_EXPLOSAO_BOSS)
                            else:
                                if tocar_som_posicional and s.SOM_EXPLOSAO_NPC:
                                    tocar_som_posicional(s.SOM_EXPLOSAO_NPC, inimigo.posicao, nave_player.posicao, VOLUME_BASE_EXPLOSAO_NPC)
            colisoes = pygame.sprite.groupcollide(grupo_bots, grupo_projeteis_inimigos, False, False)
            for bot, proj_list in colisoes.items():
                for proj in proj_list:
                    if isinstance(proj, ProjetilCongelante):
                        bot.aplicar_congelamento(s.DURACAO_CONGELAMENTO)
                    elif isinstance(proj, ProjetilTeleguiadoLento):
                        bot.aplicar_lentidao(6000)
                    else: 
                        bot.foi_atingido(1, estado_jogo, proj.posicao)
                    proj.kill()
            colisoes = pygame.sprite.groupcollide(grupo_bots, grupo_vidas_coletaveis, False, True)
            for bot, vida_list in colisoes.items():
                if vida_list: bot.coletar_vida(s.VIDA_COLETADA_CURA)
            for bot in grupo_bots:
                inimigos_colididos = pygame.sprite.spritecollide(bot, grupo_inimigos, False)
                for inimigo in inimigos_colididos:
                    dano = 1 if not isinstance(inimigo, InimigoBomba) else inimigo.DANO_EXPLOSAO
                    bot.foi_atingido(dano, estado_jogo, inimigo.posicao)
                    morreu = inimigo.foi_atingido(1)
                    if morreu: 
                        bot.ganhar_pontos(inimigo.pontos_por_morte)
                        if isinstance(inimigo, (InimigoMothership, BossCongelante)):
                            if isinstance(inimigo, InimigoMothership): inimigo.grupo_minions.empty()
                            if tocar_som_posicional and s.SOM_EXPLOSAO_BOSS:
                                tocar_som_posicional(s.SOM_EXPLOSAO_BOSS, inimigo.posicao, nave_player.posicao, VOLUME_BASE_EXPLOSAO_BOSS)
                        else:
                            if tocar_som_posicional and s.SOM_EXPLOSAO_NPC:
                                tocar_som_posicional(s.SOM_EXPLOSAO_NPC, inimigo.posicao, nave_player.posicao, VOLUME_BASE_EXPLOSAO_NPC)
        
        # --- FIM DA MODIFICAÇÃO (Bugs 1 e 2) ---

        # (Atualizações de Auxiliares e Explosões correm sempre)
        for bot in grupo_bots: 
            bot.grupo_auxiliares_ativos.update(lista_todos_alvos_para_aux, grupo_projeteis_bots, estado_jogo, nave_player)
        nave_player.grupo_auxiliares_ativos.update(lista_todos_alvos_para_aux, grupo_projeteis_player, estado_jogo, nave_player)
        grupo_explosoes.update()

        # (Spawns de Vidas e Obstáculos também correm sempre)
        if len(grupo_vidas_coletaveis) < s.MAX_VIDAS_COLETAVEIS: spawnar_vida(nave_player.posicao)
        if len(grupo_obstaculos) < s.MAX_OBSTACULOS: spawnar_obstaculo(nave_player.posicao)

    # --- Atualizações e Colisões Específicas do Jogador (Só quando JOGANDO) ---
    if estado_jogo == "JOGANDO":
        
        if client_socket:
            # Online: Atualiza a posição do jogador com base nos dados da rede
            with network_state_lock:
                my_state = online_players_states.get(MEU_NOME_REDE)
                if my_state:
                    nova_pos = pygame.math.Vector2(my_state['x'], my_state['y'])
                    nave_player.posicao = nave_player.posicao.lerp(nova_pos, 0.4) 
                    nave_player.angulo = my_state['angulo']
                
            nave_player.rect.center = nave_player.posicao
            nave_player.update(grupo_projeteis_player, camera, client_socket)
        else:
            # Offline: O update processa o input e calcula o movimento
            nave_player.update(grupo_projeteis_player, camera, None)

        # Colisões QUE AFETAM O JOGADOR (Apenas Offline)
        if client_socket is None:
            colisoes_proj_inimigo_player = pygame.sprite.spritecollide(nave_player, grupo_projeteis_inimigos, False)
            for proj in colisoes_proj_inimigo_player:
                if isinstance(proj, ProjetilCongelante):
                    nave_player.aplicar_lentidao(s.DURACAO_CONGELAMENTO)
                elif isinstance(proj, ProjetilTeleguiadoLento):
                    nave_player.aplicar_lentidao(6000)
                else:
                    if nave_player.foi_atingido(1, estado_jogo, proj.posicao):
                         estado_jogo = "GAME_OVER"
                proj.kill()
            
            # --- ADICIONADO (Bugs 1 e 2: Colisões de RAM vs Jogador) ---
            colisoes_proj_bot_player = pygame.sprite.spritecollide(nave_player, grupo_projeteis_bots, True)
            for proj in colisoes_proj_bot_player:
                if nave_player.foi_atingido(1, estado_jogo, proj.posicao):
                     estado_jogo = "GAME_OVER" 

            colisoes_vida_player = pygame.sprite.spritecollide(nave_player, grupo_vidas_coletaveis, True)
            for _ in colisoes_vida_player: nave_player.coletar_vida(s.VIDA_COLETADA_CURA)

            colisoes_ram_inimigo_player = pygame.sprite.spritecollide(nave_player, grupo_inimigos, False)
            for inimigo in colisoes_ram_inimigo_player:
                dano = 1 if not isinstance(inimigo, InimigoBomba) else inimigo.DANO_EXPLOSAO
                if nave_player.foi_atingido(dano, estado_jogo, inimigo.posicao):
                    estado_jogo = "GAME_OVER"
                morreu = inimigo.foi_atingido(1)
                if morreu:
                    nave_player.ganhar_pontos(inimigo.pontos_por_morte)
                    if isinstance(inimigo, (InimigoMothership, BossCongelante)):
                        if isinstance(inimigo, InimigoMothership): inimigo.grupo_minions.empty()
                        if tocar_som_posicional and s.SOM_EXPLOSAO_BOSS:
                            tocar_som_posicional(s.SOM_EXPLOSAO_BOSS, inimigo.posicao, nave_player.posicao, VOLUME_BASE_EXPLOSAO_BOSS)
                    else:
                        if tocar_som_posicional and s.SOM_EXPLOSAO_NPC:
                            tocar_som_posicional(s.SOM_EXPLOSAO_NPC, inimigo.posicao, nave_player.posicao, VOLUME_BASE_EXPLOSAO_NPC)
            
            colisoes_ram_bot_player = pygame.sprite.spritecollide(nave_player, grupo_bots, False)
            for bot in colisoes_ram_bot_player:
                if nave_player.foi_atingido(1, estado_jogo, bot.posicao):
                    estado_jogo = "GAME_OVER"
                bot.foi_atingido(1, estado_jogo, nave_player.posicao)
            # --- FIM DO BLOCO ADICIONADO ---

    # 13. Desenho
    if estado_jogo == "MENU":
        ui.desenhar_menu(tela, LARGURA_TELA, ALTURA_TELA)
        
    elif estado_jogo == "GET_NAME":
        ui.desenhar_tela_nome(tela, nome_jogador_input, input_nome_ativo)
        
    elif estado_jogo == "GET_SERVER_INFO":
        ui.desenhar_tela_conexao(tela, nome_jogador_input, ip_servidor_input, input_connect_ativo)
    
    else: # Desenha o jogo e as UIs sobrepostas
        # Fundo estrelado
        tela.fill(s.PRETO)
        for pos_base, raio, parallax_fator in lista_estrelas:
            pos_jogador = nave_player.posicao
            pos_tela_x = (pos_base.x - (pos_jogador.x * parallax_fator)) % LARGURA_TELA
            pos_tela_y = (pos_base.y - (pos_jogador.y * parallax_fator)) % ALTURA_TELA
            pygame.draw.circle(tela, s.CORES_ESTRELAS[raio - 1], (int(pos_tela_x), int(pos_tela_y)), raio)

        # Sprites do Jogo
        for obst in grupo_obstaculos: tela.blit(obst.image, camera.apply(obst.rect))
        for vida in grupo_vidas_coletaveis: tela.blit(vida.image, camera.apply(vida.rect))
        
        # --- INÍCIO DA MODIFICAÇÃO (Desenhar Online) ---
        online_players_copy = {}
        online_projectiles_copy = []
        online_npcs_copy = {} # <-- ADICIONADO
        
        if client_socket:
            # Modo Online: Copia os estados
            with network_state_lock:
                online_players_copy = online_players_states.copy() 
                online_projectiles_copy = list(online_projectiles) 
                online_npcs_copy = online_npcs.copy() # <-- ADICIONADO
                
            for nome, state in online_players_copy.items():
                if nome == MEU_NOME_REDE:
                    continue 
                
                # Desenha a nave (triângulo) e nome
                img_rotacionada = pygame.transform.rotate(nave_player.imagem_original, state['angulo'])
                pos_rect = img_rotacionada.get_rect(center=(state['x'], state['y']))
                
                tela.blit(img_rotacionada, camera.apply(pos_rect))
                
                nome_surf = s.FONT_NOME_JOGADOR.render(nome, True, s.BRANCO)
                nome_rect = nome_surf.get_rect(midbottom=(state['x'], state['y'] - 33))
                tela.blit(nome_surf, camera.apply(nome_rect))
            
            # Desenha os projéteis da rede
            for (x, y, tipo) in online_projectiles_copy:
                cor = s.VERMELHO_TIRO
                if tipo == 'npc': 
                    cor = s.LARANJA_TIRO_INIMIGO
                elif tipo == 'player':
                    cor = s.VERMELHO_TIRO
                
                pos_tela = camera.apply(pygame.Rect(x, y, 0, 0)).topleft
                pygame.draw.circle(tela, cor, pos_tela, 5) # Raio 5
            
            # --- ADICIONADO: Desenhar NPCs ---
            for npc_id, state in online_npcs_copy.items():
                cor = s.CINZA_OBSTACULO # Cor padrão
                tamanho = (30, 30)
                
                if state['tipo'] == 'perseguidor':
                    cor = s.VERMELHO_PERSEGUIDOR
                    tamanho = (30, 30) # Tamanho do InimigoPerseguidor
                
                # (Não podemos rodar o rect, então desenhamos um rect simples)
                # (No futuro, podemos usar a mesma lógica de rotação do 'player')
                npc_rect_mundo = pygame.Rect(0, 0, tamanho[0], tamanho[1])
                npc_rect_mundo.center = (state['x'], state['y'])
                pygame.draw.rect(tela, cor, camera.apply(npc_rect_mundo))
            # --- FIM DO BLOCO ADICIONADO ---

        else:
            # Modo Offline: Desenha os bots e inimigos locais
            for inimigo in grupo_inimigos: inimigo.desenhar_vida(tela, camera); tela.blit(inimigo.image, camera.apply(inimigo.rect))
            for bot in grupo_bots:
                bot.desenhar(tela, camera); bot.desenhar_vida(tela, camera)
                bot.desenhar_nome(tela, camera)
                for aux in bot.grupo_auxiliares_ativos: aux.desenhar(tela, camera)
            
            # Desenha projéteis locais (offline)
            for proj in grupo_projeteis_player: tela.blit(proj.image, camera.apply(proj.rect))
            for proj in grupo_projeteis_bots: tela.blit(proj.image, camera.apply(proj.rect))
            for proj in grupo_projeteis_inimigos: tela.blit(proj.image, camera.apply(proj.rect))
        # --- FIM DA MODIFICAÇÃO ---
        
        # Desenha o nosso jogador (Sempre)
        if estado_jogo != "GAME_OVER": 
            nave_player.desenhar(tela, camera); nave_player.desenhar_vida(tela, camera)
            nave_player.desenhar_nome(tela, camera)
            for aux in nave_player.grupo_auxiliares_ativos: aux.desenhar(tela, camera)
        
        for explosao in grupo_explosoes: explosao.draw(tela, camera)

        # UI Estática
        ui.desenhar_hud(tela, nave_player, estado_jogo)
        
        # --- INÍCIO DA MODIFICAÇÃO (Chamada do Minimapa) ---
        online_players_copy = {}
        if client_socket:
             with network_state_lock:
                 online_players_copy = online_players_states.copy()
        
        ui.desenhar_minimapa(tela, nave_player, grupo_bots, estado_jogo, s.MAP_WIDTH, s.MAP_HEIGHT, online_players_copy, MEU_NOME_REDE)
        if client_socket:
            # (Futuramente, o servidor deve enviar os pontos também)
            lista_ordenada = sorted([nave_player], key=lambda n: n.pontos, reverse=True); top_5 = lista_ordenada[:5]
        else:
            # Modo Offline (como estava antes)
            if estado_jogo != "GAME_OVER":
                todos_os_jogadores = [nave_player] + list(grupo_bots.sprites())
            else:
                todos_os_jogadores = list(grupo_bots.sprites()) 
            lista_ordenada = sorted(todos_os_jogadores, key=lambda n: n.pontos, reverse=True); top_5 = lista_ordenada[:5]
        
        ui.desenhar_ranking(tela, top_5, nave_player)
        # --- FIM DA MODIFICAÇÃO (Ranking) ---

        # Overlays 
        if estado_jogo == "PAUSE":
            ui.desenhar_pause(tela, max_bots_atual, s.MAX_BOTS_LIMITE_SUPERIOR, len(grupo_bots))
        elif estado_jogo == "LOJA":
            ui.desenhar_loja(tela, nave_player, LARGURA_TELA, ALTURA_TELA)
        elif estado_jogo == "TERMINAL":
            ui.desenhar_terminal(tela, variavel_texto_terminal, LARGURA_TELA, ALTURA_TELA)
        elif estado_jogo == "GAME_OVER":
            ui.desenhar_game_over(tela, LARGURA_TELA, ALTURA_TELA)
        # --- FIM DO CÓDIGO QUE ESTAVA EM FALTA ---

    # 14. Atualiza a Tela e Controla FPS
    pygame.display.flip()
    clock.tick(60)

# 15. Finalização
fechar_conexao() # Garante que a conexão e a thread são fechadas ao sair
pygame.quit()
sys.exit()
