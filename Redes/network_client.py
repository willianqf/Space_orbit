# network_client.py
import socket
import threading
import pygame # Usado para Vector2
import settings as s

class NetworkClient:
    def __init__(self):
        self.client_socket = None
        self.listener_thread = None
        self.listener_thread_running = False
        self.network_buffer = ""
        self.my_network_name = ""

        # Dicionários de estado que serão atualizados pela thread
        self.online_players_states = {}
        self.online_projectiles = []
        self.online_npcs = {}
        self.network_state_lock = threading.Lock()
        
        self.connection_status = "DISCONNECTED" # DISCONNECTED, CONNECTING, CONNECTED, ERROR
        self.connection_error_message = ""
        
        # --- (Variáveis de estado do jogador local que o servidor precisa saber) ---
        # Estas são as flags que o 'main.py' irá definir
        self.local_player_state_to_send = {
            'w': False, 'a': False, 's': False, 'd': False, 'space': False,
            'alvo_mouse': None,
            'alvo_lock': None, # O alvo_lock local no main.py (o sprite) é diferente do ID enviado
            'click_target': None, # (x, y) do clique
            'click_move': None, # (x, y) do clique
            'buy_upgrade': None, # "motor", "dano", etc.
            'toggle_regen': False,
            'respawn_me': False,
            'enter_spectator': False
        }
        # Thread para enviar inputs em background (opcional, mas melhora)
        # self.sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
        # self.sender_thread.start()


    def connect(self, ip, porta, nome):
        """ Tenta conectar ao servidor, enviar o nome e iniciar a thread de escuta. """
        if self.connection_status == "CONNECTED":
            print("[Network] Já conectado.")
            return True
            
        self.connection_status = "CONNECTING"
        self.connection_error_message = ""
        nome_final = nome.strip() if nome.strip() else "Jogador"
        
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5.0)
            
            print(f"Tentando conectar a {ip}:{porta}...")
            self.client_socket.connect((ip, porta))
            
            print("Conexão estabelecida. Enviando nome...")
            self.client_socket.send(nome_final.encode('utf-8'))
            
            print("Aguardando resposta de spawn do servidor...")
            data = self.client_socket.recv(2048)
            resposta_servidor = data.decode('utf-8')
            
            if resposta_servidor.startswith("BEMVINDO|"):
                parts = resposta_servidor.split('|')
                if len(parts) == 4:
                    self.my_network_name = parts[1]
                    spawn_x = int(parts[2])
                    spawn_y = int(parts[3])
                    
                    print(f"Servidor aceitou! Nome: '{self.my_network_name}'. Spawn: ({spawn_x}, {spawn_y}).")
                    
                    self.client_socket.settimeout(None)
                    
                    self.listener_thread_running = True
                    self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
                    self.listener_thread.start()
                    
                    self.connection_status = "CONNECTED"
                    
                    # Retorna os dados de spawn para o main.py
                    return True, self.my_network_name, (spawn_x, spawn_y)
                else:
                    raise socket.error(f"Resposta 'BEMVINDO' mal formatada: {resposta_servidor}")
            else:
                 raise socket.error(f"Resposta inesperada do servidor: {resposta_servidor}")

        except (socket.timeout, socket.error) as e:
            print(f"[ERRO DE REDE] Falha ao conectar: {e}")
            self.connection_error_message = str(e)
            if self.client_socket:
                self.client_socket.close()
            self.client_socket = None
            self.connection_status = "ERROR"
            return False, "", (0, 0)

    def close(self):
        """ Fecha o socket e para as threads. """
        self.listener_thread_running = False
        
        if self.client_socket:
            print("Fechando conexão de rede...")
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
            except (socket.error, OSError):
                pass 
        self.client_socket = None
        
        if self.listener_thread:
            # Não podemos dar .join() na própria thread se ela estiver se fechando
            # Apenas definimos como None e deixamos o Python limpar
            self.listener_thread = None
            
        self.my_network_name = ""
        self.connection_status = "DISCONNECTED"
        with self.network_state_lock:
            self.online_players_states.clear()
            self.online_projectiles.clear()
            self.online_npcs.clear()

    def send(self, message):
        """ Envia uma única mensagem (com \n) para o servidor. """
        if self.client_socket and self.listener_thread_running:
            try:
                self.client_socket.sendall((message + '\n').encode('utf-8'))
            except (socket.error, BrokenPipeError) as e:
                print(f"[ERRO DE REDE] Falha ao enviar input '{message}'. Conexão pode estar fechada. Erro: {e}")
                self.close() # Força a desconexão
        
    def get_state(self):
        """ Retorna uma cópia segura do estado de rede atual. """
        with self.network_state_lock:
            return {
                "players": self.online_players_states.copy(),
                "projectiles": list(self.online_projectiles),
                "npcs": self.online_npcs.copy()
            }
            
    def get_my_name(self):
        return self.my_network_name
        
    def is_connected(self):
        return self.client_socket is not None and self.listener_thread_running

    def _listener_loop(self):
        """
        Corre na thread separada. Escuta por dados do servidor
        e atualiza os dicionários de estado.
        (Função 'network_listener_thread' original, agora como método)
        """
        print("[Thread de Rede] Iniciada.")
        self.network_buffer = ""
        
        while self.listener_thread_running:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    if self.listener_thread_running:
                        print("[Thread de Rede] Conexão perdida (recv vazio).")
                    break
                    
                self.network_buffer += data.decode('utf-8')
                
                while '\n' in self.network_buffer:
                    message, self.network_buffer = self.network_buffer.split('\n', 1)
                    
                    if message.startswith("STATE|"):
                        self._parse_state_message(message)
                
            except (socket.error, ConnectionResetError, BrokenPipeError) as e:
                if self.listener_thread_running:
                    print(f"[Thread de Rede] Erro de socket: {e}")
                break
            except Exception as e:
                if self.listener_thread_running:
                    print(f"[Thread de Rede] Erro inesperado na thread: {e}")
                break

        print("[Thread de Rede] Encerrada.")
        self.listener_thread_running = False
        # (Não chamamos close() aqui, pois o 'main.py' pode querer
        #  mostrar uma tela de "desconectado" antes de fechar tudo)

    def _parse_state_message(self, message):
        """ Processa uma única mensagem 'STATE|...' """
        parts = message.split('|')
        if len(parts) < 6 or parts[0] != 'STATE' or parts[2] != 'PROJ' or parts[4] != 'NPC':
            print(f"[Thread de Rede] Recebeu mensagem 'STATE' mal formatada.")
            return
        
        payload_players = parts[1]
        payload_proj = parts[3]
        payload_npcs = parts[5]
        
        # --- Processar Jogadores ---
        new_player_states = {}
        player_data_list = payload_players.split(';')
        
        for player_data in player_data_list:
            if not player_data: continue
            
            parts_player = player_data.split(':')
            if len(parts_player) == 17: # Checa o formato esperado
                try:
                    nome = parts_player[0]
                    new_player_states[nome] = {
                        'x': float(parts_player[1]),
                        'y': float(parts_player[2]),
                        'angulo': float(parts_player[3]),
                        'hp': float(parts_player[4]),
                        'max_hp': int(float(parts_player[5])),
                        'pontos': int(parts_player[6]),
                        'esta_regenerando': bool(int(parts_player[7])),
                        'pontos_upgrade_disponiveis': int(parts_player[8]),
                        'total_upgrades_feitos': int(parts_player[9]),
                        'nivel_motor': int(parts_player[10]),
                        'nivel_dano': int(parts_player[11]),
                        'nivel_max_vida': int(parts_player[12]),
                        'nivel_escudo': int(parts_player[13]),
                        'nivel_aux': int(parts_player[14]),
                        'is_lento': bool(int(parts_player[15])),
                        'is_congelado': bool(int(parts_player[16])),
                    }
                except (ValueError, IndexError) as e:
                    print(f"Erro ao processar dados do jogador: {parts_player} | Erro: {e}")
                    pass
        
        # --- Processar Projéteis ---
        new_projectiles_list = []
        proj_data_list = payload_proj.split(';')
        
        for proj_data in proj_data_list:
            if not proj_data: continue
            
            parts_proj = proj_data.split(':')
            if len(parts_proj) == 5:
                try:
                    new_projectiles_list.append(
                        {'id': parts_proj[0],
                         'x': float(parts_proj[1]),
                         'y': float(parts_proj[2]),
                         'tipo': parts_proj[3],
                         'tipo_proj': parts_proj[4]}
                    )
                except (ValueError, IndexError):
                    pass
        
        # --- Processar NPCs ---
        new_npc_states = {}
        npc_data_list = payload_npcs.split(';')
        
        for npc_data in npc_data_list:
            if not npc_data: continue
            
            parts_npc = npc_data.split(':')
            if len(parts_npc) == 8:
                try:
                    npc_id = parts_npc[0]
                    new_npc_states[npc_id] = {
                        'tipo': parts_npc[1],
                        'x': float(parts_npc[2]),
                        'y': float(parts_npc[3]),
                        'angulo': float(parts_npc[4]),
                        'hp': float(parts_npc[5]), # Corrigido para float
                        'max_hp': int(float(parts_npc[6])),
                        'tamanho': int(parts_npc[7])
                    }
                except (ValueError, IndexError) as e:
                    print(f"Erro ao processar dados do NPC: {parts_npc} | Erro: {e}")
                    pass

        # --- Atualizar Estado Global (com lock) ---
        with self.network_state_lock:
            self.online_players_states = new_player_states
            self.online_projectiles = new_projectiles_list
            self.online_npcs = new_npc_states