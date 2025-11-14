# server.py
import socket
import threading
import random
import settings as s 
import multi.pvp_settings as pvp_s # <-- MODIFICAÇÃO PVP
import math 
import time 
import pygame 
import server_bot_ai 

# 1. Configurações do Servidor
HOST = '127.0.0.1'  
PORT = 5555         
MAX_JOGADORES_PVE = 16 
TICK_RATE = 60 
MAX_BOTS_ONLINE = 3 

# --- INÍCIO: MODIFICAÇÃO PVP (Constantes PVP) ---
MAX_JOGADORES_PVP = pvp_s.MAX_JOGADORES_PVP # 4
LOBBY_COUNTDOWN_MS = pvp_s.PVP_LOBBY_COUNTDOWN_SEGUNDOS * 1000 # 30000
PARTIDA_COUNTDOWN_MS = pvp_s.PVP_PARTIDA_DURACAO_SEGUNDOS * 1000 # 180000
PRE_MATCH_FREEZE_MS = 5000 # 5 segundos de "PRE_MATCH"
# --- FIM: MODIFICAÇÃO PVP ---

COLISAO_JOGADOR_PROJ_DIST_SQ = (15 + 5)**2
COLISAO_JOGADOR_NPC_DIST_SQ = (15 + 15)**2 

# --- INÍCIO: MODIFICAÇÃO PVP (Estado de Jogo Unificado) ---
# Estado PVE (Mundo principal)
pve_player_states = {} # Dicionário de estados de jogadores PVE
network_npcs = [] # NPCs (apenas PVE)
pve_network_projectiles = [] # Projéteis (apenas PVE)

# Estado PVP (Arena)
pvp_player_states = {} # Dicionário de estados de jogadores PVP
pvp_network_projectiles = [] # Projéteis (apenas PVP)
pvp_lobby_state = "WAITING" # WAITING, COUNTDOWN, PRE_MATCH, PLAYING, GAME_OVER
pvp_lobby_countdown_end = 0
pvp_pre_match_countdown_end = 0
pvp_match_countdown_end = 0
pvp_winner_name = ""

next_npc_id = 0
game_state_lock = threading.Lock() 
# --- FIM: MODIFICAÇÃO PVP ---


# --- (Constantes de Jogo e IA - Sem alterações) ---
COOLDOWN_TIRO = 250 
VELOCIDADE_PROJETIL = 10 
OFFSET_PONTA_TIRO = 25 
VELOCIDADE_BASE_NAVE = 4 
VELOCIDADE_MOVIMENTO_NAVE = VELOCIDADE_BASE_NAVE + 1 
VELOCIDADE_PERSEGUIDOR = 2.0 
DISTANCIA_PARAR_PERSEGUIDOR_SQ = 200**2 
SPAWN_DIST_MIN = s.SPAWN_DIST_MIN
COOLDOWN_TIRO_PERSEGUIDOR = 2000 
DISTANCIA_TIRO_PERSEGUIDOR_SQ = 500**2 
VELOCIDADE_PROJETIL_NPC = 7 
MAX_TARGET_LOCK_DISTANCE_SQ = s.MAX_TARGET_LOCK_DISTANCE**2 
TARGET_CLICK_SIZE_SQ = (s.TARGET_CLICK_SIZE / 2)**2 
REGEN_POR_TICK = s.REGEN_POR_TICK
REGEN_TICK_RATE_MS = s.REGEN_TICK_RATE
NPC_DETECTION_RANGE_SQ = (3000 ** 2)

# --- (Constantes de Upgrade - Sem alterações) ---
MAX_TOTAL_UPGRADES = s.MAX_TOTAL_UPGRADES
MAX_NIVEL_MOTOR = s.MAX_NIVEL_MOTOR
MAX_NIVEL_DANO = s.MAX_NIVEL_DANO
MAX_NIVEL_ESCUDO = s.MAX_NIVEL_ESCUDO
MAX_AUXILIARES = 4 
CUSTOS_AUXILIARES = s.CUSTOS_AUXILIARES
PONTOS_LIMIARES_PARA_UPGRADE = s.PONTOS_LIMIARES_PARA_UPGRADE[:]
PONTOS_SCORE_PARA_MUDAR_LIMIAR = s.PONTOS_SCORE_PARA_MUDAR_LIMIAR[:]

# --- (Constantes de Auxiliares - Sem alterações) ---
AUX_POSICOES = [
    pygame.math.Vector2(-40, 20), 
    pygame.math.Vector2(40, 20), 
    pygame.math.Vector2(-50, -10), 
    pygame.math.Vector2(50, -10)
]
AUX_COOLDOWN_TIRO = 1000 
AUX_DISTANCIA_TIRO_SQ = 600**2 

# --- (Constantes para novos projéteis e status - Sem alterações) ---
VELOCIDADE_PROJETIL_TELE = 14    
DURACAO_PROJETIL_TELE_MS = 700   
TURN_SPEED_TELE = 0.055
VELOCIDADE_PROJ_LENTO = 9.0
DURACAO_PROJ_LENTO_MS = 5000
VELOCIDADE_PROJ_CONGELANTE = 8.0
DURACAO_PROJ_CONGELANTE_MS = 700
DURACAO_LENTIDAO_MS = 6000
DURACAO_CONGELAMENTO_MS = 2000

# --- (Constantes dos Bosses - Sem alterações) ---
COOLDOWN_SPAWN_MINION_CONGELANTE = 10000
MAX_MINIONS_CONGELANTE = 6
MAX_MINIONS_MOTHERSHIP = 8
COOLDOWN_TIRO_MINION_CONGELANTE = 600
HP_MINION_CONGELANTE = 10
PONTOS_MINION_CONGELANTE = 5
VELOCIDADE_MINION_CONGELANTE = 2.5 

# --- (Funções de Lógica de Upgrade - Modificadas para PVP) ---
def server_ganhar_pontos(player_state, quantidade):
    if quantidade <= 0: return
    player_state['pontos'] += quantidade 
    player_state['_pontos_acumulados_para_upgrade'] += quantidade
    while player_state['_pontos_acumulados_para_upgrade'] >= player_state['_limiar_pontos_atual']:
        player_state['pontos_upgrade_disponiveis'] += 1
        player_state['_pontos_acumulados_para_upgrade'] -= player_state['_limiar_pontos_atual'] 
        print(f"[LOG] [{player_state['nome']}] Ganhou 1 Ponto de Upgrade! (Total: {player_state['pontos_upgrade_disponiveis']})")
        pontos_totais_aproximados = player_state['pontos'] 
        if (player_state['_indice_limiar'] < len(PONTOS_SCORE_PARA_MUDAR_LIMIAR) and 
            pontos_totais_aproximados >= PONTOS_SCORE_PARA_MUDAR_LIMIAR[player_state['_indice_limiar']]):
            player_state['_indice_limiar'] += 1
            if player_state['_indice_limiar'] < len(PONTOS_LIMIARES_PARA_UPGRADE):
                player_state['_limiar_pontos_atual'] = PONTOS_LIMIARES_PARA_UPGRADE[player_state['_indice_limiar']]
                print(f"[LOG] [{player_state['nome']}] Próximo Ponto de Upgrade a cada {player_state['_limiar_pontos_atual']} pontos de score.")

def server_comprar_upgrade(player_state, tipo_upgrade):
    
    is_pvp = player_state.get('is_pvp', False)
    limite_total_upgrades = pvp_s.PONTOS_ATRIBUTOS_INICIAIS if is_pvp else MAX_TOTAL_UPGRADES

    if player_state['pontos_upgrade_disponiveis'] <= 0:
        if player_state.get('is_bot', False) == False: 
            print(f"[LOG] [{player_state['nome']}] Pedido de compra negado (Sem Pontos de Upgrade)!")
        return
    
    if player_state['total_upgrades_feitos'] >= limite_total_upgrades:
        if player_state.get('is_bot', False) == False:
            print(f"[LOG] [{player_state['nome']}] Pedido de compra negado (Limite de {limite_total_upgrades} upgrades atingido)!")
        return
        
    comprou = False
    custo_padrao = 1
    if tipo_upgrade == "motor":
        if player_state['nivel_motor'] < MAX_NIVEL_MOTOR:
            if player_state['pontos_upgrade_disponiveis'] >= custo_padrao:
                player_state['pontos_upgrade_disponiveis'] -= custo_padrao
                player_state['total_upgrades_feitos'] += 1
                player_state['nivel_motor'] += 1
                comprou = True
                print(f"[LOG] [{player_state['nome']}] Motor comprado! Nível {player_state['nivel_motor']}.")
    elif tipo_upgrade == "dano":
        if player_state['nivel_dano'] < MAX_NIVEL_DANO:
            if player_state['pontos_upgrade_disponiveis'] >= custo_padrao:
                player_state['pontos_upgrade_disponiveis'] -= custo_padrao
                player_state['total_upgrades_feitos'] += 1
                player_state['nivel_dano'] += 1
                comprou = True
                print(f"[LOG] [{player_state['nome']}] Dano comprado! Nível {player_state['nivel_dano']}.")
    elif tipo_upgrade == "auxiliar":
        if is_pvp:
             print(f"[LOG] [{player_state['nome']}] Auxiliares desabilitados no modo PVP.")
             return
        num_ativos = player_state['nivel_aux']
        if num_ativos < MAX_AUXILIARES:
            custo_atual_aux = CUSTOS_AUXILIARES[num_ativos] 
            if player_state['pontos_upgrade_disponiveis'] >= custo_atual_aux:
                player_state['pontos_upgrade_disponiveis'] -= custo_atual_aux 
                player_state['total_upgrades_feitos'] += 1 
                player_state['nivel_aux'] += 1 
                comprou = True
                print(f"[LOG] [{player_state['nome']}] Auxiliar {num_ativos + 1} comprado por {custo_atual_aux} pts!")
            else:
                if player_state.get('is_bot', False) == False:
                    print(f"[LOG] [{player_state['nome']}] Pontos insuficientes para Auxiliar! Custo: {custo_atual_aux} Pts.")
    elif tipo_upgrade == "max_health":
        if s.VIDA_POR_NIVEL is None: 
            print("[ERRO] s.VIDA_POR_NIVEL não inicializada no servidor!")
            return
        if player_state['nivel_max_vida'] >= len(s.VIDA_POR_NIVEL) - 1:
            if player_state.get('is_bot', False) == False:
                print(f"[LOG] [{player_state['nome']}] Pedido de compra negado (Vida Máx. já está no Nível 5)!")
            return 
        
        if player_state['pontos_upgrade_disponiveis'] >= custo_padrao:
            player_state['pontos_upgrade_disponiveis'] -= custo_padrao
            player_state['total_upgrades_feitos'] += 1
            player_state['nivel_max_vida'] += 1
            player_state['max_hp'] = s.VIDA_POR_NIVEL[player_state['nivel_max_vida']]
            player_state['hp'] += 1 
            comprou = True
            print(f"[LOG] [{player_state['nome']}] Vida Máx. aumentada! Nível {player_state['nivel_max_vida']}.")
    elif tipo_upgrade == "escudo":
        if player_state['nivel_escudo'] < MAX_NIVEL_ESCUDO:
            if player_state['pontos_upgrade_disponiveis'] >= custo_padrao:
                player_state['pontos_upgrade_disponiveis'] -= custo_padrao
                player_state['total_upgrades_feitos'] += 1
                player_state['nivel_escudo'] += 1
                comprou = True
                print(f"[LOG] [{player_state['nome']}] Escudo comprado! Nível {player_state['nivel_escudo']}.")
    if not comprou and player_state.get('is_bot', False) == False:
        print(f"[LOG] [{player_state['nome']}] Pedido de compra para '{tipo_upgrade}' falhou (nível máx. atingido ou custo).")


def server_calcular_posicao_spawn(pos_referencia_lista, map_width, map_height):
    """ Encontra um ponto de spawn longe de todos os jogadores na lista. """
    while True:
        x = random.uniform(0, map_width)
        y = random.uniform(0, map_height)
        pos_spawn = pygame.math.Vector2(x, y) 
        longe_suficiente = True
        if pos_referencia_lista: 
            for pos_ref in pos_referencia_lista:
                try:
                    if pos_spawn.distance_to(pygame.math.Vector2(pos_ref[0], pos_ref[1])) < SPAWN_DIST_MIN:
                        longe_suficiente = False; break
                except (TypeError, IndexError): continue 
        if longe_suficiente:
            return (float(x), float(y)) 

def update_player_logic(player_state, agora_ms=0, map_width=s.MAP_WIDTH, map_height=s.MAP_HEIGHT): 
    """ Calcula a nova posição, ângulo E processa o tiro de UM jogador. """
    
    if s.DANO_POR_NIVEL is None: 
        print("[ERRO] update_player_logic chamado antes de s.DANO_POR_NIVEL ser definido.")
        return None
        
    if agora_ms == 0: agora_ms = int(time.time() * 1000) 

    is_congelado = agora_ms < player_state.get('tempo_fim_congelamento', 0)
    is_lento = agora_ms < player_state.get('tempo_fim_lentidao', 0)
    is_pre_match = player_state.get('is_pre_match', False)

    if is_congelado or is_pre_match: 
        player_state['alvo_mouse'] = None 
        return None 
    
    # --- 1. Lógica de Rotação ---
    angulo_alvo = None
    if player_state['alvo_lock']:
        target_id = player_state['alvo_lock']
        alvo_coords = None; alvo_encontrado = False
        
        lista_alvos_busca = []
        if player_state.get('is_pvp', False):
            lista_alvos_busca = pvp_player_states.values()
        else:
            lista_alvos_busca = list(pve_player_states.values()) + network_npcs

        for entity in lista_alvos_busca:
            entity_id = entity.get('id', entity.get('nome'))
            if entity_id == target_id:
                alvo_coords = (entity['x'], entity['y']); alvo_encontrado = True; break
        
        if not alvo_encontrado:
            player_state['alvo_lock'] = None 
        else:
            target_x, target_y = alvo_coords
            dist_sq = (target_x - player_state['x'])**2 + (target_y - player_state['y'])**2
            if dist_sq > MAX_TARGET_LOCK_DISTANCE_SQ:
                player_state['alvo_lock'] = None 
            else:
                vec_x = target_x - player_state['x']; vec_y = target_y - player_state['y']
                if (vec_x**2 + vec_y**2) > 0: 
                     radianos = math.atan2(vec_y, vec_x)
                     angulo_alvo = -math.degrees(radianos) - 90 
    elif player_state['alvo_mouse']:
        target_x, target_y = player_state['alvo_mouse']
        vec_x = target_x - player_state['x']; vec_y = target_y - player_state['y']
        if (vec_x**2 + vec_y**2) > 5.0**2: 
             radianos = math.atan2(vec_y, vec_x)
             angulo_alvo = -math.degrees(radianos) - 90
    if angulo_alvo is not None:
        player_state['angulo'] = angulo_alvo
    elif player_state['teclas']['a']:
        player_state['angulo'] += s.VELOCIDADE_ROTACAO_NAVE
    elif player_state['teclas']['d']:
        player_state['angulo'] -= s.VELOCIDADE_ROTACAO_NAVE
    player_state['angulo'] %= 360

    # --- 2. Lógica de Movimento ---
    velocidade_base_atual = 4 + (player_state['nivel_motor'] * 0.5)
    if is_lento:
        velocidade_base_atual *= 0.4 
    velocidade_atual = velocidade_base_atual + 1
    nova_pos_x = player_state['x']; nova_pos_y = player_state['y']
    
    if player_state['teclas']['w'] or player_state['teclas']['s']:
        radianos = math.radians(player_state['angulo'])
        if player_state['teclas']['w']:
            nova_pos_x += -math.sin(radianos) * velocidade_atual
            nova_pos_y += -math.cos(radianos) * velocidade_atual
        if player_state['teclas']['s']:
            nova_pos_x -= -math.sin(radianos) * velocidade_atual
            nova_pos_y -= -math.cos(radianos) * velocidade_atual
    elif player_state['alvo_mouse']:
        try:
            target_x, target_y = player_state['alvo_mouse']
            vec_x = target_x - nova_pos_x; vec_y = target_y - nova_pos_y
            dist_sq = vec_x**2 + vec_y**2 
            if dist_sq > 5.0**2: 
                dist = math.sqrt(dist_sq)
                dir_x = vec_x / dist; dir_y = vec_y / dist
                nova_pos_x += dir_x * velocidade_atual
                nova_pos_y += dir_y * velocidade_atual
                novo_vec_x = target_x - nova_pos_x; novo_vec_y = target_y - nova_pos_y
                if (novo_vec_x * vec_x + novo_vec_y * vec_y) < 0: 
                    nova_pos_x, nova_pos_y = target_x, target_y
                    player_state['alvo_mouse'] = None 
            else:
                player_state['alvo_mouse'] = None 
        except TypeError: 
            player_state['alvo_mouse'] = None

    # --- 3. Limitar ao Mapa (Clamping) ---
    meia_largura = 15; meia_altura = 15
    nova_pos_x = max(meia_largura, min(nova_pos_x, map_width - meia_largura))
    nova_pos_y = max(meia_altura, min(nova_pos_y, map_height - meia_altura))
    player_state['x'] = nova_pos_x
    player_state['y'] = nova_pos_y

    # --- 4. Lógica de Tiro ---
    if player_state['teclas']['space'] or player_state['alvo_lock']:
        if agora_ms - player_state['ultimo_tiro_tempo'] > player_state['cooldown_tiro']:
            player_state['ultimo_tiro_tempo'] = agora_ms
            radianos = math.radians(player_state['angulo'])
            pos_x = player_state['x'] + (-math.sin(radianos) * OFFSET_PONTA_TIRO)
            pos_y = player_state['y'] + (-math.cos(radianos) * OFFSET_PONTA_TIRO)
            vel_x_inicial = -math.sin(radianos); vel_y_inicial = -math.cos(radianos)

            dano_calculado = s.DANO_POR_NIVEL[player_state['nivel_dano']]
            
            novo_projetil = {'id': f"{player_state['nome']}_{agora_ms}", 'owner_nome': player_state['nome'],
                'x': pos_x, 'y': pos_y, 'pos_inicial_x': pos_x, 'pos_inicial_y': pos_y,
                'dano': dano_calculado, 
                'tipo': 'player_pvp' if player_state.get('is_pvp', False) else 'player_pve', 
                'timestamp_criacao': agora_ms
            }

            if player_state['alvo_lock']:
                novo_projetil['tipo_proj'] = 'teleguiado' 
                novo_projetil['velocidade'] = VELOCIDADE_PROJETIL_TELE
                novo_projetil['alvo_id'] = player_state['alvo_lock']
                novo_projetil['vel_x'] = vel_x_inicial * VELOCIDADE_PROJETIL_TELE
                novo_projetil['vel_y'] = vel_y_inicial * VELOCIDADE_PROJETIL_TELE
            else:
                novo_projetil['tipo_proj'] = 'normal' 
                novo_projetil['velocidade'] = 25 
                novo_projetil['vel_x'] = vel_x_inicial * 25
                novo_projetil['vel_y'] = vel_y_inicial * 25
            return novo_projetil
    return None

# --- (Funções de Lógica de NPC/Boss/Minion PVE - Sem alterações) ---
def update_npc_logic(npc, players_pos_lista, agora_ms=0):
    if npc.get('hp', 0) <= 0: return None
    alvo_pos = None; dist_min_sq = float('inf')
    if not players_pos_lista: return None 
    for p_pos in players_pos_lista:
        try:
            dist_sq = (npc['x'] - p_pos[0])**2 + (npc['y'] - p_pos[1])**2
            if dist_sq > NPC_DETECTION_RANGE_SQ: continue
            if dist_sq < dist_min_sq: dist_min_sq = dist_sq; alvo_pos = p_pos 
        except TypeError: continue 
    if not alvo_pos: return None
    vec_x = alvo_pos[0] - npc['x']; vec_y = alvo_pos[1] - npc['y']
    dist = math.sqrt(dist_min_sq)
    velocidade = VELOCIDADE_PERSEGUIDOR 
    if npc['tipo'] == 'rapido': velocidade = 4.0 
    elif npc['tipo'] == 'bomba': velocidade = 3.0 
    elif npc['tipo'] == 'tiro_rapido': velocidade = 1.5
    elif npc['tipo'] == 'atordoador': velocidade = 1.0
    if dist_min_sq > DISTANCIA_PARAR_PERSEGUIDOR_SQ or npc['tipo'] == 'bomba': 
        if dist > 0:
            dir_x = vec_x / dist; dir_y = vec_y / dist
            npc['x'] += dir_x * velocidade
            npc['y'] += dir_y * velocidade
    radianos = math.atan2(vec_y, vec_x)
    npc['angulo'] = -math.degrees(radianos) - 90
    npc['angulo'] %= 360
    if npc['tipo'] in ['bomba']: return None 
    if dist_min_sq < DISTANCIA_TIRO_PERSEGUIDOR_SQ: 
        if agora_ms == 0: agora_ms = int(time.time() * 1000)
        if agora_ms - npc['ultimo_tiro_tempo'] > npc['cooldown_tiro']:
            npc['ultimo_tiro_tempo'] = agora_ms
            dir_x = vec_x / dist; dir_y = vec_y / dist
            tipo_proj_npc = 'normal'
            velocidade_proj = VELOCIDADE_PROJETIL_NPC
            alvo_id_proj = None 
            if npc['tipo'] == 'tiro_rapido': velocidade_proj = 22 
            elif npc['tipo'] == 'rapido': velocidade_proj = 12 
            elif npc['tipo'] == 'atordoador':
                tipo_proj_npc = 'teleguiado_lento'
                velocidade_proj = VELOCIDADE_PROJ_LENTO
                alvo_player_obj = None
                dist_min_sq_alvo = float('inf')
                for p_state in pve_player_states.values():
                    if p_state['hp'] <= 0: continue
                    p_dist_sq = (npc['x'] - p_state['x'])**2 + (npc['y'] - p_state['y'])**2
                    if p_dist_sq < dist_min_sq_alvo:
                        dist_min_sq_alvo = p_dist_sq
                        alvo_player_obj = p_state
                if alvo_player_obj:
                    alvo_id_proj = alvo_player_obj['nome']
            if tipo_proj_npc == 'normal':
                novo_projetil = {'id': f"{npc['id']}_{agora_ms}", 'owner_nome': npc['id'],
                    'x': npc['x'], 'y': npc['y'], 'pos_inicial_x': npc['x'], 'pos_inicial_y': npc['y'],
                    'angulo_rad': radianos, 'velocidade': velocidade_proj, 'dano': 1, 
                    'tipo': 'npc', 'tipo_proj': 'normal', 'timestamp_criacao': agora_ms
                }
            else: 
                if not alvo_id_proj: return None 
                novo_projetil = {'id': f"{npc['id']}_{agora_ms}", 'owner_nome': npc['id'],
                    'x': npc['x'], 'y': npc['y'], 'pos_inicial_x': npc['x'], 'pos_inicial_y': npc['y'],
                    'vel_x': dir_x * velocidade_proj, 'vel_y': dir_y * velocidade_proj, 
                    'velocidade': velocidade_proj, 'dano': 1, 'tipo': 'npc', 
                    'tipo_proj': tipo_proj_npc, 'alvo_id': alvo_id_proj, 'timestamp_criacao': agora_ms
                }
            return novo_projetil 
    return None
def server_spawnar_inimigo_aleatorio(x, y, npc_id):
    chance = random.random()
    tipo = "perseguidor"; hp = 3; max_hp = 3; tamanho = 30
    cooldown_tiro = COOLDOWN_TIRO_PERSEGUIDOR; pontos = 5
    if chance < 0.05: 
        tipo = "bomba"; hp, max_hp = 1, 1; tamanho = 25
        cooldown_tiro = 999999; pontos = 3
    elif chance < 0.10: 
        tipo = "tiro_rapido"; hp, max_hp = 10, 10; tamanho = 30
        cooldown_tiro = 1500; pontos = 20
    elif chance < 0.15: 
        tipo = "atordoador"; hp, max_hp = 5, 5; tamanho = 30
        cooldown_tiro = 5000; pontos = 25
    elif chance < 0.35: 
        tipo = "atirador_rapido"; hp, max_hp = 1, 1; tamanho = 30
        cooldown_tiro = 500; pontos = 10
    elif chance < 0.55: 
        tipo = "rapido"; hp, max_hp = 5, 5; tamanho = 30
        cooldown_tiro = 800; pontos = 9
    return {'id': npc_id, 'tipo': tipo, 'x': float(x), 'y': float(y), 'angulo': 0.0,
        'hp': hp, 'max_hp': max_hp, 'tamanho': tamanho,
        'cooldown_tiro': cooldown_tiro, 'ultimo_tiro_tempo': 0, 'pontos_por_morte': pontos }
def server_spawnar_mothership(x, y, npc_id):
    mothership = {
        'id': npc_id, 'tipo': 'mothership', 'x': float(x), 'y': float(y), 'angulo': 0.0,
        'hp': 200, 'max_hp': 200, 'tamanho': 80, 'cooldown_tiro': 999999,   
        'ultimo_tiro_tempo': 0, 'pontos_por_morte': 100,
        'ia_estado': 'VAGANDO', 'ia_alvo_retaliacao': None, 'ia_ultimo_hit_tempo': 0,
        'ia_minions_ativos': [] }
    return mothership
def server_spawnar_boss_congelante(x, y, npc_id):
    boss = {
        'id': npc_id, 'tipo': 'boss_congelante', 'x': float(x), 'y': float(y), 'angulo': 0.0,
        'hp': s.HP_BOSS_CONGELANTE, 'max_hp': s.HP_BOSS_CONGELANTE, 'tamanho': 100,             
        'cooldown_tiro': s.COOLDOWN_TIRO_CONGELANTE, 'ultimo_tiro_tempo': 0,
        'pontos_por_morte': s.PONTOS_BOSS_CONGELANTE,
        'ia_ultimo_spawn_minion': 0, 'ia_minions_ativos': [], 'ia_ultimo_hit_tempo': 0,
        'ia_wander_target': None }
    return boss
def debug_dano_npc(owner_nome, npc_id, npc_tipo, dano, hp_antes, hp_depois):
    print(f"[DANO] {owner_nome} → {npc_tipo}#{npc_id}: {dano:.1f} dmg | HP: {hp_antes:.1f} → {hp_depois:.1f}")
def server_spawnar_minion_mothership(owner_npc, alvo_id):
    global next_npc_id
    angulo_rad = random.uniform(0, 2 * math.pi)
    raio_spawn = owner_npc['tamanho'] * 0.8
    spawn_x = owner_npc['x'] + math.cos(angulo_rad) * raio_spawn
    spawn_y = owner_npc['y'] + math.sin(angulo_rad) * raio_spawn
    minion_id = f"minion_ms_{next_npc_id}"; next_npc_id += 1
    minion_npc = {
        'id': minion_id, 'tipo': 'minion_mothership', 'owner_id': owner_npc['id'],
        'x': float(spawn_x), 'y': float(spawn_y), 'angulo': 0.0,
        'hp': 2, 'max_hp': 2, 'tamanho': 15, 'pontos_por_morte': 1,
        'cooldown_tiro': 1000, 'ultimo_tiro_tempo': 0,
        'ia_alvo_id': alvo_id, 'ia_raio_orbita': owner_npc['tamanho'] * 0.8 + random.randint(30, 60),
        'ia_angulo_orbita': random.uniform(0, 360), 'ia_vel_orbita': random.uniform(0.5, 1.0) }
    return minion_npc
def server_spawnar_minion_congelante(owner_npc, alvo_id):
    global next_npc_id
    angulo_rad = random.uniform(0, 2 * math.pi)
    raio_spawn = owner_npc['tamanho'] * 0.7
    spawn_x = owner_npc['x'] + math.cos(angulo_rad) * raio_spawn
    spawn_y = owner_npc['y'] + math.sin(angulo_rad) * raio_spawn
    minion_id = f"minion_bc_{next_npc_id}"; next_npc_id += 1
    minion_npc = {
        'id': minion_id, 'tipo': 'minion_congelante', 'owner_id': owner_npc['id'],
        'x': float(spawn_x), 'y': float(spawn_y), 'angulo': 0.0,
        'hp': HP_MINION_CONGELANTE, 'max_hp': HP_MINION_CONGELANTE, 'tamanho': 18,
        'pontos_por_morte': PONTOS_MINION_CONGELANTE,
        'cooldown_tiro': COOLDOWN_TIRO_MINION_CONGELANTE, 'ultimo_tiro_tempo': 0,
        'ia_alvo_id': alvo_id, 'ia_vel': VELOCIDADE_MINION_CONGELANTE }
    return minion_npc
def update_mothership_logic(npc, all_living_players):
    if npc.get('hp', 0) <= 0: return ([], []) 
    novos_minions = []
    agora = int(time.time() * 1000)
    if (agora - npc.get('ia_ultimo_hit_tempo', 0) < 1000) and npc['ia_alvo_retaliacao'] is None:
        alvo_prox = None; dist_min = float('inf')
        for p in all_living_players:
            dist_sq = (p['x'] - npc['x'])**2 + (p['y'] - npc['y'])**2
            if dist_sq > (NPC_DETECTION_RANGE_SQ * (1.5**2)): continue
            if dist_sq < dist_min: dist_min = dist_sq; alvo_prox = p
        if alvo_prox:
            npc['ia_alvo_retaliacao'] = alvo_prox['nome']
            npc['ia_estado'] = 'RETALIANDO'
            print(f"[LOG] Mothership {npc['id']} retaliando contra {alvo_prox['nome']}")
    if npc['ia_estado'] == 'VAGANDO':
        vec_x = (s.MAP_WIDTH / 2) - npc['x']; vec_y = (s.MAP_HEIGHT / 2) - npc['y']
        dist_sq = vec_x**2 + vec_y**2
        if dist_sq > 50**2:
            dist = math.sqrt(dist_sq)
            npc['x'] += (vec_x / dist) * 0.5 
            npc['y'] += (vec_y / dist) * 0.5
    elif npc['ia_estado'] == 'RETALIANDO':
        alvo_id = npc['ia_alvo_retaliacao']; alvo = None
        for p in all_living_players:
            if p['nome'] == alvo_id: alvo = p; break
        if alvo is None: 
            npc['ia_estado'] = 'VAGANDO'; npc['ia_alvo_retaliacao'] = None
        else:
            minions_vivos = [m_id for m_id in npc['ia_minions_ativos'] if m_id in [n['id'] for n in network_npcs]]
            npc['ia_minions_ativos'] = minions_vivos
            if len(minions_vivos) == 0:
                print(f"[LOG] Mothership {npc['id']} spawnando minions!")
                for _ in range(MAX_MINIONS_MOTHERSHIP):
                    novo_minion = server_spawnar_minion_mothership(npc, alvo_id)
                    novos_minions.append(novo_minion)
                    npc['ia_minions_ativos'].append(novo_minion['id'])
            vec_x = npc['x'] - alvo['x']; vec_y = npc['y'] - alvo['y']
            dist = math.sqrt(vec_x**2 + vec_y**2) + 1e-6
            npc['x'] += (vec_x / dist) * 1.0; npc['y'] += (vec_y / dist) * 1.0
    return ([], novos_minions)
def update_boss_congelante_logic(npc, all_living_players, agora_ms):
    if npc.get('hp', 0) <= 0: return ([], []) 
    novos_projeteis = []; novos_minions = []
    alvo = None; dist_min = float('inf')
    for p in all_living_players:
        dist_sq = (p['x'] - npc['x'])**2 + (p['y'] - npc['y'])**2
        if dist_sq > (NPC_DETECTION_RANGE_SQ * (1.5**2)): continue
        if dist_sq < dist_min: dist_min = dist_sq; alvo = p
    if alvo is None: return ([], []) 
    if agora_ms - npc['ultimo_tiro_tempo'] > npc['cooldown_tiro']:
        npc['ultimo_tiro_tempo'] = agora_ms
        vec_x = alvo['x'] - npc['x']; vec_y = alvo['y'] - npc['y']
        dist = math.sqrt(vec_x**2 + vec_y**2) + 1e-6
        proj_congelante = {'id': f"{npc['id']}_{agora_ms}", 'owner_nome': npc['id'],
            'x': npc['x'], 'y': npc['y'], 'pos_inicial_x': npc['x'], 'pos_inicial_y': npc['y'],
            'vel_x': (vec_x / dist) * VELOCIDADE_PROJ_CONGELANTE, 
            'vel_y': (vec_y / dist) * VELOCIDADE_PROJ_CONGELANTE,
            'velocidade': VELOCIDADE_PROJ_CONGELANTE, 'dano': 1, 'tipo': 'npc', 
            'tipo_proj': 'congelante', 'alvo_id': alvo['nome'], 'timestamp_criacao': agora_ms
        }
        novos_projeteis.append(proj_congelante)
    foi_atacado = agora_ms - npc.get('ia_ultimo_hit_tempo', 0) < 1000
    if foi_atacado and (agora_ms - npc['ia_ultimo_spawn_minion'] > COOLDOWN_SPAWN_MINION_CONGELANTE):
        minions_vivos = [m_id for m_id in npc['ia_minions_ativos'] if m_id in [n['id'] for n in network_npcs]]
        npc['ia_minions_ativos'] = minions_vivos
        if len(minions_vivos) < MAX_MINIONS_CONGELANTE:
            npc['ia_ultimo_spawn_minion'] = agora_ms
            print(f"[LOG] Boss Congelante {npc['id']} spawnando minion!")
            novo_minion = server_spawnar_minion_congelante(npc, alvo['nome'])
            novos_minions.append(novo_minion)
            npc['ia_minions_ativos'].append(novo_minion['id'])
    if npc['ia_wander_target'] is None or (npc['x'] - npc['ia_wander_target'][0])**2 + (npc['y'] - npc['ia_wander_target'][1])**2 < 100**2:
        target_x = random.randint(100, s.MAP_WIDTH - 100)
        target_y = random.randint(100, s.MAP_HEIGHT - 100)
        npc['ia_wander_target'] = (target_x, target_y)
    target_x, target_y = npc['ia_wander_target']
    vec_x = target_x - npc['x']; vec_y = target_y - npc['y']
    dist = math.sqrt(vec_x**2 + vec_y**2) + 1e-6
    if dist > 5:
        npc['x'] += (vec_x / dist) * 1.0; npc['y'] += (vec_y / dist) * 1.0
    return (novos_projeteis, novos_minions)
def update_minion_logic(npc, all_living_players, agora_ms):
    if npc.get('hp', 0) <= 0: return [] 
    alvo_id = npc.get('ia_alvo_id'); alvo = None
    if alvo_id:
        for p in all_living_players:
            if p['nome'] == alvo_id: alvo = p; break
    if alvo is None:
        dist_min = float('inf')
        for p in all_living_players:
            dist_sq = (p['x'] - npc['x'])**2 + (p['y'] - npc['y'])**2
            if dist_sq > (NPC_DETECTION_RANGE_SQ * (1.5**2)): continue
            if dist_sq < dist_min: dist_min = dist_sq; alvo = p
    
    owner = None
    owner_id = npc.get('owner_id')
    if owner_id:
        for n_owner in network_npcs: 
            if n_owner['id'] == owner_id: owner = n_owner; break
    if owner is None: npc['hp'] = 0; return []

    novos_projeteis = []
    if npc['tipo'] == 'minion_mothership':
        npc['ia_angulo_orbita'] = (npc['ia_angulo_orbita'] + npc['ia_vel_orbita']) % 360
        rad = math.radians(npc['ia_angulo_orbita']); raio = npc['ia_raio_orbita']
        pos_alvo_orbita_x = owner['x'] + math.cos(rad) * raio
        pos_alvo_orbita_y = owner['y'] + math.sin(rad) * raio
        npc['x'] = npc['x'] + (pos_alvo_orbita_x - npc['x']) * 0.05
        npc['y'] = npc['y'] + (pos_alvo_orbita_y - npc['y']) * 0.05
        
        if alvo: 
            vec_x = alvo['x'] - npc['x']; vec_y = alvo['y'] - npc['y']
            dist_sq_alvo = vec_x**2 + vec_y**2
            if dist_sq_alvo < 500**2 and (agora_ms - npc['ultimo_tiro_tempo'] > npc['cooldown_tiro']):
                npc['ultimo_tiro_tempo'] = agora_ms
                dist = math.sqrt(dist_sq_alvo) + 1e-6
                proj = {'id': f"{npc['id']}_{agora_ms}", 'owner_nome': npc['id'],
                    'x': npc['x'], 'y': npc['y'], 'pos_inicial_x': npc['x'], 'pos_inicial_y': npc['y'],
                    'angulo_rad': math.atan2(vec_y, vec_x), 'velocidade': VELOCIDADE_PROJETIL_NPC, 
                    'dano': 1, 'tipo': 'npc', 'tipo_proj': 'normal', 'timestamp_criacao': agora_ms }
                novos_projeteis.append(proj)
    elif npc['tipo'] == 'minion_congelante':
        target_in_leash = False
        if alvo:
            try:
                dist_dono_alvo_sq = (owner['x'] - alvo['x'])**2 + (owner['y'] - alvo['y'])**2
                if dist_dono_alvo_sq < (s.MINION_CONGELANTE_LEASH_RANGE ** 2):
                    target_in_leash = True
            except (ValueError, KeyError): target_in_leash = False
        pos_alvo_seguir_x = owner['x']; pos_alvo_seguir_y = owner['y']
        is_attacking = False
        if target_in_leash:
            pos_alvo_seguir_x = alvo['x']; pos_alvo_seguir_y = alvo['y']
            is_attacking = True
        else:
            pos_alvo_seguir_x = owner['x']; pos_alvo_seguir_y = owner['y']
            is_attacking = False
        vec_x = pos_alvo_seguir_x - npc['x']; vec_y = pos_alvo_seguir_y - npc['y']
        dist_sq = vec_x**2 + vec_y**2; dist = math.sqrt(dist_sq) + 1e-6
        distancia_parar = 150; distancia_orbita_dono = 100 
        if is_attacking and dist > distancia_parar:
            npc['x'] += (vec_x / dist) * VELOCIDADE_MINION_CONGELANTE
            npc['y'] += (vec_y / dist) * VELOCIDADE_MINION_CONGELANTE
        elif not is_attacking and dist > distancia_orbita_dono:
            npc['x'] += (vec_x / dist) * (VELOCIDADE_MINION_CONGELANTE * 0.8) 
            npc['y'] += (vec_y / dist) * (VELOCIDADE_MINION_CONGELANTE * 0.8)
        
        if is_attacking and dist_sq < (400**2) and (agora_ms - npc['ultimo_tiro_tempo'] > npc['cooldown_tiro']):
            npc['ultimo_tiro_tempo'] = agora_ms
            proj = {'id': f"{npc['id']}_{agora_ms}", 'owner_nome': npc['id'],
                'x': npc['x'], 'y': npc['y'], 'pos_inicial_x': npc['x'], 'pos_inicial_y': npc['y'],
                'angulo_rad': math.atan2(vec_y, vec_x), 'velocidade': VELOCIDADE_PROJETIL_NPC, 
                'dano': 1, 'tipo': 'npc', 'tipo_proj': 'normal', 'timestamp_criacao': agora_ms }
            novos_projeteis.append(proj)
    return novos_projeteis


# --- INÍCIO: MODIFICAÇÃO (Game Loop dividido) ---
def game_loop(bot_manager): 
    """ O loop principal do servidor. """
    global next_npc_id, network_npcs, pve_network_projectiles, pvp_network_projectiles
    global pvp_lobby_state, pvp_lobby_countdown_end, pvp_pre_match_countdown_end
    global pvp_match_countdown_end, pvp_winner_name
    
    print("[LOG] [GAME LOOP INICIADO] O servidor está agora a calcular e a enviar o estado.")
    TICK_INTERVAL = 1.0 / TICK_RATE 
    
    while True:
        loop_start_time = time.time()
        agora_ms = int(time.time() * 1000) 
        
        novos_projeteis_pve = []
        novos_projeteis_pvp = []
        novos_npcs_pve = []

        with game_state_lock:
            if s.DANO_POR_NIVEL is None or s.VIDA_POR_NIVEL is None:
                print("[ERRO FATAL] s.DANO_POR_NIVEL ou s.VIDA_POR_NIVEL não foram carregados. Loop pausado.")
                time.sleep(1)
                continue
            
            # --- LÓGICA 1: ATUALIZAR ESTADO PVE ---
            novos_proj_pve, novos_npcs = _update_pve_game_state(bot_manager, agora_ms)
            novos_projeteis_pve.extend(novos_proj_pve)
            novos_npcs_pve.extend(novos_npcs)
            
            # --- LÓGICA 2: ATUALIZAR ESTADO PVP ---
            novos_proj_pvp = _update_pvp_game_state(agora_ms)
            novos_projeteis_pvp.extend(novos_proj_pvp)

            pve_network_projectiles.extend(novos_projeteis_pve)
            pvp_network_projectiles.extend(novos_projeteis_pvp)
            network_npcs.extend(novos_npcs_pve) 

            # --- LÓGICA 3: CONSTRUIR E ENVIAR ESTADOS ---
            
            # --- Pacote PVE ---
            lista_estados_pve = _build_player_state_list(pve_player_states, agora_ms)
            payload_players_pve = ";".join(lista_estados_pve)
            lista_projeteis_pve = [f"{proj['id']}:{proj['x']:.1f}:{proj['y']:.1f}:{proj['tipo']}:{proj.get('tipo_proj', 'normal')}" 
                                 for proj in pve_network_projectiles]
            payload_proj_pve = ";".join(lista_projeteis_pve)
            lista_de_npcs = [f"{npc['id']}:{npc['tipo']}:{npc['x']:.1f}:{npc['y']:.1f}:{npc['angulo']:.0f}:{npc['hp']}:{npc['max_hp']}:{npc['tamanho']}"
                            for npc in network_npcs if npc.get('hp', 0) > 0]
            payload_npcs = ";".join(lista_de_npcs)
            pve_message = f"STATE|{payload_players_pve}|PROJ|{payload_proj_pve}|NPC|{payload_npcs}\n"
            pve_message_bytes = pve_message.encode('utf-8')
            
            # --- Pacote PVP ---
            lista_estados_pvp = _build_player_state_list(pvp_player_states, agora_ms)
            payload_players_pvp = ";".join(lista_estados_pvp)
            lista_projeteis_pvp = [f"{proj['id']}:{proj['x']:.1f}:{proj['y']:.1f}:{proj['tipo']}:{proj.get('tipo_proj', 'normal')}" 
                                 for proj in pvp_network_projectiles]
            payload_proj_pvp = ";".join(lista_projeteis_pvp)
            pvp_message = f"STATE|{payload_players_pvp}|PROJ|{payload_proj_pvp}|NPC|\n"
            pvp_message_bytes = pvp_message.encode('utf-8')


            # --- INÍCIO: MODIFICAÇÃO (Problema 2 e 3: Enviar timers PVP) ---
            # --- Pacote de Status PVP (Lobby E Partida) ---
            pvp_status_message_bytes = None
            
            # Apenas envia status se houver jogadores PVP para receber
            if pvp_player_states:
                # 1. Calcular contagem do Lobby (30s)
                contagem_segundos_lobby = 0
                if pvp_lobby_state == "COUNTDOWN":
                    contagem_segundos_lobby = max(0, int((pvp_lobby_countdown_end - agora_ms) / 1000))
                
                # 2. Calcular contagem da Partida (3min)
                match_countdown_sec = 0
                if pvp_lobby_state == "PLAYING" or pvp_lobby_state == "PRE_MATCH":
                    match_countdown_sec = max(0, int((pvp_match_countdown_end - agora_ms) / 1000))
                
                # 3. Montar a mensagem
                #    Formato: STATUS|Jogadores|TempoLobby|TempoPartida
                status_msg = f"PVP_STATUS_UPDATE|{len(pvp_player_states)}|{contagem_segundos_lobby}|{match_countdown_sec}\n"
                pvp_status_message_bytes = status_msg.encode('utf-8')
            # --- FIM: MODIFICAÇÃO ---
            

            # --- LÓGICA 4: ENVIAR PARA OS CLIENTES CORRETOS ---
            clientes_mortos = []
            
            for conn_key, state in pve_player_states.items():
                if state.get('handshake_completo', False) and state.get('conn') is not None:
                    try:
                        state['conn'].sendall(pve_message_bytes)
                    except (socket.error, BrokenPipeError):
                        clientes_mortos.append(conn_key)

            for conn_key, state in pvp_player_states.items():
                if state.get('handshake_completo', False) and state.get('conn') is not None:
                    try:
                        # --- INÍCIO: MODIFICAÇÃO (Envia a nova mensagem de status) ---
                        if pvp_status_message_bytes:
                            state['conn'].sendall(pvp_status_message_bytes)
                        # --- FIM: MODIFICAÇÃO ---
                        state['conn'].sendall(pvp_message_bytes)
                    except (socket.error, BrokenPipeError):
                        clientes_mortos.append(conn_key)

        # --- Limpeza de Conexões Mortas ---
        if clientes_mortos:
            with game_state_lock:
                for conn_key in clientes_mortos:
                    conn = None
                    if conn_key in pve_player_states:
                        conn = pve_player_states[conn_key].get('conn')
                        del pve_player_states[conn_key]
                    elif conn_key in pvp_player_states:
                        conn = pvp_player_states[conn_key].get('conn')
                        del pvp_player_states[conn_key]
                    
                    if conn:
                        try: conn.close() 
                        except: pass
        
        time_elapsed = time.time() - loop_start_time
        sleep_time = TICK_INTERVAL - time_elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

def _build_player_state_list(player_dict, agora_ms):
    """ Helper para construir a string de estado dos jogadores. """
    lista_de_estados = []
    for state in player_dict.values():
        if state.get('handshake_completo', True):
            regen_status = 1 if state.get('esta_regenerando', False) else 0
            is_lento = 1 if agora_ms < state.get('tempo_fim_lentidao', 0) else 0
            is_congelado = 1 if agora_ms < state.get('tempo_fim_congelamento', 0) else 0
            
            is_pre_match = 1 if state.get('is_pre_match', False) else 0
            
            estado_str = (
                f"{state['nome']}:{state['x']:.1f}:{state['y']:.1f}:{state['angulo']:.0f}:{state['hp']:.1f}:{state['max_hp']:.1f}"
                f":{state['pontos']}:{regen_status}"
                f":{state['pontos_upgrade_disponiveis']}:{state['total_upgrades_feitos']}"
                f":{state['nivel_motor']}:{state['nivel_dano']}:{state['nivel_max_vida']}"
                f":{state['nivel_escudo']}:{state['nivel_aux']}"
                f":{is_lento}:{is_congelado}:{is_pre_match}" # <-- Campo 18
            )
            lista_de_estados.append(estado_str)
    return lista_de_estados

def _update_pve_game_state(bot_manager, agora_ms):
    """ Processa toda a lógica do PVE (antigo game_loop). """
    global next_npc_id, network_npcs, pve_network_projectiles 
    
    novos_projeteis_de_players = []
    novos_projeteis_de_npcs = []
    novos_npcs_spawnados = [] 
    
    projeteis_para_remover = [] 
    npcs_para_remover = [] 
    
    bots_para_remover = bot_manager.manage_bot_population(MAX_BOTS_ONLINE)

    all_living_pve_players = []
    if pve_player_states:
        try:
            all_living_pve_players = [p for p in pve_player_states.values() 
                                     if p.get('handshake_completo', True) and p.get('hp', 0) > 0]
        except RuntimeError: pass 

    posicoes_jogadores_pve_vivos = [(state['x'], state['y']) for state in all_living_pve_players]

    for state in all_living_pve_players:
        if state.get('is_bot', False):
            bot_manager.process_bot_logic(state, all_living_pve_players, agora_ms)
        
        novo_proj = update_player_logic(state, agora_ms, s.MAP_WIDTH, s.MAP_HEIGHT) 
        if novo_proj:
            novos_projeteis_de_players.append(novo_proj)
            
        num_aux = state.get('nivel_aux', 0)
        if num_aux > 0 and state.get('alvo_lock'):
            target_id = state['alvo_lock']
            alvo_coords_aux = None; alvo_vivo_aux = False
            alvo_npc = next((npc for npc in network_npcs if npc['id'] == target_id and npc.get('hp', 0) > 0), None)
            if alvo_npc:
                alvo_coords_aux = (alvo_npc['x'], alvo_npc['y']); alvo_vivo_aux = True
            else:
                alvo_player = next((p for p in all_living_pve_players if p['nome'] == target_id), None)
                if alvo_player:
                    alvo_coords_aux = (alvo_player['x'], alvo_player['y']); alvo_vivo_aux = True
            if alvo_vivo_aux:
                alvo_aux_x, alvo_aux_y = alvo_coords_aux
                for i in range(num_aux):
                    if agora_ms > state['aux_cooldowns'][i]:
                        offset_vec = AUX_POSICOES[i]; rotated_vec = offset_vec.rotate(-state['angulo'])
                        aux_x = state['x'] + rotated_vec.x; aux_y = state['y'] + rotated_vec.y
                        dist_sq = (alvo_aux_x - aux_x)**2 + (alvo_aux_y - aux_y)**2
                        if dist_sq < AUX_DISTANCIA_TIRO_SQ:
                            state['aux_cooldowns'][i] = agora_ms + AUX_COOLDOWN_TIRO
                            radianos = math.radians(state['angulo'])
                            vel_x_inicial = -math.sin(radianos) * 14; vel_y_inicial = -math.cos(radianos) * 14
                            dano_calculado_aux = s.DANO_POR_NIVEL[state['nivel_dano']]
                            proj_aux = {'id': f"{state['nome']}_aux{i}_{agora_ms}", 'owner_nome': state['nome'], 
                                'x': aux_x, 'y': aux_y, 'pos_inicial_x': aux_x, 'pos_inicial_y': aux_y, 
                                'dano': dano_calculado_aux, 'tipo': 'player_pve', 'timestamp_criacao': agora_ms, 
                                'tipo_proj': 'teleguiado', 'velocidade': 14, 'alvo_id': target_id,
                                'vel_x': vel_x_inicial, 'vel_y': vel_y_inicial}
                            novos_projeteis_de_players.append(proj_aux)

    for state in all_living_pve_players:
        if state.get('esta_regenerando', False):
            if not state.get('is_bot', False): 
                if (state['teclas']['w'] or state['teclas']['a'] or 
                     state['teclas']['s'] or state['teclas']['d'] or state['alvo_mouse'] is not None):
                    state['esta_regenerando'] = False
            
            if state['hp'] >= state['max_hp']:
                state['hp'] = state['max_hp']
                state['esta_regenerando'] = False
            
            elif state['esta_regenerando'] and (agora_ms - state.get('ultimo_tick_regeneracao', 0) > REGEN_TICK_RATE_MS):
                state['ultimo_tick_regeneracao'] = agora_ms
                state['hp'] = min(state['max_hp'], state['hp'] + REGEN_POR_TICK)
                state['ultimo_hit_tempo'] = agora_ms 

    pve_network_projectiles.extend(novos_projeteis_de_players)

    for proj in pve_network_projectiles:
        if proj in projeteis_para_remover: continue
        tipo_proj_mov = proj.get('tipo_proj', 'normal')
        
        if tipo_proj_mov in ['teleguiado', 'teleguiado_lento', 'congelante']:
            duracao_max = DURACAO_PROJETIL_TELE_MS
            if tipo_proj_mov == 'teleguiado_lento': duracao_max = DURACAO_PROJ_LENTO_MS
            elif tipo_proj_mov == 'congelante': duracao_max = DURACAO_PROJ_CONGELANTE_MS
            
            if agora_ms - proj.get('timestamp_criacao', 0) > duracao_max:
                projeteis_para_remover.append(proj); continue
                
            alvo_id = proj.get('alvo_id'); alvo_entidade = None 
            if alvo_id:
                if proj['tipo'] == 'player_pve': 
                    alvo_entidade = next((npc for npc in network_npcs if npc['id'] == alvo_id and npc.get('hp', 0) > 0), None)
                    if not alvo_entidade:
                        alvo_entidade = next((p for p_name, p in pve_player_states.items() if p_name == alvo_id and p['hp'] > 0), None)
                else: 
                    alvo_entidade = next((p for p_name, p in pve_player_states.items() if p_name == alvo_id and p['hp'] > 0), None)
            
            if alvo_entidade:
                try:
                    vec_para_alvo_x = alvo_entidade['x'] - proj['x']
                    vec_para_alvo_y = alvo_entidade['y'] - proj['y']
                    dist = math.sqrt(vec_para_alvo_x**2 + vec_para_alvo_y**2)
                    if dist > 0:
                        ideal_vel_x = (vec_para_alvo_x / dist) * proj['velocidade']
                        ideal_vel_y = (vec_para_alvo_y / dist) * proj['velocidade']
                        proj['vel_x'] = proj['vel_x'] + (ideal_vel_x - proj['vel_x']) * TURN_SPEED_TELE
                        proj['vel_y'] = proj['vel_y'] + (ideal_vel_y - proj['vel_y']) * TURN_SPEED_TELE
                except (ValueError, KeyError, AttributeError): pass 
            
            proj['x'] += proj.get('vel_x', 0)
            proj['y'] += proj.get('vel_y', 0)

        elif tipo_proj_mov == 'normal' and proj['tipo'] == 'player_pve': 
            proj['x'] += proj.get('vel_x', 0)
            proj['y'] += proj.get('vel_y', 0)
        elif tipo_proj_mov == 'normal' and proj['tipo'] == 'npc':
            proj['x'] += math.cos(proj['angulo_rad']) * proj['velocidade']
            proj['y'] += math.sin(proj['angulo_rad']) * proj['velocidade']

        dist_sq = (proj['x'] - proj['pos_inicial_x'])**2 + (proj['y'] - proj['pos_inicial_y'])**2
        if dist_sq > s.MAX_DISTANCIA_TIRO**2:
            projeteis_para_remover.append(proj)
        elif not s.MAP_RECT.collidepoint((proj['x'], proj['y'])):
            projeteis_para_remover.append(proj)

    ids_npcs_mortos_neste_tick = set()

    projeteis_ativos = pve_network_projectiles[:]
    for proj in projeteis_ativos:
        if proj in projeteis_para_remover: continue
        
        if proj['tipo'] == 'player_pve': 
            
            owner_state = None
            owner_nome_proj = proj.get('owner_nome')
            if owner_nome_proj:
                try:
                    for state in pve_player_states.values(): 
                        if state.get('nome') == owner_nome_proj:
                            owner_state = state; break
                except RuntimeError: pass 
            
            dano_real = proj.get('dano', 1.0) 
            
            for npc in network_npcs:
                if npc in npcs_para_remover: continue 
                if npc.get('hp', 0) <= 0: continue
                dist_colisao_sq = ( (npc['tamanho']/2 + 5)**2 ) 
                dist_sq = (npc['x'] - proj['x'])**2 + (npc['y'] - proj['y'])**2
                
                if dist_sq < dist_colisao_sq:
                    hp_antes = npc['hp']
                    npc['hp'] -= dano_real
                    if npc['tipo'] in ['mothership', 'boss_congelante']:
                        npc['ia_ultimo_hit_tempo'] = agora_ms
                    projeteis_para_remover.append(proj) 
                    if npc['hp'] <= 0:
                        npcs_para_remover.append(npc) 
                        ids_npcs_mortos_neste_tick.add(npc['id'])
                        if owner_state: 
                            server_ganhar_pontos(owner_state, npc.get('pontos_por_morte', 5))
                            print(f"[KILL] {owner_state['nome']} destruiu {npc['tipo']}#{npc['id']} (+{npc.get('pontos_por_morte', 5)} pts)")
                    break 
            
            if proj in projeteis_para_remover: continue 
            
            for target_state in all_living_pve_players:
                if target_state['nome'] == proj['owner_nome']: continue 
                if target_state.get('invencivel', False): continue
                dist_sq = (target_state['x'] - proj['x'])**2 + (target_state['y'] - proj['y'])**2
                if dist_sq < COLISAO_JOGADOR_PROJ_DIST_SQ:
                    if agora_ms - target_state.get('ultimo_hit_tempo', 0) > 150:
                        dano_real_pvp = proj.get('dano', 1.0) 
                        reducao_percent = min(target_state['nivel_escudo'] * s.REDUCAO_DANO_POR_NIVEL, 75)
                        dano_reduzido = dano_real_pvp * (1 - reducao_percent / 100.0)
                        target_state['hp'] -= dano_reduzido
                        target_state['ultimo_hit_tempo'] = agora_ms
                        target_state['esta_regenerando'] = False 
                        projeteis_para_remover.append(proj) 
                        if target_state['hp'] <= 0:
                            if owner_state: server_ganhar_pontos(owner_state, 10) 
                        break 
        
        elif proj['tipo'] == 'npc':
            for player_state in all_living_pve_players: 
                if player_state.get('invencivel', False): continue
                dist_sq = (player_state['x'] - proj['x'])**2 + (player_state['y'] - proj['y'])**2
                if dist_sq < COLISAO_JOGADOR_PROJ_DIST_SQ:
                    if agora_ms - player_state.get('ultimo_hit_tempo', 0) > 150:
                        proj_tipo = proj.get('tipo_proj', 'normal')
                        if proj_tipo == 'teleguiado_lento':
                            player_state['tempo_fim_lentidao'] = agora_ms + DURACAO_LENTIDAO_MS
                        elif proj_tipo == 'congelante':
                            player_state['tempo_fim_congelamento'] = agora_ms + DURACAO_CONGELAMENTO_MS
                        
                        reducao_percent = min(player_state['nivel_escudo'] * s.REDUCAO_DANO_POR_NIVEL, 75)
                        dano_reduzido = proj['dano'] * (1 - reducao_percent / 100.0)
                        player_state['hp'] -= dano_reduzido
                        player_state['ultimo_hit_tempo'] = agora_ms
                        player_state['esta_regenerando'] = False 
                        
                        if player_state.get('is_bot', False):
                            player_state['bot_last_attacker_id'] = proj.get('owner_nome')
                        
                        projeteis_para_remover.append(proj) 
                        if player_state['hp'] <= 0:
                            print(f"[LOG] Jogador {player_state['nome']} morreu!")
                        break 
            
    for npc in network_npcs:
        if npc in npcs_para_remover: continue
        if npc.get('hp', 0) <= 0: continue
        if 'minion' in npc['tipo'] or npc['tipo'] in ['bomba', 'perseguidor', 'rapido']: 
            for player_state in all_living_pve_players:
                if player_state.get('invencivel', False): continue
                dist_sq = (player_state['x'] - npc['x'])**2 + (player_state['y'] - npc['y'])**2
                if dist_sq < COLISAO_JOGADOR_NPC_DIST_SQ: 
                    if agora_ms - player_state.get('ultimo_hit_tempo', 0) > 300: 
                        dano_ram = 3 if npc['tipo'] == 'bomba' else 1
                        reducao_percent = min(player_state['nivel_escudo'] * s.REDUCAO_DANO_POR_NIVEL, 75)
                        dano_reduzido = dano_ram * (1 - reducao_percent / 100.0)
                        player_state['hp'] -= dano_reduzido
                        player_state['ultimo_hit_tempo'] = agora_ms
                        player_state['esta_regenerando'] = False 
                        
                        if player_state.get('is_bot', False):
                            player_state['bot_last_attacker_id'] = npc.get('id')

                        if npc['tipo'] in ['bomba', 'minion_mothership', 'minion_congelante']:
                            npc['hp'] = 0 
                            npcs_para_remover.append(npc)
                            ids_npcs_mortos_neste_tick.add(npc['id'])
                            
                        if player_state['hp'] <= 0:
                            print(f"[LOG] Jogador {player_state['nome']} morreu por colisão!")
                        break

    if projeteis_para_remover:
        ids_projeteis_remover = {proj['id'] for proj in projeteis_para_remover}
        pve_network_projectiles = [p for p in pve_network_projectiles if p['id'] not in ids_projeteis_remover]

    if npcs_para_remover:
        ids_npcs_mortos = {n['id'] for n in npcs_para_remover}
        for n_boss in network_npcs:
            if n_boss['tipo'] in ['mothership', 'boss_congelante']:
                n_boss['ia_minions_ativos'] = [m_id for m_id in n_boss['ia_minions_ativos'] 
                                                if m_id not in ids_npcs_mortos]
        ids_bosses_mortos = {n['id'] for n in npcs_para_remover 
                            if n['tipo'] in ['mothership', 'boss_congelante']}
        minions_orfaos = []
        if ids_bosses_mortos:
            for npc in network_npcs:
                if npc['tipo'] in ['minion_mothership', 'minion_congelante']:
                    owner_id = npc.get('owner_id')
                    if owner_id in ids_bosses_mortos:
                        minions_orfaos.append(npc)
        
        npcs_para_remover.extend(minions_orfaos)
        ids_npcs_mortos.update({n['id'] for n in minions_orfaos})
        network_npcs = [n for n in network_npcs if n['id'] not in ids_npcs_mortos]
        
        try:
            for state in list(pve_player_states.values()): 
                if state.get('alvo_lock') in ids_npcs_mortos:
                    state['alvo_lock'] = None
        except RuntimeError: print("[AVISO] RuntimeError ao limpar alvo_lock PVE.")

    if bots_para_remover:
        for nome_bot in bots_para_remover:
            if nome_bot in pve_player_states:
                del pve_player_states[nome_bot]

    if posicoes_jogadores_pve_vivos: 
        npcs_para_processar = network_npcs[:]
        for npc in npcs_para_processar: 
            if npc.get('hp', 0) <= 0: continue
            
            if npc['tipo'] == 'mothership':
                novos_proj, novos_minions = update_mothership_logic(npc, all_living_pve_players)
                novos_projeteis_de_npcs.extend(novos_proj); novos_npcs_spawnados.extend(novos_minions)
            elif npc['tipo'] == 'boss_congelante':
                novos_proj, novos_minions = update_boss_congelante_logic(npc, all_living_pve_players, agora_ms)
                novos_projeteis_de_npcs.extend(novos_proj); novos_npcs_spawnados.extend(novos_minions)
            elif 'minion' in npc['tipo']:
                novos_proj = update_minion_logic(npc, all_living_pve_players, agora_ms)
                novos_projeteis_de_npcs.extend(novos_proj)
            else:
                novo_proj = update_npc_logic(npc, posicoes_jogadores_pve_vivos, agora_ms) 
                if novo_proj: novos_projeteis_de_npcs.append(novo_proj)
    
    if posicoes_jogadores_pve_vivos:
        contagem_inimigos_normais = sum(1 for npc in network_npcs 
            if npc.get('hp', 0) > 0 and npc['tipo'] not in ['mothership', 'boss_congelante', 'minion_mothership', 'minion_congelante'])
        contagem_motherships = sum(1 for npc in network_npcs if npc.get('hp', 0) > 0 and npc['tipo'] == 'mothership')
        contagem_boss_congelante = sum(1 for npc in network_npcs if npc.get('hp', 0) > 0 and npc['tipo'] == 'boss_congelante')
        
        if contagem_inimigos_normais < s.MAX_INIMIGOS:
            spawn_x, spawn_y = server_calcular_posicao_spawn(posicoes_jogadores_pve_vivos, s.MAP_WIDTH, s.MAP_HEIGHT)
            novo_npc = server_spawnar_inimigo_aleatorio(spawn_x, spawn_y, f"npc_{next_npc_id}")
            novos_npcs_spawnados.append(novo_npc); next_npc_id += 1
        
        if contagem_motherships < s.MAX_MOTHERSHIPS:
            spawn_x, spawn_y = server_calcular_posicao_spawn(posicoes_jogadores_pve_vivos, s.MAP_WIDTH, s.MAP_HEIGHT)
            novo_boss = server_spawnar_mothership(spawn_x, spawn_y, f"ms_{next_npc_id}")
            novos_npcs_spawnados.append(novo_boss); next_npc_id += 1
        
        if contagem_boss_congelante < s.MAX_BOSS_CONGELANTE:
            spawn_x, spawn_y = server_calcular_posicao_spawn(posicoes_jogadores_pve_vivos, s.MAP_WIDTH, s.MAP_HEIGHT)
            novo_boss = server_spawnar_boss_congelante(spawn_x, spawn_y, f"bc_{next_npc_id}")
            novos_npcs_spawnados.append(novo_boss); next_npc_id += 1

    return novos_projeteis_de_npcs, novos_npcs_spawnados

def _reset_pvp_lobby():
    """ Helper interno para resetar o estado do lobby PVP para WAITING. """
    global pvp_lobby_state, pvp_lobby_countdown_end, pvp_pre_match_countdown_end
    global pvp_match_countdown_end, pvp_winner_name, pvp_network_projectiles
    
    print("[PVP] Resetando lobby para o estado 'WAITING'.")
    pvp_lobby_state = "WAITING"
    pvp_lobby_countdown_end = 0
    pvp_pre_match_countdown_end = 0
    pvp_match_countdown_end = 0
    pvp_winner_name = ""
    pvp_network_projectiles.clear() # Limpa projéteis da partida anterior
    
    # Zera o 'is_pre_match' de todos os jogadores que ainda possam estar conectados
    for state in pvp_player_states.values():
        state['is_pre_match'] = False
        # Manda os jogadores de volta para o spawn do lobby
        state['x'] = pvp_s.SPAWN_LOBBY.x
        state['y'] = pvp_s.SPAWN_LOBBY.y


def _update_pvp_game_state(agora_ms):
    """ Processa toda a lógica do PVP (Lobby, Jogo, Colisões). """
    global pvp_network_projectiles, pvp_lobby_state, pvp_lobby_countdown_end
    global pvp_pre_match_countdown_end, pvp_match_countdown_end, pvp_winner_name

    novos_projeteis_de_players = []
    projeteis_para_remover = [] 
    
    # --- INÍCIO: CORREÇÃO (Requisito 1: Encerrar se todos saírem) ---
    # Se a partida já começou (não está em WAITING) e não há mais jogadores
    if pvp_lobby_state != "WAITING" and not pvp_player_states:
        print("[PVP] Todos os jogadores saíram. Resetando lobby.")
        _reset_pvp_lobby() # Chama a nova função de reset
        return [] # Retorna cedo, sem mais lógica PVP
    # --- FIM: CORREÇÃO ---

    # --- PARTE 1: Gerenciar Estado do Lobby/Partida ---
    
    if pvp_lobby_state == "WAITING":
        if len(pvp_player_states) >= MAX_JOGADORES_PVP:
            print("[PVP] Lobby cheio! Iniciando contagem de 30s.")
            pvp_lobby_state = "COUNTDOWN"
            pvp_lobby_countdown_end = agora_ms + LOBBY_COUNTDOWN_MS
    
    elif pvp_lobby_state == "COUNTDOWN":
        if len(pvp_player_states) < MAX_JOGADORES_PVP:
            print("[PVP] Jogador saiu durante a contagem. Voltando a esperar.")
            _reset_pvp_lobby() # Reseta para WAITING
        elif agora_ms > pvp_lobby_countdown_end:
            print("[PVP] Contagem do lobby terminada. Iniciando Pré-Partida (5s).")
            pvp_lobby_state = "PRE_MATCH"
            pvp_pre_match_countdown_end = agora_ms + PRE_MATCH_FREEZE_MS
            # Define o timer final da partida AGORA
            pvp_match_countdown_end = agora_ms + PRE_MATCH_FREEZE_MS + PARTIDA_COUNTDOWN_MS 
            
            jogadores_para_spawnar = list(pvp_player_states.values())
            for i, state in enumerate(jogadores_para_spawnar):
                if i < len(pvp_s.SPAWN_POSICOES):
                    pos_canto = pvp_s.SPAWN_POSICOES[i]
                    state['x'] = pos_canto.x
                    state['y'] = pos_canto.y
                    state['hp'] = state['max_hp'] 
                    state['esta_regenerando'] = False
                    state['alvo_lock'] = None
                    state['alvo_mouse'] = None
                    state['is_pre_match'] = True 

    elif pvp_lobby_state == "PRE_MATCH":
        if agora_ms > pvp_pre_match_countdown_end:
            print("[PVP] Pré-partida terminada. A PARTIDA COMEÇOU!")
            pvp_lobby_state = "PLAYING"
            # O timer da partida (pvp_match_countdown_end) JÁ FOI DEFINIDO acima
            for state in pvp_player_states.values():
                state['is_pre_match'] = False
    
    elif pvp_lobby_state == "PLAYING":
        jogadores_vivos = [p for p in pvp_player_states.values() if p['hp'] > 0]
        
        if len(jogadores_vivos) <= 1:
            pvp_lobby_state = "GAME_OVER"
            pvp_winner_name = jogadores_vivos[0]['nome'] if jogadores_vivos else "Empate"
            # --- INÍCIO: CORREÇÃO (Requisito 2: Timer de Reset) ---
            # Usa 'pvp_pre_match_countdown_end' como timer de reset de 10s
            pvp_pre_match_countdown_end = agora_ms + 10000 
            print(f"[PVP] Partida terminada (Morte Súbita). Vencedor: {pvp_winner_name}. Resetando em 10s.")
            # --- FIM: CORREÇÃO ---
        elif agora_ms > pvp_match_countdown_end:
            pvp_lobby_state = "GAME_OVER"
            jogadores_vivos.sort(key=lambda p: p['hp'], reverse=True)
            pvp_winner_name = jogadores_vivos[0]['nome'] if jogadores_vivos else "Empate"
            # --- INÍCIO: CORREÇÃO (Requisito 2: Timer de Reset) ---
            # Usa 'pvp_pre_match_countdown_end' como timer de reset de 10s
            pvp_pre_match_countdown_end = agora_ms + 10000 
            print(f"[PVP] Partida terminada (Tempo). Vencedor: {pvp_winner_name}. Resetando em 10s.")
            # --- FIM: CORREÇÃO ---
    
    # --- INÍCIO: CORREÇÃO (Requisito 2: Lógica de Reset) ---
    elif pvp_lobby_state == "GAME_OVER":
        # Checa o timer de 10s (que guardamos em 'pvp_pre_match_countdown_end')
        if agora_ms > pvp_pre_match_countdown_end: 
            print("[PVP] Timer de Fim de Jogo terminou. Resetando para WAITING.")
            _reset_pvp_lobby() # Chama a nova função de reset
    # --- FIM: CORREÇÃO ---

    # --- PARTE 2: Atualizar Jogadores PVP (Movimento, Tiros) ---
    all_living_pvp_players = [p for p in pvp_player_states.values() if p.get('handshake_completo', True) and p['hp'] > 0]

    for state in pvp_player_states.values(): 
        # Só atualiza a lógica (mover, atirar) se o jogador ESTIVER VIVO
        if state.get('hp', 0) > 0:
            novo_proj = update_player_logic(state, agora_ms, pvp_s.MAP_WIDTH, pvp_s.MAP_HEIGHT) 
            if novo_proj:
                novos_projeteis_de_players.append(novo_proj)
            
    pvp_network_projectiles.extend(novos_projeteis_de_players)

    # --- PARTE 3: Mover Projéteis PVP ---
    for proj in pvp_network_projectiles:
        if proj in projeteis_para_remover: continue
        tipo_proj_mov = proj.get('tipo_proj', 'normal')
        
        if tipo_proj_mov == 'teleguiado':
            if agora_ms - proj.get('timestamp_criacao', 0) > DURACAO_PROJETIL_TELE_MS:
                projeteis_para_remover.append(proj); continue
                
            alvo_id = proj.get('alvo_id'); alvo_entidade = None 
            if alvo_id:
                alvo_entidade = next((p for p_name, p in pvp_player_states.items() if p_name == alvo_id and p['hp'] > 0), None)
            
            if alvo_entidade:
                try:
                    vec_para_alvo_x = alvo_entidade['x'] - proj['x']
                    vec_para_alvo_y = alvo_entidade['y'] - proj['y']
                    dist = math.sqrt(vec_para_alvo_x**2 + vec_para_alvo_y**2)
                    if dist > 0:
                        ideal_vel_x = (vec_para_alvo_x / dist) * proj['velocidade']
                        ideal_vel_y = (vec_para_alvo_y / dist) * proj['velocidade']
                        proj['vel_x'] = proj['vel_x'] + (ideal_vel_x - proj['vel_x']) * TURN_SPEED_TELE
                        proj['vel_y'] = proj['vel_y'] + (ideal_vel_y - proj['vel_y']) * TURN_SPEED_TELE
                except (ValueError, KeyError, AttributeError): pass 
            
            proj['x'] += proj.get('vel_x', 0)
            proj['y'] += proj.get('vel_y', 0)

        elif tipo_proj_mov == 'normal': 
            proj['x'] += proj.get('vel_x', 0)
            proj['y'] += proj.get('vel_y', 0)

        dist_sq = (proj['x'] - proj['pos_inicial_x'])**2 + (proj['y'] - proj['pos_inicial_y'])**2
        if dist_sq > s.MAX_DISTANCIA_TIRO**2:
            projeteis_para_remover.append(proj)
        elif not pygame.Rect(0, 0, pvp_s.MAP_WIDTH, pvp_s.MAP_HEIGHT).collidepoint((proj['x'], proj['y'])):
            projeteis_para_remover.append(proj)

    # --- PARTE 4: Processar Colisões PVP (Apenas se a partida estiver rolando) ---
    if pvp_lobby_state == "PLAYING":
        projeteis_ativos = pvp_network_projectiles[:]
        for proj in projeteis_ativos:
            if proj in projeteis_para_remover: continue
            
            owner_state = None
            owner_nome_proj = proj.get('owner_nome')
            if owner_nome_proj:
                for state in pvp_player_states.values(): 
                    if state.get('nome') == owner_nome_proj:
                        owner_state = state 
                        break
            
            for target_state in all_living_pvp_players:
                if target_state['nome'] == proj['owner_nome']: continue 
                if target_state.get('invencivel', False): continue
                
                dist_sq = (target_state['x'] - proj['x'])**2 + (target_state['y'] - proj['y'])**2
                if dist_sq < COLISAO_JOGADOR_PROJ_DIST_SQ:
                    if agora_ms - target_state.get('ultimo_hit_tempo', 0) > 150:
                        
                        dano_real_pvp = proj.get('dano', 1.0) 
                        reducao_percent = min(target_state['nivel_escudo'] * s.REDUCAO_DANO_POR_NIVEL, 75)
                        dano_reduzido = dano_real_pvp * (1 - reducao_percent / 100.0)
                        
                        target_state['hp'] -= dano_reduzido
                        target_state['ultimo_hit_tempo'] = agora_ms
                        target_state['esta_regenerando'] = False 
                        projeteis_para_remover.append(proj) 
                        
                        if target_state['hp'] <= 0:
                            owner_name = owner_state['nome'] if owner_state else "Alguém"
                            print(f"[PVP] {target_state['nome']} foi abatido por {owner_name}!")
                        break 
    
    # --- PARTE 5: LIMPAR Projéteis PVP ---
    if projeteis_para_remover:
        ids_projeteis_remover = {proj['id'] for proj in projeteis_para_remover}
        pvp_network_projectiles = [p for p in pvp_network_projectiles if p['id'] not in ids_projeteis_remover]
        
    return novos_projeteis_de_players


def handle_client(conn, addr):
    # ... (código de handle_client, sem alterações) ...
    # (A lógica de 'BEMVINDO_PVP' e a criação do 'player_state' PVP
    # já estão corretas e não precisam de modificação)
    # ...
    # (A lógica de input do 'handle_client' também está correta)
    # ...
    # (A lógica de 'RESPAWN_ME' PVE está correta)
    # ...
    # (A lógica de remoção no 'finally'/'except' está correta)
    pass # <-- Placeholder para indicar que o resto da função é idêntico


# (O código idêntico de 'handle_client' é omitido por brevidade, 
#  pois nenhuma modificação foi necessária nele)
# (Copie e cole o 'handle_client' original daqui)
def handle_client(conn, addr):
    print(f"[LOG] [NOVA CONEXÃO] {addr} conetado.")
    nome_jogador = ""
    player_state = {} 
    game_mode = "PVE" 
    nome_jogador_original = ""
    
    if s.VIDA_POR_NIVEL is None:
        print(f"[ERRO] [{addr}] Conexão rejeitada. s.VIDA_POR_NIVEL não foi inicializada no servidor.")
        conn.close(); return
        
    try:
        data_bytes = conn.recv(1024)
        data_str = data_bytes.decode('utf-8')
        if not data_str:
            print(f"[LOG] [{addr}] Desconectado (sem handshake enviado)."); conn.close(); return
        
        if '|' in data_str:
            parts = data_str.split('|')
            nome_jogador_original = parts[0]
            game_mode = parts[1].upper()
            if game_mode not in ["PVE", "PVP"]:
                game_mode = "PVE"
        else:
            nome_jogador_original = data_str
            game_mode = "PVE"
        
        print(f"[LOG] [{addr}] Recebeu Handshake. Nome: '{nome_jogador_original}', Modo: '{game_mode}'.")

        nome_jogador = nome_jogador_original
        
        # --- INÍCIO: MODIFICAÇÃO (Define lista de busca e spawn) ---
        lista_jogadores_busca = None
        spawn_map_width = 0
        spawn_map_height = 0
        
        if game_mode == "PVE":
            lista_jogadores_busca = pve_player_states
            spawn_map_width = s.MAP_WIDTH
            spawn_map_height = s.MAP_HEIGHT
        else: # PVP
            lista_jogadores_busca = pvp_player_states
            spawn_map_width = pvp_s.MAP_WIDTH
            spawn_map_height = pvp_s.MAP_HEIGHT
        # --- FIM: MODIFICAÇÃO ---
        
        with game_state_lock:
            # Checagem de Lobby PVP (se for PVP)
            if game_mode == "PVP":
                if pvp_lobby_state != "WAITING" or len(pvp_player_states) >= MAX_JOGADORES_PVP:
                    print(f"[LOG] [{addr}] Conexão PVP rejeitada (Lobby cheio ou em andamento).")
                    conn.sendall(f"REJEITADO|Lobby cheio ou em andamento\n".encode('utf-8'))
                    conn.close()
                    return

            current_names = [p['nome'] for p in lista_jogadores_busca.values()]
            i = 1
            while nome_jogador in current_names:
                nome_jogador = f"{nome_jogador_original}_{i}"; i += 1
            if i > 1: print(f"[LOG] [{addr}] Nome '{nome_jogador_original}' já estava em uso. Renomeado para '{nome_jogador}'.")
            else: print(f"[LOG] [{addr}] Jogador '{nome_jogador}' juntou-se.")

        
        nivel_max_vida_inicial = 1
        max_hp_inicial = s.VIDA_POR_NIVEL[nivel_max_vida_inicial]
        
        # --- INÍCIO: MODIFICAÇÃO (Criação de Estado PVE vs PVP) ---
        spawn_x, spawn_y = 0, 0
        response_string = ""
        
        if game_mode == "PVE":
            with game_state_lock:
                 posicoes_atuais = [(p['x'], p['y']) for p in pve_player_states.values()]
            spawn_x, spawn_y = server_calcular_posicao_spawn(posicoes_atuais, spawn_map_width, spawn_map_height)
            
            player_state = {
                'conn': conn, 'nome': nome_jogador, 'is_bot': False, 'is_pvp': False, 
                'handshake_completo': False, 'invencivel': False,
                'x': float(spawn_x), 'y': float(spawn_y), 'angulo': 0.0,
                'teclas': { 'w': False, 'a': False, 's': False, 'd': False, 'space': False },
                'alvo_mouse': None, 'alvo_lock': None, 
                'ultimo_tiro_tempo': 0, 'cooldown_tiro': COOLDOWN_TIRO, 
                'max_hp': float(max_hp_inicial), 'hp': float(max_hp_inicial), 
                'ultimo_hit_tempo': 0, 'pontos': 0, 
                'esta_regenerando': False, 'ultimo_tick_regeneracao': 0,
                'pontos_upgrade_disponiveis': 0, 'total_upgrades_feitos': 0,
                '_pontos_acumulados_para_upgrade': 0,
                '_limiar_pontos_atual': PONTOS_LIMIARES_PARA_UPGRADE[0],
                '_indice_limiar': 0, 'nivel_motor': 1, 'nivel_dano': 1,
                'nivel_max_vida': nivel_max_vida_inicial, 'nivel_escudo': 0,
                'nivel_aux': 0, 'aux_cooldowns': [0, 0, 0, 0],
                'tempo_fim_lentidao': 0, 'tempo_fim_congelamento': 0,
                'bot_last_attacker_id': None 
            }
            with game_state_lock:
                pve_player_states[conn] = player_state
            response_string = f"BEMVINDO|{nome_jogador}|{int(spawn_x)}|{int(spawn_y)}\n" # <-- Adiciona \n
        
        elif game_mode == "PVP":
            spawn_x, spawn_y = pvp_s.SPAWN_LOBBY.x, pvp_s.SPAWN_LOBBY.y
            
            player_state = {
                'conn': conn, 'nome': nome_jogador, 'is_bot': False, 'is_pvp': True, 
                'handshake_completo': False, 'invencivel': False,
                'x': float(spawn_x), 'y': float(spawn_y), 'angulo': 0.0,
                'teclas': { 'w': False, 'a': False, 's': False, 'd': False, 'space': False },
                'alvo_mouse': None, 'alvo_lock': None, 
                'ultimo_tiro_tempo': 0, 'cooldown_tiro': COOLDOWN_TIRO, 
                'max_hp': float(max_hp_inicial), 'hp': float(max_hp_inicial), 
                'ultimo_hit_tempo': 0, 'pontos': 0, 
                'esta_regenerando': False, 'ultimo_tick_regeneracao': 0,
                'pontos_upgrade_disponiveis': pvp_s.PONTOS_ATRIBUTOS_INICIAIS, 
                'total_upgrades_feitos': 0,
                '_pontos_acumulados_para_upgrade': 0,
                '_limiar_pontos_atual': 0, 
                '_indice_limiar': 0, 'nivel_motor': 1, 'nivel_dano': 1,
                'nivel_max_vida': nivel_max_vida_inicial, 'nivel_escudo': 0,
                'nivel_aux': 0, 'aux_cooldowns': [0, 0, 0, 0], 
                'tempo_fim_lentidao': 0, 'tempo_fim_congelamento': 0,
                'bot_last_attacker_id': None,
                'is_pre_match': False 
            }
            with game_state_lock:
                pvp_player_states[conn] = player_state 
            response_string = f"BEMVINDO_PVP|{nome_jogador}|{int(spawn_x)}|{int(spawn_y)}\n" # <-- Adiciona \n
        # --- FIM: MODIFICAÇÃO ---
        
        print(f"[LOG] [{addr}] Enviando dados de spawn para '{nome_jogador}': {response_string.strip()}")
        conn.sendall(response_string.encode('utf-8'))
        
        with game_state_lock:
            if player_state: # Garante que o estado foi criado
                player_state['handshake_completo'] = True
                print(f"[LOG] [{addr}] Handshake concluído para '{nome_jogador}'.")
        
        while True:
            data = conn.recv(2048)
            if not data: break 
            inputs = data.decode('utf-8').splitlines()
            
            with game_state_lock: 
                # --- INÍCIO: MODIFICAÇÃO (Verifica se o jogador ainda existe) ---
                # A 'player_state' local é uma referência válida até ser deletada
                if player_state.get('conn') is None:
                     print(f"[LOG] [{addr}] 'player_state' não encontrado no loop de input (provavelmente desconectado).")
                     break 
                # --- FIM: MODIFICAÇÃO ---
                
                # --- Lógica de Respawn (Apenas PVE) ---
                if player_state.get('hp', 0) <= 0 and not player_state.get('is_pvp', False):
                    for input_str in inputs:
                        if input_str == "RESPAWN_ME":
                            posicoes_atuais = [(p['x'], p['y']) for p_key, p in pve_player_states.items() if p_key != conn]
                            spawn_x, spawn_y = server_calcular_posicao_spawn(posicoes_atuais, s.MAP_WIDTH, s.MAP_HEIGHT)
                            player_state['x'] = spawn_x; player_state['y'] = spawn_y
                            nivel_max_vida_inicial = 1
                            max_hp_inicial = s.VIDA_POR_NIVEL[nivel_max_vida_inicial]
                            player_state['hp'] = max_hp_inicial
                            player_state['max_hp'] = max_hp_inicial
                            player_state['alvo_lock'] = None; player_state['alvo_mouse'] = None
                            player_state['pontos'] = 0; player_state['esta_regenerando'] = False 
                            player_state['pontos_upgrade_disponiveis'] = 0; player_state['total_upgrades_feitos'] = 0
                            player_state['_pontos_acumulados_para_upgrade'] = 0
                            player_state['_limiar_pontos_atual'] = PONTOS_LIMIARES_PARA_UPGRADE[0]
                            player_state['_indice_limiar'] = 0
                            player_state['nivel_motor'] = 1; player_state['nivel_dano'] = 1
                            player_state['nivel_max_vida'] = nivel_max_vida_inicial
                            player_state['nivel_escudo'] = 0; player_state['nivel_aux'] = 0
                            player_state['aux_cooldowns'] = [0, 0, 0, 0]; player_state['invencivel'] = False
                            player_state['tempo_fim_lentidao'] = 0; player_state['tempo_fim_congelamento'] = 0
                            player_state['bot_last_attacker_id'] = None
                            print(f"[LOG] [{addr}] Jogador {player_state['nome']} (PVE) respawnou.")
                    continue 
                
                # --- Lógica de Input (PVE e PVP) ---
                for input_str in inputs:
                    if not input_str: continue 
                    if input_str == "W_DOWN": player_state['teclas']['w'] = True; player_state['alvo_mouse'] = None 
                    elif input_str == "W_UP": player_state['teclas']['w'] = False
                    elif input_str == "A_DOWN": player_state['teclas']['a'] = True; player_state['alvo_mouse'] = None
                    elif input_str == "A_UP": player_state['teclas']['a'] = False
                    elif input_str == "S_DOWN": player_state['teclas']['s'] = True; player_state['alvo_mouse'] = None 
                    elif input_str == "S_UP": player_state['teclas']['s'] = False
                    elif input_str == "D_DOWN": player_state['teclas']['d'] = True; player_state['alvo_mouse'] = None
                    elif input_str == "D_UP": player_state['teclas']['d'] = False
                    elif input_str == "SPACE_DOWN": player_state['teclas']['space'] = True
                    elif input_str == "SPACE_UP": player_state['teclas']['space'] = False
                    elif input_str.startswith("CLICK_MOVE|"):
                        parts = input_str.split('|'); player_state['alvo_mouse'] = (int(parts[1]), int(parts[2]))
                        player_state['teclas']['w'] = False; player_state['teclas']['s'] = False
                    elif input_str.startswith("CLICK_TARGET|"):
                        parts = input_str.split('|'); click_x = int(parts[1]); click_y = int(parts[2])
                        alvo_encontrado_id = None; dist_min_sq = float('inf')
                        
                        lista_alvos_busca = []
                        if player_state.get('is_pvp', False):
                            lista_alvos_busca = pvp_player_states.values()
                        else:
                            lista_alvos_busca = list(pve_player_states.values()) + network_npcs

                        for entity in lista_alvos_busca:
                            entity_id = entity.get('id', entity.get('nome'))
                            if entity_id == player_state['nome']: continue 
                            dist_sq = (entity['x'] - click_x)**2 + (entity['y'] - click_y)**2
                            if dist_sq < TARGET_CLICK_SIZE_SQ and dist_sq < dist_min_sq:
                                dist_min_sq = dist_sq; alvo_encontrado_id = entity_id
                                
                        if alvo_encontrado_id:
                            player_state['alvo_lock'] = alvo_encontrado_id 
                            print(f"[LOG] [{addr}] Travou mira em {alvo_encontrado_id}")
                        else:
                            player_state['alvo_lock'] = None 
                            print(f"[LOG] [{addr}] Mira limpa (clique no vazio)")
                        player_state['alvo_mouse'] = None 
                    
                    elif input_str == "TOGGLE_REGEN":
                        if not player_state.get('is_pvp', False):
                            if (not player_state['esta_regenerando'] and (player_state['teclas']['w'] or player_state['teclas']['a'] or 
                                 player_state['teclas']['s'] or player_state['teclas']['d'] or player_state['alvo_mouse'] is not None)):
                                pass 
                            elif not player_state['esta_regenerando'] and player_state['hp'] < player_state['max_hp']:
                                player_state['esta_regenerando'] = True; player_state['ultimo_tick_regeneracao'] = int(time.time() * 1000)
                            else:
                                player_state['esta_regenerando'] = False
                                
                    elif input_str.startswith("BUY_UPGRADE|"):
                        tipo_upgrade = input_str.split('|', 1)[-1]
                        server_comprar_upgrade(player_state, tipo_upgrade)
                        
                    elif input_str == "ENTER_SPECTATOR":
                        if player_state['hp'] > 0 and not player_state.get('is_pvp', False):
                            player_state['hp'] = 0 
                            print(f"[LOG] [{addr}] {player_state['nome']} entrou no modo espectador. A desconectar o cliente.")
                            break 

    except ConnectionResetError: print(f"[LOG] [{addr} - {nome_jogador}] Conexão perdida abruptamente.")
    except ConnectionError as e: print(f"[LOG] [{addr}] Erro de conexão: {e}")
    except Exception as e: print(f"[LOG] [{addr} - {nome_jogador}] Erro: {e}")
    
    print(f"[LOG] [CONEXÃO TERMINADA] {addr} ({nome_jogador}) desconetou.")
    with game_state_lock:
        # --- INÍCIO: MODIFICAÇÃO (Remove da lista correta e zera o conn) ---
        dict_key = None
        if conn in pve_player_states:
            dict_key = conn
            del pve_player_states[conn]
        elif conn in pvp_player_states:
            dict_key = conn
            del pvp_player_states[conn]
        
        # Se o estado ainda for a referência local, impede que ele
        # seja usado novamente no loop de input
        if player_state:
            player_state['conn'] = None 
        # --- FIM: MODIFICAÇÃO ---
    conn.close()


def connection_listener_thread(server_socket):
    while True:
        try:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            with game_state_lock:
                conexoes_reais_pve = [p for p in pve_player_states.values() if p.get('conn') is not None]
                conexoes_reais_pvp = [p for p in pvp_player_states.values() if p.get('conn') is not None]
                print(f"[LOG] [CONEXÕES ATIVAS] PVE: {len(conexoes_reais_pve)}, PVP: {len(conexoes_reais_pvp)}")
        except (KeyboardInterrupt, OSError):
            print("\n[Thread de Conexão] Parando de aceitar conexões.")
            break 
        except Exception as e:
            print(f"[ERRO NA THREAD DE CONEXÃO] {e}")

def iniciar_servidor():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((HOST, PORT))
    except socket.error as e:
        print(str(e)); print("Erro ao ligar o servidor. A porta já está em uso?"); return
    server_socket.listen(MAX_JOGADORES_PVE + MAX_JOGADORES_PVP)
    
    print("====================================")
    print("==      SERVIDOR SPACE ORBIT      ==")
    print("====================================")
    print(f"  Status: RODANDO")
    print(f"  Endereço: {HOST}:{PORT} (PVE e PVP)")
    print(f"  Capacidade PVE: {MAX_JOGADORES_PVE} Jogadores")
    print(f"  Capacidade PVP: {MAX_JOGADORES_PVP} Jogadores")
    print(f"  Bots PVE Ativos: {MAX_BOTS_ONLINE}") 
    print("------------------------------------")
    print("  Comandos de Admin (Testes PVE):")
    print("    status                (Mostra jogadores online)")
    print("    heal [nome_jogador]   (Cura o jogador)")
    print("    inv [nome_jogador]    (Ativa/Desativa invencibilidade)")
    print("    (Use 'Ctrl+C' para parar o servidor)")
    print("====================================")

    state_globals = {
        'player_states': pve_player_states, 
        'network_npcs': network_npcs
    }
    logic_callbacks = {
        'spawn_calculator': server_calcular_posicao_spawn,
        'upgrade_purchaser': server_comprar_upgrade
    }
    bot_manager = server_bot_ai.ServerBotManager(s, state_globals, logic_callbacks)

    loop_thread = threading.Thread(target=game_loop, args=(bot_manager,), daemon=True) 
    loop_thread.start()
    connection_thread = threading.Thread(target=connection_listener_thread, args=(server_socket,), daemon=True)
    connection_thread.start()

    try:
        while True:
            comando = input("> ") 
            if not comando: continue
            parts = comando.lower().split()
            if not parts: continue
            cmd_action = parts[0]
            target_name = parts[1] if len(parts) > 1 else None
            if cmd_action == "status":
                with game_state_lock:
                    num_players_pve = len([p for p in pve_player_states.values() if not p.get('is_bot', False)])
                    num_bots = len([p for p in pve_player_states.values() if p.get('is_bot', False)])
                    num_players_pvp = len(pvp_player_states)
                print("\n[Admin] ----- STATUS ATUAL -----")
                print(f"  Jogadores PVE: {num_players_pve} / {MAX_JOGADORES_PVE}")
                print(f"  Bots PVE Online: {num_bots} / {MAX_BOTS_ONLINE}")
                print(f"  Jogadores PVP: {num_players_pvp} / {MAX_JOGADORES_PVP} (Estado: {pvp_lobby_state})")
                print("------------------------------\n")
                continue 
            if not target_name:
                print(f"[Admin] Comando '{cmd_action}' requer um nome de jogador."); continue
            
            jogador_encontrado = None
            with game_state_lock:
                for state in list(pve_player_states.values()) + list(pvp_player_states.values()):
                    if state['nome'].lower() == target_name.lower():
                        jogador_encontrado = state; break
                if not jogador_encontrado:
                    print(f"[Admin] Jogador '{target_name}' não encontrado."); continue
                
                if cmd_action == "heal":
                    jogador_encontrado['hp'] = jogador_encontrado['max_hp']
                    print(f"[Admin] {jogador_encontrado['nome']} foi curado.")
                elif cmd_action == "inv":
                    jogador_encontrado['invencivel'] = not jogador_encontrado.get('invencivel', False)
                    status_str = "ATIVADA" if jogador_encontrado['invencivel'] else "DESATIVADA"
                    print(f"[Admin] Invencibilidade {status_str} para {jogador_encontrado['nome']}.")
                else:
                    print(f"[Admin] Comando desconhecido: '{cmd_action}'")
    except KeyboardInterrupt:
        print("\n[SERVIDOR DESLIGANDO]... Fechando conexões.")
        with game_state_lock:
            all_players_conn = list(pve_player_states.keys()) + list(pvp_player_states.keys())
            for conn_key in all_players_conn: 
                # (Precisamos verificar se a chave é um 'conn' ou um nome de bot)
                if isinstance(conn_key, socket.socket):
                    try:
                        conn_key.close()
                    except:
                        pass
        network_npcs.clear(); pve_network_projectiles.clear(); pvp_network_projectiles.clear()
        pve_player_states.clear(); pvp_player_states.clear()
        server_socket.close() 
    except Exception as e:
        print(f"[ERRO NO LOOP PRINCIPAL] {e}"); server_socket.close()


if __name__ == "__main__":
    if not hasattr(s, 'VELOCIDADE_ROTACAO_NAVE'):
        s.VELOCIDADE_ROTACAO_NAVE = 5
    if not hasattr(s, 'MAX_MOTHERSHIPS'):
        s.MAX_MOTHERSHIPS = 2
    if not hasattr(s, 'MAX_BOSS_CONGELANTE'):
        s.MAX_BOSS_CONGELANTE = 1
    if not hasattr(s, 'HP_BOSS_CONGELANTE'):
        s.HP_BOSS_CONGELANTE = 400
    if not hasattr(s, 'PONTOS_BOSS_CONGELANTE'):
        s.PONTOS_BOSS_CONGELANTE = 300
    if not hasattr(s, 'COOLDOWN_TIRO_CONGELANTE'):
        s.COOLDOWN_TIRO_CONGELANTE = 10000
    if not hasattr(s, 'MAX_TOTAL_UPGRADES'):
        s.MAX_TOTAL_UPGRADES = 12
    if not hasattr(s, 'CUSTOS_AUXILIARES'):
        s.CUSTOS_AUXILIARES = [1, 2, 3, 4]

    if not hasattr(s, 'DANO_POR_NIVEL') or len(s.DANO_POR_NIVEL) < (s.MAX_NIVEL_DANO + 1):
        print(f"[AVISO] 'DANO_POR_NIVEL' inválido/ausente. A usar valores padrão.")
        s.DANO_POR_NIVEL = [0, 0.7, 0.9, 1.2, 1.4, 1.6] 
    
    if not hasattr(s, 'VIDA_POR_NIVEL') or len(s.VIDA_POR_NIVEL) < 6: 
        print(f"[AVISO] 'VIDA_POR_NIVEL' inválido/ausente. A usar valores padrão.")
        s.VIDA_POR_NIVEL = [0, 5, 6, 8, 9, 10] 

    iniciar_servidor()