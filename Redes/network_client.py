# Redes/network_client.py
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
        self.local_player_state_to_send = {
            'w': False, 'a': False, 's': False, 'd': False, 'space': False,
            'alvo_mouse': None,
            'alvo_lock': None, 
            'click_target': None, 
            'click_move': None, 
            'buy_upgrade': None, 
            'toggle_regen': False,
            'respawn_me': False,
            'enter_spectator': False
        }
        
        # --- INÍCIO: MODIFICAÇÃO (Variável para Lobby) ---
        # Esta variável será atualizada pela thread de escuta
        self.pvp_lobby_status = {"num_players": 0, "countdown_sec": 0}
        # --- FIM: MODIFICAÇÃO ---


    # --- INÍCIO: MODIFICAÇÃO (Assinatura e Lógica de Retorno) ---
    def connect(self, ip, porta, nome, game_mode="PVE"):
        """ 
        Tenta conectar ao servidor, enviar o nome E O MODO DE JOGO.
        Retorna: (Sucesso, ModoDeJogo, NomeServidor, PosSpawn)
        Ex: (True, "PVE", "Jogador_1", (100, 100))
        Ex: (True, "PVP", "JogadorPVP_2", (750, 750))
        Ex: (False, "NONE", "", None)
        """
    # --- FIM: MODIFICAÇÃO ---
        if self.connection_status == "CONNECTED":
            print("[Network] Já conectado.")
            # Retorna "PVE" como padrão, pois não sabemos o modo
            return True, "PVE", self.my_network_name, (0, 0)
            
        self.connection_status = "CONNECTING"
        self.connection_error_message = ""
        nome_final = nome.strip() if nome.strip() else "Jogador"
        
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5.0)
            
            print(f"Tentando conectar a {ip}:{porta}...")
            self.client_socket.connect((ip, porta))
            
            print(f"Conexão estabelecida. Enviando nome '{nome_final}' e modo '{game_mode}'...")
            handshake_message = f"{nome_final}|{game_mode}"
            self.client_socket.send(handshake_message.encode('utf-8'))
            
            print("Aguardando resposta de spawn do servidor...")
            data = self.client_socket.recv(2048)
            resposta_servidor = data.decode('utf-8').strip() # .strip() para remover \n
            
            # --- INÍCIO: MODIFICAÇÃO (Lógica de Resposta Múltipla) ---
            modo_retornado = "NONE"
            parts = resposta_servidor.split('|') # Divide a resposta
            
            if resposta_servidor.startswith("BEMVINDO|"):
                modo_retornado = "PVE"
            elif resposta_servidor.startswith("BEMVINDO_PVP|"):
                modo_retornado = "PVP"
            elif resposta_servidor.startswith("REJEITADO|"):
                self.connection_error_message = parts[1] if len(parts) > 1 else "Conexão rejeitada"
                raise socket.error(self.connection_error_message)
            else:
                 raise socket.error(f"Resposta inesperada do servidor: {resposta_servidor}")

            if len(parts) == 4:
                self.my_network_name = parts[1]
                spawn_x = int(parts[2])
                spawn_y = int(parts[3])
                
                print(f"Servidor aceitou! Modo: '{modo_retornado}'. Nome: '{self.my_network_name}'. Spawn: ({spawn_x}, {spawn_y}).")
                
                self.client_socket.settimeout(None)
                
                self.listener_thread_running = True
                self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
                self.listener_thread.start()
                
                self.connection_status = "CONNECTED"
                
                # Retorna os 4 valores
                return True, modo_retornado, self.my_network_name, (spawn_x, spawn_y)
            else:
                raise socket.error(f"Resposta 'BEMVINDO' mal formatada: {resposta_servidor}")
            # --- FIM: MODIFICAÇÃO ---

        except (socket.timeout, socket.error) as e:
            print(f"[ERRO DE REDE] Falha ao conectar: {e}")
            self.connection_error_message = str(e)
            if self.client_socket:
                self.client_socket.close()
            self.client_socket = None
            self.connection_status = "ERROR"
            # Retorna 4 valores na falha
            return False, "NONE", "", (0, 0)

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
                self.close() 
        
    def get_state(self):
        """ Retorna uma cópia segura do estado de rede atual. """
        with self.network_state_lock:
            return {
                "players": self.online_players_states.copy(),
                "projectiles": list(self.online_projectiles),
                "npcs": self.online_npcs.copy()
            }
    
    # --- INÍCIO: MODIFICAÇÃO (Função para Lobby) ---
    def get_lobby_status(self):
        """ Retorna uma cópia segura do estado do lobby PVP. """
        with self.network_state_lock:
            return self.pvp_lobby_status.copy()
    # --- FIM: MODIFICAÇÃO ---
            
    def get_my_name(self):
        return self.my_network_name
        
    def is_connected(self):
        return self.client_socket is not None and self.listener_thread_running

    def _listener_loop(self):
        """
        Corre na thread separada. Escuta por dados do servidor
        e atualiza os dicionários de estado.
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
                    
                    # --- INÍCIO: MODIFICAÇÃO (Recebe mensagens do Lobby PVP) ---
                    elif message.startswith("PVP_LOBBY_UPDATE|"):
                        try:
                            parts = message.split('|')
                            num_players = int(parts[1])
                            countdown_sec = int(parts[2])
                            
                            with self.network_state_lock:
                                self.pvp_lobby_status["num_players"] = num_players
                                self.pvp_lobby_status["countdown_sec"] = countdown_sec
                        except (IndexError, ValueError):
                            print(f"[REDE] Recebeu PVP_LOBBY_UPDATE mal formatado: {message}")
                    # --- FIM: MODIFICAÇÃO ---

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

    def _parse_state_message(self, message):
        """ Processa uma única mensagem 'STATE|...' """
        parts = message.split('|')
        
        is_pve_state = (len(parts) >= 6 and parts[0] == 'STATE' and parts[2] == 'PROJ' and parts[4] == 'NPC')
        is_pvp_state = (len(parts) >= 4 and parts[0] == 'STATE' and parts[2] == 'PROJ')

        if not is_pve_state and not is_pvp_state:
             print(f"[Thread de Rede] Recebeu mensagem 'STATE' mal formatada.")
             return
        
        payload_players = parts[1]
        payload_proj = parts[3]
        
        payload_npcs = ""
        if is_pve_state and len(parts) >= 6:
            payload_npcs = parts[5]
        
        # --- Processar Jogadores ---
        new_player_states = {}
        player_data_list = payload_players.split(';')
        
        for player_data in player_data_list:
            if not player_data: continue
            
            parts_player = player_data.split(':')
            # --- INÍCIO: MODIFICAÇÃO (Lê 18 campos) ---
            if len(parts_player) == 18: # Checa o novo formato
            # --- FIM: MODIFICAÇÃO ---
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
                        # --- INÍCIO: MODIFICAÇÃO (Lê o 18º campo) ---
                        'is_pre_match': bool(int(parts_player[17])),
                        # --- FIM: MODIFICAÇÃO ---
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
                        'hp': float(parts_npc[5]), 
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