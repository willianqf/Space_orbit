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
        self.alvo_atual = None
        self.estado_ia = "VAGANDO"
        self.virando_aleatoriamente_timer = 0
        self.direcao_virada_aleatoria = "direita"
        
        # Constantes de comportamento da IA
        self.distancia_scan_geral = 800      # Distância máxima para "ver" qualquer coisa
        self.distancia_scan_inimigo = 600    # Distância para começar a ATACAR
        self.distancia_parar_ia = 300
        self.distancia_tiro_ia = 500
        
        # Distância da borda para começar a evitar (aumentada para 300px)
        self.dist_borda_segura = 300 

    def update_ai(self, player_ref, grupo_bots_ref, grupo_inimigos_ref, grupo_obstaculos_ref, grupo_vidas_ref):
        """ 
        O "tick" principal do cérebro da IA. 
        Chamado a cada frame pelo NaveBot.
        """
        
        # 1. Encontrar um novo alvo se o atual for inválido ou se estivermos "livres"
        if (self.alvo_atual is None or not self.alvo_atual.groups()) and self.estado_ia not in ["EVITANDO_BORDA"]:
            lista_alvos_naves = [player_ref] + list(grupo_bots_ref.sprites())
            self._encontrar_alvo(grupo_inimigos_ref, grupo_obstaculos_ref, lista_alvos_naves, grupo_vidas_ref)
        
        # 2. Processar o estado atual (VAGANDO, ATACANDO, FUGINDO, etc.)
        self._processar_input_ia()


    def _encontrar_alvo(self, grupo_inimigos, grupo_obstaculos, lista_alvos_naves, grupo_vidas):
        """ 
        Encontra o alvo mais próximo válido com base na prioridade.
        """
        
        self.alvo_atual = None
        alvo_final = None
        dist_min = float('inf')
        
        LIMITE_HP_BUSCAR_VIDA = self.bot.max_vida * 0.40 # Começa a procurar vida com 40%
        
        # --- LÓGICA DE BUSCA DE ALVO CORRIGIDA ---

        # 1. Prioridade Máxima: Buscar Vida se a vida estiver baixa
        if self.bot.vida_atual <= LIMITE_HP_BUSCAR_VIDA:
            self.estado_ia = "BUSCANDO_VIDA"
            for vida in grupo_vidas:
                if not vida.groups(): continue
                dist = self.bot.posicao.distance_to(vida.posicao)
                if dist < self.distancia_scan_geral and dist < dist_min:
                    dist_min = dist
                    alvo_final = vida
            
            if alvo_final:
                self.alvo_atual = alvo_final
                self.estado_ia = "COLETANDO"
                return # Encontrou vida, é a única prioridade

        # 2. Se a vida está OK, procura por alvos para atacar (Naves, Inimigos, Obstáculos)
        # Lista de todos os grupos de alvos
        grupos_para_atacar = [lista_alvos_naves, grupo_inimigos, grupo_obstaculos]
        dist_min = float('inf') # Reseta a distância

        for grupo in grupos_para_atacar:
            for alvo in grupo:
                # Pula alvos inválidos (ele mesmo, mortos, etc.)
                if alvo == self.bot or not alvo.groups():
                    continue
                
                dist = self.bot.posicao.distance_to(alvo.posicao)
                
                # Se este alvo é o mais próximo até agora
                if dist < dist_min:
                    dist_min = dist
                    alvo_final = alvo

        # 3. Define o estado com base no alvo encontrado
        if alvo_final and dist_min <= self.distancia_scan_geral:
            self.alvo_atual = alvo_final
            # Se o alvo está dentro do alcance de ataque, ATACA.
            if dist_min < self.distancia_scan_inimigo:
                 self.estado_ia = "ATACANDO"
            else:
                 # Se estiver fora (mas visível), CAÇA.
                 self.estado_ia = "CAÇANDO"
        else:
            # Se não há alvos de forma alguma, VAGA.
            self.alvo_atual = None
            self.estado_ia = "VAGANDO"

    def _processar_input_ia(self):
        """ 
        Define as intenções do bot (quer_mover, quer_atirar, etc.) 
        com base em uma ÁRVORE DE PRIORIDADE.
        """
        
        # 1. Reseta as intenções (no bot)
        self.bot.quer_virar_esquerda = False
        self.bot.quer_virar_direita = False
        self.bot.quer_mover_frente = False
        self.bot.quer_mover_tras = False
        self.bot.quer_atirar = False

        # 2. Define constantes da IA
        LIMITE_HP_FUGIR = self.bot.max_vida * 0.15
        
        # --- INÍCIO DA ÁRVORE DE DECISÃO (PRIORIDADES) ---

        # === PRIORIDADE 1: EVITAR A BORDA ===
        # (Esta deve ser a PRIMEIRA verificação, acima de todas as outras)
        angulo_fuga_borda = None
        if self.bot.posicao.x < self.dist_borda_segura:
            angulo_fuga_borda = 90 # Vira para a Direita (Leste)
        elif self.bot.posicao.x > MAP_WIDTH - self.dist_borda_segura:
            angulo_fuga_borda = -90 # Vira para a Esquerda (Oeste)
        elif self.bot.posicao.y < self.dist_borda_segura:
            angulo_fuga_borda = 180 # Vira para Baixo (Sul)
        elif self.bot.posicao.y > MAP_HEIGHT - self.dist_borda_segura:
            angulo_fuga_borda = 0 # Vira para Cima (Norte)
        
        if angulo_fuga_borda is not None:
            self.estado_ia = "EVITANDO_BORDA"
            diff_angulo = (angulo_fuga_borda - self.bot.angulo + 180) % 360 - 180
            if diff_angulo > 5: self.bot.quer_virar_direita = True
            elif diff_angulo < -5: self.bot.quer_virar_esquerda = True
            
            self.bot.quer_mover_frente = True
            self.alvo_atual = None # Larga o alvo para focar em sair da borda
            return # FIM DA LÓGICA (NÃO FAZ MAIS NADA NESTE FRAME)
        
        elif self.estado_ia == "EVITANDO_BORDA":
            # Se não está mais perto da borda, volta a vagar e reavalia
            self.estado_ia = "VAGANDO"
            self.alvo_atual = None 
            # (Deixa o resto do código rodar para encontrar um novo alvo)


        # === PRIORIDADE 2: FUGIR ===
        is_alvo_ameaca = self.alvo_atual and type(self.alvo_atual).__name__ not in ['Obstaculo', 'VidaColetavel']
        
        if (self.bot.vida_atual <= LIMITE_HP_FUGIR and is_alvo_ameaca) or self.estado_ia == "FUGINDO":
            self.estado_ia = "FUGINDO" # Garante que o estado permaneça
            
            if not (self.alvo_atual and self.alvo_atual.groups()):
                self.estado_ia = "BUSCANDO_VIDA" # Ameaça desapareceu
                self.alvo_atual = None
                return 
            
            try:
                direcao_alvo_vec = (self.alvo_atual.posicao - self.bot.posicao)
                distancia_alvo = direcao_alvo_vec.length()
                
                if distancia_alvo > self.distancia_scan_inimigo: # Conseguiu fugir (600px)
                    self.estado_ia = "BUSCANDO_VIDA"
                    self.alvo_atual = None
                    return

                # Lógica de Fuga: Move para o lado OPOSTO do alvo
                angulo_fuga = pygame.math.Vector2(0, -1).angle_to(-direcao_alvo_vec.normalize())
                diff_angulo = (angulo_fuga - self.bot.angulo + 180) % 360 - 180
                
                if diff_angulo > 5: self.bot.quer_virar_direita = True
                elif diff_angulo < -5: self.bot.quer_virar_esquerda = True
                
                self.bot.quer_mover_frente = True # Move para frente (na direção oposta do alvo)
                self.bot.quer_atirar = True # Atira enquanto foge
                return # FIM DA LÓGICA DE FUGA
            
            except ValueError:
                self.estado_ia = "VAGANDO" 
                return

        # === PRIORIDADE 3: COLETAR VIDA ===
        if self.estado_ia == "COLETANDO": 
            if not (self.alvo_atual and self.alvo_atual.groups()):
                self.estado_ia = "VAGANDO" # Alvo de vida desapareceu
            else:
                try:
                    direcao_alvo_vec = (self.alvo_atual.posicao - self.bot.posicao)
                    angulo_alvo = pygame.math.Vector2(0, -1).angle_to(direcao_alvo_vec.normalize())
                    diff_angulo = (angulo_alvo - self.bot.angulo + 180) % 360 - 180
                    
                    if diff_angulo > 5: self.bot.quer_virar_direita = True
                    elif diff_angulo < -5: self.bot.quer_virar_esquerda = True
                    
                    self.bot.quer_mover_frente = True
                    self.bot.quer_atirar = False # Não atira na vida
                    return # FIM DA LÓGICA DE COLETAR VIDA
                except ValueError:
                    self.estado_ia = "VAGANDO"

        # === PRIORIDADE 4: CAÇAR (Movimento Natural) ===
        if self.estado_ia == "CAÇANDO":
            if not (self.alvo_atual and self.alvo_atual.groups()):
                self.estado_ia = "VAGANDO" 
            else:
                try:
                    direcao_alvo_vec = (self.alvo_atual.posicao - self.bot.posicao)
                    distancia_alvo = direcao_alvo_vec.length()

                    if distancia_alvo < self.distancia_scan_inimigo: # Entrou em alcance
                        self.estado_ia = "ATACANDO" 
                        return 

                    # Lógica de Caça: Move direto para o alvo
                    angulo_alvo = pygame.math.Vector2(0, -1).angle_to(direcao_alvo_vec.normalize())
                    diff_angulo = (angulo_alvo - self.bot.angulo + 180) % 360 - 180
                    
                    if diff_angulo > 10: self.bot.quer_virar_direita = True
                    elif diff_angulo < -10: self.bot.quer_virar_esquerda = True
                    
                    self.bot.quer_mover_frente = True
                    self.bot.quer_atirar = False 
                    return 
                except ValueError:
                    self.estado_ia = "VAGANDO"

        # === PRIORIDADE 5: ATACAR (Orbitar) ===
        if self.estado_ia == "ATACANDO":
            if not (self.alvo_atual and self.alvo_atual.groups()):
                self.estado_ia = "VAGANDO" # Alvo morreu
            else:
                try:
                    direcao_alvo_vec = (self.alvo_atual.posicao - self.bot.posicao)
                    distancia_alvo = direcao_alvo_vec.length()
                    
                    # Se o alvo fugiu para muito longe, volta a caçar
                    if distancia_alvo > self.distancia_scan_inimigo:
                        self.estado_ia = "CAÇANDO"
                        return

                    angulo_para_alvo = pygame.math.Vector2(0, -1).angle_to(direcao_alvo_vec.normalize())
                    
                    # Tática de Orbitar
                    dist_orbita_desejada = self.distancia_parar_ia 
                    angulo_movimento = angulo_para_alvo
                    
                    if distancia_alvo > dist_orbita_desejada + 50: 
                        self.bot.quer_mover_frente = True
                    elif distancia_alvo < dist_orbita_desejada - 50: 
                        self.bot.quer_mover_tras = True 
                    else:
                        # Em alcance de órbita: "Strafe"
                        angulo_movimento = (angulo_para_alvo + 75) 
                        self.bot.quer_mover_frente = True

                    # O bot sempre tenta mirar no alvo
                    diff_angulo_mira = (angulo_para_alvo - self.bot.angulo + 180) % 360 - 180
                    # Mas seu movimento pode ser para o lado
                    diff_angulo_mov = (angulo_movimento - self.bot.angulo + 180) % 360 - 180

                    # Tenta mirar
                    if diff_angulo_mira > 5: self.bot.quer_virar_direita = True
                    elif diff_angulo_mira < -5: self.bot.quer_virar_esquerda = True
                    
                    # Se não precisa virar para mirar, vira para mover (strafe)
                    if not (self.bot.quer_virar_direita or self.bot.quer_virar_esquerda):
                         if diff_angulo_mov > 5: self.bot.quer_virar_direita = True
                         elif diff_angulo_mov < -5: self.bot.quer_virar_esquerda = True

                    if distancia_alvo < self.distancia_tiro_ia:
                        self.bot.quer_atirar = True
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
            elif random.random() < 0.01: # 1% de chance por frame de virar
                self.virando_aleatoriamente_timer = random.randint(30, 90) # Vira por 0.5s a 1.5s
                self.direcao_virada_aleatoria = random.choice(["esquerda", "direita"])

    def resetar_ia(self):
        """ Chamado quando o bot morre/respawna. """
        print(f"[{self.bot.nome}] Resetando estado da IA para VAGANDO.")
        self.alvo_atual = None
        self.estado_ia = "VAGANDO"
        self.virando_aleatoriamente_timer = 0