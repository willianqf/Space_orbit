# server.py
import socket
import threading
import random
import settings as s # Para saber o tamanho do mapa
import math 
import time 
import pygame # <--- Importado para usar Vector2

# 1. Configurações do Servidor
HOST = '127.0.0.1'  # IP para escutar
PORT = 5555         # Porta para escutar
MAX_JOGADORES = 16
TICK_RATE = 60 # 60 atualizações por segundo

COLISAO_JOGADOR_PROJ_DIST_SQ = (15 + 5)**2

# --- (Estado de Jogo Unificado - Sem alterações) ---
player_states = {}
network_projectiles = []
network_npcs = []
next_npc_id = 0
game_state_lock = threading.Lock() 
# --- FIM ---


# --- (Constantes de Jogo e IA - Sem alterações) ---
COOLDOWN_TIRO = 250 # ms
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
# --- FIM ---

# --- (Constantes de Projéteis e Regeneração - Sem alterações) ---
VELOCIDADE_PROJETIL_NORMAL = 25   
VELOCIDADE_PROJETIL_TELE = 14    
DURACAO_PROJETIL_TELE_MS = 700   
TURN_SPEED_TELE = 0.02           
REGEN_POR_TICK = s.REGEN_POR_TICK
REGEN_TICK_RATE_MS = s.REGEN_TICK_RATE
# --- FIM ---

# --- (Constantes de Upgrade - Sem alterações) ---
MAX_TOTAL_UPGRADES = s.MAX_TOTAL_UPGRADES
MAX_NIVEL_MOTOR = s.MAX_NIVEL_MOTOR
MAX_NIVEL_DANO = s.MAX_NIVEL_DANO
MAX_NIVEL_ESCUDO = s.MAX_NIVEL_ESCUDO
MAX_AUXILIARES = 4 
CUSTOS_AUXILIARES = s.CUSTOS_AUXILIARES
PONTOS_LIMIARES_PARA_UPGRADE = s.PONTOS_LIMIARES_PARA_UPGRADE[:]
PONTOS_SCORE_PARA_MUDAR_LIMIAR = s.PONTOS_SCORE_PARA_MUDAR_LIMIAR[:]
# --- FIM: CONSTANTES DE UPGRADE ---

# --- INÍCIO: CONSTANTES DE AUXILIARES (de ships.py) ---
#
AUX_POSICOES = [
    pygame.math.Vector2(-40, 20), 
    pygame.math.Vector2(40, 20), 
    pygame.math.Vector2(-50, -10), 
    pygame.math.Vector2(50, -10)
]
AUX_COOLDOWN_TIRO = 1000 # ms, de NaveAuxiliar.__init__
AUX_DISTANCIA_TIRO_SQ = 600**2 # de NaveAuxiliar.__init__
# --- FIM: CONSTANTES DE AUXILIARES ---


# --- (Funções de Lógica de Upgrade - Sem alterações) ---

def server_ganhar_pontos(player_state, quantidade):
    """ Adiciona pontos de score e calcula pontos de upgrade (lógica de ships.py). """
    if quantidade <= 0:
        return
    
    player_state['pontos'] += quantidade 
    player_state['_pontos_acumulados_para_upgrade'] += quantidade
    
    while player_state['_pontos_acumulados_para_upgrade'] >= player_state['_limiar_pontos_atual']:
        player_state['pontos_upgrade_disponiveis'] += 1
        player_state['_pontos_acumulados_para_upgrade'] -= player_state['_limiar_pontos_atual'] 
        print(f"[{player_state['nome']}] Ganhou 1 Ponto de Upgrade! (Total: {player_state['pontos_upgrade_disponiveis']})")
        
        pontos_totais_aproximados = player_state['pontos'] 
        if (player_state['_indice_limiar'] < len(PONTOS_SCORE_PARA_MUDAR_LIMIAR) and 
            pontos_totais_aproximados >= PONTOS_SCORE_PARA_MUDAR_LIMIAR[player_state['_indice_limiar']]):
            
            player_state['_indice_limiar'] += 1
            if player_state['_indice_limiar'] < len(PONTOS_LIMIARES_PARA_UPGRADE):
                player_state['_limiar_pontos_atual'] = PONTOS_LIMIARES_PARA_UPGRADE[player_state['_indice_limiar']]
                print(f"[{player_state['nome']}] Próximo Ponto de Upgrade a cada {player_state['_limiar_pontos_atual']} pontos de score.")

def server_comprar_upgrade(player_state, tipo_upgrade):
    """ Processa um pedido de compra de upgrade (lógica de ships.py). """
    
    if player_state['pontos_upgrade_disponiveis'] <= 0:
        print(f"[{player_state['nome']}] Pedido de compra negado (Sem Pontos de Upgrade)!")
        return
    if player_state['total_upgrades_feitos'] >= MAX_TOTAL_UPGRADES:
        print(f"[{player_state['nome']}] Pedido de compra negado (Limite de {MAX_TOTAL_UPGRADES} upgrades atingido)!")
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
                print(f"[{player_state['nome']}] Motor comprado! Nível {player_state['nivel_motor']}.")
    
    elif tipo_upgrade == "dano":
        if player_state['nivel_dano'] < MAX_NIVEL_DANO:
            if player_state['pontos_upgrade_disponiveis'] >= custo_padrao:
                player_state['pontos_upgrade_disponiveis'] -= custo_padrao
                player_state['total_upgrades_feitos'] += 1
                player_state['nivel_dano'] += 1
                comprou = True
                print(f"[{player_state['nome']}] Dano comprado! Nível {player_state['nivel_dano']}.")

    elif tipo_upgrade == "auxiliar":
        num_ativos = player_state['nivel_aux']
        if num_ativos < MAX_AUXILIARES:
            custo_atual_aux = CUSTOS_AUXILIARES[num_ativos] 
            if player_state['pontos_upgrade_disponiveis'] >= custo_atual_aux:
                player_state['pontos_upgrade_disponiveis'] -= custo_atual_aux 
                player_state['total_upgrades_feitos'] += 1 
                player_state['nivel_aux'] += 1 
                comprou = True
                print(f"[{player_state['nome']}] Auxiliar {num_ativos + 1} comprado por {custo_atual_aux} pts!")
            else:
                print(f"[{player_state['nome']}] Pontos insuficientes para Auxiliar! Custo: {custo_atual_aux} Pts.")
    
    elif tipo_upgrade == "max_health":
        if player_state['pontos_upgrade_disponiveis'] >= custo_padrao:
            player_state['pontos_upgrade_disponiveis'] -= custo_padrao
            player_state['total_upgrades_feitos'] += 1
            player_state['nivel_max_vida'] += 1
            player_state['max_hp'] = 4 + player_state['nivel_max_vida'] 
            player_state['hp'] += 1 
            comprou = True
            print(f"[{player_state['nome']}] Vida Máx. aumentada! Nível {player_state['nivel_max_vida']}.")
    
    elif tipo_upgrade == "escudo":
        if player_state['nivel_escudo'] < MAX_NIVEL_ESCUDO:
            if player_state['pontos_upgrade_disponiveis'] >= custo_padrao:
                player_state['pontos_upgrade_disponiveis'] -= custo_padrao
                player_state['total_upgrades_feitos'] += 1
                player_state['nivel_escudo'] += 1
                comprou = True
                print(f"[{player_state['nome']}] Escudo comprado! Nível {player_state['nivel_escudo']}.")
                
    if not comprou:
        print(f"[{player_state['nome']}] Pedido de compra para '{tipo_upgrade}' falhou (nível máx. atingido ou custo).")

# --- FIM: FUNÇÕES DE LÓGICA ---


# --- (Função server_calcular_posicao_spawn - Sem alterações) ---
def server_calcular_posicao_spawn(pos_referencia_lista):
    """ Encontra um ponto de spawn longe de todos os jogadores na lista. """
    while True:
        x = random.uniform(0, s.MAP_WIDTH)
        y = random.uniform(0, s.MAP_HEIGHT)
        pos_spawn = pygame.math.Vector2(x, y) 
        
        longe_suficiente = True
        if pos_referencia_lista: 
            for pos_ref in pos_referencia_lista:
                if pos_spawn.distance_to(pygame.math.Vector2(pos_ref[0], pos_ref[1])) < SPAWN_DIST_MIN:
                    longe_suficiente = False
                    break
        
        if longe_suficiente:
            return (float(x), float(y)) 
# --- FIM ---

# --- (Função update_player_logic - Sem alterações) ---
def update_player_logic(player_state):
    """ Calcula a nova posição, ângulo E processa o tiro de UM jogador. """
    
    # --- 1. Lógica de Rotação ---
    angulo_alvo = None
    
    if player_state['alvo_lock']:
        target_id = player_state['alvo_lock']
        alvo_coords = None
        alvo_encontrado = False

        for npc in network_npcs: 
            if npc['id'] == target_id:
                alvo_coords = (npc['x'], npc['y'])
                alvo_encontrado = True
                break
        
        if not alvo_encontrado:
            player_state['alvo_lock'] = None 
        else:
            target_x, target_y = alvo_coords
            
            dist_sq = (target_x - player_state['x'])**2 + (target_y - player_state['y'])**2
            if dist_sq > MAX_TARGET_LOCK_DISTANCE_SQ:
                player_state['alvo_lock'] = None 
            else:
                vec_x = target_x - player_state['x']
                vec_y = target_y - player_state['y']
                if (vec_x**2 + vec_y**2) > 0: 
                     radianos = math.atan2(vec_y, vec_x)
                     angulo_alvo = -math.degrees(radianos) - 90 

    elif player_state['alvo_mouse']:
        target_x, target_y = player_state['alvo_mouse']
        vec_x = target_x - player_state['x']
        vec_y = target_y - player_state['y']
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
    velocidade_atual = velocidade_base_atual + 1
    
    nova_pos_x = player_state['x']
    nova_pos_y = player_state['y']
    
    if player_state['teclas']['w'] or player_state['teclas']['s']:
        radianos = math.radians(player_state['angulo'])
        if player_state['teclas']['w']:
            nova_pos_x += -math.sin(radianos) * velocidade_atual
            nova_pos_y += -math.cos(radianos) * velocidade_atual
        if player_state['teclas']['s']:
            nova_pos_x -= -math.sin(radianos) * velocidade_atual
            nova_pos_y -= -math.cos(radianos) * velocidade_atual
    elif player_state['alvo_mouse']:
        target_x, target_y = player_state['alvo_mouse']
        vec_x = target_x - nova_pos_x
        vec_y = target_y - nova_pos_y
        dist_sq = vec_x**2 + vec_y**2 
        
        if dist_sq > 5.0**2: 
            dist = math.sqrt(dist_sq)
            dir_x = vec_x / dist
            dir_y = vec_y / dist
            
            nova_pos_x += dir_x * velocidade_atual
            nova_pos_y += dir_y * velocidade_atual
            
            novo_vec_x = target_x - nova_pos_x
            novo_vec_y = target_y - nova_pos_y
            if (novo_vec_x * vec_x + novo_vec_y * vec_y) < 0: 
                nova_pos_x, nova_pos_y = target_x, target_y
                player_state['alvo_mouse'] = None 
        else:
            player_state['alvo_mouse'] = None 

    # --- 3. Limitar ao Mapa (Clamping) ---
    meia_largura = 15 
    meia_altura = 15
    nova_pos_x = max(meia_largura, min(nova_pos_x, s.MAP_WIDTH - meia_largura))
    nova_pos_y = max(meia_altura, min(nova_pos_y, s.MAP_HEIGHT - meia_altura))

    player_state['x'] = nova_pos_x
    player_state['y'] = nova_pos_y

    # --- 4. Lógica de Tiro ---
    if player_state['teclas']['space'] or player_state['alvo_lock']:
        agora_ms = int(time.time() * 1000) 
        if agora_ms - player_state['ultimo_tiro_tempo'] > player_state['cooldown_tiro']:
            player_state['ultimo_tiro_tempo'] = agora_ms
            radianos = math.radians(player_state['angulo'])
            pos_x = player_state['x'] + (-math.sin(radianos) * OFFSET_PONTA_TIRO)
            pos_y = player_state['y'] + (-math.cos(radianos) * OFFSET_PONTA_TIRO)
            
            vel_x_inicial = -math.sin(radianos)
            vel_y_inicial = -math.cos(radianos)

            novo_projetil = {
                'id': f"{player_state['nome']}_{agora_ms}", 
                'owner_nome': player_state['nome'],
                'x': pos_x, 'y': pos_y,
                'pos_inicial_x': pos_x, 'pos_inicial_y': pos_y,
                'dano': player_state['nivel_dano'], 
                'tipo': 'player', 
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
                novo_projetil['velocidade'] = VELOCIDADE_PROJETIL_NORMAL
                novo_projetil['vel_x'] = vel_x_inicial * VELOCIDADE_PROJETIL_NORMAL
                novo_projetil['vel_y'] = vel_y_inicial * VELOCIDADE_PROJETIL_NORMAL
            
            return novo_projetil
            
    return None
# --- FIM ---

# --- (Função update_npc_logic - Sem alterações) ---
def update_npc_logic(npc, players_pos_lista):
    """ Atualiza a lógica de IA para um NPC e retorna um projétil se atirar. """
    
    alvo_pos = None
    dist_min_sq = float('inf')
    
    if not players_pos_lista:
        return None 

    for p_pos in players_pos_lista:
        dist_sq = (npc['x'] - p_pos[0])**2 + (npc['y'] - p_pos[1])**2
        if dist_sq < dist_min_sq:
            dist_min_sq = dist_sq
            alvo_pos = p_pos 
    
    if not alvo_pos:
        return None
        
    vec_x = alvo_pos[0] - npc['x']
    vec_y = alvo_pos[1] - npc['y']
    dist = math.sqrt(dist_min_sq)

    velocidade = VELOCIDADE_PERSEGUIDOR 
    
    if npc['tipo'] == 'rapido':
        velocidade = 4.0 
    elif npc['tipo'] == 'bomba':
        velocidade = 3.0 
    elif npc['tipo'] == 'tiro_rapido':
        velocidade = 1.5
    elif npc['tipo'] == 'atordoador':
        velocidade = 1.0
    elif npc['tipo'] == 'mothership':
        velocidade = 1.0 
    elif npc['tipo'] == 'boss_congelante':
        velocidade = 1.0 
        
    if dist_min_sq > DISTANCIA_PARAR_PERSEGUIDOR_SQ:
        dir_x = vec_x / dist
        dir_y = vec_y / dist
        npc['x'] += dir_x * velocidade
        npc['y'] += dir_y * velocidade
        
    radianos = math.atan2(vec_y, vec_x)
    npc['angulo'] = -math.degrees(radianos) - 90
    npc['angulo'] %= 360
    
    if npc['tipo'] in ['bomba', 'mothership']:
        return None 
        
    if dist_min_sq < DISTANCIA_TIRO_PERSEGUIDOR_SQ: 
        agora_ms = int(time.time() * 1000)
        if agora_ms - npc['ultimo_tiro_tempo'] > npc['cooldown_tiro']:
            npc['ultimo_tiro_tempo'] = agora_ms
            
            dir_x = vec_x / dist
            dir_y = vec_y / dist
            angulo_rad_proj = radianos 
            
            velocidade_proj = VELOCIDADE_PROJETIL_NPC
            if npc['tipo'] == 'tiro_rapido':
                velocidade_proj = 22 
            elif npc['tipo'] == 'rapido':
                velocidade_proj = 12 

            novo_projetil = {
                'id': f"{npc['id']}_{agora_ms}", 
                'owner_nome': npc['id'],
                'x': npc['x'], 'y': npc['y'], 
                'pos_inicial_x': npc['x'], 'pos_inicial_y': npc['y'],
                'angulo_rad': angulo_rad_proj, 
                'velocidade': velocidade_proj,
                'dano': 1, 
                'tipo': 'npc' 
            }
            return novo_projetil 
            
    return None 
# --- FIM ---

# --- (Função server_spawnar_inimigo_aleatorio - Sem alterações) ---
def server_spawnar_inimigo_aleatorio(x, y, npc_id):
    """
    Cria um dicionário de estado para um novo NPC aleatório.
    Baseado na lógica offline de 'spawnar_inimigo_aleatorio'.
    """
    chance = random.random()
    tipo = "perseguidor" # Padrão
    hp = 3
    max_hp = 3
    tamanho = 30
    cooldown_tiro = COOLDOWN_TIRO_PERSEGUIDOR # Padrão
    pontos = 5 # Padrão
    
    if chance < 0.05: 
        tipo = "bomba"
        hp, max_hp = 1, 1
        tamanho = 25
        cooldown_tiro = 999999 
        pontos = 3
    elif chance < 0.10: 
        tipo = "tiro_rapido"
        hp, max_hp = 10, 10
        tamanho = 30
        cooldown_tiro = 1500
        pontos = 20
    elif chance < 0.15: 
        tipo = "atordoador"
        hp, max_hp = 5, 5
        tamanho = 30
        cooldown_tiro = 5000
        pontos = 25
    elif chance < 0.35: 
        tipo = "atirador_rapido"
        hp, max_hp = 1, 1
        tamanho = 30
        cooldown_tiro = 500
        pontos = 10
    elif chance < 0.55: 
        tipo = "rapido"
        hp, max_hp = 5, 5
        tamanho = 30
        cooldown_tiro = 800
        pontos = 9
    
    return {
        'id': npc_id,
        'tipo': tipo,
        'x': float(x), 'y': float(y),
        'angulo': 0.0,
        'hp': hp,
        'max_hp': max_hp,
        'tamanho': tamanho,
        'cooldown_tiro': cooldown_tiro, 
        'ultimo_tiro_tempo': 0,
        'pontos_por_morte': pontos 
    }
# --- FIM ---


# --- (Funções de Spawn de Boss - Sem alterações) ---
def server_spawnar_mothership(x, y, npc_id):
    """ Cria um dicionário de estado para uma Mothership. """
    return {
        'id': npc_id,
        'tipo': 'mothership',
        'x': float(x), 'y': float(y),
        'angulo': 0.0,
        'hp': 200,                 
        'max_hp': 200,             
        'tamanho': 80,             
        'cooldown_tiro': 999999,   
        'ultimo_tiro_tempo': 0,
        'pontos_por_morte': 100    
    }

def server_spawnar_boss_congelante(x, y, npc_id):
    """ Cria um dicionário de estado para um Boss Congelante. """
    return {
        'id': npc_id,
        'tipo': 'boss_congelante',
        'x': float(x), 'y': float(y),
        'angulo': 0.0,
        'hp': s.HP_BOSS_CONGELANTE,
        'max_hp': s.HP_BOSS_CONGELANTE,
        'tamanho': 100,             
        'cooldown_tiro': s.COOLDOWN_TIRO_CONGELANTE, 
        'ultimo_tiro_tempo': 0,
        'pontos_por_morte': s.PONTOS_BOSS_CONGELANTE
    }
# --- FIM: FUNÇÕES DE SPAWN DE BOSS ---


def game_loop():
    """
    O loop principal do servidor.
    """
    global next_npc_id, network_npcs, network_projectiles 
    
    print("[GAME LOOP INICIADO] O servidor está agora a calcular e a enviar o estado.")
    
    TICK_INTERVAL = 1.0 / TICK_RATE 
    
    while True:
        loop_start_time = time.time()
        
        novos_projeteis = []
        
        with game_state_lock:
            agora_ms = int(time.time() * 1000) 
            projeteis_para_remover = [] 
            npcs_para_remover = [] 

            # --- Parte 1: Atualizar Jogadores (Mover e Disparar) ---
            posicoes_jogadores = [] 
            for state in player_states.values():
                if state.get('handshake_completo', False) and state.get('hp', 0) > 0:
                    posicoes_jogadores.append( (state['x'], state['y']) )
                    
                    if state.get('esta_regenerando', False):
                        if (state['teclas']['w'] or state['teclas']['a'] or 
                            state['teclas']['s'] or state['teclas']['d'] or 
                            state['alvo_mouse'] is not None):
                            state['esta_regenerando'] = False
                        
                        elif state['hp'] >= state['max_hp']:
                            state['hp'] = state['max_hp']
                            state['esta_regenerando'] = False
                        
                        elif agora_ms - state.get('ultimo_tick_regeneracao', 0) > REGEN_TICK_RATE_MS:
                            state['ultimo_tick_regeneracao'] = agora_ms
                            state['hp'] = min(state['max_hp'], state['hp'] + REGEN_POR_TICK)
                            state['ultimo_hit_tempo'] = agora_ms 
                    
                    # Atualiza lógica de movimento/tiro do jogador
                    novo_proj = update_player_logic(state)
                    if novo_proj:
                        novos_projeteis.append(novo_proj)
                    
                    # --- INÍCIO: LÓGICA DE AUXILIARES ---
                    num_aux = state.get('nivel_aux', 0)
                    if num_aux > 0 and state.get('alvo_lock'):
                        target_id = state['alvo_lock']
                        
                        # Verifica se o alvo (NPC) ainda existe
                        alvo_npc = next((npc for npc in network_npcs if npc['id'] == target_id), None)
                        
                        if alvo_npc:
                            for i in range(num_aux):
                                # 1. Verificar Cooldown
                                if agora_ms > state['aux_cooldowns'][i]:
                                    
                                    # 2. Calcular Posição do Auxiliar
                                    offset_vec = AUX_POSICOES[i]
                                    rotated_vec = offset_vec.rotate(-state['angulo'])
                                    aux_x = state['x'] + rotated_vec.x
                                    aux_y = state['y'] + rotated_vec.y
                                    
                                    # 3. Verificar Distância
                                    dist_sq = (alvo_npc['x'] - aux_x)**2 + (alvo_npc['y'] - aux_y)**2
                                    
                                    if dist_sq < AUX_DISTANCIA_TIRO_SQ:
                                        # 4. Disparar Projétil Teleguiado
                                        state['aux_cooldowns'][i] = agora_ms + AUX_COOLDOWN_TIRO
                                        
                                        # (Calcula ângulo para o projétil - não precisa ser perfeito, é teleguiado)
                                        radianos = math.radians(state['angulo'])
                                        vel_x_inicial = -math.sin(radianos) * VELOCIDADE_PROJETIL_TELE
                                        vel_y_inicial = -math.cos(radianos) * VELOCIDADE_PROJETIL_TELE

                                        proj_aux = {
                                            'id': f"{state['nome']}_aux{i}_{agora_ms}", 
                                            'owner_nome': state['nome'],
                                            'x': aux_x, 'y': aux_y,
                                            'pos_inicial_x': aux_x, 'pos_inicial_y': aux_y,
                                            'dano': state['nivel_dano'], # Auxiliares usam o dano do jogador
                                            'tipo': 'player', 
                                            'timestamp_criacao': agora_ms,
                                            'tipo_proj': 'teleguiado',
                                            'velocidade': VELOCIDADE_PROJETIL_TELE,
                                            'alvo_id': target_id,
                                            'vel_x': vel_x_inicial,
                                            'vel_y': vel_y_inicial
                                        }
                                        novos_projeteis.append(proj_aux)
                    # --- FIM: LÓGICA DE AUXILIARES ---

            network_projectiles.extend(novos_projeteis)
            novos_projeteis.clear() 

            # --- Parte 2: Atualizar Projéteis (Mover) ---
            for proj in network_projectiles:
                
                if proj['tipo'] == 'player':
                    tipo_logica = proj.get('tipo_proj', 'normal')

                    if tipo_logica == 'teleguiado':
                        if agora_ms - proj.get('timestamp_criacao', 0) > DURACAO_PROJETIL_TELE_MS:
                            projeteis_para_remover.append(proj)
                            continue
                        
                        alvo_id = proj.get('alvo_id')
                        alvo_npc = None
                        if alvo_id:
                            alvo_npc = next((npc for npc in network_npcs if npc['id'] == alvo_id), None)
                        
                        if alvo_npc:
                            try:
                                vec_para_alvo_x = alvo_npc['x'] - proj['x']
                                vec_para_alvo_y = alvo_npc['y'] - proj['y']
                                dist = math.sqrt(vec_para_alvo_x**2 + vec_para_alvo_y**2)
                                
                                if dist > 0:
                                    ideal_vel_x = (vec_para_alvo_x / dist) * proj['velocidade']
                                    ideal_vel_y = (vec_para_alvo_y / dist) * proj['velocidade']
                                    
                                    proj['vel_x'] = proj['vel_x'] + (ideal_vel_x - proj['vel_x']) * TURN_SPEED_TELE
                                    proj['vel_y'] = proj['vel_y'] + (ideal_vel_y - proj['vel_y']) * TURN_SPEED_TELE
                            except (ValueError, KeyError):
                                pass 

                    proj['x'] += proj.get('vel_x', 0)
                    proj['y'] += proj.get('vel_y', 0)
                else: # 'npc'
                    proj['x'] += math.cos(proj['angulo_rad']) * proj['velocidade']
                    proj['y'] += math.sin(proj['angulo_rad']) * proj['velocidade']

                dist_sq = (proj['x'] - proj['pos_inicial_x'])**2 + (proj['y'] - proj['pos_inicial_y'])**2
                if dist_sq > s.MAX_DISTANCIA_TIRO**2:
                    projeteis_para_remover.append(proj)
                elif not s.MAP_RECT.collidepoint((proj['x'], proj['y'])):
                    projeteis_para_remover.append(proj)
            
            # --- (Parte 3: Spawns e Atualização de NPCs - Sem alterações) ---
            if posicoes_jogadores: 
                
                contagem_inimigos_normais = 0
                contagem_motherships = 0
                contagem_boss_congelante = 0
                
                for npc in network_npcs:
                    tipo = npc.get('tipo', 'perseguidor')
                    if tipo == 'mothership':
                        contagem_motherships += 1
                    elif tipo == 'boss_congelante':
                        contagem_boss_congelante += 1
                    elif 'minion' not in tipo: 
                        contagem_inimigos_normais += 1
                
                if contagem_inimigos_normais < s.MAX_INIMIGOS:
                    spawn_x, spawn_y = server_calcular_posicao_spawn(posicoes_jogadores)
                    novo_npc = server_spawnar_inimigo_aleatorio(spawn_x, spawn_y, f"npc_{next_npc_id}")
                    network_npcs.append(novo_npc)
                    next_npc_id += 1
                
                if contagem_motherships < s.MAX_MOTHERSHIPS:
                    spawn_x, spawn_y = server_calcular_posicao_spawn(posicoes_jogadores)
                    novo_boss = server_spawnar_mothership(spawn_x, spawn_y, f"ms_{next_npc_id}")
                    network_npcs.append(novo_boss)
                    next_npc_id += 1
                    print(f"[SERVIDOR] Spawnow Mothership {novo_boss['id']}")

                if contagem_boss_congelante < s.MAX_BOSS_CONGELANTE:
                    spawn_x, spawn_y = server_calcular_posicao_spawn(posicoes_jogadores)
                    novo_boss = server_spawnar_boss_congelante(spawn_x, spawn_y, f"bc_{next_npc_id}")
                    network_npcs.append(novo_boss)
                    next_npc_id += 1
                    print(f"[SERVIDOR] Spawnow Boss Congelante {novo_boss['id']}")

                for npc in network_npcs:
                    novo_proj_npc = update_npc_logic(npc, posicoes_jogadores) 
                    if novo_proj_npc:
                        novos_projeteis.append(novo_proj_npc)
                
                network_projectiles.extend(novos_projeteis)

            # --- (Parte 4: Lógica de Colisão - MODIFICADA) ---
            projeteis_ativos = network_projectiles[:] 

            for proj in projeteis_ativos:
                if proj in projeteis_para_remover:
                    continue

                if proj['tipo'] == 'player':
                    for npc in network_npcs:
                        if npc in npcs_para_remover: 
                            continue
                        
                        dist_colisao_sq = ( (npc['tamanho']/2 + 5)**2 ) 
                        dist_sq = (npc['x'] - proj['x'])**2 + (npc['y'] - proj['y'])**2
                        
                        if dist_sq < dist_colisao_sq:
                            # Encontra o jogador que atirou
                            owner_state = None
                            for p_state in player_states.values():
                                if p_state['nome'] == proj['owner_nome']:
                                    owner_state = p_state
                                    break
                            
                            dano_real = proj['dano']
                            if owner_state:
                                # Dano é sempre baseado no dono (para tiros normais e de aux)
                                dano_real = owner_state['nivel_dano']
                            
                            npc['hp'] -= dano_real
                            
                            projeteis_para_remover.append(proj) 
                            
                            if npc['hp'] <= 0:
                                npcs_para_remover.append(npc) 
                                
                                owner_nome = proj['owner_nome']
                                if owner_state: # Se encontrámos o dono
                                    # --- MODIFICADO: Chamar função de ganhar pontos ---
                                    server_ganhar_pontos(owner_state, npc.get('pontos_por_morte', 5))
                                    # --- FIM DA MODIFICAÇÃO ---
                                    print(f"Jogador {owner_nome} ganhou {npc.get('pontos_por_morte', 5)} pontos. Total: {owner_state['pontos']}") 
                            
                            break 
                
                elif proj['tipo'] == 'npc':
                    for player_state in player_states.values():
                        if player_state['hp'] <= 0 or not player_state.get('handshake_completo', False):
                            continue

                        dist_sq = (player_state['x'] - proj['x'])**2 + (player_state['y'] - proj['y'])**2
                        
                        if dist_sq < COLISAO_JOGADOR_PROJ_DIST_SQ:
                            if agora_ms - player_state.get('ultimo_hit_tempo', 0) > 150:
                                
                                reducao_percent = min(player_state['nivel_escudo'] * s.REDUCAO_DANO_POR_NIVEL, 75)
                                dano_reduzido = proj['dano'] * (1 - reducao_percent / 100.0)
                                player_state['hp'] -= dano_reduzido
                                
                                player_state['ultimo_hit_tempo'] = agora_ms
                                player_state['esta_regenerando'] = False 
                                projeteis_para_remover.append(proj) 
                                
                                if player_state['hp'] <= 0:
                                    print(f"[SERVIDOR] Jogador {player_state['nome']} morreu!")
                                
                                break 

            # --- Limpeza ---
            if projeteis_para_remover:
                projeteis_a_manter = []
                for p in network_projectiles:
                    if p not in projeteis_para_remover:
                        projeteis_a_manter.append(p)
                network_projectiles = projeteis_a_manter
            
            if npcs_para_remover:
                network_npcs = [n for n in network_npcs if n not in npcs_para_remover]
                for state in player_states.values():
                    if state.get('alvo_lock') in [npc['id'] for npc in npcs_para_remover]:
                        state['alvo_lock'] = None
            
            
            # --- (Parte 5: Construir a string de estado global - MODIFICADA) ---
            if not player_states: 
                time.sleep(TICK_INTERVAL)
                continue
                
            lista_de_estados = []
            for state in player_states.values():
                if state.get('handshake_completo', False):
                    # --- INÍCIO: MODIFICAÇÃO (Adicionar dados de UPGRADE) ---
                    regen_status = 1 if state.get('esta_regenerando', False) else 0
                    # Formato: 15 campos
                    estado_str = (
                        f"{state['nome']}:{state['x']:.1f}:{state['y']:.1f}:{state['angulo']:.0f}:{state['hp']:.1f}:{state['max_hp']}:{state['pontos']}:{regen_status}"
                        f":{state['pontos_upgrade_disponiveis']}:{state['total_upgrades_feitos']}"
                        f":{state['nivel_motor']}:{state['nivel_dano']}:{state['nivel_max_vida']}"
                        f":{state['nivel_escudo']}:{state['nivel_aux']}"
                    )
                    # --- FIM: MODIFICAÇÃO ---
                    lista_de_estados.append(estado_str)
            payload_players = ";".join(lista_de_estados)

            lista_de_projeteis = []
            for proj in network_projectiles:
                proj_str = f"{proj['id']}:{proj['x']:.1f}:{proj['y']:.1f}:{proj['tipo']}"
                lista_de_projeteis.append(proj_str)
            payload_proj = ";".join(lista_de_projeteis)

            lista_de_npcs = []
            for npc in network_npcs:
                npc_str = (
                    f"{npc['id']}:{npc['tipo']}:{npc['x']:.1f}:{npc['y']:.1f}:{npc['angulo']:.0f}:{npc['hp']}:{npc['max_hp']}:{npc['tamanho']}"
                )
                lista_de_npcs.append(npc_str)
            payload_npcs = ";".join(lista_de_npcs)
            
            full_message = f"STATE|{payload_players}|PROJ|{payload_proj}|NPC|{payload_npcs}\n"
            full_message_bytes = full_message.encode('utf-8')
            
            # --- (Parte 6: Enviar a string global - Sem alterações) ---
            clientes_mortos = []
            for conn, state in player_states.items():
                
                if state.get('handshake_completo', False):
                    try:
                        conn.sendall(full_message_bytes)
                    except (socket.error, BrokenPipeError) as e:
                        print(f"[Game Loop] Erro ao enviar para {state['nome']}. Marcando para remoção.")
                        clientes_mortos.append(conn)

        # --- FIM DO BLOCO DE ATUALIZAÇÃO ---
        
        if clientes_mortos:
            with game_state_lock:
                for conn in clientes_mortos:
                    if conn in player_states:
                        print(f"[Game Loop] Removendo cliente morto: {player_states[conn]['nome']}")
                        del player_states[conn]
                        try:
                            conn.close() 
                        except:
                            pass 

        # Controla o Tick Rate
        time_elapsed = time.time() - loop_start_time
        sleep_time = TICK_INTERVAL - time_elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
# --- FIM ---


def handle_client(conn, addr):
    """
    Esta função corre numa thread separada para cada cliente.
    """
    print(f"[NOVA CONEXÃO] {addr} conetado.")
    
    nome_jogador = ""
    player_state = {} 
    
    try:
        # --- (ETAPA 1: Receber o nome do jogador - Sem alterações) ---
        data = conn.recv(1024)
        nome_jogador_original = data.decode('utf-8')
        
        if not nome_jogador_original:
            print(f"[{addr}] Desconectado (sem nome enviado).")
            conn.close()
            return
        
        nome_jogador = nome_jogador_original
        with game_state_lock:
            current_names = [p['nome'] for p in player_states.values()]
            
            i = 1
            while nome_jogador in current_names:
                nome_jogador = f"{nome_jogador_original}_{i}"
                i += 1
        
        if nome_jogador != nome_jogador_original:
             print(f"[{addr}] Nome '{nome_jogador_original}' já estava em uso. Renomeado para '{nome_jogador}'.")
        else:
             print(f"[{addr}] Jogador '{nome_jogador}' juntou-se.")

        # --- (ETAPA 2: Gerar Posição e Criar Estado - MODIFICADA) ---
        with game_state_lock:
             posicoes_atuais = [(p['x'], p['y']) for p in player_states.values()]
        spawn_x, spawn_y = server_calcular_posicao_spawn(posicoes_atuais)
        
        nivel_max_vida_inicial = 1
        max_hp_inicial = 4 + nivel_max_vida_inicial
        
        player_state = {
            'conn': conn, 
            'nome': nome_jogador,
            'x': float(spawn_x), 
            'y': float(spawn_y), 
            'angulo': 0.0,
            'teclas': { 'w': False, 'a': False, 's': False, 'd': False, 'space': False },
            'alvo_mouse': None, 
            'alvo_lock': None, 
            'ultimo_tiro_tempo': 0, 
            'cooldown_tiro': COOLDOWN_TIRO, 
            'handshake_completo': False,
            
            'max_hp': max_hp_inicial, 
            'hp': float(max_hp_inicial), 
            'ultimo_hit_tempo': 0,
            'pontos': 0, 
            'esta_regenerando': False,
            'ultimo_tick_regeneracao': 0,
            
            # --- INÍCIO: ADIÇÕES DE UPGRADE ---
            'pontos_upgrade_disponiveis': 0,
            'total_upgrades_feitos': 0,
            '_pontos_acumulados_para_upgrade': 0,
            '_limiar_pontos_atual': PONTOS_LIMIARES_PARA_UPGRADE[0],
            '_indice_limiar': 0,
            
            'nivel_motor': 1,
            'nivel_dano': 1,
            'nivel_max_vida': nivel_max_vida_inicial,
            'nivel_escudo': 0,
            'nivel_aux': 0,
            'aux_cooldowns': [0, 0, 0, 0] # <-- Novo Cooldown
            # --- FIM: ADIÇÕES DE UPGRADE ---
        }
        with game_state_lock:
            player_states[conn] = player_state
        
        response_string = f"BEMVINDO|{nome_jogador}|{int(spawn_x)}|{int(spawn_y)}"
        
        print(f"[{addr}] Enviando dados de spawn para '{nome_jogador}': {response_string}")
        conn.sendall(response_string.encode('utf-8'))
        
        with game_state_lock:
            if conn in player_states:
                player_states[conn]['handshake_completo'] = True
                print(f"[{addr}] Handshake concluído para '{nome_jogador}'.")
        
        # --- (ETAPA 3: Loop de Recebimento de Inputs - MODIFICADA) ---
        while True:
            data = conn.recv(2048)
            if not data:
                break 
            
            inputs = data.decode('utf-8').splitlines()
            
            with game_state_lock: 
                if conn not in player_states:
                    break 
                
                if player_state.get('hp', 0) <= 0:
                    for input_str in inputs:
                        if input_str == "RESPAWN_ME":
                            posicoes_atuais = [(p['x'], p['y']) for p in player_states.values() if p['conn'] != conn]
                            spawn_x, spawn_y = server_calcular_posicao_spawn(posicoes_atuais)
                            
                            player_state['x'] = spawn_x
                            player_state['y'] = spawn_y
                            
                            # --- INÍCIO: RESETAR ESTADO NO RESPAWN ---
                            nivel_max_vida_inicial = 1
                            max_hp_inicial = 4 + nivel_max_vida_inicial
                            
                            player_state['hp'] = max_hp_inicial
                            player_state['max_hp'] = max_hp_inicial
                            player_state['alvo_lock'] = None
                            player_state['alvo_mouse'] = None
                            player_state['pontos'] = 0 
                            player_state['esta_regenerando'] = False 
                            
                            player_state['pontos_upgrade_disponiveis'] = 0
                            player_state['total_upgrades_feitos'] = 0
                            player_state['_pontos_acumulados_para_upgrade'] = 0
                            player_state['_limiar_pontos_atual'] = PONTOS_LIMIARES_PARA_UPGRADE[0]
                            player_state['_indice_limiar'] = 0
                            
                            player_state['nivel_motor'] = 1
                            player_state['nivel_dano'] = 1
                            player_state['nivel_max_vida'] = nivel_max_vida_inicial
                            player_state['nivel_escudo'] = 0
                            player_state['nivel_aux'] = 0
                            player_state['aux_cooldowns'] = [0, 0, 0, 0] # Resetar cooldowns
                            # --- FIM: RESETAR ESTADO ---
                            
                            print(f"[{addr}] Jogador {player_state['nome']} respawnou.")
                    continue 
                
                for input_str in inputs:
                    if not input_str: continue 
                    
                    if input_str == "W_DOWN":
                        player_state['teclas']['w'] = True
                        player_state['alvo_mouse'] = None 
                    elif input_str == "W_UP":
                        player_state['teclas']['w'] = False
                    
                    elif input_str == "A_DOWN":
                        player_state['teclas']['a'] = True
                        player_state['alvo_mouse'] = None
                    
                    elif input_str == "A_UP":
                        player_state['teclas']['a'] = False
                    elif input_str == "S_DOWN":
                        player_state['teclas']['s'] = True
                        player_state['alvo_mouse'] = None 
                    elif input_str == "S_UP":
                        player_state['teclas']['s'] = False
                        
                    elif input_str == "D_DOWN":
                        player_state['teclas']['d'] = True
                        player_state['alvo_mouse'] = None
                    
                    elif input_str == "D_UP":
                        player_state['teclas']['d'] = False
                    elif input_str == "SPACE_DOWN":
                        player_state['teclas']['space'] = True
                    elif input_str == "SPACE_UP":
                        player_state['teclas']['space'] = False

                    elif input_str.startswith("CLICK_MOVE|"):
                        parts = input_str.split('|')
                        player_state['alvo_mouse'] = (int(parts[1]), int(parts[2]))
                        player_state['teclas']['w'] = False 
                        player_state['teclas']['s'] = False
                    
                    elif input_str.startswith("CLICK_TARGET|"):
                        parts = input_str.split('|')
                        click_x = int(parts[1])
                        click_y = int(parts[2])
                        
                        alvo_encontrado_id = None
                        dist_min_sq = float('inf')

                        for npc in network_npcs:
                            dist_sq = (npc['x'] - click_x)**2 + (npc['y'] - click_y)**2
                            if dist_sq < TARGET_CLICK_SIZE_SQ and dist_sq < dist_min_sq:
                                dist_min_sq = dist_sq
                                alvo_encontrado_id = npc['id']
                        
                        if alvo_encontrado_id:
                            player_state['alvo_lock'] = alvo_encontrado_id 
                            print(f"[{addr}] Travou mira no NPC {alvo_encontrado_id}")
                        else:
                            player_state['alvo_lock'] = None 
                            print(f"[{addr}] Mira limpa (clique no vazio)")
                        
                        player_state['alvo_mouse'] = None 
                    
                    elif input_str == "TOGGLE_REGEN":
                        if (not player_state['esta_regenerando'] and 
                            (player_state['teclas']['w'] or player_state['teclas']['a'] or 
                             player_state['teclas']['s'] or player_state['teclas']['d'] or
                             player_state['alvo_mouse'] is not None)):
                            pass 
                        
                        elif not player_state['esta_regenerando'] and player_state['hp'] < player_state['max_hp']:
                            player_state['esta_regenerando'] = True
                            player_state['ultimo_tick_regeneracao'] = int(time.time() * 1000)
                        else:
                            player_state['esta_regenerando'] = False
                    
                    # --- INÍCIO: ADICIONAR INPUT DE UPGRADE ---
                    elif input_str.startswith("BUY_UPGRADE|"):
                        tipo_upgrade = input_str.split('|', 1)[-1]
                        server_comprar_upgrade(player_state, tipo_upgrade)
                    # --- FIM: ADICIONAR INPUT DE UPGRADE ---

    except ConnectionResetError:
        print(f"[{addr} - {nome_jogador}] Conexão perdida abruptamente.")
    except ConnectionError as e:
        print(f"[{addr}] Erro de conexão: {e}")
    except Exception as e:
        print(f"[{addr} - {nome_jogador}] Erro: {e}")
    
    print(f"[CONEXÃO TERMINADA] {addr} ({nome_jogador}) desconetou.")
    
    with game_state_lock:
        if conn in player_states:
            del player_states[conn]
    
    conn.close()


# --- (Função iniciar_servidor - Sem alterações) ---
def iniciar_servidor():
    """
    Inicia o servidor, o Game Loop, e escuta por conexões.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        server_socket.bind((HOST, PORT))
    except socket.error as e:
        print(str(e))
        print("Erro ao ligar o servidor. A porta já está em uso?")
        return

    server_socket.listen(MAX_JOGADORES)
    print(f"[SERVIDOR INICIADO] À escuta em {HOST}:{PORT}")

    loop_thread = threading.Thread(target=game_loop, daemon=True)
    loop_thread.start()

    while True:
        try:
            conn, addr = server_socket.accept()
            
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            
            with game_state_lock:
                print(f"[CONEXÕES ATIVAS] {len(player_states)}")
        
        except KeyboardInterrupt:
            print("\n[SERVIDOR DESLIGANDO]... Fechando conexões.")
            with game_state_lock:
                for conn in player_states:
                    conn.close()
            network_npcs.clear()
            network_projectiles.clear()
            player_states.clear()
            
            server_socket.close()
            break 
        except Exception as e:
            print(f"[ERRO NO LOOP PRINCIPAL] {e}")
# --- FIM ---


# --- (Inicia o Servidor - Sem alterações) ---
if __name__ == "__main__":
    if not hasattr(s, 'VELOCIDADE_ROTACAO_NAVE'):
        print("[AVISO] 'VELOCIDADE_ROTACAO_NAVE' não encontrada em settings.py. A usar valor padrão 5.")
        s.VELOCIDADE_ROTACAO_NAVE = 5
    
    if not hasattr(s, 'MAX_MOTHERSHIPS'):
        print("[AVISO] 'MAX_MOTHERSHIPS' não encontrada em settings.py. A usar valor padrão 2.")
        s.MAX_MOTHERSHIPS = 2
    if not hasattr(s, 'MAX_BOSS_CONGELANTE'):
        print("[AVISO] 'MAX_BOSS_CONGELANTE' não encontrada em settings.py. A usar valor padrão 1.")
        s.MAX_BOSS_CONGELANTE = 1
    if not hasattr(s, 'HP_BOSS_CONGELANTE'):
        print("[AVISO] 'HP_BOSS_CONGELANTE' não encontrada em settings.py. A usar valor padrão 400.")
        s.HP_BOSS_CONGELANTE = 400
    if not hasattr(s, 'PONTOS_BOSS_CONGELANTE'):
        print("[AVISO] 'PONTOS_BOSS_CONGELANTE' não encontrada em settings.py. A usar valor padrão 300.")
        s.PONTOS_BOSS_CONGELANTE = 300
    if not hasattr(s, 'COOLDOWN_TIRO_CONGELANTE'):
        print("[AVISO] 'COOLDOWN_TIRO_CONGELANTE' não encontrada em settings.py. A usar valor padrão 10000.")
        s.COOLDOWN_TIRO_CONGELANTE = 10000
    
    # Validações de constantes de Upgrade
    if not hasattr(s, 'MAX_TOTAL_UPGRADES'):
        print("[AVISO] 'MAX_TOTAL_UPGRADES' não encontrada. A usar valor padrão 12.")
        s.MAX_TOTAL_UPGRADES = 12
    if not hasattr(s, 'CUSTOS_AUXILIARES'):
        print("[AVISO] 'CUSTOS_AUXILIARES' não encontrada. A usar valor padrão [1, 2, 3, 4].")
        s.CUSTOS_AUXILIARES = [1, 2, 3, 4]

    iniciar_servidor()