# server_bot_ai.py
import random
import math
import pygame # Para Vector2
from settings import (
    PONTOS_LIMIARES_PARA_UPGRADE, MAX_TOTAL_UPGRADES, MAX_NIVEL_MOTOR,
    MAX_NIVEL_ESCUDO, MAX_NIVEL_DANO
)

# --- CONSTANTES DA IA DO BOT (Movidas de server.py) ---
BOT_DISTANCIA_SCAN_GERAL_SQ = 800**2
BOT_DISTANCIA_SCAN_INIMIGO_SQ = 600**2
BOT_DISTANCIA_ORBITA_MAX_SQ = 300**2
BOT_DISTANCIA_ORBITA_MIN_SQ = 200**2
BOT_DISTANCIA_TIRO_IA_SQ = 500**2
BOT_DIST_BORDA_SEGURA = 400
BOT_HP_FUGIR_PERC = 0.20 # 20%
BOT_HP_REGENERAR_PERC = 0.50 # 50%
BOT_WANDER_TURN_CHANCE = 0.01 # 1% de chance por tick de virar
BOT_WANDER_TURN_DURATION_TICKS = 90 # Duração da virada
COOLDOWN_TIRO = 250 # ms

class ServerBotManager:
    def __init__(self, settings, state_globals, logic_callbacks):
        """
        Inicializa o gerenciador de IA dos bots.
        """
        self.s = settings
        
        # Referências de estado global
        self.player_states = state_globals['player_states']
        self.network_npcs = state_globals['network_npcs']
        
        # Funções "emprestadas" do server.py para evitar import circular
        self.spawn_calculator = logic_callbacks['spawn_calculator']
        self.upgrade_purchaser = logic_callbacks['upgrade_purchaser']

    
    def manage_bot_population(self, max_bots):
        """
        Verifica bots mortos e spawna novos se necessário.
        Chamado a cada tick do game_loop.
        """
        bots_atuais = []
        bots_para_remover = []

        # Usamos list(self.player_states.items()) para evitar erro de iteração
        for player_key, p_state in list(self.player_states.items()):
            if p_state.get('is_bot', False):
                if p_state.get('hp', 0) <= 0: # Se o bot morreu
                    bots_para_remover.append(player_key)
                else:
                    bots_atuais.append(p_state)
        
        # Remove bots mortos (o game_loop fará isso)
        if bots_para_remover:
            print(f"[LOG] Bots mortos para remover: {bots_para_remover}")
            
        # Spawna novos bots se necessário
        if len(bots_atuais) < max_bots:
            self.spawn_bot() # Spawna um novo bot
            
        return bots_para_remover # Retorna a lista de chaves para o server remover

    def spawn_bot(self):
        """ Cria um novo bot e o adiciona ao player_states. """
        
        nome_bot = ""
        # Encontra um nome único (Bot_1, Bot_2, etc.)
        nomes_existentes = [p['nome'] for p in self.player_states.values()]
        i = 1
        while True:
            nome_bot = f"Bot_{i}"
            if nome_bot not in nomes_existentes:
                break
            i += 1
            if i > 99: # Salvaguarda maior
                print("[LOG] [ERRO] Não foi possível encontrar um nome único para o bot.")
                return

        posicoes_atuais = [(p['x'], p['y']) for p in self.player_states.values()]
        
        spawn_x, spawn_y = self.spawn_calculator(posicoes_atuais)
        
        nivel_max_vida_inicial = 1
        max_hp_inicial = 4 + nivel_max_vida_inicial
        
        bot_state = {
            'nome': nome_bot,
            'is_bot': True,
            'handshake_completo': True, 
            'conn': None, 
            'x': float(spawn_x), 
            'y': float(spawn_y), 
            'angulo': 0.0,
            'max_hp': max_hp_inicial, 
            'hp': float(max_hp_inicial), 
            'pontos': 0, 
            'invencivel': False,
            'teclas': { 'w': False, 'a': False, 's': False, 'd': False, 'space': False },
            'alvo_mouse': None, 
            'alvo_lock': None, 
            'ultimo_tiro_tempo': 0, 
            'cooldown_tiro': COOLDOWN_TIRO, 
            'esta_regenerando': False,
            'ultimo_tick_regeneracao': 0,
            'ultimo_hit_tempo': 0,
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
            'aux_cooldowns': [0, 0, 0, 0],
            'bot_estado_ia': "VAGANDO",
            'bot_frames_sem_movimento': 0,
            'bot_posicao_anterior': (0,0),
            'bot_wander_target': None, # <-- MODIFICAÇÃO (Adicionado)
            'tempo_fim_lentidao': 0,
            'tempo_fim_congelamento': 0
        }
        
        self.player_states[nome_bot] = bot_state # Usa o nome como chave
        print(f"[LOG] [SERVIDOR] Bot {nome_bot} spawnou em ({int(spawn_x)}, {int(spawn_y)}).")

    def process_bot_logic(self, bot_state, all_living_players, agora_ms):
        """ Função principal chamada pelo game_loop para fazer um bot pensar. """
        
        # 0. Verifica Status (Não pensa se estiver congelado)
        if agora_ms < bot_state.get('tempo_fim_congelamento', 0):
            bot_state['teclas'] = { 'w': False, 'a': False, 's': False, 'd': False, 'space': False }
            bot_state['alvo_mouse'] = None
            return

        # 1. IA toma decisões (define 'teclas', 'alvo_mouse', 'alvo_lock')
        self._update_ia_decision(bot_state, all_living_players)
        
        # 2. IA processa upgrades
        self._process_upgrades(bot_state)
        
        # 3. IA processa regeneração
        self._process_regeneration(bot_state, agora_ms)

    def _process_upgrades(self, bot_state):
        """ IA simples para comprar upgrades (de ships.py/NaveBot). """
        if bot_state['pontos_upgrade_disponiveis'] > 0 and bot_state['total_upgrades_feitos'] < MAX_TOTAL_UPGRADES:
            if bot_state['nivel_motor'] < MAX_NIVEL_MOTOR:
                 self.upgrade_purchaser(bot_state, "motor")
            elif bot_state['nivel_escudo'] < MAX_NIVEL_ESCUDO: 
                 self.upgrade_purchaser(bot_state, "escudo")
            elif bot_state['nivel_dano'] < MAX_NIVEL_DANO:
                 self.upgrade_purchaser(bot_state, "dano")
            else: 
                 self.upgrade_purchaser(bot_state, "max_health")

    def _process_regeneration(self, bot_state, agora_ms):
        """ Controla a regeneração do Bot, baseado no estado da IA. """
        
        estado_ia = bot_state.get('bot_estado_ia')
        
        # --- MODIFICAÇÃO: Não regenera se estiver FUGINDO (se movendo) ---
        if estado_ia == "FUGINDO":
             bot_state['esta_regenerando'] = False # Garante que pare
             return
        # --- FIM DA MODIFICAÇÃO ---
        
        # Se estivermos parados (REGENERANDO_NA_BORDA) OU VAGANDO com HP baixo (tentando parar)
        esta_parado_para_regen = (estado_ia == "REGENERANDO_NA_BORDA") or \
                               (estado_ia == "VAGANDO" and bot_state['hp'] < (bot_state['max_hp'] * BOT_HP_REGENERAR_PERC))
        
        # Condições para INICIAR a regeneração
        if esta_parado_para_regen and \
           bot_state['alvo_lock'] is None and \
           not bot_state['esta_regenerando']:
            
            # Força parada (caso VAGANDO tenha setado movimento)
            bot_state['teclas']['w'] = False
            bot_state['alvo_mouse'] = None
            bot_state['esta_regenerando'] = True
            bot_state['ultimo_tick_regeneracao'] = agora_ms
            # print(f"[LOG] {bot_state['nome']} iniciando regeneração (Estado: {estado_ia})") # DEBUG

        # Condições para PARAR a regeneração
        if bot_state['esta_regenerando']:
            # Se começarmos a nos mover (VAGANDO com HP cheio) ou mirarmos, para
            if (bot_state['alvo_mouse'] is not None or bot_state['alvo_lock'] is not None):
                bot_state['esta_regenerando'] = False
                # print(f"[LOG] {bot_state['nome']} parando regeneração (Movimento/Alvo)") # DEBUG
            elif bot_state['hp'] >= bot_state['max_hp']:
                bot_state['hp'] = bot_state['max_hp']
                bot_state['esta_regenerando'] = False
                # print(f"[LOG] {bot_state['nome']} parando regeneração (HP Cheio)") # DEBUG
                if estado_ia == "REGENERANDO_NA_BORDA":
                    # Volte a vagar (e a IA de VAGAR vai tirar ele da borda)
                    bot_state['bot_estado_ia'] = "VAGANDO"

    def _update_ia_decision(self, bot_state, all_living_players):
        """ O "Cérebro" do Bot. Decide o que fazer (define 'teclas', 'alvo_mouse', 'alvo_lock'). """
        
        # --- 1. Resetar Intenções ---
        bot_state['teclas']['w'] = False
        bot_state['teclas']['a'] = False
        bot_state['teclas']['s'] = False
        bot_state['teclas']['d'] = False
        bot_state['teclas']['space'] = False
        bot_state['alvo_mouse'] = None
        
        # --- 2. Lógica Anti-Stuck (Anti-Preso) ---
        pos_atual = (bot_state['x'], bot_state['y'])
        pos_anterior = bot_state['bot_posicao_anterior']
        dist_sq_movido = (pos_atual[0] - pos_anterior[0])**2 + (pos_atual[1] - pos_anterior[1])**2
        
        if dist_sq_movido < (3**2):
            bot_state['bot_frames_sem_movimento'] += 1
            # --- INÍCIO DA MODIFICAÇÃO (Anti-Stuck) ---
            # Aumentamos o limiar para 60 frames (1 segundo)
            if bot_state['bot_frames_sem_movimento'] > 60: 
                print(f"[LOG] [BOT] {bot_state['nome']} está preso. A forçar novo 'wander target'.")
                # Força o bot a mudar de estado e a encontrar um novo ponto de fuga
                bot_state['bot_estado_ia'] = "VAGANDO"
                bot_state['alvo_lock'] = None
                bot_state['alvo_mouse'] = None
                bot_state['bot_wander_target'] = None # Força a recalculação na próxima
                bot_state['bot_frames_sem_movimento'] = 0
            # --- FIM DA MODIFICAÇÃO ---
        else:
            bot_state['bot_frames_sem_movimento'] = 0
        bot_state['bot_posicao_anterior'] = pos_atual

        # --- 3. PRIORIDADE 1: FUGIR / REGENERAR NA BORDA (Se HP < 20%) ---
        hp_limite_fugir = bot_state['max_hp'] * BOT_HP_FUGIR_PERC
        if bot_state['hp'] <= hp_limite_fugir:
            
            # Checa se está na borda
            zona_perigo = BOT_DIST_BORDA_SEGURA
            em_zona_perigo = (bot_state['x'] < zona_perigo or 
                              bot_state['x'] > self.s.MAP_WIDTH - zona_perigo or
                              bot_state['y'] < zona_perigo or 
                              bot_state['y'] > self.s.MAP_HEIGHT - zona_perigo)

            # SE estiver na borda E HP baixo, o estado muda para REGENERAR (parado)
            if em_zona_perigo:
                bot_state['bot_estado_ia'] = "REGENERANDO_NA_BORDA"
                bot_state['alvo_mouse'] = None # PARA DE MOVER
            else:
                # SE HP baixo e NÃO na borda, o estado é FUGINDO (movendo-se)
                bot_state['bot_estado_ia'] = "FUGINDO"
                
                # Tenta encontrar o inimigo mais próximo para fugir DELE
                alvo_ameacador = None
                dist_min_sq = BOT_DISTANCIA_SCAN_GERAL_SQ # Foge de qualquer coisa perto
                
                # Procura NPCs
                for npc in self.network_npcs:
                    dist_sq = (npc['x'] - bot_state['x'])**2 + (npc['y'] - bot_state['y'])**2
                    if dist_sq < dist_min_sq:
                        dist_min_sq = dist_sq
                        alvo_ameacador = npc
                
                # Procura Players
                if alvo_ameacador is None:
                    for player in all_living_players:
                        if player['nome'] == bot_state['nome']: continue 
                        dist_sq = (player['x'] - bot_state['x'])**2 + (player['y'] - bot_state['y'])**2
                        if dist_sq < dist_min_sq:
                            dist_min_sq = dist_sq
                            alvo_ameacador = player
                
                if alvo_ameacador:
                    # Foge do alvo
                    vec_x = alvo_ameacador['x'] - bot_state['x']
                    vec_y = alvo_ameacador['y'] - bot_state['y']
                    dist = math.sqrt(vec_x**2 + vec_y**2) + 1e-6
                    ponto_fuga_x = bot_state['x'] - (vec_x / dist) * 500 # Foge 500px
                    ponto_fuga_y = bot_state['y'] - (vec_y / dist) * 500
                    bot_state['alvo_mouse'] = (ponto_fuga_x, ponto_fuga_y)
                else:
                    # Foge para o wander target (se não houver inimigos)
                    if bot_state.get('bot_wander_target') is None:
                        # Define um wander target se não tiver
                        map_margin = 100
                        target_x = random.randint(map_margin, self.s.MAP_WIDTH - map_margin)
                        target_y = random.randint(map_margin, self.s.MAP_HEIGHT - map_margin)
                        bot_state['bot_wander_target'] = (target_x, target_y)
                    
                    bot_state['alvo_mouse'] = bot_state.get('bot_wander_target')
            
            bot_state['alvo_lock'] = None 

        # --- 4. Encontrar Alvo (SÓ SE NÃO ESTIVER FUGINDO) ---
        # (Se estiver REGENERANDO_NA_BORDA, PODE procurar alvo para se defender)
        if bot_state.get('bot_estado_ia') != "FUGINDO":
            
            alvo_ainda_valido = False
            if bot_state['alvo_lock']:
                alvo_id_lock = bot_state['alvo_lock']
                # Checa se está nos NPCs vivos
                for npc in self.network_npcs:
                    if npc['id'] == alvo_id_lock and npc['hp'] > 0:
                        alvo_ainda_valido = True
                        break
                # Checa se está nos Players vivos
                if not alvo_ainda_valido:
                    for p in all_living_players:
                        if p['nome'] == alvo_id_lock and p['nome'] != bot_state['nome']:
                            alvo_ainda_valido = True
                            break
            
            if not alvo_ainda_valido:
                bot_state['alvo_lock'] = None
                if bot_state.get('bot_estado_ia') != "REGENERANDO_NA_BORDA":
                    bot_state['bot_estado_ia'] = "VAGANDO"

                alvo_final_id = None
                dist_min_sq = BOT_DISTANCIA_SCAN_GERAL_SQ

                # 4a. Prioridade 1: NPCs
                for npc in self.network_npcs:
                    dist_sq = (npc['x'] - bot_state['x'])**2 + (npc['y'] - bot_state['y'])**2
                    if dist_sq < dist_min_sq:
                        dist_min_sq = dist_sq
                        alvo_final_id = npc['id']

                # 4b. Prioridade 2: Jogadores/Bots
                if alvo_final_id is None: 
                    for player in all_living_players:
                        if player['nome'] == bot_state['nome']: continue 
                        
                        dist_sq = (player['x'] - bot_state['x'])**2 + (player['y'] - bot_state['y'])**2
                        if dist_sq < dist_min_sq:
                            dist_min_sq = dist_sq
                            alvo_final_id = player['nome']
                
                if alvo_final_id:
                    bot_state['alvo_lock'] = alvo_final_id
                    if bot_state.get('bot_estado_ia') != "REGENERANDO_NA_BORDA":
                        bot_state['bot_estado_ia'] = "CAÇANDO"
                else:
                    if bot_state.get('bot_estado_ia') != "REGENERANDO_NA_BORDA":
                        bot_state['bot_estado_ia'] = "VAGANDO"

        # --- 5. Processar Estados (Definir Inputs) ---
        
        # Se estiver FUGINDO, a lógica de movimento já foi definida acima
        if bot_state['bot_estado_ia'] == "FUGINDO":
            return # Sai da função
            
        # Se estiver REGENERANDO NA BORDA, para de mover, mas permite atirar (lógica de alvo abaixo)
        if bot_state['bot_estado_ia'] == "REGENERANDO_NA_BORDA":
            bot_state['alvo_mouse'] = None # Garante que está parado
            # (Propositalmente não retorna, para que a lógica de "ATACANDO" possa rodar)
            
        if bot_state['bot_estado_ia'] == "VAGANDO" or bot_state['esta_regenerando']:
            # (Se 'esta_regenerando' for True, a lógica _process_regeneration vai parar se
            #  o alvo_mouse for setado. Se for False, ele pode vagar.)
            
            if not bot_state['esta_regenerando']: 
                
                # --- LÓGICA DE VAGAR (WANDER) ---
                chegou_perto = False
                wander_target = bot_state.get('bot_wander_target') # Usar .get para segurança
                
                if wander_target:
                    dist_sq = (bot_state['x'] - wander_target[0])**2 + (bot_state['y'] - wander_target[1])**2
                    if dist_sq < 100**2: # (100 pixels)
                        chegou_perto = True
                
                if wander_target is None or chegou_perto:
                    # Usa valores hardcoded do mapa (8000x8000)
                    map_margin = 100
                    # Usa self.s (settings) que foi passado no init
                    target_x = random.randint(map_margin, self.s.MAP_WIDTH - map_margin)
                    target_y = random.randint(map_margin, self.s.MAP_HEIGHT - map_margin)
                    bot_state['bot_wander_target'] = (target_x, target_y)
                
                bot_state['alvo_mouse'] = bot_state['bot_wander_target']
                # --- FIM DA NOVA LÓGICA ---
            
            # Se 'esta_regenerando' for True, 'alvo_mouse' não é setado, e o bot fica parado.
            return 

        # --- 6. Lógica de Combate (Se tem alvo_lock) ---
        if bot_state['alvo_lock']:
            alvo_coords = None
            alvo_vivo = False
            
            target_id = bot_state['alvo_lock']
            
            alvo_npc = next((npc for npc in self.network_npcs if npc['id'] == target_id and npc['hp'] > 0), None)
            if alvo_npc:
                alvo_coords = (alvo_npc['x'], alvo_npc['y'])
                alvo_vivo = True
            else:
                alvo_player = next((p for p in all_living_players if p['nome'] == target_id), None)
                if alvo_player:
                    alvo_coords = (alvo_player['x'], alvo_player['y'])
                    alvo_vivo = True

            if not alvo_vivo or alvo_coords is None:
                bot_state['alvo_lock'] = None
                if bot_state.get('bot_estado_ia') != "REGENERANDO_NA_BORDA":
                    bot_state['bot_estado_ia'] = "VAGANDO"
                return

            alvo_x, alvo_y = alvo_coords
            vec_x = alvo_x - bot_state['x']
            vec_y = alvo_y - bot_state['y']
            dist_sq_alvo = vec_x**2 + vec_y**2
            
            # (Lógica de fugir foi movida para cima)
            
            if dist_sq_alvo > BOT_DISTANCIA_SCAN_INIMIGO_SQ:
                bot_state['bot_estado_ia'] = "CAÇANDO"
                # Se estivermos regenerando parados, NÃO caçamos (apenas atiramos)
                if bot_state.get('bot_estado_ia') != "REGENERANDO_NA_BORDA":
                    bot_state['alvo_mouse'] = (alvo_x, alvo_y) 
            
            else:
                bot_state['bot_estado_ia'] = "ATACANDO"
                
                # Se estivermos regenerando parados, NÃO orbitamos
                if bot_state.get('bot_estado_ia') == "REGENERANDO_NA_BORDA":
                    bot_state['alvo_mouse'] = None # Fica parado
                    bot_state['teclas']['w'] = False
                    bot_state['teclas']['s'] = False
                    bot_state['teclas']['a'] = False
                else:
                    # --- INÍCIO DA NOVA LÓGICA DE ORBITAR COM TECLAS ---
                    # O 'alvo_lock' já está a mirar no inimigo.
                    # A IA só precisa de decidir se avança, recua ou anda de lado (strafe).
                    bot_state['alvo_mouse'] = None # Nunca usar alvo_mouse e teclas ao mesmo tempo
                    
                    if dist_sq_alvo > BOT_DISTANCIA_ORBITA_MAX_SQ: 
                        # Muito longe: Avança
                        bot_state['teclas']['w'] = True
                        bot_state['teclas']['s'] = False
                        bot_state['teclas']['a'] = False
                    elif dist_sq_alvo < BOT_DISTANCIA_ORBITA_MIN_SQ: 
                        # Muito perto: Recua
                        bot_state['teclas']['w'] = False
                        bot_state['teclas']['s'] = True
                        bot_state['teclas']['a'] = False
                    else:
                        # Distância correta: Anda de lado (Strafe Esquerdo)
                        bot_state['teclas']['w'] = False
                        bot_state['teclas']['s'] = False
                        bot_state['teclas']['a'] = True 
                    # --- FIM DA NOVA LÓGICA ---