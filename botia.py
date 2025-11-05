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
        self.distancia_scan_inimigo = 600    # Distância para começar a ATACAR inimigos/obstáculos
        self.distancia_parar_ia = 250        # Distância de órbita ideal
        self.distancia_tiro_ia = 500         # Distância para atirar
        
        # Distância da borda para começar a evitar
        self.dist_borda_segura = 400
        
        # Sistema de detecção de "preso"
        self.posicao_anterior = pygame.math.Vector2(0, 0)
        self.frames_sem_movimento = 0

    def update_ai(self, player_ref, grupo_bots_ref, grupo_inimigos_ref, grupo_obstaculos_ref, grupo_vidas_ref):
        """ 
        O "tick" principal do cérebro da IA. 
        Chamado a cada frame pelo NaveBot.
        """
        
        # Detecção de bot preso
        if self.bot.posicao.distance_to(self.posicao_anterior) < 3:
            self.frames_sem_movimento += 1
            if self.frames_sem_movimento > 30:  # Preso por 0.5 segundos
                # Se está preso E perto da borda, força ir pro centro
                if (self.bot.posicao.x < self.dist_borda_segura * 1.5 or 
                    self.bot.posicao.x > MAP_WIDTH - self.dist_borda_segura * 1.5 or
                    self.bot.posicao.y < self.dist_borda_segura * 1.5 or 
                    self.bot.posicao.y > MAP_HEIGHT - self.dist_borda_segura * 1.5):
                    # Aponta DIRETO pro centro sem sutileza
                    centro = pygame.math.Vector2(MAP_WIDTH / 2, MAP_HEIGHT / 2)
                    direcao_centro = centro - self.bot.posicao
                    self.bot.angulo = pygame.math.Vector2(0, -1).angle_to(direcao_centro)
                    print(f"[{self.bot.nome}] PRESO NA BORDA! Forçando rotação direta pro centro.")
                else:
                    # Preso em outro lugar, rotação aleatória
                    self.bot.angulo += random.randint(90, 180)
                    print(f"[{self.bot.nome}] Detectado como preso! Forçando rotação.")
                self.frames_sem_movimento = 0
        else:
            self.frames_sem_movimento = 0
        self.posicao_anterior = self.bot.posicao.copy()
        
        # 1. Encontrar um novo alvo se o atual for inválido ou se estivermos "livres"
        if (self.alvo_atual is None or not self.alvo_atual.groups()) and self.estado_ia not in ["EVITANDO_BORDA"]:
            lista_alvos_naves = [player_ref] + list(grupo_bots_ref.sprites())
            self._encontrar_alvo(grupo_inimigos_ref, grupo_obstaculos_ref, lista_alvos_naves, grupo_vidas_ref)
        
        # 2. Processar o estado atual (VAGANDO, ATACANDO, FUGINDO, etc.)
        self._processar_input_ia()


    def _encontrar_alvo(self, grupo_inimigos, grupo_obstaculos, lista_alvos_naves, grupo_vidas):
        """ 
        Encontra o alvo mais próximo válido com base na prioridade.
        
        PRIORIDADE DE ALVOS:
        1. Buscar vida se HP baixo
        2. Inimigos (mais próximos)
        3. Obstáculos (mais próximos)
        4. Outras naves (player/bots) se nada mais disponível
        """
        
        self.alvo_atual = None
        alvo_final = None
        dist_min = float('inf')
        
        LIMITE_HP_BUSCAR_VIDA = self.bot.max_vida * 0.40 # Começa a procurar vida com 40%
        
        # --- LÓGICA DE BUSCA DE ALVO ---

        # 1. Prioridade Máxima: Buscar Vida se a vida estiver baixa
        if self.bot.vida_atual <= LIMITE_HP_BUSCAR_VIDA:
            for vida in grupo_vidas:
                if not vida.groups(): continue
                try:
                    dist = self.bot.posicao.distance_to(vida.posicao)
                    if dist < self.distancia_scan_geral and dist < dist_min:
                        dist_min = dist
                        alvo_final = vida
                except (ValueError, AttributeError):
                    continue
            
            if alvo_final:
                self.alvo_atual = alvo_final
                self.estado_ia = "COLETANDO"
                print(f"[{self.bot.nome}] HP BAIXO! Buscando vida.")
                return # Encontrou vida, é a única prioridade

        # 2. Segunda Prioridade: INIMIGOS
        dist_min = float('inf')
        alvo_final = None
        
        for inimigo in grupo_inimigos:
            if not inimigo.groups():
                continue
            
            try:
                dist = self.bot.posicao.distance_to(inimigo.posicao)
                
                if dist < dist_min and dist < self.distancia_scan_geral:
                    dist_min = dist
                    alvo_final = inimigo
            except (ValueError, AttributeError):
                continue
        
        # Se encontrou um inimigo, prioriza ele
        if alvo_final:
            self.alvo_atual = alvo_final
            if dist_min < self.distancia_scan_inimigo:
                self.estado_ia = "ATACANDO"
                print(f"[{self.bot.nome}] ATACANDO inimigo a {int(dist_min)}px")
            else:
                self.estado_ia = "CAÇANDO"
                print(f"[{self.bot.nome}] CAÇANDO inimigo a {int(dist_min)}px")
            return

        # 3. Terceira Prioridade: OBSTÁCULOS
        dist_min = float('inf')
        alvo_final = None
        
        for obstaculo in grupo_obstaculos:
            if not obstaculo.groups():
                continue
            
            try:
                dist = self.bot.posicao.distance_to(obstaculo.posicao)
                
                if dist < dist_min and dist < self.distancia_scan_geral:
                    dist_min = dist
                    alvo_final = obstaculo
            except (ValueError, AttributeError):
                continue
        
        # Se encontrou um obstáculo, ataca ele
        if alvo_final:
            self.alvo_atual = alvo_final
            if dist_min < self.distancia_scan_inimigo:
                self.estado_ia = "ATACANDO"
                print(f"[{self.bot.nome}] ATACANDO obstáculo a {int(dist_min)}px")
            else:
                self.estado_ia = "CAÇANDO"
                print(f"[{self.bot.nome}] CAÇANDO obstáculo a {int(dist_min)}px")
            return

        # 4. Última Prioridade: Outras Naves (apenas se não há nada mais)
        dist_min = float('inf')
        alvo_final = None
        
        for alvo in lista_alvos_naves:
            # Pula alvos inválidos (ele mesmo, mortos, etc.)
            if alvo == self.bot or not alvo.groups():
                continue
            
            try:
                dist = self.bot.posicao.distance_to(alvo.posicao)
                
                # Se este alvo é o mais próximo até agora
                if dist < dist_min and dist < self.distancia_scan_geral:
                    dist_min = dist
                    alvo_final = alvo
            except (ValueError, AttributeError):
                continue

        # 5. Define o estado com base no alvo encontrado
        if alvo_final:
            self.alvo_atual = alvo_final
            # Se o alvo está dentro do alcance de ataque, ATACA.
            if dist_min < self.distancia_scan_inimigo:
                 self.estado_ia = "ATACANDO"
                 print(f"[{self.bot.nome}] ATACANDO nave a {int(dist_min)}px")
            else:
                 # Se estiver fora (mas visível), CAÇA.
                 self.estado_ia = "CAÇANDO"
                 print(f"[{self.bot.nome}] CAÇANDO nave a {int(dist_min)}px")
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
        margem_histerese = 50
        
        # --- INÍCIO DA ÁRVORE DE DECISÃO (PRIORIDADES) ---

        # === PRIORIDADE 1: EVITAR A BORDA (AGRESSIVA) ===
        centro_mapa = pygame.math.Vector2(MAP_WIDTH / 2, MAP_HEIGHT / 2)
        
        # Define zonas com histerese maior
        zona_perigo = self.dist_borda_segura
        zona_segura_minima = self.dist_borda_segura + 200  # +200px para garantir saída
        
        # Verifica se está em zona de perigo
        em_zona_perigo = (
            self.bot.posicao.x < zona_perigo or 
            self.bot.posicao.x > MAP_WIDTH - zona_perigo or
            self.bot.posicao.y < zona_perigo or 
            self.bot.posicao.y > MAP_HEIGHT - zona_perigo
        )
        
        # Verifica se está em zona segura
        em_zona_segura = (
            self.bot.posicao.x > zona_segura_minima and
            self.bot.posicao.x < MAP_WIDTH - zona_segura_minima and
            self.bot.posicao.y > zona_segura_minima and
            self.bot.posicao.y < MAP_HEIGHT - zona_segura_minima
        )
        
        # Entra no modo de evitar borda
        if em_zona_perigo and self.estado_ia != "EVITANDO_BORDA":
            self.estado_ia = "EVITANDO_BORDA"
            self.alvo_atual = None
        
        # Se já está evitando a borda, continua até estar em zona segura
        if self.estado_ia == "EVITANDO_BORDA":
            # Só sai desse estado quando estiver BEM dentro da zona segura
            if em_zona_segura:
                self.estado_ia = "VAGANDO"
                self.alvo_atual = None
                print(f"[{self.bot.nome}] Saiu da borda com segurança!")
            else:
                # Continua fugindo para o centro COM TOLERÂNCIA ALTA
                direcao_centro = centro_mapa - self.bot.posicao
                
                if direcao_centro.length() > 0:
                    angulo_para_centro = pygame.math.Vector2(0, -1).angle_to(direcao_centro.normalize())
                    diff_angulo = (angulo_para_centro - self.bot.angulo + 180) % 360 - 180
                    
                    # Tolerância MUITO maior - move mesmo não estando perfeitamente alinhado
                    if diff_angulo > 30:
                        self.bot.quer_virar_direita = True
                    elif diff_angulo < -30:
                        self.bot.quer_virar_esquerda = True
                    
                    # SEMPRE move para frente INDEPENDENTE do ângulo
                    self.bot.quer_mover_frente = True
                
                return  # Não faz mais nada neste frame


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
                        # Muito longe, aproxima-se direto
                        self.bot.quer_mover_frente = True
                    elif distancia_alvo < dist_orbita_desejada - 50: 
                        # Muito perto, recua
                        self.bot.quer_mover_tras = True 
                    else:
                        # Em alcance de órbita: "Strafe" (move de lado)
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

                    # Atira se estiver no alcance
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
        self.frames_sem_movimento = 0
        self.posicao_anterior = pygame.math.Vector2(0, 0)