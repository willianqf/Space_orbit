import pygame
import random
# Importa as constantes do mapa
from settings import MAP_WIDTH, MAP_HEIGHT

class BotAI:
    def __init__(self, bot_nave):
        """\n        Inicializa o cérebro da IA.\n        'bot_nave' é a referência para a instância de NaveBot que este cérebro controla.\n        """
        self.bot = bot_nave 
        
        # Variáveis de estado da IA
        self.alvo_atual = None
        self.estado_ia = "VAGANDO"
        self.virando_aleatoriamente_timer = 0
        self.direcao_virada_aleatoria = "direita"
        self.direcao_orbita = 1  # 1 = horário, -1 = anti-horário
        
        # === CONSTANTES DE COMPORTAMENTO DA IA (OTIMIZADAS) ===
        self.distancia_scan_geral = 900          # Distância máxima para "ver" qualquer coisa
        self.distancia_scan_inimigo = 700        # Distância para começar a ATACAR inimigos/obstáculos
        self.distancia_parar_ia = 280            # Distância de órbita ideal (reduzida)
        self.distancia_tiro_ia = 650             # Distância para atirar (aumentada)
        
        # Distância da borda para começar a evitar
        self.dist_borda_segura = 300
        
        # Sistema de detecção de "preso" (MELHORADO)
        self.posicao_anterior = pygame.math.Vector2(0, 0)
        self.frames_sem_movimento = 0
        self.frames_sem_movimento_limite = 60  # Aumentado de 30 para 60 (1 segundo)

    def update_ai(self, player_ref, grupo_bots_ref, grupo_inimigos_ref, grupo_obstaculos_ref, grupo_vidas_ref):
        """ 
        O "tick" principal do cérebro da IA. 
        Chamado a cada frame pelo NaveBot.
        """
        
        # === DETECÇÃO DE BOT PRESO (MELHORADA) ===
        # Só detecta como "preso" se NÃO estiver em combate ativo
        em_combate = self.estado_ia in ["ATACANDO", "CAÇANDO"]
        
        if self.bot.posicao.distance_to(self.posicao_anterior) < 2:  # Reduzido de 3 para 2
            self.frames_sem_movimento += 1
            
            # Só age se realmente estiver preso POR MUITO TEMPO e NÃO em combate
            if self.frames_sem_movimento > self.frames_sem_movimento_limite and not em_combate:
                # Se está preso E perto da borda, força ir pro centro
                if (self.bot.posicao.x < self.dist_borda_segura * 1.5 or 
                    self.bot.posicao.x > MAP_WIDTH - self.dist_borda_segura * 1.5 or
                    self.bot.posicao.y < self.dist_borda_segura * 1.5 or 
                    self.bot.posicao.y > MAP_HEIGHT - self.dist_borda_segura * 1.5):
                    # Aponta DIRETO pro centro
                    centro = pygame.math.Vector2(MAP_WIDTH / 2, MAP_HEIGHT / 2)
                    direcao_centro = centro - self.bot.posicao
                    self.bot.angulo = pygame.math.Vector2(0, -1).angle_to(direcao_centro)
                    print(f"[{self.bot.nome}] PRESO NA BORDA! Forçando rotação direta pro centro.")
                else:
                    # Preso em outro lugar, rotação aleatória MAIOR
                    self.bot.angulo += random.randint(120, 240)  # Aumentado
                    print(f"[{self.bot.nome}] Detectado como preso! Forçando rotação de {120}-{240}°.")
                
                self.frames_sem_movimento = 0
                # Força movimento para sair do local
                self.bot.quer_mover_frente = True
        else:
            self.frames_sem_movimento = 0
        
        self.posicao_anterior = self.bot.posicao.copy()
        
        # 1. Encontrar um novo alvo se o atual for inválido
        if (self.alvo_atual is None or not self.alvo_atual.groups()) and self.estado_ia not in ["EVITANDO_BORDA"]:
            lista_alvos_naves = [player_ref] + list(grupo_bots_ref.sprites())
            self._encontrar_alvo(grupo_inimigos_ref, grupo_obstaculos_ref, lista_alvos_naves, grupo_vidas_ref)
        
        # 2. Processar o estado atual
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
        
        LIMITE_HP_BUSCAR_VIDA = self.bot.max_vida * 0.40
        
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
                return

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
        
        if alvo_final:
            self.alvo_atual = alvo_final
            # Define direção de órbita aleatória ao encontrar novo alvo
            self.direcao_orbita = random.choice([1, -1])
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
        
        if alvo_final:
            self.alvo_atual = alvo_final
            self.direcao_orbita = random.choice([1, -1])
            if dist_min < self.distancia_scan_inimigo:
                self.estado_ia = "ATACANDO"
                print(f"[{self.bot.nome}] ATACANDO obstáculo a {int(dist_min)}px")
            else:
                self.estado_ia = "CAÇANDO"
                print(f"[{self.bot.nome}] CAÇANDO obstáculo a {int(dist_min)}px")
            return

        # 4. Última Prioridade: Outras Naves
        dist_min = float('inf')
        alvo_final = None
        
        for alvo in lista_alvos_naves:
            if alvo == self.bot or not alvo.groups():
                continue
            
            try:
                dist = self.bot.posicao.distance_to(alvo.posicao)
                
                if dist < dist_min and dist < self.distancia_scan_geral:
                    dist_min = dist
                    alvo_final = alvo
            except (ValueError, AttributeError):
                continue

        if alvo_final:
            self.alvo_atual = alvo_final
            self.direcao_orbita = random.choice([1, -1])
            if dist_min < self.distancia_scan_inimigo:
                 self.estado_ia = "ATACANDO"
                 print(f"[{self.bot.nome}] ATACANDO nave a {int(dist_min)}px")
            else:
                 self.estado_ia = "CAÇANDO"
                 print(f"[{self.bot.nome}] CAÇANDO nave a {int(dist_min)}px")
        else:
            self.alvo_atual = None
            self.estado_ia = "VAGANDO"

    def _processar_input_ia(self):
        """ 
        Define as intenções do bot com base em uma ÁRVORE DE PRIORIDADE.
        """
        
        # 1. Reseta as intenções
        self.bot.quer_virar_esquerda = False
        self.bot.quer_virar_direita = False
        self.bot.quer_mover_frente = False
        self.bot.quer_mover_tras = False
        self.bot.quer_atirar = False

        # 2. Constantes
        LIMITE_HP_FUGIR = self.bot.max_vida * 0.15
        
        # --- ÁRVORE DE DECISÃO ---

        # === PRIORIDADE 1: EVITAR A BORDA ===
        centro_mapa = pygame.math.Vector2(MAP_WIDTH / 2, MAP_HEIGHT / 2)
        
        zona_perigo = self.dist_borda_segura
        zona_segura_minima = self.dist_borda_segura + 150
        
        em_zona_perigo = (
            self.bot.posicao.x < zona_perigo or 
            self.bot.posicao.x > MAP_WIDTH - zona_perigo or
            self.bot.posicao.y < zona_perigo or 
            self.bot.posicao.y > MAP_HEIGHT - zona_perigo
        )
        
        em_zona_segura = (
            self.bot.posicao.x > zona_segura_minima and
            self.bot.posicao.x < MAP_WIDTH - zona_segura_minima and
            self.bot.posicao.y > zona_segura_minima and
            self.bot.posicao.y < MAP_HEIGHT - zona_segura_minima
        )
        
        # Só entra no modo de evitar borda se NÃO estiver atacando
        if em_zona_perigo and self.estado_ia not in ["EVITANDO_BORDA", "ATACANDO"]:
            self.estado_ia = "EVITANDO_BORDA"
            self.alvo_atual = None
        
        if self.estado_ia == "EVITANDO_BORDA":
            if em_zona_segura:
                self.estado_ia = "VAGANDO"
                self.alvo_atual = None
                print(f"[{self.bot.nome}] Saiu da borda com segurança!")
            else:
                direcao_centro = centro_mapa - self.bot.posicao
                
                if direcao_centro.length() > 0:
                    angulo_para_centro = pygame.math.Vector2(0, -1).angle_to(direcao_centro.normalize())
                    diff_angulo = (angulo_para_centro - self.bot.angulo + 180) % 360 - 180
                    
                    if diff_angulo > 45:
                        self.bot.quer_virar_direita = True
                    elif diff_angulo < -45:
                        self.bot.quer_virar_esquerda = True
                    
                    self.bot.quer_mover_frente = True
                
                return

        # === PRIORIDADE 2: FUGIR ===
        is_alvo_ameaca = self.alvo_atual and type(self.alvo_atual).__name__ not in ['Obstaculo', 'VidaColetavel']
        
        if (self.bot.vida_atual <= LIMITE_HP_FUGIR and is_alvo_ameaca) or self.estado_ia == "FUGINDO":
            self.estado_ia = "FUGINDO"
            
            if not (self.alvo_atual and self.alvo_atual.groups()):
                self.estado_ia = "BUSCANDO_VIDA"
                self.alvo_atual = None
                return 
            
            try:
                direcao_alvo_vec = (self.alvo_atual.posicao - self.bot.posicao)
                distancia_alvo = direcao_alvo_vec.length()
                
                if distancia_alvo > self.distancia_scan_inimigo:
                    self.estado_ia = "BUSCANDO_VIDA"
                    self.alvo_atual = None
                    return

                angulo_fuga = pygame.math.Vector2(0, -1).angle_to(-direcao_alvo_vec.normalize())
                diff_angulo = (angulo_fuga - self.bot.angulo + 180) % 360 - 180
                
                if diff_angulo > 5: self.bot.quer_virar_direita = True
                elif diff_angulo < -5: self.bot.quer_virar_esquerda = True
                
                self.bot.quer_mover_frente = True
                self.bot.quer_atirar = True
                return
                
            except ValueError:
                self.estado_ia = "VAGANDO" 
                return

        # === PRIORIDADE 3: COLETAR VIDA ===
        if self.estado_ia == "COLETANDO": 
            if not (self.alvo_atual and self.alvo_atual.groups()):
                self.estado_ia = "VAGANDO"
            else:
                try:
                    direcao_alvo_vec = (self.alvo_atual.posicao - self.bot.posicao)
                    angulo_alvo = pygame.math.Vector2(0, -1).angle_to(direcao_alvo_vec.normalize())
                    diff_angulo = (angulo_alvo - self.bot.angulo + 180) % 360 - 180
                    
                    if diff_angulo > 5: self.bot.quer_virar_direita = True
                    elif diff_angulo < -5: self.bot.quer_virar_esquerda = True
                    
                    self.bot.quer_mover_frente = True
                    self.bot.quer_atirar = False
                    return
                except ValueError:
                    self.estado_ia = "VAGANDO"

        # === PRIORIDADE 4: CAÇAR ===
        if self.estado_ia == "CAÇANDO":
            if not (self.alvo_atual and self.alvo_atual.groups()):
                self.estado_ia = "VAGANDO" 
            else:
                try:
                    direcao_alvo_vec = (self.alvo_atual.posicao - self.bot.posicao)
                    distancia_alvo = direcao_alvo_vec.length()

                    if distancia_alvo < self.distancia_scan_inimigo:
                        self.estado_ia = "ATACANDO" 
                        return 

                    angulo_alvo = pygame.math.Vector2(0, -1).angle_to(direcao_alvo_vec.normalize())
                    diff_angulo = (angulo_alvo - self.bot.angulo + 180) % 360 - 180
                    
                    if diff_angulo > 10: self.bot.quer_virar_direita = True
                    elif diff_angulo < -10: self.bot.quer_virar_esquerda = True
                    
                    self.bot.quer_mover_frente = True
                    self.bot.quer_atirar = False 
                    return 
                except ValueError:
                    self.estado_ia = "VAGANDO"

        # === PRIORIDADE 5: ATACAR (ÓRBITA MELHORADA) ===
        if self.estado_ia == "ATACANDO":
            if not (self.alvo_atual and self.alvo_atual.groups()):
                self.estado_ia = "VAGANDO"
            else:
                try:
                    direcao_alvo_vec = (self.alvo_atual.posicao - self.bot.posicao)
                    distancia_alvo = direcao_alvo_vec.length()
                    
                    if distancia_alvo > self.distancia_scan_inimigo:
                        self.estado_ia = "CAÇANDO"
                        return

                    # === NOVA LÓGICA DE ÓRBITA ===
                    angulo_para_alvo = pygame.math.Vector2(0, -1).angle_to(direcao_alvo_vec.normalize())
                    diff_angulo_mira = (angulo_para_alvo - self.bot.angulo + 180) % 360 - 180
                    
                    # Define o ângulo de órbita (perpendicular ao alvo)
                    # Adiciona 80° na direção escolhida (horário ou anti-horário)
                    angulo_orbita = angulo_para_alvo + (80 * self.direcao_orbita)
                    diff_angulo_orbita = (angulo_orbita - self.bot.angulo + 180) % 360 - 180
                    
                    dist_orbita_desejada = self.distancia_parar_ia;
                    
                    # Decisão de rotação: prioriza MIRA quando longe, ÓRBITA quando perto
                    if distancia_alvo > dist_orbita_desejada + 80:
                        # LONGE: Mira direto no alvo e aproxima
                        if diff_angulo_mira > 8:
                            self.bot.quer_virar_direita = True
                        elif diff_angulo_mira < -8:
                            self.bot.quer_virar_esquerda = True
                        self.bot.quer_mover_frente = True
                        
                    elif distancia_alvo < dist_orbita_desejada - 80:
                        # MUITO PERTO: Mira no alvo e recua
                        if diff_angulo_mira > 8:
                            self.bot.quer_virar_direita = True
                        elif diff_angulo_mira < -8:
                            self.bot.quer_virar_esquerda = True
                        self.bot.quer_mover_tras = True
                        
                    else:
                        # DISTÂNCIA IDEAL: Orbita ao redor do alvo
                        if diff_angulo_orbita > 10:
                            self.bot.quer_virar_direita = True
                        elif diff_angulo_orbita < -10:
                            self.bot.quer_virar_esquerda = True
                        
                        # Move para frente sempre (cria movimento de órbita)
                        self.bot.quer_mover_frente = True
                        
                        # Se a mira estiver muito ruim, para de orbitar e mira
                        if abs(diff_angulo_mira) > 60:
                            if diff_angulo_mira > 10:
                                self.bot.quer_virar_direita = True
                            elif diff_angulo_mira < -10:
                                self.bot.quer_virar_esquerda = True
                    
                    # Atira se estiver razoavelmente alinhado
                    mira_boa = abs(diff_angulo_mira) < 30
                    if distancia_alvo < self.distancia_tiro_ia and mira_boa:
                        self.bot.quer_atirar = True
                    
                    # Debug reduzido
                    if random.random() < 0.015:
                        estado_movimento = "APROXIMA" if distancia_alvo > dist_orbita_desejada + 80 else ("RECUA" if distancia_alvo < dist_orbita_desejada - 80 else "ORBITA")
                        print(f"[{self.bot.nome}] {estado_movimento}: dist={int(distancia_alvo)}px, "
                              f"mira={int(diff_angulo_mira)}°, atirar={self.bot.quer_atirar}")
                    
                    return 
                    
                except ValueError:
                    self.estado_ia = "VAGANDO"

        # === PRIORIDADE 6: VAGAR ===
        if self.estado_ia == "VAGANDO":
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
        print(f"[{self.bot.nome}] Resetando estado da IA para VAGANDO.")
        self.alvo_atual = None
        self.estado_ia = "VAGANDO"
        self.virando_aleatoriamente_timer = 0
        self.frames_sem_movimento = 0
        self.posicao_anterior = pygame.math.Vector2(0, 0)
        self.direcao_orbita = random.choice([1, -1])