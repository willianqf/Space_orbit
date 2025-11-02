# server.py
import socket
import threading
import random
import settings as s # Para saber o tamanho do mapa
import math 
import time 

# 1. Configurações do Servidor
HOST = '127.0.0.1'  # IP para escutar
PORT = 5555         # Porta para escutar
MAX_JOGADORES = 16
TICK_RATE = 60 # 60 atualizações por segundo

# --- INÍCIO DA MODIFICAÇÃO (Estado Global do Jogo) ---
# Dicionário global para guardar o estado de todos os jogadores
player_states = {}
player_states_lock = threading.Lock() 

# Lista global para guardar todos os projéteis ativos
network_projectiles = []
projectiles_lock = threading.Lock()
# --- FIM DA MODIFICAÇÃO ---

# --- Constantes de Jogo (copiadas de settings.py e ships.py) ---
# (Idealmente, estas estariam num ficheiro de settings partilhado)
COOLDOWN_TIRO = 250 # ms
VELOCIDADE_PROJETIL = 10
OFFSET_PONTA_TIRO = 25 # (altura 30 / 2 + 10)
VELOCIDADE_BASE_NAVE = 4 #
# (Assume nível motor 1 por agora)
VELOCIDADE_MOVIMENTO_NAVE = VELOCIDADE_BASE_NAVE + 1 


def update_player_logic(player_state):
    """
    Calcula a nova posição, ângulo E processa o tiro de UM jogador,
    baseado no seu estado de input (teclas).
    """
    
    # --- 1. Lógica de Rotação (copiado de ships.py: rotacionar) ---
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

    # --- 2. Lógica de Movimento (copiado de ships.py: mover) ---
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

    # --- INÍCIO DA MODIFICAÇÃO (Lógica de Tiro) ---
    if player_state['teclas']['space'] or player_state['alvo_lock']:
        agora_ms = int(time.time() * 1000) # Tempo atual em milissegundos
        
        if agora_ms - player_state['ultimo_tiro_tempo'] > player_state['cooldown_tiro']:
            player_state['ultimo_tiro_tempo'] = agora_ms
            
            # Cria um projétil (lógica de ships.py: criar_projetil)
            radianos = math.radians(player_state['angulo'])
            pos_x = player_state['x'] + (-math.sin(radianos) * OFFSET_PONTA_TIRO)
            pos_y = player_state['y'] + (-math.cos(radianos) * OFFSET_PONTA_TIRO)
            
            novo_projetil = {
                'id': f"{player_state['nome']}_{agora_ms}", # ID único
                'owner_nome': player_state['nome'],
                'x': pos_x,
                'y': pos_y,
                'pos_inicial_x': pos_x,
                'pos_inicial_y': pos_y,
                'angulo_rad': radianos,
                'velocidade': VELOCIDADE_PROJETIL,
                'dano': player_state['nivel_dano'],
                'tipo': 'player' # (Para diferenciar de projéteis de NPCs no futuro)
            }
            
            # Adiciona à lista global de forma segura
            with projectiles_lock:
                network_projectiles.append(novo_projetil)
    # --- FIM DA MODIFICAÇÃO ---


def game_loop():
    """
    O loop principal do servidor. Corre 60x por segundo numa thread separada.
    Calcula a física e ENVIA O ESTADO DE TODOS para TODOS.
    """
    print("[GAME LOOP INICIADO] O servidor está agora a calcular e a enviar o estado.")
    
    TICK_INTERVAL = 1.0 / TICK_RATE 
    
    while True:
        loop_start_time = time.time()
        
        # --- Parte 1: Calcular todas as novas posições de jogadores ---
        with player_states_lock:
            for state in player_states.values():
                update_player_logic(state) # (Isto agora também trata do disparo)
        
        # --- INÍCIO DA MODIFICAÇÃO (Parte 2: Atualizar Projéteis) ---
        projeteis_para_remover = []
        with projectiles_lock:
            for proj in network_projectiles:
                # Move o projétil (lógica de projectiles.py: update)
                proj['x'] += -math.sin(proj['angulo_rad']) * proj['velocidade']
                proj['y'] += -math.cos(proj['angulo_rad']) * proj['velocidade']
                
                # Verifica distância
                dist_sq = (proj['x'] - proj['pos_inicial_x'])**2 + (proj['y'] - proj['pos_inicial_y'])**2
                if dist_sq > s.MAX_DISTANCIA_TIRO**2:
                    projeteis_para_remover.append(proj)
                    continue
                    
                # Verifica limites do mapa
                if not s.MAP_RECT.collidepoint((proj['x'], proj['y'])):
                    projeteis_para_remover.append(proj)
            
            # Remove os projéteis mortos
            for proj in projeteis_para_remover:
                network_projectiles.remove(proj)
        # --- FIM DA MODIFICAÇÃO ---

        # (Se não houver jogadores, não faz nada)
        if not player_states:
            time.sleep(TICK_INTERVAL)
            continue
            
        # --- Parte 3: Construir a string de estado global ---
        lista_de_estados = []
        with player_states_lock:
            for state in player_states.values():
                estado_str = (
                    f"{state['nome']}:{state['x']:.1f}:{state['y']:.1f}:{state['angulo']:.0f}"
                )
                lista_de_estados.append(estado_str)
        
        payload_players = ";".join(lista_de_estados)

        # --- INÍCIO DA MODIFICAÇÃO (Construir Payload de Projéteis) ---
        lista_de_projeteis = []
        with projectiles_lock:
            for proj in network_projectiles:
                # Formato: X:Y:TIPO
                # (O tipo 'player' dirá ao cliente para usar a cor vermelha)
                proj_str = f"{proj['x']:.1f}:{proj['y']:.1f}:{proj['tipo']}"
                lista_de_projeteis.append(proj_str)
        
        payload_proj = ";".join(lista_de_projeteis)
        
        # Formato: STATE|payload_players|PROJ|payload_proj\n
        full_message = f"STATE|{payload_players}|PROJ|{payload_proj}\n"
        full_message_bytes = full_message.encode('utf-8')
        # --- FIM DA MODIFICAÇÃO ---

        # --- Parte 4: Enviar a string global para TODOS os jogadores ---
        clientes_mortos = []
        with player_states_lock:
            for conn, state in player_states.items():
                try:
                    conn.sendall(full_message_bytes)
                except (socket.error, BrokenPipeError) as e:
                    print(f"[Game Loop] Erro ao enviar para {state['nome']}. Marcando para remoção.")
                    clientes_mortos.append(conn)

        if clientes_mortos:
            with player_states_lock:
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
        
        with player_states_lock:
            for state in player_states.values():
                if state['nome'] == nome_jogador:
                    nome_jogador = f"{nome_jogador}_{random.randint(1, 99)}"
                    break
        
        print(f"[{addr}] Jogador '{nome_jogador}' juntou-se.")

        # --- ETAPA 2: Gerar Posição e Criar Estado ---
        margin = 100
        spawn_x = random.randint(margin, s.MAP_WIDTH - margin)
        spawn_y = random.randint(margin, s.MAP_HEIGHT - margin)
        
        # --- INÍCIO DA MODIFICAÇÃO (Adicionar estado de tiro) ---
        player_state = {
            'conn': conn, 
            'nome': nome_jogador,
            'x': float(spawn_x), 
            'y': float(spawn_y), 
            'angulo': 0.0,
            'teclas': { 'w': False, 'a': False, 's': False, 'd': False, 'space': False },
            'alvo_mouse': None, 
            'alvo_lock': None,
            'ultimo_tiro_tempo': 0, # Tempo do último tiro em ms
            'cooldown_tiro': COOLDOWN_TIRO, # Cooldown em ms
            'nivel_dano': 1 # (Futuramente, isto pode ser aumentado)
        }
        # --- FIM DA MODIFICAÇÃO ---
        
        with player_states_lock:
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
            
            with player_states_lock:
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
    
    with player_states_lock:
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
            
            with player_states_lock:
                print(f"[CONEXÕES ATIVAS] {len(player_states)}")
        
        except KeyboardInterrupt:
            print("\n[SERVIDOR DESLIGANDO]... Fechando conexões.")
            with player_states_lock:
                for conn in player_states:
                    conn.close()
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