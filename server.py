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

# --- INÍCIO DA MODIFICAÇÃO (Estado de Jogo Unificado) ---
# Dicionário global para guardar o estado de todos os jogadores
player_states = {}
# Lista global para guardar todos os projéteis ativos
network_projectiles = []
# Lista global para guardar todos os NPCs ativos
network_npcs = []
# ID Único para os NPCs
next_npc_id = 0

# UM 'LOCK' PARA PROTEGER TODO O ESTADO DO JOGO
game_state_lock = threading.Lock() 
# --- FIM DA MODIFICAÇÃO ---


# --- Constantes de Jogo (copiadas de settings.py e ships.py) ---
COOLDOWN_TIRO = 250 # ms
VELOCIDADE_PROJETIL = 10
OFFSET_PONTA_TIRO = 25 # (altura 30 / 2 + 10)
VELOCIDADE_BASE_NAVE = 4 #
VELOCIDADE_MOVIMENTO_NAVE = VELOCIDADE_BASE_NAVE + 1 

# --- Constantes de IA (copiadas de enemies.py) ---
VELOCIDADE_PERSEGUIDOR = 2.0 #
DISTANCIA_PARAR_PERSEGUIDOR_SQ = 200**2 # (Quadrado para cálculos mais rápidos)
# (Usamos SPAWN_DIST_MIN para a função de spawn)
SPAWN_DIST_MIN = s.SPAWN_DIST_MIN

# --- INÍCIO DA MODIFICAÇÃO (Funções de Lógica de Jogo do Servidor) ---

def server_calcular_posicao_spawn(pos_referencia_lista):
    """ Encontra um ponto de spawn longe de todos os jogadores na lista. """
    while True:
        x = random.uniform(0, s.MAP_WIDTH)
        y = random.uniform(0, s.MAP_HEIGHT)
        pos_spawn = pygame.math.Vector2(x, y) # (Usamos Vector2 para cálculos de distância)
        
        # Verifica se está longe de todos os jogadores
        longe_suficiente = True
        if pos_referencia_lista: # Se a lista não estiver vazia
            for pos_ref in pos_referencia_lista:
                if pos_spawn.distance_to(pygame.math.Vector2(pos_ref[0], pos_ref[1])) < SPAWN_DIST_MIN:
                    longe_suficiente = False
                    break
        
        if longe_suficiente:
            return (float(x), float(y)) # Retorna como floats

def update_player_logic(player_state):
    """ Calcula a nova posição, ângulo E processa o tiro de UM jogador. """
    
    # --- 1. Lógica de Rotação ---
    angulo_alvo = None
    if player_state['alvo_lock']:
        target_x, target_y = player_state['alvo_lock']
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
            radianos = math.radians(player_state['angulo'])
            nova_pos_x += -math.sin(radianos) * velocidade_atual
            nova_pos_y += -math.cos(radianos) * velocidade_atual
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
            
            novo_projetil = {
                'id': f"{player_state['nome']}_{agora_ms}", 
                'owner_nome': player_state['nome'],
                'x': pos_x, 'y': pos_y,
                'pos_inicial_x': pos_x, 'pos_inicial_y': pos_y,
                'angulo_rad': radianos, 'velocidade': VELOCIDADE_PROJETIL,
                'dano': player_state['nivel_dano'], 'tipo': 'player' 
            }
            # (Adicionamos à lista global fora da função, usando o lock)
            return novo_projetil
    return None

def update_npc_logic(npc, players_pos_lista):
    """ Atualiza a lógica de IA para um NPC. """
    
    # 1. Encontra o jogador mais próximo
    alvo = None
    dist_min_sq = float('inf')
    
    if not players_pos_lista:
        return # Ninguém para perseguir

    for p_pos in players_pos_lista:
        dist_sq = (npc['x'] - p_pos[0])**2 + (npc['y'] - p_pos[1])**2
        if dist_sq < dist_min_sq:
            dist_min_sq = dist_sq
            alvo = p_pos # (x, y) do jogador
            
    # 2. Move-se em direção ao alvo (Lógica do InimigoPerseguidor)
    if alvo and dist_min_sq > DISTANCIA_PARAR_PERSEGUIDOR_SQ:
        vec_x = alvo[0] - npc['x']
        vec_y = alvo[1] - npc['y']
        
        # Normaliza
        dist = math.sqrt(dist_min_sq)
        dir_x = vec_x / dist
        dir_y = vec_y / dist
        
        # Move
        npc['x'] += dir_x * VELOCIDADE_PERSEGUIDOR
        npc['y'] += dir_y * VELOCIDADE_PERSEGUIDOR
        
        # Atualiza o ângulo (opcional, mas bom para o visual)
        radianos = math.atan2(vec_y, vec_x)
        npc['angulo'] = -math.degrees(radianos) - 90
        npc['angulo'] %= 360
        

def game_loop():
    """
    O loop principal do servidor. Corre 60x por segundo numa thread separada.
    Calcula a física e ENVIA O ESTADO DE TODOS para TODOS.
    """
    global next_npc_id
    
    print("[GAME LOOP INICIADO] O servidor está agora a calcular e a enviar o estado.")
    
    TICK_INTERVAL = 1.0 / TICK_RATE 
    
    while True:
        loop_start_time = time.time()
        
        # Listas temporárias para novos objetos
        novos_projeteis = []
        
        # --- BLOCO DE ATUALIZAÇÃO (TUDO DENTRO DE UM LOCK) ---
        with game_state_lock:
            # --- Parte 1: Atualizar Jogadores (Mover e Disparar) ---
            posicoes_jogadores = [] # (Necessário para a IA dos NPCs)
            for state in player_states.values():
                posicoes_jogadores.append( (state['x'], state['y']) )
                
                # Esta função calcula movimento E retorna um projétil se disparar
                novo_proj = update_player_logic(state)
                if novo_proj:
                    novos_projeteis.append(novo_proj)
            
            # Adiciona os projéteis disparados à lista principal
            network_projectiles.extend(novos_projeteis)

            # --- Parte 2: Atualizar Projéteis (Mover) ---
            projeteis_para_remover = []
            for proj in network_projectiles:
                proj['x'] += -math.sin(proj['angulo_rad']) * proj['velocidade']
                proj['y'] += -math.cos(proj['angulo_rad']) * proj['velocidade']
                
                dist_sq = (proj['x'] - proj['pos_inicial_x'])**2 + (proj['y'] - proj['pos_inicial_y'])**2
                if dist_sq > s.MAX_DISTANCIA_TIRO**2:
                    projeteis_para_remover.append(proj)
                elif not s.MAP_RECT.collidepoint((proj['x'], proj['y'])):
                    projeteis_para_remover.append(proj)
            
            for proj in projeteis_para_remover:
                network_projectiles.remove(proj)
            
            # --- Parte 3: Spawns e Atualização de NPCs ---
            # (Só spawna se houver jogadores)
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
                        'hp': 3 # (Baseado no InimigoPerseguidor)
                    }
                    network_npcs.append(novo_npc)
                    next_npc_id += 1
                
                # Atualiza IA dos NPCs
                for npc in network_npcs:
                    update_npc_logic(npc, posicoes_jogadores)

            # --- Parte 4: Lógica de Colisão (Projéteis vs Jogadores/NPCs) ---
            # (Futuramente: Implementar colisões aqui)
            
            # --- Parte 5: Construir a string de estado global ---
            if not player_states: # Se todos saíram
                time.sleep(TICK_INTERVAL)
                continue
                
            lista_de_estados = []
            for state in player_states.values():
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

            # --- INÍCIO DA MODIFICAÇÃO (Adicionar NPCs ao Payload) ---
            lista_de_npcs = []
            for npc in network_npcs:
                # Formato: ID:TIPO:X:Y:ANGULO
                npc_str = (
                    f"{npc['id']}:{npc['tipo']}:{npc['x']:.1f}:{npc['y']:.1f}:{npc['angulo']:.0f}"
                )
                lista_de_npcs.append(npc_str)
            payload_npcs = ";".join(lista_de_npcs)
            
            # Formato: STATE|payload_players|PROJ|payload_proj|NPC|payload_npcs\n
            full_message = f"STATE|{payload_players}|PROJ|{payload_proj}|NPC|{payload_npcs}\n"
            full_message_bytes = full_message.encode('utf-8')
            # --- FIM DA MODIFICAÇÃO ---
            
            # --- Parte 6: Enviar a string global para TODOS os jogadores ---
            clientes_mortos = []
            for conn, state in player_states.items():
                try:
                    conn.sendall(full_message_bytes)
                except (socket.error, BrokenPipeError) as e:
                    print(f"[Game Loop] Erro ao enviar para {state['nome']}. Marcando para remoção.")
                    clientes_mortos.append(conn)

        # --- FIM DO BLOCO DE ATUALIZAÇÃO (LOCK LIBERTADO) ---
        
        # Limpa clientes mortos fora do loop principal
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

        # Controla o Tick Rate (60 FPS)
        time_elapsed = time.time() - loop_start_time
        sleep_time = TICK_INTERVAL - time_elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)


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
        margin = 100
        # (Chama a função de spawn com uma lista das posições atuais)
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
            'alvo_lock': None,
            'ultimo_tiro_tempo': 0, 
            'cooldown_tiro': COOLDOWN_TIRO, 
            'nivel_dano': 1 
        }
        with game_state_lock:
            player_states[conn] = player_state
        
        response_string = f"BEMVINDO|{nome_jogador}|{spawn_x}|{spawn_y}"
        
        print(f"[{addr}] Enviando dados de spawn para '{nome_jogador}': {response_string}")
        conn.sendall(response_string.encode('utf-8'))
        
        # --- ETAPA 3: Loop de Recebimento de Inputs ---
        while True:
            data = conn.recv(2048)
            if not data:
                break 
            
            inputs = data.decode('utf-8').splitlines()
            
            with game_state_lock: # Protege o 'player_state'
                for input_str in inputs:
                    if not input_str: continue 
                    
                    if input_str == "W_DOWN":
                        player_state['teclas']['w'] = True
                        player_state['alvo_mouse'] = None 
                    elif input_str == "W_UP":
                        player_state['teclas']['w'] = False
                    elif input_str == "A_DOWN":
                        player_state['teclas']['a'] = True
                        player_state['alvo_lock'] = None 
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
                        player_state['alvo_lock'] = None 
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
                        player_state['alvo_lock'] = None 
                        player_state['teclas']['w'] = False
                        player_state['teclas']['s'] = False
                    elif input_str.startswith("CLICK_TARGET|"):
                        parts = input_str.split('|')
                        player_state['alvo_lock'] = (int(parts[1]), int(parts[2])) 
                        player_state['alvo_mouse'] = None


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

    # Loop principal para aceitar novas conexões
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
            # Limpa as listas
            network_npcs.clear()
            network_projectiles.clear()
            player_states.clear()
            
            server_socket.close()
            break 
        except Exception as e:
            print(f"[ERRO NO LOOP PRINCIPAL] {e}")


# --- Inicia o Servidor ---
if __name__ == "__main__":
    if not hasattr(s, 'VELOCIDADE_ROTACAO_NAVE'):
        print("[AVISO] 'VELOCIDADE_ROTACAO_NAVE' não encontrada em settings.py. A usar valor padrão 5.")
        s.VELOCIDADE_ROTACAO_NAVE = 5
    
    iniciar_servidor()