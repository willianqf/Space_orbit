# botia.py
import pygame
import random
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

    def update_ai(self, player_ref, grupo_bots_ref, grupo_inimigos_ref, grupo_obstaculos_ref, grupo_vidas_ref):
        """ 
        O "tick" principal do cérebro da IA. 
        Chamado a cada frame pelo NaveBot.
        """
        
        # --- INÍCIO DA CORREÇÃO DO BUG ---
        # Salva a referência ao grupo de vidas para que _processar_input_ia possa usá-lo
        self.grupo_vidas_ref = grupo_vidas_ref
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
            # --- FIM DA CORREÇÃO DO BUG ---
                    if not vida.groups(): continue
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
            if alvo == self.bot or not alvo.groups(): continue
            try:
                dist = self.bot.posicao.distance_to(alvo.posicao)
                if dist < dist_min and dist < self.distancia_scan_geral:
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
        
        # Reseta intenções de movimento
        self.bot.quer_mover_frente = False
        self.bot.quer_mover_tras = False
        
        self.bot.posicao_alvo_mouse = None
        
        LIMITE_HP_FUGIR = self.bot.max_vida * 0.15
        
        # === PRIORIDADE 1: EVITAR A BORDA ===
        centro_mapa = pygame.math.Vector2(MAP_WIDTH / 2, MAP_HEIGHT / 2)
        zona_perigo = self.dist_borda_segura
        zona_segura_minima = self.dist_borda_segura + 200
        em_zona_perigo = (self.bot.posicao.x < zona_perigo or self.bot.posicao.x > MAP_WIDTH - zona_perigo or
                          self.bot.posicao.y < zona_perigo or self.bot.posicao.y > MAP_HEIGHT - zona_perigo)
        em_zona_segura = (self.bot.posicao.x > zona_segura_minima and self.bot.posicao.x < MAP_WIDTH - zona_segura_minima and
                          self.bot.posicao.y > zona_segura_minima and self.bot.posicao.y < MAP_HEIGHT - zona_segura_minima)
        
        if em_zona_perigo and self.estado_ia != "EVITANDO_BORDA":
            self.estado_ia = "EVITANDO_BORDA"
            self.bot.alvo_selecionado = None # Cancela a mira
        
        if self.estado_ia == "EVITANDO_BORDA":
            if em_zona_segura:
                self.estado_ia = "VAGANDO"
            else:
                self.bot.posicao_alvo_mouse = centro_mapa
            return

        # === PRIORIDADE 2: FUGIR ===
        is_alvo_ameaca = self.bot.alvo_selecionado and type(self.bot.alvo_selecionado).__name__ not in ['Obstaculo', 'VidaColetavel']
        if (self.bot.vida_atual <= LIMITE_HP_FUGIR and is_alvo_ameaca) or self.estado_ia == "FUGINDO":
            self.estado_ia = "FUGINDO" 
            alvo = self.bot.alvo_selecionado
            
            if not (alvo and alvo.groups()):
                self.estado_ia = "BUSCANDO_VIDA"; self.bot.alvo_selecionado = None; return 
            try:
                direcao_alvo_vec = (alvo.posicao - self.bot.posicao)
                distancia_alvo = direcao_alvo_vec.length()
                if distancia_alvo > self.distancia_scan_inimigo: 
                    self.estado_ia = "BUSCANDO_VIDA"; self.bot.alvo_selecionado = None; return

                if direcao_alvo_vec.length() > 0:
                    ponto_fuga = self.bot.posicao - direcao_alvo_vec.normalize() * 200
                    self.bot.posicao_alvo_mouse = ponto_fuga
                return
            except ValueError:
                self.estado_ia = "VAGANDO"; return

        # === PRIORIDADE 3: COLETAR VIDA ===
        if self.estado_ia == "COLETANDO": 
            vida_perto = None
            dist_min = self.distancia_scan_geral
            
            # --- INÍCIO DA CORREÇÃO DO BUG ---
            # Acessa o grupo de vidas através de 'self.' e verifica se não é None
            if self.grupo_vidas_ref:
                for vida in self.grupo_vidas_ref: 
            # --- FIM DA CORREÇÃO DO BUG ---
                     if not vida.groups(): continue
                     dist = self.bot.posicao.distance_to(vida.posicao)
                     if dist < dist_min:
                         dist_min = dist
                         vida_perto = vida
            
            if vida_perto:
                self.bot.posicao_alvo_mouse = vida_perto.posicao
            else:
                self.estado_ia = "VAGANDO" # Acabou a vida
            return

        # === PRIORIDADE 4: CAÇAR (Movimento Natural) ===
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

        # === PRIORIDADE 5: ATACAR (ÓRBITA COM MIRA TRAVADA) ===
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

        # === PRIORIDADE 6: VAGAR (Default) ===
        if self.estado_ia == "VAGANDO":
            self.bot.quer_mover_frente = True
            if self.virando_aleatoriamente_timer > 0:
                if self.direcao_virada_aleatoria == "esquerda": self.bot.quer_virar_esquerda = True
                else: self.bot.quer_virar_direita = True
                self.virando_aleatoriamente_timer -= 1
            elif random.random() < 0.01:
                self.virando_aleatoriamente_timer = random.randint(30, 90)
                self.direcao_virada_aleatoria = random.choice(["esquerda", "direita"])
        
        # --- O HACK GLOBAL FOI REMOVIDO DAQUI ---

    def resetar_ia(self):
        """ Chamado quando o bot morre/respawna. """
        self.bot.alvo_selecionado = None
        self.bot.posicao_alvo_mouse = None
        self.estado_ia = "VAGANDO"
        self.virando_aleatoriamente_timer = 0
        self.frames_sem_movimento = 0
        self.posicao_anterior = pygame.math.Vector2(0, 0)

# --- O HACK GLOBAL FOI REMOVIDO DAQUI ---