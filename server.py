# server.py
import socket
import threading
import random
import settings as s # Para saber o tamanho do mapa
import math 
import time 
import pygame

# 1. Configurações do Servidor
HOST = '127.0.0.1'  # IP para escutar
PORT = 5555         # Porta para escutar
MAX_JOGADORES = 16
TICK_RATE = 60 # 60 atualizações por segundo

# --- (Estado de Jogo Unificado - Sem alterações) ---
player_states = {}
network_projectiles = []
network_npcs = []
next_npc_id = 0
game_state_lock = threading.Lock() 
# --- FIM ---


# --- (Constantes de Jogo e IA - COM ADIÇÕES) ---
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

# --- INÍCIO DA MODIFICAÇÃO (Problemas 1 e 2: Constantes de Mira) ---
# (Valor de settings.py)
MAX_TARGET_LOCK_DISTANCE_SQ = s.MAX_TARGET_LOCK_DISTANCE**2 # 1000 * 1000
# (Valor de settings.py)
TARGET_CLICK_SIZE_SQ = (s.TARGET_CLICK_SIZE / 2)**2 # (150/2)^2 = 75^2
# --- FIM DA MODIFICAÇÃO ---


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

# --- INÍCIO DA MODIFICAÇÃO (Problemas 1 e 3: Lógica de Rotação) ---
def update_player_logic(player_state):
    """ Calcula a nova posição, ângulo E processa o tiro de UM jogador. """
    
    # --- 1. Lógica de Rotação (REESCRITA para usar ID) ---
    angulo_alvo = None
    
    # Se o jogador tem um alvo travado (agora é um ID, ex: "npc_1")
    if player_state['alvo_lock']:
        target_id = player_state['alvo_lock']
        alvo_coords = None
        alvo_encontrado = False

        # Procura o alvo na lista de NPCs
        # (Esta função corre DENTRO do game_loop lock, por isso é seguro ler network_npcs)
        for npc in network_npcs: 
            if npc['id'] == target_id:
                alvo_coords = (npc['x'], npc['y'])
                alvo_encontrado = True
                break
        
        # (No futuro, procurar também em 'player_states' para PvP)
        
        # Se o alvo não foi encontrado (morreu ou desconectou)
        if not alvo_encontrado:
            player_state['alvo_lock'] = None # Cancela a trava
        else:
            target_x, target_y = alvo_coords
            
            # Problema 1: Verifica a distância (como no offline)
            dist_sq = (target_x - player_state['x'])**2 + (target_y - player_state['y'])**2
            if dist_sq > MAX_TARGET_LOCK_DISTANCE_SQ:
                player_state['alvo_lock'] = None # Cancela (muito longe)
            else:
                # Se passou em tudo, mira no alvo
                vec_x = target_x - player_state['x']
                vec_y = target_y - player_state['y']
                if (vec_x**2 + vec_y**2) > 0: 
                     radianos = math.atan2(vec_y, vec_x)
                     angulo_alvo = -math.degrees(radianos) - 90 

    # Se NÃO tem trava, usa o mouse de movimento (clique direito) para mirar
    elif player_state['alvo_mouse']:
        target_x, target_y = player_state['alvo_mouse']
        vec_x = target_x - player_state['x']
        vec_y = target_y - player_state['y']
        if (vec_x**2 + vec_y**2) > 5.0**2: 
             radianos = math.atan2(vec_y, vec_x)
             angulo_alvo = -math.degrees(radianos) - 90
             
    if angulo_alvo is not None:
        player_state['angulo'] = angulo_alvo
    # Se não houver mira (nem trava, nem mouse), usa as teclas A/D
    elif player_state['teclas']['a']:
        player_state['angulo'] += s.VELOCIDADE_ROTACAO_NAVE
    elif player_state['teclas']['d']:
        player_state['angulo'] -= s.VELOCIDADE_ROTACAO_NAVE
    player_state['angulo'] %= 360

    # --- 2. Lógica de Movimento (Sem alterações, já está correta) ---
    velocidade_atual = VELOCIDADE_MOVIMENTO_NAVE
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

    # --- 3. Limitar ao Mapa (Clamping) (Sem alterações) ---
    meia_largura = 15 
    meia_altura = 15
    nova_pos_x = max(meia_largura, min(nova_pos_x, s.MAP_WIDTH - meia_largura))
    nova_pos_y = max(meia_altura, min(nova_pos_y, s.MAP_HEIGHT - meia_altura))

    player_state['x'] = nova_pos_x
    player_state['y'] = nova_pos_y

    # --- 4. Lógica de Tiro (Sem alterações) ---
    if player_state['teclas']['space'] or player_state['alvo_lock']:
        agora_ms = int(time.time() * 1000) 
        if agora_ms - player_state['ultimo_tiro_tempo'] > player_state['cooldown_tiro']:
            player_state['ultimo_tiro_tempo'] = agora_ms
            radianos = math.radians(player_state['angulo'])
            pos_x = player_state['x'] + (-math.sin(radianos) * OFFSET_PONTA_TIRO)
            pos_y = player_state['y'] + (-math.cos(radianos) * OFFSET_PONTA_TIRO)
            
            novo_projetil = {
                'id': f"{player_state['nome']}_{agora_ms}", 
                'owner_nome': player_state['nome'],
                'x': pos_x, 'y': pos_y,
                'pos_inicial_x': pos_x, 'pos_inicial_y': pos_y,
                'angulo_rad': radianos, 'velocidade': VELOCIDADE_PROJETIL,
                'dano': player_state['nivel_dano'], 'tipo': 'player' 
            }
            return novo_projetil
    return None
# --- FIM DA MODIFICAÇÃO ---

# --- (Função update_npc_logic - COM TIROS - Sem alterações) ---
def update_npc_logic(npc, players_pos_lista):
    """ Atualiza a lógica de IA para um NPC e retorna um projétil se atirar. """
    
    # 1. Encontra o jogador mais próximo
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
        
    # 2. Move-se em direção ao alvo
    vec_x = alvo_pos[0] - npc['x']
    vec_y = alvo_pos[1] - npc['y']
    dist = math.sqrt(dist_min_sq)

    if dist_min_sq > DISTANCIA_PARAR_PERSEGUIDOR_SQ:
        dir_x = vec_x / dist
        dir_y = vec_y / dist
        npc['x'] += dir_x * VELOCIDADE_PERSEGUIDOR
        npc['y'] += dir_y * VELOCIDADE_PERSEGUIDOR
        
    # Atualiza o ângulo (sempre mira no alvo)
    radianos = math.atan2(vec_y, vec_x)
    npc['angulo'] = -math.degrees(radianos) - 90
    npc['angulo'] %= 360
    
    # 3. Lógica de Tiro
    if dist_min_sq < DISTANCIA_TIRO_PERSEGUIDOR_SQ:
        agora_ms = int(time.time() * 1000)
        if agora_ms - npc['ultimo_tiro_tempo'] > npc['cooldown_tiro']:
            npc['ultimo_tiro_tempo'] = agora_ms
            
            dir_x = vec_x / dist
            dir_y = vec_y / dist
            angulo_rad_proj = radianos 
            
            novo_projetil = {
                'id': f"{npc['id']}_{agora_ms}", 
                'owner_nome': npc['id'],
                'x': npc['x'], 'y': npc['y'], 
                'pos_inicial_x': npc['x'], 'pos_inicial_y': npc['y'],
                'angulo_rad': angulo_rad_proj, 
                'velocidade': VELOCIDADE_PROJETIL_NPC,
                'dano': 1, 
                'tipo': 'npc' 
            }
            return novo_projetil 
            
    return None 
# --- FIM ---
        

# --- (Função game_loop - COM TIROS - Sem alterações) ---
def game_loop():
    """
    O loop principal do servidor.
    """
    global next_npc_id
    
    print("[GAME LOOP INICIADO] O servidor está agora a calcular e a enviar o estado.")
    
    TICK_INTERVAL = 1.0 / TICK_RATE 
    
    while True:
        loop_start_time = time.time()
        
        novos_projeteis = []
        
        with game_state_lock:
            # --- Parte 1: Atualizar Jogadores (Mover e Disparar) ---
            posicoes_jogadores = [] 
            for state in player_states.values():
                if state.get('handshake_completo', False):
                    posicoes_jogadores.append( (state['x'], state['y']) )
                    
                    novo_proj = update_player_logic(state)
                    if novo_proj:
                        novos_projeteis.append(novo_proj)
            
            network_projectiles.extend(novos_projeteis)
            novos_projeteis.clear() 

            # --- Parte 2: Atualizar Projéteis (Mover) ---
            projeteis_para_remover = []
            for proj in network_projectiles:
                
                if proj['tipo'] == 'player':
                    proj['x'] += -math.sin(proj['angulo_rad']) * proj['velocidade']
                    proj['y'] += -math.cos(proj['angulo_rad']) * proj['velocidade']
                else: # 'npc'
                    proj['x'] += math.cos(proj['angulo_rad']) * proj['velocidade']
                    proj['y'] += math.sin(proj['angulo_rad']) * proj['velocidade']

                dist_sq = (proj['x'] - proj['pos_inicial_x'])**2 + (proj['y'] - proj['pos_inicial_y'])**2
                if dist_sq > s.MAX_DISTANCIA_TIRO**2:
                    projeteis_para_remover.append(proj)
                elif not s.MAP_RECT.collidepoint((proj['x'], proj['y'])):
                    projeteis_para_remover.append(proj)
            
            for proj in projeteis_para_remover:
                network_projectiles.remove(proj)
            
            # --- Parte 3: Spawns e Atualização de NPCs ---
            if posicoes_jogadores: 
                # Spawna novos NPCs
                if len(network_npcs) < s.MAX_INIMIGOS:
                    spawn_x, spawn_y = server_calcular_posicao_spawn(posicoes_jogadores)
                    
                    novo_npc = {
                        'id': f"npc_{next_npc_id}",
                        'tipo': "perseguidor",
                        'x': spawn_x,
                        'y': spawn_y,
                        'angulo': 0.0,
                        'hp': 3,
                        'cooldown_tiro': COOLDOWN_TIRO_PERSEGUIDOR, 
                        'ultimo_tiro_tempo': 0 
                    }
                    network_npcs.append(novo_npc)
                    next_npc_id += 1
                
                # Atualiza IA dos NPCs
                for npc in network_npcs:
                    novo_proj_npc = update_npc_logic(npc, posicoes_jogadores)
                    if novo_proj_npc:
                        novos_projeteis.append(novo_proj_npc)
                
                network_projectiles.extend(novos_projeteis)

            # --- Parte 4: Lógica de Colisão (Futuro) ---
            
            # --- Parte 5: Construir a string de estado global ---
            if not player_states: 
                time.sleep(TICK_INTERVAL)
                continue
                
            lista_de_estados = []
            for state in player_states.values():
                if state.get('handshake_completo', False):
                    estado_str = (
                        f"{state['nome']}:{state['x']:.1f}:{state['y']:.1f}:{state['angulo']:.0f}"
                    )
                    lista_de_estados.append(estado_str)
            payload_players = ";".join(lista_de_estados)

            lista_de_projeteis = []
            for proj in network_projectiles:
                proj_str = f"{proj['x']:.1f}:{proj['y']:.1f}:{proj['tipo']}"
                lista_de_projeteis.append(proj_str)
            payload_proj = ";".join(lista_de_projeteis)

            lista_de_npcs = []
            for npc in network_npcs:
                npc_str = (
                    f"{npc['id']}:{npc['tipo']}:{npc['x']:.1f}:{npc['y']:.1f}:{npc['angulo']:.0f}"
                )
                lista_de_npcs.append(npc_str)
            payload_npcs = ";".join(lista_de_npcs)
            
            full_message = f"STATE|{payload_players}|PROJ|{payload_proj}|NPC|{payload_npcs}\n"
            full_message_bytes = full_message.encode('utf-8')
            
            # --- Parte 6: Enviar a string global para TODOS os jogadores ---
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
        # --- ETAPA 1: Receber o nome do jogador ---
        data = conn.recv(2048)
        if not data:
            raise ConnectionError("Cliente desconectou antes de enviar o nome.")
            
        nome_jogador = data.decode('utf-8')
        
        with game_state_lock:
            for state in player_states.values():
                if state['nome'] == nome_jogador:
                    nome_jogador = f"{nome_jogador}_{random.randint(1, 99)}"
                    break
        
        print(f"[{addr}] Jogador '{nome_jogador}' juntou-se.")

        # --- ETAPA 2: Gerar Posição e Criar Estado ---
        with game_state_lock:
             posicoes_atuais = [(p['x'], p['y']) for p in player_states.values()]
        spawn_x, spawn_y = server_calcular_posicao_spawn(posicoes_atuais)
        
        player_state = {
            'conn': conn, 
            'nome': nome_jogador,
            'x': float(spawn_x), 
            'y': float(spawn_y), 
            'angulo': 0.0,
            'teclas': { 'w': False, 'a': False, 's': False, 'd': False, 'space': False },
            'alvo_mouse': None, 
            'alvo_lock': None, # Será um ID (ex: "npc_1") ou None
            'ultimo_tiro_tempo': 0, 
            'cooldown_tiro': COOLDOWN_TIRO, 
            'nivel_dano': 1,
            'handshake_completo': False 
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
        
        # --- ETAPA 3: Loop de Recebimento de Inputs ---
        while True:
            data = conn.recv(2048)
            if not data:
                break 
            
            inputs = data.decode('utf-8').splitlines()
            
            # --- INÍCIO DA MODIFICAÇÃO (Problema 2: Lógica de Clique) ---
            # (Precisamos do lock aqui para ler 'network_npcs' em segurança)
            with game_state_lock: 
            # --- FIM DA MODIFICAÇÃO ---
                if conn not in player_states:
                    break 
                
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
                        # NÃO limpa alvo_lock
                        player_state['teclas']['w'] = False 
                        player_state['teclas']['s'] = False
                    
                    # --- INÍCIO DA MODIFICAÇÃO (Problema 2: Lógica de Clique Vazio) ---
                    elif input_str.startswith("CLICK_TARGET|"):
                        parts = input_str.split('|')
                        click_x = int(parts[1])
                        click_y = int(parts[2])
                        
                        alvo_encontrado_id = None
                        dist_min_sq = float('inf')

                        # Verifica se o clique acertou um NPC
                        # (Como estamos dentro do lock, é seguro ler 'network_npcs')
                        for npc in network_npcs:
                            # (Usamos 75*75, que é o raio do TARGET_CLICK_SIZE)
                            dist_sq = (npc['x'] - click_x)**2 + (npc['y'] - click_y)**2
                            if dist_sq < TARGET_CLICK_SIZE_SQ and dist_sq < dist_min_sq:
                                dist_min_sq = dist_sq
                                alvo_encontrado_id = npc['id']
                        
                        # (No futuro, adicionar verificação de outros jogadores aqui)

                        if alvo_encontrado_id:
                            player_state['alvo_lock'] = alvo_encontrado_id # Trava no ID
                            print(f"[{addr}] Travou mira no NPC {alvo_encontrado_id}")
                        else:
                            player_state['alvo_lock'] = None # Clique no vazio
                            print(f"[{addr}] Mira limpa (clique no vazio)")
                        
                        player_state['alvo_mouse'] = None # Trava cancela mouse
                    # --- FIM DA MODIFICAÇÃO ---


    except ConnectionResetError:
        print(f"[{addr} - {nome_jogador}] Conexão perdida abruptamente.")
    except ConnectionError as e:
        print(f"[{addr}] Erro de conexão: {e}")
    except Exception as e:
        print(f"[{addr} - {nome_jogador}] Erro: {e}")

    # Quando o loop 'while' termina (cliente desconectou)
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


# --- Inicia o Servidor ---
if __name__ == "__main__":
    if not hasattr(s, 'VELOCIDADE_ROTACAO_NAVE'):
        print("[AVISO] 'VELOCIDADE_ROTACAO_NAVE' não encontrada em settings.py. A usar valor padrão 5.")
        s.VELOCIDADE_ROTACAO_NAVE = 5
    
    iniciar_servidor()