# Redes/network_client.py
import socket
import threading
import time
import pygame
import settings as s

class NetworkClient:
    def __init__(self):
        self.client_socket = None
        self.listener_thread = None
        self.listener_thread_running = False
        self.network_buffer = ""
        self.my_network_name = ""
        
        # Estruturas de dados protegidas por Lock
        self.online_players_states = {}
        self.online_projectiles = []
        self.online_npcs = {}
        self.pvp_lobby_status = {
            "num_players": 0, 
            "countdown_sec": 0, 
            "match_countdown_sec": 0, 
            "lobby_state": "WAITING", 
            "winner": ""
        }
        self.network_state_lock = threading.Lock()
        
        # Estados de conexão
        self.connection_status = "DISCONNECTED" 
        self.connection_error_message = ""

    def connect(self, ip, porta, nome, game_mode="PVE"):
        # Segurança: Se já achar que está conectado, fecha antes de tentar de novo
        if self.connection_status == "CONNECTED": 
            print("[REDE] Conexão anterior detectada. Fechando antes de reconectar...")
            self.close()
            time.sleep(0.2) # Pequena pausa para garantir que a thread anterior morra

        self.connection_status = "CONNECTING"
        self.connection_error_message = ""
        nome_final = nome.strip() if nome.strip() else "Jogador"
        
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5.0) # Timeout de 5s para não travar o jogo
            
            print(f"[REDE] Tentando conectar a {ip}:{porta}...")
            self.client_socket.connect((ip, porta))
            
            print(f"[REDE] Conexão TCP estabelecida. Enviando handshake...")
            handshake_message = f"{nome_final}|{game_mode}"
            self.client_socket.sendall(handshake_message.encode('utf-8'))
            
            print("[REDE] Aguardando resposta de spawn do servidor...")
            data = self.client_socket.recv(2048)
            if not data:
                raise socket.error("Servidor desconectou durante o handshake.")
                
            resposta_servidor = data.decode('utf-8').strip()
            parts = resposta_servidor.split('|')
            
            modo_retornado = "NONE"
            if resposta_servidor.startswith("BEMVINDO|"): 
                modo_retornado = "PVE"
            elif resposta_servidor.startswith("BEMVINDO_PVP|"): 
                modo_retornado = "PVP"
            elif resposta_servidor.startswith("REJEITADO|"): 
                self.connection_error_message = parts[1] if len(parts) > 1 else "Conexão rejeitada"
                raise socket.error(self.connection_error_message)
            else: 
                raise socket.error(f"Resposta inesperada do servidor: {resposta_servidor}")
            
            if len(parts) >= 4:
                self.my_network_name = parts[1]
                spawn_x = int(parts[2])
                spawn_y = int(parts[3])
                
                print(f"[REDE] Sucesso! Modo: '{modo_retornado}'. Nome: '{self.my_network_name}'. Spawn: ({spawn_x}, {spawn_y}).")
                
                # Configura para modo não-bloqueante ou timeout infinito para a thread de escuta
                self.client_socket.settimeout(None)
                
                self.listener_thread_running = True
                self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
                self.listener_thread.start()
                
                self.connection_status = "CONNECTED"
                return True, modo_retornado, self.my_network_name, (spawn_x, spawn_y)
            else: 
                raise socket.error(f"Resposta 'BEMVINDO' mal formatada: {resposta_servidor}")
                
        except (socket.timeout, socket.error, OSError) as e:
            print(f"[ERRO DE REDE] Falha ao conectar: {e}")
            self.connection_error_message = str(e)
            self.close() # Garante limpeza total em caso de falha
            self.connection_status = "ERROR"
            return False, "NONE", "", (0, 0)

    def close(self):
        """ Encerra a conexão de forma segura e limpa os estados internos. """
        self.listener_thread_running = False
        
        if self.client_socket:
            print("Fechando conexão de rede...")
            try: 
                self.client_socket.shutdown(socket.SHUT_RDWR)
            except (socket.error, OSError): 
                pass # Socket pode já estar fechado, ignora erro
            try:
                self.client_socket.close()
            except (socket.error, OSError):
                pass
                
        self.client_socket = None
        self.listener_thread = None
        self.my_network_name = ""
        self.connection_status = "DISCONNECTED"
        
        # Limpa o cache local para evitar "fantasmas" na próxima conexão
        with self.network_state_lock:
            self.online_players_states.clear()
            self.online_projectiles.clear()
            self.online_npcs.clear()
            self.pvp_lobby_status = {
                "num_players": 0, 
                "countdown_sec": 0, 
                "match_countdown_sec": 0, 
                "lobby_state": "WAITING", 
                "winner": ""
            }

    def send(self, message):
        if self.client_socket and self.listener_thread_running:
            try: 
                self.client_socket.sendall((message + '\n').encode('utf-8'))
            except (socket.error, BrokenPipeError, OSError) as e: 
                print(f"[ERRO DE REDE] Falha ao enviar '{message}'. Conexão perdida: {e}")
                self.close() 

    def get_state(self):
        with self.network_state_lock: 
            return {
                "players": self.online_players_states.copy(), 
                "projectiles": list(self.online_projectiles), 
                "npcs": self.online_npcs.copy()
            }

    def get_lobby_status(self):
        with self.network_state_lock: 
            return self.pvp_lobby_status.copy()

    def get_my_name(self): 
        return self.my_network_name

    def is_connected(self): 
        return self.client_socket is not None and self.listener_thread_running and self.connection_status == "CONNECTED"

    def _listener_loop(self):
        print("[Thread de Rede] Iniciada.")
        self.network_buffer = ""
        
        while self.listener_thread_running:
            try:
                if not self.client_socket: break
                
                data = self.client_socket.recv(4096)
                if not data:
                    print("[Thread de Rede] Servidor encerrou a conexão (recv vazio).")
                    break
                
                self.network_buffer += data.decode('utf-8', errors='ignore')
                
                while '\n' in self.network_buffer:
                    message, self.network_buffer = self.network_buffer.split('\n', 1)
                    if not message: continue
                    
                    if message.startswith("STATE|"): 
                        self._parse_state_message(message)
                    elif message.startswith("PVP_STATUS_UPDATE|"):
                        try:
                            parts = message.split('|')
                            if len(parts) >= 6:
                                with self.network_state_lock: 
                                    self.pvp_lobby_status["num_players"] = int(parts[1])
                                    self.pvp_lobby_status["countdown_sec"] = int(parts[2])
                                    self.pvp_lobby_status["match_countdown_sec"] = int(parts[3])
                                    self.pvp_lobby_status["lobby_state"] = parts[4]
                                    self.pvp_lobby_status["winner"] = parts[5]
                        except (IndexError, ValueError) as e: 
                            print(f"[REDE] Erro ao parsear PVP_STATUS: {e}")
                            
            except (socket.error, ConnectionResetError, BrokenPipeError, OSError) as e:
                if self.listener_thread_running: 
                    print(f"[Thread de Rede] Erro de socket: {e}")
                break
            except Exception as e:
                if self.listener_thread_running: 
                    print(f"[Thread de Rede] Erro inesperado: {e}")
                break
        
        # Se saiu do loop, garante que a limpeza seja feita
        print("[Thread de Rede] Encerrando...")
        self.close()

    def _parse_state_message(self, message):
        parts = message.split('|')
        
        # Detecção do formato (PVE tem NPC, PVP às vezes não)
        is_pve_state = (len(parts) >= 6 and parts[0] == 'STATE' and parts[2] == 'PROJ' and parts[4] == 'NPC')
        is_pvp_state = (len(parts) >= 4 and parts[0] == 'STATE' and parts[2] == 'PROJ')
        
        if not is_pve_state and not is_pvp_state: 
            return # Mensagem mal formatada ou incompleta
            
        payload_players = parts[1]
        payload_proj = parts[3]
        payload_npcs = parts[5] if is_pve_state and len(parts) >= 6 else ""
        
        new_player_states = {}
        player_data_list = payload_players.split(';')
        for player_data in player_data_list:
            if not player_data: continue
            parts_player = player_data.split(':')
            if len(parts_player) >= 18: 
                try:
                    nome = parts_player[0]
                    new_player_states[nome] = {
                        'x': float(parts_player[1]), 'y': float(parts_player[2]), 'angulo': float(parts_player[3]), 
                        'hp': float(parts_player[4]), 'max_hp': int(float(parts_player[5])), 'pontos': int(parts_player[6]),
                        'esta_regenerando': bool(int(parts_player[7])), 'pontos_upgrade_disponiveis': int(parts_player[8]), 
                        'total_upgrades_feitos': int(parts_player[9]), 'nivel_motor': int(parts_player[10]),
                        'nivel_dano': int(parts_player[11]), 'nivel_max_vida': int(parts_player[12]), 
                        'nivel_escudo': int(parts_player[13]), 'nivel_aux': int(parts_player[14]),
                        'is_lento': bool(int(parts_player[15])), 'is_congelado': bool(int(parts_player[16])), 
                        'is_pre_match': bool(int(parts_player[17]))
                    }
                    if len(parts_player) >= 19:
                        new_player_states[nome]['last_hit_angle'] = float(parts_player[18])
                except (ValueError, IndexError): pass
        
        new_projectiles_list = []
        proj_data_list = payload_proj.split(';')
        for proj_data in proj_data_list:
            if not proj_data: continue
            parts_proj = proj_data.split(':')
            if len(parts_proj) == 5:
                try: 
                    new_projectiles_list.append({
                        'id': parts_proj[0], 'x': float(parts_proj[1]), 'y': float(parts_proj[2]), 
                        'tipo': parts_proj[3], 'tipo_proj': parts_proj[4]
                    })
                except (ValueError, IndexError): pass
        
        new_npc_states = {}
        npc_data_list = payload_npcs.split(';')
        for npc_data in npc_data_list:
            if not npc_data: continue
            parts_npc = npc_data.split(':')
            if len(parts_npc) == 8:
                try: 
                    npc_id = parts_npc[0]
                    new_npc_states[npc_id] = {
                        'tipo': parts_npc[1], 'x': float(parts_npc[2]), 'y': float(parts_npc[3]), 
                        'angulo': float(parts_npc[4]), 'hp': float(parts_npc[5]), 
                        'max_hp': int(float(parts_npc[6])), 'tamanho': int(parts_npc[7])
                    }
                except (ValueError, IndexError): pass
        
        with self.network_state_lock: 
            self.online_players_states = new_player_states
            self.online_projectiles = new_projectiles_list
            self.online_npcs = new_npc_states