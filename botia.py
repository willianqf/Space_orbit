# botia.py
import pygame
import random
import math
# Importa as constantes do mapa
from settings import MAP_WIDTH, MAP_HEIGHT

class BotAI:
    def __init__(self, bot_nave):
        """
        Inicializa o cérebro da IA.
        'bot_nave' é a referência para a instância de NaveBot que este cérebro controla.
        """
        self.bot = bot_nave 
        
        # Variáveis de estado da IA
        self.estado_ia = "VAGANDO"
        self.virando_aleatoriamente_timer = 0
        self.direcao_virada_aleatoria = "direita"
        
        # Referência para o grupo de vidas (será atualizado a cada frame)
        self.grupo_vidas_ref = None # <--- ADICIONADO PARA CORRIGIR O BUG
        
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

    def update_ai(self, player_ref, grupo_bots_ref, grupo_inimigos_ref, grupo_obstaculos_ref, grupo_vidas_ref):
        """ 
        O "tick" principal do cérebro da IA. 
        Chamado a cada frame pelo NaveBot.
        """
        
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
                    self.bot.posicao.x > MAP_WIDTH - self.dist_borda_segura * 1.5 or
                    self.bot.posicao.y < self.dist_borda_segura * 1.5 or 
                    self.bot.posicao.y > MAP_HEIGHT - self.dist_borda_segura * 1.5):
                    centro = pygame.math.Vector2(MAP_WIDTH / 2, MAP_HEIGHT / 2)
                    direcao_centro = centro - self.bot.posicao
                    if direcao_centro.length() > 0:
                        self.bot.angulo = pygame.math.Vector2(0, -1).angle_to(direcao_centro)
                else:
                    self.bot.angulo += random.randint(90, 180)
                self.frames_sem_movimento = 0
        else:
            self.frames_sem_movimento = 0
        self.posicao_anterior = self.bot.posicao.copy()
        
        # 1. Encontrar um novo alvo se o atual for inválido
        #    (self.bot.alvo_selecionado é a "trava de mira" da Nave)
        if (self.bot.alvo_selecionado is None or not self.bot.alvo_selecionado.groups()) and self.estado_ia not in ["EVITANDO_BORDA"]:
            lista_alvos_naves = [player_ref] + list(grupo_bots_ref.sprites())
            self._encontrar_alvo(grupo_inimigos_ref, grupo_obstaculos_ref, lista_alvos_naves, grupo_vidas_ref)
        
        # 2. Processar o estado atual
        self._processar_input_ia()


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

        # 2. Segunda Prioridade: INIMIGOS
        dist_min = float('inf'); alvo_final = None       
        for inimigo in grupo_inimigos:
            if not inimigo.groups(): continue
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

        # 4. Última Prioridade: Outras Naves
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
        LIMITE_HP_REGENERAR_PERC = self.bot.max_vida * 0.8 # 80% (Threshold do VAGANDO)

        # === 2. PRIORIDADE 1: FUGIR / REGENERAR NA BORDA (Se HP < 20%) ===
        if self.bot.vida_atual <= LIMITE_HP_FUGIR:
            
            # Checa se está na borda
            zona_perigo = self.dist_borda_segura
            em_zona_perigo = (self.bot.posicao.x < zona_perigo or 
                              self.bot.posicao.x > MAP_WIDTH - zona_perigo or
                              self.bot.posicao.y < zona_perigo or 
                              self.bot.posicao.y > MAP_HEIGHT - zona_perigo)

            if em_zona_perigo:
                # 2A. PARAR NA BORDA E REGENERAR
                self.estado_ia = "REGENERANDO_NA_BORDA"
                self.bot.posicao_alvo_mouse = None
                self.bot.quer_mover_frente = False
                # (A lógica de encontrar alvo abaixo vai rodar, para atirar parado)
            
            else:
                # 2B. FUGIR (MOVENDO)
                self.estado_ia = "FUGINDO"
                
                # Tenta encontrar o inimigo mais próximo para fugir DELE
                alvo_ameacador_pos = None
                dist_min = float('inf')
                
                # Procura Inimigos
                if self.grupo_inimigos_ref_cache:
                    for inimigo in self.grupo_inimigos_ref_cache:
                        if not inimigo.groups(): continue
                        try:
                            dist = self.bot.posicao.distance_to(inimigo.posicao)
                            if dist < self.distancia_scan_geral and dist < dist_min:
                                dist_min = dist; alvo_ameacador_pos = inimigo.posicao
                        except (ValueError, AttributeError): continue
                
                # Procura Players/Bots
                if alvo_ameacador_pos is None:
                    lista_alvos_naves = [self.player_ref_cache] + list(self.grupo_bots_ref_cache.sprites())
                    for alvo in lista_alvos_naves:
                        if alvo == self.bot or not alvo.groups() or alvo.vida_atual <= 0: 
                            continue
                        try:
                            dist = self.bot.posicao.distance_to(alvo.posicao)
                            if dist < self.distancia_scan_geral and dist < dist_min:
                                dist_min = dist; alvo_ameacador_pos = alvo.posicao
                        except (ValueError, AttributeError): continue

                if alvo_ameacador_pos:
                    # Foge do alvo
                    vec_x = alvo_ameacador_pos.x - self.bot.posicao.x
                    vec_y = alvo_ameacador_pos.y - self.bot.posicao.y
                    dist_fuga = math.sqrt(vec_x**2 + vec_y**2) + 1e-6
                    ponto_fuga_x = self.bot.posicao.x - (vec_x / dist_fuga) * 500 # Foge 500px
                    ponto_fuga_y = self.bot.posicao.y - (vec_y / dist_fuga) * 500
                    self.bot.posicao_alvo_mouse = pygame.math.Vector2(ponto_fuga_x, ponto_fuga_y)
                else:
                    # Foge para o wander target (se não houver inimigos)
                    self.bot.posicao_alvo_mouse = self.bot_wander_target
            
            self.bot.alvo_selecionado = None # Limpa a mira (para de seguir)
            
        # === 3. PRIORIDADE 2: EVITAR A BORDA (Se HP ALTO) ===
        elif self.estado_ia != "EVITANDO_BORDA": # Só checa se não estiver FUGINDO
            centro_mapa = pygame.math.Vector2(MAP_WIDTH / 2, MAP_HEIGHT / 2)
            zona_perigo = self.dist_borda_segura
            em_zona_perigo = (self.bot.posicao.x < zona_perigo or self.bot.posicao.x > MAP_WIDTH - zona_perigo or
                              self.bot.posicao.y < zona_perigo or self.bot.posicao.y > MAP_HEIGHT - zona_perigo)
            
            if em_zona_perigo:
                self.estado_ia = "EVITANDO_BORDA"
                self.bot.alvo_selecionado = None # Cancela a mira
        
        if self.estado_ia == "EVITANDO_BORDA":
            zona_segura_minima = self.dist_borda_segura + 200
            em_zona_segura = (self.bot.posicao.x > zona_segura_minima and self.bot.posicao.x < MAP_WIDTH - zona_segura_minima and
                              self.bot.posicao.y > zona_segura_minima and self.bot.posicao.y < MAP_HEIGHT - zona_segura_minima)
            if em_zona_segura:
                self.estado_ia = "VAGANDO"
            else:
                centro_mapa = pygame.math.Vector2(MAP_WIDTH / 2, MAP_HEIGHT / 2)
                self.bot.posicao_alvo_mouse = centro_mapa
            return # EVITAR BORDA (com HP alto) tem prioridade sobre atacar

        # === 4. LÓGICA DE ALVO (Se não estiver FUGINDO/EVITANDO) ===
        if self.estado_ia not in ["FUGINDO", "REGENERANDO_NA_BORDA"]:
            # (Se HP baixo, _encontrar_alvo VAI para COLETANDO)
            if (self.bot.alvo_selecionado is None or not self.bot.alvo_selecionado.groups()):
                lista_alvos_naves = [self.player_ref_cache] + list(self.grupo_bots_ref_cache.sprites())
                self._encontrar_alvo(self.grupo_inimigos_ref_cache, self.grupo_obstaculos_ref_cache, lista_alvos_naves, self.grupo_vidas_ref)
        
        # === 5. PROCESSAR ESTADOS DE COMBATE/VAGANDO ===
        
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
                self.estado_ia = "VAGANDO" # Acabou a vida
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
                        vetor_orbita = direcao_alvo_vec.rotate(75).normalize()
                        ponto_movimento = self.bot.posicao + vetor_orbita * 200
                
                self.bot.posicao_alvo_mouse = ponto_movimento
                return 
            
            except ValueError:
                self.estado_ia = "VAGANDO"

        if self.estado_ia == "VAGANDO" or self.estado_ia == "REGENERANDO_NA_BORDA":
            
            # Se estiver regenerando (parado na borda) OU
            # Se estiver vagando E com HP baixo (tentando parar para regenerar)
            if self.estado_ia == "REGENERANDO_NA_BORDA" or \
               (self.estado_ia == "VAGANDO" and self.bot.vida_atual < LIMITE_HP_REGENERAR_PERC):
                
                # Fica parado (não seta 'posicao_alvo_mouse')
                # A lógica em NaveBot.update (ships.py) vai iniciar a regeneração.
                pass
            
            else:
                # Estado VAGANDO com HP alto
                # --- LÓGICA DE VAGAR (WANDER) ---
                chegou_perto = False
                if self.bot_wander_target:
                    try:
                        if self.bot.posicao.distance_to(self.bot_wander_target) < 100:
                            chegou_perto = True
                    except ValueError:
                        chegou_perto = True
                
                if self.bot_wander_target is None or chegou_perto:
                    map_margin = 100
                    target_x = random.randint(map_margin, MAP_WIDTH - map_margin)
                    target_y = random.randint(map_margin, MAP_HEIGHT - map_margin)
                    self.bot_wander_target = pygame.math.Vector2(target_x, target_y)
                
                self.bot.posicao_alvo_mouse = self.bot_wander_target
            
            # Se estiver regenerando ou com vida baixa, a IA não define
            # 'posicao_alvo_mouse', fazendo o bot parar (correto).

    def resetar_ia(self):
        """ Chamado quando o bot morre/respawna. """
        self.bot.alvo_selecionado = None
        self.bot.posicao_alvo_mouse = None
        self.estado_ia = "VAGANDO"
        self.virando_aleatoriamente_timer = 0
        self.frames_sem_movimento = 0
        self.posicao_anterior = pygame.math.Vector2(0, 0)

# --- O HACK GLOBAL FOI REMOVIDO DAQUI ---