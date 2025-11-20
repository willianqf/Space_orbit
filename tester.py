import socket
import threading
import time
import random
import sys

# --- CONFIGURAÇÕES DO SERVIDOR ---
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5555

# --- CONFIGURAÇÕES DE CARGA ---
# O objetivo é lotar tudo:
# 2 Salas PVE * 16 players = 32
# 4 Salas PVP * 4 players = 16
# Total = 48 conexões simultâneas
QTD_PVE = 31
QTD_PVP = 15

class SmartDummyClient(threading.Thread):
    def __init__(self, client_id, mode):
        super().__init__()
        self.client_id = client_id
        self.mode = mode
        self.sock = None
        self.running = True
        self.name = f"Bot_{mode}_{client_id}"
        self.my_hp = 100 # Começa assumindo que está vivo
        self.is_dead = False

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10.0) # Timeout para não travar
            self.sock.connect((SERVER_IP, SERVER_PORT))
            
            # 1. Handshake (SEM O \n ERRADO)
            msg = f"{self.name}|{self.mode}" 
            self.sock.sendall(msg.encode('utf-8'))
            
            # 2. Aguarda resposta
            response = self.sock.recv(2048).decode('utf-8')
            if "BEMVINDO" in response:
                # O servidor pode renomear o bot (ex: Bot_PVE_0_1), pegamos o nome real
                parts = response.split('|')
                if len(parts) >= 2:
                    self.name = parts[1]
                print(f"[{self.name}] Conectado em {self.mode}!")
                return True
            else:
                print(f"[{self.name}] Recusado: {response}")
                return False
        except Exception as e:
            print(f"[{self.name}] Falha conexão: {e}")
            return False

    def parse_state(self, data_str):
        """
        Lê o pacote STATE|... para descobrir se morreu.
        Formato: STATE|nome:x:y:ang:hp:max_hp...;nome2...|PROJ|...
        """
        try:
            if not data_str.startswith("STATE"):
                # Em PVP pode vir PVP_STATUS_UPDATE antes, ignoramos por enquanto
                if "STATE|" in data_str:
                    data_str = data_str.split("STATE|")[1]
                else:
                    return

            parts = data_str.split('|')
            if len(parts) < 2: return
            
            players_block = parts[1] # Bloco com dados dos jogadores
            player_list = players_block.split(';')
            
            for p_data in player_list:
                # Formato: nome:x:y:ang:hp:...
                p_parts = p_data.split(':')
                if len(p_parts) >= 5:
                    p_name = p_parts[0]
                    if p_name == self.name:
                        # Achei meu bot!
                        hp = float(p_parts[4])
                        self.my_hp = hp
                        if hp <= 0:
                            self.is_dead = True
                        else:
                            self.is_dead = False
                        break
        except:
            pass # Ignora erros de parse para não travar o teste

    def run(self):
        if not self.connect():
            return

        # Thread de Input (Cérebro do Bot)
        input_thread = threading.Thread(target=self.logic_loop)
        input_thread.daemon = True
        input_thread.start()

        # Loop de Rede (Escuta)
        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    self.running = False
                    break
                
                text_data = data.decode('utf-8', errors='ignore')
                
                # Processa o buffer para pegar mensagens completas
                buffer += text_data
                while '\n' in buffer:
                    msg, buffer = buffer.split('\n', 1)
                    self.parse_state(msg)

            except socket.timeout:
                pass # Apenas continua
            except Exception as e:
                self.running = False
                break
        
        if self.sock: self.sock.close()
        print(f"[{self.name}] Desconectado.")

    def logic_loop(self):
        """ Envia comandos ou pede Respawn """
        while self.running:
            try:
                if self.is_dead:
                    if self.mode == "PVE":
                        # Se for PVE e morreu, pede respawn imediato
                        # (Dá um tempinho de 1s para simular o clique)
                        time.sleep(1)
                        self.sock.sendall(b"RESPAWN_ME\n")
                        # Reseta flag localmente para não spammar
                        self.is_dead = False 
                    else:
                        # Se for PVP, espera a rodada reiniciar (o servidor controla)
                        time.sleep(1)
                else:
                    # Se está vivo, gera carga (movimento/tiro)
                    # 1. Movimento aleatório
                    move = random.choice(["W_DOWN", "S_DOWN", "A_DOWN", "D_DOWN"])
                    self.sock.sendall((move + "\n").encode('utf-8'))
                    
                    # 2. Tiro aleatório (gera colisão e novos objetos)
                    if random.random() < 0.3:
                        self.sock.sendall(b"SPACE_DOWN\n")
                        time.sleep(0.05)
                        self.sock.sendall(b"SPACE_UP\n")
                    
                    # 3. Simula movimento de mouse (cálculo trigonométrico no server)
                    tx = random.randint(0, 8000 if self.mode == "PVE" else 1500)
                    ty = random.randint(0, 8000 if self.mode == "PVE" else 1500)
                    self.sock.sendall(f"CLICK_MOVE|{tx}|{ty}\n".encode('utf-8'))

                    time.sleep(0.1) # 10 ações por segundo aprox.

            except:
                break

def main():
    print(f"--- INICIANDO TESTE DE ESTRESSE TOTAL ---")
    print(f"Alvos: {QTD_PVE} Bots PVE + {QTD_PVP} Bots PVP")
    
    clients = []

    # 1. Lota as salas PVE primeiro
    print(">>> Iniciando onda PVE...")
    for i in range(QTD_PVE):
        bot = SmartDummyClient(i, "PVE")
        clients.append(bot)
        bot.start()
        time.sleep(0.05) # Pequeno delay para não travar o handshake do server

    # 2. Lota as salas PVP
    print("\n>>> Iniciando onda PVP...")
    for i in range(QTD_PVP):
        bot = SmartDummyClient(i, "PVP")
        clients.append(bot)
        bot.start()
        time.sleep(0.05)

    print(f"\n--- TOTAL DE {len(clients)} BOTS RODANDO ---")
    print("Os bots PVE irão renascer automaticamente ao morrer.")
    print("Os bots PVP aguardarão o reinício da rodada pelo servidor.")
    print("Pressione CTRL+C para encerrar.")

    try:
        while True:
            time.sleep(2)
            alive = sum(1 for c in clients if c.running)
            # Mostra status em uma linha que se atualiza
            sys.stdout.write(f"\r[STATUS] Conexões Ativas: {alive} / {QTD_PVE + QTD_PVP}   ")
            sys.stdout.flush()
            if alive == 0: break
    except KeyboardInterrupt:
        print("\nEncerrando teste...")
        for c in clients: c.running = False

if __name__ == "__main__":
    main()