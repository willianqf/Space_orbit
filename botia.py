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
        
        # self.grupo_vidas_ref = None # <-- REMOVIDO (Não precisamos mais)
        
        # Constantes de comportamento da IA
        self.distancia_scan_geral = 800
        self.distancia_scan_inimigo = 600
        
        self.distancia_orbita_max = 300
        self.distancia_orbita_min = 200
        
        self.distancia_tiro_ia = 500
        self.dist_borda_segura = 400
        
        self.posicao_anterior = pygame.math.Vector2(0, 0)
        self.frames_sem_movimento = 0

    # --- INÍCIO DA MODIFICAÇÃO (Assinatura da Função) ---
    def update_ai(self, player_ref, grupo_bots_ref, grupo_inimigos_ref, grupo_obstaculos_ref):
    # --- FIM DA MODIFICAÇÃO (grupo_vidas_ref removido) ---
        """ 
        O "tick" principal do cérebro da IA. 
        Chamado a cada frame pelo NaveBot.
        """
        
        # self.grupo_vidas_ref = grupo_vidas_ref # <-- REMOVIDO
        
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
        if (self.bot.alvo_selecionado is None or not self.bot.alvo_selecionado.groups()) and self.estado_ia not in ["EVITANDO_BORDA", "REGENERANDO"]:
            lista_alvos_naves = [player_ref] + list(grupo_bots_ref.sprites())
            # --- INÍCIO DA MODIFICAÇÃO (Chamada da Função) ---
            self._encontrar_alvo(grupo_inimigos_ref, grupo_obstaculos_ref, lista_alvos_naves)
            # --- FIM DA MODIFICAÇÃO ---
        
        # 2. Processar o estado atual
        self._processar_input_ia()


    # --- INÍCIO DA MODIFICAÇÃO (Assinatura da Função) ---
    def _encontrar_alvo(self, grupo_inimigos, grupo_obstaculos, lista_alvos_naves):
    # --- FIM DA MODIFICAÇÃO (grupo_vidas removido) ---
        """ 
        Encontra o alvo mais próximo válido e o define em self.bot.alvo_selecionado.
        """
        
        self.bot.alvo_selecionado = None
        alvo_final = None
        dist_min = float('inf')
        
        LIMITE_HP_BUSCAR_VIDA = self.bot.max_vida * 0.40
        
        # --- Bloco "Prioridade 1: Buscar Vida" REMOVIDO ---
        # (A regeneração agora é um ESTADO na Prioridade 2 de _processar_input_ia)

        # 2. Segunda Prioridade: INIMIGOS (Agora é a Prioridade 1)
        dist_min = float('inf'); alvo_final = None       
        for inimigo in grupo_inimigos:
            if not inimigo.groups(): continue
            try:
                dist = self.bot.posicao.distance_to(inimigo.posicao)
                if dist < dist_min and dist < self.distancia_scan_geral:
                    dist_min = dist; alvo_final = inimigo
            except (ValueError, AttributeError): continue
        
        if alvo_final:
            self.bot.alvo_selecionado = alvo_final
            if dist_min < self.distancia_scan_inimigo: self.estado_ia = "ATACANDO"
            else: self.estado_ia = "CAÇANDO"
            return 

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
            self.bot.alvo_selecionado = alvo_final
            if dist_min < self.distancia_scan_inimigo: self.estado_ia = "ATACANDO"
            else: self.estado_ia = "CAÇANDO"
            return 

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
            self.bot.alvo_selecionado = alvo_final
            if dist_min < self.distancia_scan_inimigo: self.estado_ia = "ATACANDO"
            else: self.estado_ia = "CAÇANDO"
        else:
            self.bot.alvo_selecionado = None
            self.estado_ia = "VAGANDO"

    def _processar_input_ia(self):
        """ 
        Define as intenções de movimento. A rotação agora é automática.
        """
        
        self.bot.quer_mover_frente = False
        self.bot.quer_mover_tras = False
        self.bot.posicao_alvo_mouse = None
        
        LIMITE_HP_FUGIR = self.bot.max_vida * 0.15
        LIMITE_HP_REGENERAR = self.bot.max_vida * 0.6 # Começa a pensar em regenerar com 60%
        
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
            self.bot.alvo_selecionado = None 
            self.bot.parar_regeneracao() # Para de regenerar se estiver perto da borda
        
        if self.estado_ia == "EVITANDO_BORDA":
            if em_zona_segura:
                self.estado_ia = "VAGANDO"
            else:
                self.bot.posicao_alvo_mouse = centro_mapa
            return

        # --- INÍCIO DA ADIÇÃO (Prioridade 2: Regenerar) ---
        # Se a vida está baixa E não há alvo E não está fugindo
        if (self.bot.vida_atual < LIMITE_HP_REGENERAR) and \
           (self.bot.alvo_selecionado is None) and \
           (self.estado_ia not in ["FUGINDO", "EVITANDO_BORDA"]):
            
            self.estado_ia = "REGENERANDO"
            
            # Para de vagar
            self.bot.quer_mover_frente = False
            self.bot.quer_virar_esquerda = False
            self.bot.quer_virar_direita = False
            
            # Tenta iniciar a regeneração (a função 'iniciar_regeneracao'
            # já verifica se está parado e com vida baixa)
            self.bot.iniciar_regeneracao(grupo_efeitos_visuais_global)
            return # Fica parado regenerando
        
        # Se estava regenerando mas um alvo apareceu (ou a vida encheu), para
        if self.estado_ia == "REGENERANDO":
            if self.bot.alvo_selecionado is not None or self.bot.vida_atual >= self.bot.max_vida:
                self.bot.parar_regeneracao()
                self.estado_ia = "VAGANDO" # Reavalia no próximo frame
        # --- FIM DA ADIÇÃO ---

        # === PRIORIDADE 3: FUGIR ===
        is_alvo_ameaca = self.bot.alvo_selecionado and type(self.bot.alvo_selecionado).__name__ not in ['Obstaculo']
        if (self.bot.vida_atual <= LIMITE_HP_FUGIR and is_alvo_ameaca) or self.estado_ia == "FUGINDO":
            self.estado_ia = "FUGINDO" 
            self.bot.parar_regeneracao() # Para de regenerar se precisar fugir
            alvo = self.bot.alvo_selecionado
            
            if not (alvo and alvo.groups()):
                self.estado_ia = "VAGANDO"; self.bot.alvo_selecionado = None; return 
            try:
                direcao_alvo_vec = (alvo.posicao - self.bot.posicao)
                distancia_alvo = direcao_alvo_vec.length()
                if distancia_alvo > self.distancia_scan_inimigo: 
                    self.estado_ia = "VAGANDO"; self.bot.alvo_selecionado = None; return

                if direcao_alvo_vec.length() > 0:
                    ponto_fuga = self.bot.posicao - direcao_alvo_vec.normalize() * 200
                    self.bot.posicao_alvo_mouse = ponto_fuga
                return
            except ValueError:
                self.estado_ia = "VAGANDO"; return

        # --- "PRIORIDADE COLETAR VIDA" REMOVIDA ---

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
            self.bot.parar_regeneracao() # Para de regenerar se for atacar
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
            # self.bot.alvo_selecionado já é None
            # Usa o movimento antigo (teclas) para vagar
            self.bot.quer_mover_frente = True
            if self.virando_aleatoriamente_timer > 0:
                if self.direcao_virada_aleatoria == "esquerda": self.bot.quer_virar_esquerda = True
                else: self.bot.quer_virar_direita = True
                self.virando_aleatoriamente_timer -= 1
            elif random.random() < 0.01:
                self.virando_aleatoriamente_timer = random.randint(30, 90)
                self.direcao_virada_aleatoria = random.choice(["esquerda", "direita"])

    def resetar_ia(self):
        """ Chamado quando o bot morre/respawna. """
        self.bot.alvo_selecionado = None
        self.bot.posicao_alvo_mouse = None
        self.estado_ia = "VAGANDO"
        self.virando_aleatoriamente_timer = 0
        self.frames_sem_movimento = 0
        self.posicao_anterior = pygame.math.Vector2(0, 0)

# --- INÍCIO DA ADIÇÃO (Referência Global) ---
# Hack para passar o grupo de efeitos para a IA do bot
grupo_efeitos_visuais_global = None
# --- FIM DA ADIÇÃO ---