# botia.py
import pygame
import random
import math
import settings as s # <-- MODIFICAÇÃO: Importa 's' em vez de MAP_WIDTH/HEIGHT
# Importa as constantes do mapa
# from settings import MAP_WIDTH, MAP_HEIGHT # <-- MODIFICAÇÃO: Linha removida

class BotAI:
    def __init__(self, bot_nave):
        """
        Inicializa o cérebro da IA.
        'bot_nave' é a referência para a instância de NaveBot que este cérebro controla.
        """
        self.bot = bot_nave 
        
        # --- INÍCIO: MODIFICAÇÃO (Map Size) ---
        self.map_width = s.MAP_WIDTH # Valor padrão (PVE)
        self.map_height = s.MAP_HEIGHT # Valor padrão (PVE)
        # --- FIM: MODIFICAÇÃO ---
        
        # Variáveis de estado da IA
        self.estado_ia = "VAGANDO"
        self.virando_aleatoriamente_timer = 0
        self.direcao_virada_aleatoria = "direita"
        
        # Referência para o grupo de vidas (será atualizado a cada frame)
        self.grupo_vidas_ref = None 
        
        # Constantes de comportamento da IA
        self.distancia_scan_geral = 800
        self.distancia_scan_inimigo = 600
        
        # Distâncias para Kiting/Orbitar
        self.distancia_orbita_max = 300      # Distância máxima (começa a avançar)
        self.distancia_orbita_min = 200      # Distância mínima (começa a recuar)
        
        self.distancia_tiro_ia = 500
        self.dist_borda_segura = 400
        
        # Sistema de detecção de "preso"
        self.posicao_anterior = pygame.math.Vector2(0, 0)
        self.frames_sem_movimento = 0
        self.bot_wander_target = None
        
        # Caches de referência
        self.player_ref_cache = None
        self.grupo_bots_ref_cache = None
        self.grupo_inimigos_ref_cache = None
        self.grupo_obstaculos_ref_cache = None
        
        # --- LÓGICA DE ÓRBITA ALEATÓRIA (da correção anterior) ---
        self.direcao_orbita = 1 
        self.timer_troca_orbita = 0 
        self.duracao_orbita_atual = random.randint(120, 300)
        
        # --- INÍCIO DA CORREÇÃO (KITING) ---
        self.flee_destination = None # Armazena o ponto de fuga na borda
        # --- FIM DA CORREÇÃO ---
    
    def _find_closest_edge_point(self):
        """
        Calcula o ponto mais próximo na borda do mapa para onde o bot deve fugir.
        """
        pos = self.bot.posicao
        dist_to_top = pos.y
        # --- MODIFICAÇÃO: Usa self.map_height ---
        dist_to_bottom = self.map_height - pos.y
        dist_to_left = pos.x
        # --- MODIFICAÇÃO: Usa self.map_width ---
        dist_to_right = self.map_width - pos.x

        min_dist = min(dist_to_top, dist_to_bottom, dist_to_left, dist_to_right)
        
        # Define uma pequena margem para não ficar "colado" na borda
        margin = 50 

        if min_dist == dist_to_top:
            return pygame.math.Vector2(pos.x, margin)
        elif min_dist == dist_to_bottom:
            # --- MODIFICAÇÃO: Usa self.map_height ---
            return pygame.math.Vector2(pos.x, self.map_height - margin)
        elif min_dist == dist_to_left:
            return pygame.math.Vector2(margin, pos.y)
        else: # dist_to_right
            # --- MODIFICAÇÃO: Usa self.map_width ---
            return pygame.math.Vector2(self.map_width - margin, pos.y)
    
    def _find_closest_threat(self):
        """
        Encontra a ameaça (Inimigo ou Player/Bot) mais próxima.
        Retorna o sprite da ameaça, ou None se nenhuma for encontrada.
        """
        alvo_ameacador_sprite = None
        dist_min = float('inf')
        
        # 1. Procura Inimigos
        if self.grupo_inimigos_ref_cache:
            for inimigo in self.grupo_inimigos_ref_cache:
                if not inimigo.groups(): continue
                
                # --- INÍCIO: CORREÇÃO (Bot se alvejando) ---
                if inimigo == self.bot:
                    continue # Não pode alvejar a si mesmo
                # --- FIM: CORREÇÃO ---
                
                try:
                    dist = self.bot.posicao.distance_to(inimigo.posicao)
                    if dist < self.distancia_scan_geral and dist < dist_min:
                        dist_min = dist
                        alvo_ameacador_sprite = inimigo 
                except (ValueError, AttributeError): continue
        
        # 2. Procura Players/Bots (se não houver inimigos)
        if alvo_ameacador_sprite is None:
            
            # --- INÍCIO DA CORREÇÃO (BUB OFFLINE: Bots atacam jogador morto) ---
            # Constrói a lista de alvos VÁLIDOS (player só se estiver vivo)
            lista_alvos_naves = []
            if self.player_ref_cache and self.player_ref_cache.vida_atual > 0:
                lista_alvos_naves.append(self.player_ref_cache)
            lista_alvos_naves.extend(list(self.grupo_bots_ref_cache.sprites()))
            # --- FIM DA CORREÇÃO ---
            
            for alvo in lista_alvos_naves:
                # A checagem de vida aqui é redundante, mas mantida por segurança
                if alvo == self.bot or not alvo.groups() or alvo.vida_atual <= 0: 
                    continue
                try:
                    dist = self.bot.posicao.distance_to(alvo.posicao)
                    if dist < self.distancia_scan_geral and dist < dist_min:
                        dist_min = dist
                        alvo_ameacador_sprite = alvo 
                except (ValueError, AttributeError): continue
        
        return alvo_ameacador_sprite
        
    # --- INÍCIO: MODIFICAÇÃO (Aceitar map_width/height) ---
    def update_ai(self, player_ref, grupo_bots_ref, grupo_inimigos_ref, grupo_obstaculos_ref, grupo_vidas_ref, map_width=None, map_height=None):
        """ 
        O "tick" principal do cérebro da IA. 
        Chamado a cada frame pelo NaveBot.
        (ORDEM CORRIGIDA: A lógica de estado (Fugir) agora roda ANTES de encontrar alvo)
        """
        
        # Atualiza as dimensões do mapa se fornecidas
        if map_width is not None:
            self.map_width = map_width
        if map_height is not None:
            self.map_height = map_height
        # --- FIM: MODIFICAÇÃO ---
        
        # --- INÍCIO DA CORREÇÃO DO BUG ---
        # Salva a referência ao grupo de vidas para que _processar_input_ia possa usá-lo
        self.grupo_vidas_ref = grupo_vidas_ref
        self.player_ref_cache = player_ref
        self.grupo_bots_ref_cache = grupo_bots_ref
        self.grupo_inimigos_ref_cache = grupo_inimigos_ref
        self.grupo_obstaculos_ref_cache = grupo_obstaculos_ref
        # --- FIM DA CORREÇÃO DO BUG ---
        
        # Detecção de bot preso
        if self.bot.posicao.distance_to(self.posicao_anterior) < 3:
            self.frames_sem_movimento += 1
            if self.frames_sem_movimento > 30:
                if (self.bot.posicao.x < self.dist_borda_segura * 1.5 or 
                    # --- MODIFICAÇÃO: Usa self.map_width ---
                    self.bot.posicao.x > self.map_width - self.dist_borda_segura * 1.5 or
                    self.bot.posicao.y < self.dist_borda_segura * 1.5 or 
                    # --- MODIFICAÇÃO: Usa self.map_height ---
                    self.bot.posicao.y > self.map_height - self.dist_borda_segura * 1.5):
                    # --- MODIFICAÇÃO: Usa self.map_width/height ---
                    centro = pygame.math.Vector2(self.map_width / 2, self.map_height / 2)
                    direcao_centro = centro - self.bot.posicao
                    if direcao_centro.length() > 0:
                        self.bot.angulo = pygame.math.Vector2(0, -1).angle_to(direcao_centro)
                else:
                    self.bot.angulo += random.randint(90, 180)
                self.frames_sem_movimento = 0
        else:
            self.frames_sem_movimento = 0
        self.posicao_anterior = self.bot.posicao.copy()
        
        # --- INÍCIO DA MUDANÇA (Correção da Prioridade de Fuga) ---
        
        # 1. Processar o estado atual (DECIDIR SE PRECISA FUGIR)
        #    Isto irá definir o estado_ia para "FUGINDO" ou "REGENERANDO_NA_BORDA"
        #    e limpar o alvo (alvo_selecionado = None) se o HP estiver baixo.
        self._processar_input_ia()
        
        # 2. Encontrar um novo alvo APENAS SE:
        #    - O alvo atual for inválido (None, morto, ou fora dos grupos)
        #    - E o estado NÃO for de fuga (FUGINDO, REGENERANDO_NA_BORDA)
        #    - E o estado NÃO for de evitar a borda (pois isso também é prioritário)
        
        # --- INÍCIO DA CORREÇÃO (BUB OFFLINE: Bots atacam jogador morto) ---
        alvo_esta_morto = False
        if self.bot.alvo_selecionado:
            # Verifica se o alvo (que pode ser player, bot ou inimigo) tem vida
            if not hasattr(self.bot.alvo_selecionado, 'vida_atual') or self.bot.alvo_selecionado.vida_atual <= 0:
                alvo_esta_morto = True
        
        if (self.bot.alvo_selecionado is None or not self.bot.alvo_selecionado.groups() or alvo_esta_morto) and \
           self.estado_ia not in ["FUGINDO", "REGENERANDO_NA_BORDA", "EVITANDO_BORDA"]:
            
            # Constrói a lista de alvos VÁLIDOS (player só se estiver vivo)
            lista_alvos_naves = []
            if player_ref and player_ref.vida_atual > 0:
                lista_alvos_naves.append(player_ref)
            lista_alvos_naves.extend(list(grupo_bots_ref.sprites()))
            
            self._encontrar_alvo(grupo_inimigos_ref, grupo_obstaculos_ref, lista_alvos_naves, grupo_vidas_ref)
        # --- FIM DA CORREÇÃO ---
        
        # --- FIM DA MUDANÇA ---

    def _encontrar_alvo(self, grupo_inimigos, grupo_obstaculos, lista_alvos_naves, grupo_vidas):
        """ 
        Encontra o alvo mais próximo válido e o define em self.bot.alvo_selecionado.
        """
        
        # Reseta a mira
        self.bot.alvo_selecionado = None
        alvo_final = None
        dist_min = float('inf')
        
        LIMITE_HP_BUSCAR_VIDA = self.bot.max_vida * 0.40
        
        # 1. Prioridade Máxima: Buscar Vida
        if self.bot.vida_atual <= LIMITE_HP_BUSCAR_VIDA:
            # --- INÍCIO DA CORREÇÃO DO BUG ---
            # Verifica se grupo_vidas não é None ANTES de iterar
            if grupo_vidas: 
                for vida in grupo_vidas:
                    # FIX: Ignora sprites que não tenham .posicao (como Explosoes)
                    if not vida.groups() or not hasattr(vida, 'posicao'): continue
                    try:
                        dist = self.bot.posicao.distance_to(vida.posicao)
                        if dist < self.distancia_scan_geral and dist < dist_min:
                            dist_min = dist
                            alvo_final = vida
                    except (ValueError, AttributeError):
                        continue
            
            if alvo_final:
                # self.bot.alvo_selecionado = alvo_final # NÃO trava a mira em vida
                self.estado_ia = "COLETANDO"
                return 

        # 2. Segunda Prioridade: INIMIGOS (No PVP, são os outros jogadores)
        dist_min = float('inf'); alvo_final = None       
        for inimigo in grupo_inimigos:
            if not inimigo.groups(): continue
            
            # --- INÍCIO: CORREÇÃO (Bot se alvejando) ---
            if inimigo == self.bot:
                continue # Não pode alvejar a si mesmo
            # --- FIM: CORREÇÃO ---
            
            try:
                dist = self.bot.posicao.distance_to(inimigo.posicao)
                if dist < dist_min and dist < self.distancia_scan_geral:
                    dist_min = dist; alvo_final = inimigo
            except (ValueError, AttributeError): continue
        
        if alvo_final:
            self.bot.alvo_selecionado = alvo_final # <--- TRAVA A MIRA
            if dist_min < self.distancia_scan_inimigo: self.estado_ia = "ATACANDO"
            else: self.estado_ia = "CAÇANDO"
            return # <--- Foco no inimigo

        # 3. Terceira Prioridade: OBSTÁCULOS
        dist_min = float('inf'); alvo_final = None       
        for obstaculo in grupo_obstaculos:
            if not obstaculo.groups(): continue
            try:
                dist = self.bot.posicao.distance_to(obstaculo.posicao)
                if dist < dist_min and dist < self.distancia_scan_geral:
                    dist_min = dist; alvo_final = obstaculo
            except (ValueError, AttributeError): continue
        
        if alvo_final:
            self.bot.alvo_selecionado = alvo_final # <--- TRAVA A MIRA
            if dist_min < self.distancia_scan_inimigo: self.estado_ia = "ATACANDO"
            else: self.estado_ia = "CAÇANDO"
            return # <--- Foco no obstáculo

        # 4. Última Prioridade: Outras Naves (Redundante no PVP, mas bom para PVE)
        dist_min = float('inf'); alvo_final = None       
        for alvo in lista_alvos_naves:
            
            # --- INÍCIO DA MODIFICAÇÃO: Checar se o alvo (jogador/bot) está vivo ---
            # Se o alvo for o próprio bot, ou não estiver em um grupo, OU estiver com vida <= 0, ignore.
            if alvo == self.bot or not alvo.groups() or alvo.vida_atual <= 0: 
                continue
            # --- FIM DA MODIFICAÇÃO ---

            try:
                dist = self.bot.posicao.distance_to(alvo.posicao)
                if dist < self.distancia_scan_geral and dist < dist_min:
                    dist_min = dist; alvo_final = alvo
            except (ValueError, AttributeError): continue

        if alvo_final:
            self.bot.alvo_selecionado = alvo_final # <--- TRAVA A MIRA
            if dist_min < self.distancia_scan_inimigo: self.estado_ia = "ATACANDO"
            else: self.estado_ia = "CAÇANDO"
        else:
            self.bot.alvo_selecionado = None # Garante que está limpo
            self.estado_ia = "VAGANDO"
    
    def _processar_input_ia(self):
        """ 
        Define as intenções de movimento. A rotação agora é automática.
        """
        
        # --- 1. Resetar Intenções ---
        self.bot.quer_mover_frente = False
        self.bot.quer_mover_tras = False
        self.bot.posicao_alvo_mouse = None
        
        LIMITE_HP_FUGIR = self.bot.max_vida * 0.20 # 20%
        LIMITE_HP_REGENERAR_OBRIGATORIO = self.bot.max_vida * 0.80 # 80%

        # === PRIORIDADE 0: JÁ ESTÁ REGENERANDO FORÇADAMENTE? ===
        # Se o bot está no estado REGENERANDO_NA_BORDA, ele não pode sair
        # até que seu HP esteja em 80%.
        if self.estado_ia == "REGENERANDO_NA_BORDA":
            if self.bot.vida_atual < LIMITE_HP_REGENERAR_OBRIGATORIO:
                self.bot.posicao_alvo_mouse = None # Garante que fica parado
                self.flee_destination = None 
                
                # Procura alvos para se defender (kiting parado)
                self.bot.alvo_selecionado = self._find_closest_threat()
                return # Decisão final: Ficar parado e atirar
            else:
                # Atingiu 80%! Volta a vagar.
                print(f"[{self.bot.nome}] Regeneração concluída. Voltando a vagar.")
                self.estado_ia = "VAGANDO"
                self.flee_destination = None

        # === PRIORIDADE 1: FUGIR (HP < 20%) ===
        if self.bot.vida_atual <= LIMITE_HP_FUGIR:
            
            zona_perigo = self.dist_borda_segura
            em_zona_perigo = (self.bot.posicao.x < zona_perigo or 
                              # --- MODIFICAÇÃO: Usa self.map_width ---
                              self.bot.posicao.x > self.map_width - zona_perigo or
                              self.bot.posicao.y < zona_perigo or 
                              # --- MODIFICAÇÃO: Usa self.map_height ---
                              self.bot.posicao.y > self.map_height - zona_perigo)

            if em_zona_perigo:
                # 2A. CHEGOU NA BORDA: PARAR E REGENERAR
                # Este é o único local que define este estado
                self.estado_ia = "REGENERANDO_NA_BORDA"
                self.bot.posicao_alvo_mouse = None # Para de mover
                self.flee_destination = None # Limpa o destino de fuga
            
            else:
                # 2B. PRECISA FUGIR (AINDA NÃO ESTÁ NA BORDA)
                if self.estado_ia != "FUGINDO":
                    self.estado_ia = "FUGINDO"
                    self.flee_destination = self._find_closest_edge_point()
                    print(f"[{self.bot.nome}] HP baixo! Fugindo para {self.flee_destination}")
                
                if self.flee_destination:
                    self.bot.posicao_alvo_mouse = self.flee_destination
            
            # LÓGICA DE KITING (atirar enquanto foge/regenera)
            self.bot.alvo_selecionado = self._find_closest_threat()
            return # Fuga/Regeneração é prioridade máxima
            
        # === 3. RESETAR ESTADO DE FUGA (Se HP > 20% e não estava regenerando) ===
        if self.estado_ia == "FUGINDO":
            self.estado_ia = "VAGANDO"
            self.flee_destination = None

        # === 4. PRIORIDADE 2: EVITAR A BORDA (Se HP ALTO) ===
        elif self.estado_ia != "EVITANDO_BORDA": 
            # --- MODIFICAÇÃO: Usa self.map_width/height ---
            centro_mapa = pygame.math.Vector2(self.map_width / 2, self.map_height / 2)
            zona_perigo = self.dist_borda_segura
            em_zona_perigo = (self.bot.posicao.x < zona_perigo or self.bot.posicao.x > self.map_width - zona_perigo or
                              self.bot.posicao.y < zona_perigo or self.bot.posicao.y > self.map_height - zona_perigo)
            
            if em_zona_perigo:
                self.estado_ia = "EVITANDO_BORDA"
                self.bot.alvo_selecionado = None 
        
        if self.estado_ia == "EVITANDO_BORDA":
            zona_segura_minima = self.dist_borda_segura + 200
            # --- MODIFICAÇÃO: Usa self.map_width/height ---
            em_zona_segura = (self.bot.posicao.x > zona_segura_minima and self.bot.posicao.x < self.map_width - zona_segura_minima and
                              self.bot.posicao.y > zona_segura_minima and self.bot.posicao.y < self.map_height - zona_segura_minima)
            if em_zona_segura:
                self.estado_ia = "VAGANDO"
            else:
                # --- MODIFICAÇÃO: Usa self.map_width/height ---
                centro_mapa = pygame.math.Vector2(self.map_width / 2, self.map_height / 2)
                self.bot.posicao_alvo_mouse = centro_mapa
            return 

        # === 5. LÓGICA DE ALVO (Se não estiver FUGINDO/EVITANDO) ===
        # (Esta lógica está em update_ai, o que é correto)

        # === 6. PROCESSAR ESTADOS DE COMBATE/VAGANDO (HP ALTO) ===
        
        if self.estado_ia == "COLETANDO": 
            vida_perto = None
            dist_min = self.distancia_scan_geral
            
            if self.grupo_vidas_ref:
                for vida in self.grupo_vidas_ref: 
                     if not vida.groups() or not hasattr(vida, 'posicao'): continue
                     try:
                         dist = self.bot.posicao.distance_to(vida.posicao)
                         if dist < dist_min:
                             dist_min = dist
                             vida_perto = vida
                     except ValueError: pass
            
            if vida_perto:
                self.bot.posicao_alvo_mouse = vida_perto.posicao
            else:
                self.estado_ia = "VAGANDO" 
            return

        if self.estado_ia == "CAÇANDO":
            alvo = self.bot.alvo_selecionado
            if not (alvo and alvo.groups()):
                self.estado_ia = "VAGANDO"; return
            try:
                distancia_alvo = self.bot.posicao.distance_to(alvo.posicao)
                if distancia_alvo < self.distancia_scan_inimigo: 
                    self.estado_ia = "ATACANDO"; return 

                self.bot.posicao_alvo_mouse = alvo.posicao
                return 
            except ValueError:
                self.estado_ia = "VAGANDO"

        if self.estado_ia == "ATACANDO":
            alvo = self.bot.alvo_selecionado
            if not (alvo and alvo.groups()):
                self.estado_ia = "VAGANDO"; return
            
            try:
                direcao_alvo_vec = (alvo.posicao - self.bot.posicao)
                distancia_alvo = direcao_alvo_vec.length()
                
                if distancia_alvo > self.distancia_scan_inimigo:
                    self.estado_ia = "CAÇANDO"; return

                ponto_movimento = self.bot.posicao 

                if distancia_alvo > self.distancia_orbita_max: 
                    ponto_movimento = alvo.posicao
                
                elif distancia_alvo < self.distancia_orbita_min: 
                    if direcao_alvo_vec.length() > 0:
                        ponto_movimento = self.bot.posicao - direcao_alvo_vec.normalize() * 200
                
                else:
                    if direcao_alvo_vec.length() > 0:
                        
                        self.timer_troca_orbita += 1
                        if self.timer_troca_orbita > self.duracao_orbita_atual:
                            self.timer_troca_orbita = 0 
                            self.direcao_orbita = -self.direcao_orbita 
                            self.duracao_orbita_atual = random.randint(120, 300) 
                        
                        vetor_orbita = direcao_alvo_vec.rotate(75 * self.direcao_orbita).normalize() 
                        ponto_movimento = self.bot.posicao + vetor_orbita * 200
                
                self.bot.posicao_alvo_mouse = ponto_movimento
                return 
            
            except ValueError:
                self.estado_ia = "VAGANDO"

        if self.estado_ia == "VAGANDO":
            # Se HP < 80% (mas > 20%), para de andar para regenerar
            if self.bot.vida_atual < LIMITE_HP_REGENERAR_OBRIGATORIO:
                self.bot.posicao_alvo_mouse = None
            else:
                # HP alto: anda por aí
                chegou_perto = False
                if self.bot_wander_target:
                    try:
                        if self.bot.posicao.distance_to(self.bot_wander_target) < 100:
                            chegou_perto = True
                    except ValueError:
                        chegou_perto = True
                
                if self.bot_wander_target is None or chegou_perto:
                    map_margin = 100
                    # --- MODIFICAÇÃO: Usa self.map_width/height ---
                    target_x = random.randint(map_margin, self.map_width - map_margin)
                    target_y = random.randint(map_margin, self.map_height - map_margin)
                    self.bot_wander_target = pygame.math.Vector2(target_x, target_y)
                
                self.bot.posicao_alvo_mouse = self.bot_wander_target

    def resetar_ia(self):
        """ Chamado quando o bot morre/respawna. """
        self.bot.alvo_selecionado = None
        self.bot.posicao_alvo_mouse = None
        self.estado_ia = "VAGANDO"
        self.virando_aleatoriamente_timer = 0
        self.frames_sem_movimento = 0
        self.posicao_anterior = pygame.math.Vector2(0, 0)
        
        # --- LÓGICA DE ÓRBITA ALEATÓRIA (da correção anterior) ---
        self.direcao_orbita = 1
        self.timer_troca_orbita = 0
        self.duracao_orbita_atual = random.randint(120, 300)
        
        # --- INÍCIO DA CORREÇÃO (KITING) ---
        self.flee_destination = None # Reseta o ponto de fuga
        # --- FIM DA CORREÇÃO ---
# --- O HACK GLOBAL FOI REMOVIDO DAQUI ---