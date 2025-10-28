# ships.py
import pygame
import math
import random
from settings import (AZUL_NAVE, PONTA_NAVE, VERDE_AUXILIAR, LARANJA_BOT, MAP_WIDTH, MAP_HEIGHT,
                      MAX_TARGET_LOCK_DISTANCE, CUSTO_BASE_MOTOR, MAX_NIVEL_MOTOR,
                      CUSTO_BASE_DANO, MAX_NIVEL_DANO, CUSTO_BASE_AUXILIAR,
                      CUSTO_BASE_MAX_VIDA, CUSTO_BASE_ESCUDO, MAX_NIVEL_ESCUDO,
                      REDUCAO_DANO_POR_NIVEL, DURACAO_FX_ESCUDO, COR_ESCUDO_FX,
                      RASTRO_MAX_PARTICULAS, RASTRO_DURACAO, RASTRO_TAMANHO_INICIAL, COR_RASTRO_MOTOR,
                      VERMELHO_VIDA_FUNDO, VERDE_VIDA)
# Importa classes necessárias
from projectiles import Projetil
from effects import Explosao
# REMOVED: from enemies import InimigoBase, ...
from entities import Obstaculo, VidaColetavel # Obstaculo is needed for bot's finding target logic

# Referência global para o grupo de explosões
grupo_explosoes_ref = None
def set_global_ship_references(explosions_group):
    global grupo_explosoes_ref
    grupo_explosoes_ref = explosions_group

# Nave Auxiliar
class NaveAuxiliar(pygame.sprite.Sprite):
    def __init__(self, owner_nave, offset_pos):
        super().__init__(); self.owner = owner_nave; self.offset_pos = offset_pos; self.tamanho = 15
        self.imagem_original = pygame.Surface((self.tamanho + 5, self.tamanho + 5), pygame.SRCALPHA)
        centro = (self.tamanho + 5) / 2; ponto_topo = (centro, centro - self.tamanho / 2); ponto_base_esq = (centro - self.tamanho / 2, centro + self.tamanho / 2); ponto_base_dir = (centro + self.tamanho / 2, centro + self.tamanho / 2)
        pygame.draw.polygon(self.imagem_original, VERDE_AUXILIAR, [ponto_topo, ponto_base_esq, ponto_base_dir])
        self.posicao = self.owner.posicao + self.offset_pos.rotate(-self.owner.angulo); self.rect = self.imagem_original.get_rect(center=self.posicao)
        self.angulo = self.owner.angulo; self.alvo_atual = None; self.distancia_tiro = 600; self.cooldown_tiro = 1000; self.ultimo_tiro_tempo = 0

    def update(self, lista_alvos, grupo_projeteis_destino, estado_jogo_atual, nave_player_ref):
        parar_ataque = (self.owner == nave_player_ref and estado_jogo_atual == "GAME_OVER")
        offset_rotacionado = self.offset_pos.rotate(-self.owner.angulo); posicao_alvo_seguir = self.owner.posicao + offset_rotacionado
        self.posicao = self.posicao.lerp(posicao_alvo_seguir, 0.1) # Movimento de seguir o dono
        
        self.alvo_atual = None # Reseta o alvo a cada frame

        if not parar_ataque:
            
            # --- INÍCIO DA CORREÇÃO (Revisada) ---
            alvo_nave_mais_proxima = None
            dist_min_nave = self.distancia_tiro # Distância máxima de tiro da auxiliar
            
            alvo_inimigo_mais_proximo = None
            dist_min_inimigo = self.distancia_tiro

            for alvo in lista_alvos:
                # 1. Pula alvos inválidos (próprio dono, morto, etc.)
                if alvo == self.owner or alvo is None or not alvo.groups(): 
                    continue
                    
                # 2. Pula Obstáculos e Vidas (não são alvos de tiro)
                if isinstance(alvo, (Obstaculo, VidaColetavel)):
                    continue

                # 3. Calcula a distância
                dist = self.posicao.distance_to(alvo.posicao)
                
                # 4. Verifica se é uma Nave (Player ou Bot) USANDO O NOME DA CLASSE
                #    (Necessário porque Nave/Player/NaveBot são definidos DEPOIS de NaveAuxiliar)
                is_nave_alvo = type(alvo).__name__ in ('Player', 'NaveBot')
                
                if is_nave_alvo:
                    if dist < dist_min_nave:
                        dist_min_nave = dist
                        alvo_nave_mais_proxima = alvo
                
                # 5. Se não for Nave, deve ser um Inimigo
                else:
                    if dist < dist_min_inimigo:
                        dist_min_inimigo = dist
                        alvo_inimigo_mais_proximo = alvo

            # 6. Define o alvo final baseado na prioridade
            if alvo_nave_mais_proxima:
                self.alvo_atual = alvo_nave_mais_proxima
            elif alvo_inimigo_mais_proximo:
                self.alvo_atual = alvo_inimigo_mais_proximo
            # --- FIM DA CORREÇÃO ---

            # Lógica de Mirar e Atirar (Original)
            if self.alvo_atual:
                try: 
                    direcao = (self.alvo_atual.posicao - self.posicao).normalize()
                    self.angulo = direcao.angle_to(pygame.math.Vector2(0, -1))
                except ValueError: 
                    self.angulo = self.owner.angulo # Se der erro, alinha com o dono
                
                # Atira se o cooldown permitir
                agora = pygame.time.get_ticks()
                if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
                    self.ultimo_tiro_tempo = agora
                    radianos = math.radians(self.angulo)
                    proj = Projetil(self.posicao.x, self.posicao.y, radianos, self.owner.nivel_dano)
                    grupo_projeteis_destino.add(proj)
            else:
                # Se não tem alvo, alinha com o dono
                self.angulo = self.owner.angulo
        
        else: # Se o jogo acabou (para o player)
            self.angulo = self.owner.angulo
        
        # Atualiza o rect da auxiliar
        self.rect.center = self.posicao
    def desenhar(self, surface, camera):
        imagem_rotacionada = pygame.transform.rotate(self.imagem_original, self.angulo); rect_desenho = imagem_rotacionada.get_rect(center = self.posicao)
        surface.blit(imagem_rotacionada, camera.apply(rect_desenho))

# Classe Base para Naves
class Nave(pygame.sprite.Sprite):
    POSICOES_AUXILIARES = [pygame.math.Vector2(-40, 20), pygame.math.Vector2(40, 20), pygame.math.Vector2(-50, -10), pygame.math.Vector2(50, -10)]
    def __init__(self, x, y, cor=AZUL_NAVE, nome="Nave"):
        # ... (init code remains the same) ...
        super().__init__()
        self.nome = nome; self.posicao = pygame.math.Vector2(x, y); self.largura_base = 30; self.altura = 30; self.cor = cor
        self.velocidade_rotacao = 5; self.angulo = 0.0; self.velocidade_movimento_base = 4
        tamanho_surface = max(self.largura_base, self.altura) + 10; self.imagem_original = pygame.Surface((tamanho_surface, tamanho_surface), pygame.SRCALPHA)
        centro_x = tamanho_surface / 2; centro_y = tamanho_surface / 2; ponto_topo = (centro_x, centro_y - self.altura / 2); ponto_base_esq = (centro_x - self.largura_base / 2, centro_y + self.altura / 2); ponto_base_dir = (centro_x + self.largura_base / 2, centro_y + self.altura / 2)
        pygame.draw.polygon(self.imagem_original, self.cor, [ponto_topo, ponto_base_esq, ponto_base_dir])
        ponta_largura = 4; ponta_altura = 8; pygame.draw.rect(self.imagem_original, PONTA_NAVE, (ponto_topo[0] - ponta_largura / 2, ponto_topo[1] - ponta_altura, ponta_largura, ponta_altura))
        self.image = self.imagem_original; self.rect = pygame.Rect(x, y, self.largura_base * 0.8, self.altura * 0.8); self.rect.center = self.posicao
        self.cooldown_tiro = 250; self.ultimo_tiro_tempo = 0; self.pontos = 0; self.nivel_motor = 1; self.nivel_dano = 1; self.nivel_max_vida = 1; self.nivel_escudo = 0
        self.max_vida = 4 + self.nivel_max_vida; self.vida_atual = self.max_vida; self.velocidade_movimento_base = 4 + self.nivel_motor
        self.quer_virar_esquerda = False; self.quer_virar_direita = False; self.quer_mover_frente = False; self.quer_mover_tras = False; self.quer_atirar = False
        self.alvo_selecionado = None; self.posicao_alvo_mouse = None; self.tempo_barra_visivel = 2000; self.ultimo_hit_tempo = 0
        self.mostrar_escudo_fx = False; self.angulo_impacto_rad_pygame = 0; self.tempo_escudo_fx = 0; self.rastro_particulas = []
        self.tempo_fim_lentidao = 0; self.lista_todas_auxiliares = []; self.grupo_auxiliares_ativos = pygame.sprite.Group()
        for pos in self.POSICOES_AUXILIARES: self.lista_todas_auxiliares.append(NaveAuxiliar(self, pos))

    def update(self, grupo_projeteis_destino, camera=None): pass
    def rotacionar(self):
        # ... (rotacionar code remains the same) ...
        angulo_alvo = None
        if self.alvo_selecionado:
            if not self.alvo_selecionado.groups(): self.alvo_selecionado = None
            elif self.posicao.distance_to(self.alvo_selecionado.posicao) > MAX_TARGET_LOCK_DISTANCE: self.alvo_selecionado = None
            else:
                try:
                    direcao_vetor = (self.alvo_selecionado.posicao - self.posicao)
                    if direcao_vetor.length() > 0: radianos = math.atan2(direcao_vetor.y, direcao_vetor.x); angulo_alvo = -math.degrees(radianos) - 90
                except ValueError: pass
        elif self.posicao_alvo_mouse:
            if self.posicao.distance_to(self.posicao_alvo_mouse) > 5.0:
                try:
                    direcao_vetor = (self.posicao_alvo_mouse - self.posicao)
                    if direcao_vetor.length() > 0: radianos = math.atan2(direcao_vetor.y, direcao_vetor.x); angulo_alvo = -math.degrees(radianos) - 90
                except ValueError: pass
        if angulo_alvo is not None: self.angulo = angulo_alvo
        elif self.quer_virar_esquerda: self.angulo += self.velocidade_rotacao
        elif self.quer_virar_direita: self.angulo -= self.velocidade_rotacao
        self.angulo %= 360
    def mover(self):
        # ... (mover code with clamping remains the same) ...
        agora = pygame.time.get_ticks(); velocidade_atual = self.velocidade_movimento_base
        if agora < self.tempo_fim_lentidao: velocidade_atual *= 0.4
        nova_pos = pygame.math.Vector2(self.posicao.x, self.posicao.y); movendo_frente = False
        if self.quer_mover_frente or self.quer_mover_tras:
            radianos = math.radians(self.angulo)
            if self.quer_mover_frente: nova_pos.x += -math.sin(radianos) * velocidade_atual; nova_pos.y += -math.cos(radianos) * velocidade_atual; movendo_frente = True
            if self.quer_mover_tras: nova_pos.x -= -math.sin(radianos) * velocidade_atual; nova_pos.y -= -math.cos(radianos) * velocidade_atual
        elif self.posicao_alvo_mouse:
            distancia = self.posicao.distance_to(self.posicao_alvo_mouse)
            if distancia > 5.0:
                try:
                    direcao = (self.posicao_alvo_mouse - self.posicao).normalize(); nova_pos = self.posicao + direcao * velocidade_atual; movendo_frente = True
                    if self.posicao.distance_to(self.posicao_alvo_mouse) < velocidade_atual: nova_pos = self.posicao_alvo_mouse; self.posicao_alvo_mouse = None
                except ValueError: nova_pos = self.posicao
            else: nova_pos = self.posicao_alvo_mouse; self.posicao_alvo_mouse = None
        meia_largura = self.largura_base / 2; meia_altura = self.altura / 2
        nova_pos.x = max(meia_largura, min(nova_pos.x, MAP_WIDTH - meia_largura)); nova_pos.y = max(meia_altura, min(nova_pos.y, MAP_HEIGHT - meia_altura))
        self.posicao = nova_pos; self.rect.center = self.posicao
        if self.nivel_motor == MAX_NIVEL_MOTOR and movendo_frente:
            agora = pygame.time.get_ticks(); radianos_oposto = math.radians(self.angulo + 180); offset_rastro = self.altura * 0.6
            pos_rastro_x = self.posicao.x + (-math.sin(radianos_oposto) * offset_rastro); pos_rastro_y = self.posicao.y + (-math.cos(radianos_oposto) * offset_rastro)
            self.rastro_particulas.append([pos_rastro_x, pos_rastro_y, agora])
            if len(self.rastro_particulas) > RASTRO_MAX_PARTICULAS: self.rastro_particulas.pop(0)
    def criar_projetil(self):
        # ... (criar_projetil code remains the same) ...
        radianos = math.radians(self.angulo); offset_ponta = self.altura / 2 + 10
        pos_x = self.posicao.x + (-math.sin(radianos) * offset_ponta); pos_y = self.posicao.y + (-math.cos(radianos) * offset_ponta)
        return Projetil(pos_x, pos_y, radianos, self.nivel_dano)
    def lidar_com_tiros(self, grupo_destino):
        # ... (lidar_com_tiros code remains the same) ...
        if self.quer_atirar or self.alvo_selecionado:
            agora = pygame.time.get_ticks()
            if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
                self.ultimo_tiro_tempo = agora; grupo_destino.add(self.criar_projetil())
    def foi_atingido(self, dano, estado_jogo_atual, proj_pos=None):
        # ... (foi_atingido code remains the same) ...
        if self.vida_atual <= 0 and estado_jogo_atual == "GAME_OVER": return False
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_hit_tempo < 150: return False
        reducao_percent = min(self.nivel_escudo * REDUCAO_DANO_POR_NIVEL, 75); dano_reduzido = max(1, int(dano * (1 - reducao_percent / 100.0)))
        vida_antes = self.vida_atual; self.vida_atual -= dano_reduzido; self.ultimo_hit_tempo = agora
        if vida_antes > 0:
            if self.nivel_escudo == MAX_NIVEL_ESCUDO:
                self.mostrar_escudo_fx = True; self.tempo_escudo_fx = agora
                if proj_pos:
                     vetor_para_origem = proj_pos - self.posicao
                     if vetor_para_origem.length() > 0: self.angulo_impacto_rad_pygame = math.atan2(vetor_para_origem.y, vetor_para_origem.x)
                     else: self.angulo_impacto_rad_pygame = math.radians(90 - self.angulo)
                else: self.angulo_impacto_rad_pygame = math.radians(90 - self.angulo)
        if self.vida_atual <= 0 and vida_antes > 0:
            print(f"[{self.nome}] MORREU!")
            if grupo_explosoes_ref is not None: explosao = Explosao(self.rect.center, self.altura // 2 + 10); grupo_explosoes_ref.add(explosao)
            return True
        return False
    def aplicar_lentidao(self, duracao_ms):
        # ... (aplicar_lentidao code remains the same) ...
        agora = pygame.time.get_ticks(); self.tempo_fim_lentidao = max(self.tempo_fim_lentidao, agora + duracao_ms)
        print(f"[{self.nome}] LENTIDÃO aplicada/estendida por {duracao_ms}ms!")
    def ganhar_pontos(self, quantidade): self.pontos += quantidade
    def comprar_auxiliar(self):
        num_ativos = len(self.grupo_auxiliares_ativos)
        if num_ativos < len(self.lista_todas_auxiliares):
            aux_para_adicionar = self.lista_todas_auxiliares[num_ativos]

            # --- INÍCIO DA CORREÇÃO ---
            # Calcula a posição ideal atual da auxiliar ANTES de adicioná-la
            offset_rotacionado = aux_para_adicionar.offset_pos.rotate(-self.angulo)
            posicao_correta_atual = self.posicao + offset_rotacionado
            # Define a posição da auxiliar IMEDIATAMENTE
            aux_para_adicionar.posicao = posicao_correta_atual
            aux_para_adicionar.rect.center = posicao_correta_atual # Atualiza o rect também
            aux_para_adicionar.angulo = self.angulo # Alinha o ângulo inicial
            # --- FIM DA CORREÇÃO ---

            self.grupo_auxiliares_ativos.add(aux_para_adicionar)
            print(f"[{self.nome}] Ativando auxiliar {num_ativos + 1}")
            return True # Compra bem-sucedida
        else:
            # print(f"[{self.nome}] Máximo de auxiliares atingido!") # Comentado para reduzir spam no console
            return False
    def comprar_upgrade(self, tipo):
        # ... (comprar_upgrade code remains the same) ...
        comprou = False
        if tipo == "motor":
            if self.nivel_motor < MAX_NIVEL_MOTOR:
                custo = CUSTO_BASE_MOTOR * self.nivel_motor
                if self.pontos >= custo: self.pontos -= custo; self.nivel_motor += 1; self.velocidade_movimento_base = 4 + self.nivel_motor; print(f"[{self.nome}] Motor comprado! Nível {self.nivel_motor}."); comprou = True
            else: print(f"[{self.nome}] Nível máximo de motor atingido!")
        elif tipo == "dano":
            if self.nivel_dano < MAX_NIVEL_DANO:
                custo = CUSTO_BASE_DANO * self.nivel_dano
                if self.pontos >= custo: self.pontos -= custo; self.nivel_dano += 1; print(f"[{self.nome}] Dano comprado! Nível {self.nivel_dano}."); comprou = True
            else: print(f"[{self.nome}] Nível máximo de dano atingido!")
        elif tipo == "auxiliar":
            num_ativos = len(self.grupo_auxiliares_ativos)
            if num_ativos < len(self.lista_todas_auxiliares):
                custo = CUSTO_BASE_AUXILIAR * (num_ativos + 1)
                if self.pontos >= custo:
                    if self.comprar_auxiliar(): self.pontos -= custo; comprou = True
            else: print(f"[{self.nome}] Nível máximo de auxiliares atingido!")
        elif tipo == "max_health":
            custo = CUSTO_BASE_MAX_VIDA * self.nivel_max_vida
            if self.pontos >= custo: self.pontos -= custo; self.nivel_max_vida += 1; self.max_vida = 4 + self.nivel_max_vida; self.vida_atual += 1; self.ultimo_hit_tempo = pygame.time.get_ticks(); print(f"[{self.nome}] Vida Máx. aumentada! Nível {self.nivel_max_vida}."); comprou = True
        elif tipo == "escudo":
            if self.nivel_escudo < MAX_NIVEL_ESCUDO:
                custo = CUSTO_BASE_ESCUDO * (self.nivel_escudo + 1)
                if self.pontos >= custo: self.pontos -= custo; self.nivel_escudo += 1; print(f"[{self.nome}] Escudo comprado! Nível {self.nivel_escudo}."); comprou = True
            else: print(f"[{self.nome}] Nível máximo de escudo atingido!")
        return comprou
    def coletar_vida(self, quantidade):
        # ... (coletar_vida code remains the same) ...
        if self.vida_atual < self.max_vida:
            self.vida_atual = min(self.max_vida, self.vida_atual + quantidade); self.ultimo_hit_tempo = pygame.time.get_ticks()
            print(f"[{self.nome}] Coletou vida! Vida: {self.vida_atual}/{self.max_vida}"); return True
        return False
    def desenhar(self, surface, camera):
        # ... (desenhar code remains the same) ...
        agora = pygame.time.get_ticks(); particulas_vivas = []
        for particula in self.rastro_particulas:
            pos_x, pos_y, tempo_criacao = particula; idade = agora - tempo_criacao
            if idade < RASTRO_DURACAO:
                particulas_vivas.append(particula); progresso = idade / RASTRO_DURACAO; tamanho_atual = max(1, int(RASTRO_TAMANHO_INICIAL * (1 - progresso)))
                alpha = int(200 * (1 - progresso)); cor_atual = (*COR_RASTRO_MOTOR, alpha)
                pos_tela_centro = camera.apply(pygame.Rect(pos_x, pos_y, 0, 0)).topleft; raio_desenho = tamanho_atual // 2
                temp_surf = pygame.Surface((tamanho_atual, tamanho_atual), pygame.SRCALPHA); pygame.draw.circle(temp_surf, cor_atual, (raio_desenho, raio_desenho), raio_desenho)
                surface.blit(temp_surf, (pos_tela_centro[0] - raio_desenho, pos_tela_centro[1] - raio_desenho))
        self.rastro_particulas = particulas_vivas
        self.image = pygame.transform.rotate(self.imagem_original, self.angulo); rect_desenho = self.image.get_rect(center = self.posicao)
        surface.blit(self.image, camera.apply(rect_desenho))
        if self.mostrar_escudo_fx:
            agora = pygame.time.get_ticks()
            if agora - self.tempo_escudo_fx < DURACAO_FX_ESCUDO:
                raio_escudo = self.altura * 0.8 + 10; largura_arco_rad = math.radians(90); cor_fx_com_alpha = COR_ESCUDO_FX
                angulo_inicio_pygame_rad = self.angulo_impacto_rad_pygame - (largura_arco_rad / 2); angulo_fim_pygame_rad = self.angulo_impacto_rad_pygame + (largura_arco_rad / 2)
                rect_escudo_mundo = pygame.Rect(0, 0, raio_escudo * 2, raio_escudo * 2); rect_escudo_mundo.center = self.posicao; rect_escudo_tela = camera.apply(rect_escudo_mundo)
                temp_surface = pygame.Surface(rect_escudo_tela.size, pygame.SRCALPHA)
                try: pygame.draw.arc(temp_surface, cor_fx_com_alpha, (0, 0, rect_escudo_tela.width, rect_escudo_tela.height), angulo_inicio_pygame_rad, angulo_fim_pygame_rad, width=3); surface.blit(temp_surface, rect_escudo_tela.topleft)
                except ValueError: pass
            else: self.mostrar_escudo_fx = False
    def desenhar_vida(self, surface, camera):
        # ... (desenhar_vida code remains the same) ...
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_hit_tempo < self.tempo_barra_visivel:
            LARGURA_BARRA = 40; ALTURA_BARRA = 5; OFFSET_Y = 30
            pos_x_mundo = self.posicao.x - LARGURA_BARRA / 2; pos_y_mundo = self.posicao.y - OFFSET_Y
            percentual = max(0, self.vida_atual / self.max_vida); largura_vida_atual = LARGURA_BARRA * percentual
            rect_fundo_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, LARGURA_BARRA, ALTURA_BARRA); rect_vida_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, largura_vida_atual, ALTURA_BARRA)
            pygame.draw.rect(surface, VERMELHO_VIDA_FUNDO, camera.apply(rect_fundo_mundo)); pygame.draw.rect(surface, VERDE_VIDA, camera.apply(rect_vida_mundo))

# --- Classe do Jogador ---
class Player(Nave):
    def __init__(self, x, y):
        super().__init__(x, y, cor=AZUL_NAVE, nome="Jogador")

    def update(self, grupo_projeteis_jogador, camera):
        self.processar_input_humano(camera); self.rotacionar(); self.mover(); self.lidar_com_tiros(grupo_projeteis_jogador)

    def processar_input_humano(self, camera):
        teclas = pygame.key.get_pressed()
        self.quer_virar_esquerda = teclas[pygame.K_a] or teclas[pygame.K_LEFT]; self.quer_virar_direita = teclas[pygame.K_d] or teclas[pygame.K_RIGHT]
        self.quer_mover_frente = teclas[pygame.K_w] or teclas[pygame.K_UP]; self.quer_mover_tras = teclas[pygame.K_s] or teclas[pygame.K_DOWN]; self.quer_atirar = teclas[pygame.K_SPACE]
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[2]:
            mouse_pos_tela = pygame.mouse.get_pos(); camera_world_topleft = (-camera.camera_rect.left, -camera.camera_rect.top)
            mouse_pos_mundo = pygame.math.Vector2(mouse_pos_tela[0] + camera_world_topleft[0], mouse_pos_tela[1] + camera_world_topleft[1])
            self.posicao_alvo_mouse = mouse_pos_mundo; self.quer_mover_frente = False; self.quer_mover_tras = False
        if self.quer_mover_frente or self.quer_mover_tras: self.posicao_alvo_mouse = None


# --- Classe do Bot Aliado ---
class NaveBot(Nave):
    def __init__(self, x, y):
        # ... (init code remains the same, including random upgrades) ...
        super().__init__(x, y, cor=LARANJA_BOT, nome=f"Bot {random.randint(1, 99)}")
        self.alvo_atual = None; self.virando_aleatoriamente_timer = 0; self.direcao_virada_aleatoria = "direita"; self.distancia_borda_virar = 100
        self.distancia_scan = 800; self.distancia_scan_inimigo = 600; self.distancia_scan_obstaculo = 800
        self.distancia_parar_ia = 300; self.distancia_tiro_ia = 500
        self.estado_ia = "VAGANDO"; self.angulo_alvo_borda = 0
        print(f"[{self.nome}] Gerando upgrades aleatórios...")
        self.nivel_motor = random.randint(1, MAX_NIVEL_MOTOR); self.velocidade_movimento_base = 4 + self.nivel_motor
        if self.nivel_motor > 1: print(f"  -> Spawn com Motor Nv. {self.nivel_motor}")
        self.nivel_dano = random.randint(1, MAX_NIVEL_DANO)
        if self.nivel_dano > 1: print(f"  -> Spawn com Dano Nv. {self.nivel_dano}")
        self.nivel_escudo = random.randint(0, MAX_NIVEL_ESCUDO)
        if self.nivel_escudo > 0: print(f"  -> Spawn com Escudo Nv. {self.nivel_escudo}")
        max_spawn_vida_lvl = 3; self.nivel_max_vida = random.randint(1, max_spawn_vida_lvl); self.max_vida = 4 + self.nivel_max_vida; self.vida_atual = self.max_vida
        if self.nivel_max_vida > 1: print(f"  -> Spawn com Vida Máx. Nv. {self.nivel_max_vida} ({self.max_vida} HP)")
        max_aux = len(self.lista_todas_auxiliares); num_auxiliares = random.randint(0, max_aux)
        if num_auxiliares > 0:
            print(f"  -> Spawn com {num_auxiliares} Auxiliares.")
            for _ in range(num_auxiliares): self.comprar_auxiliar()

    def foi_atingido(self, dano, estado_jogo_atual, proj_pos=None):
        # ... (foi_atingido code remains the same) ...
        vida_antes = self.vida_atual; morreu = super().foi_atingido(dano, estado_jogo_atual, proj_pos)
        if morreu:
            print(f"[{self.nome}] BOT MORREU! Resetando...")
            self.posicao = pygame.math.Vector2(MAP_WIDTH // 2, MAP_HEIGHT // 2); self.rect.center = self.posicao
            self.grupo_auxiliares_ativos.empty(); self.pontos = 0; self.nivel_motor = 1; self.nivel_dano = 1; self.nivel_max_vida = 1; self.nivel_escudo = 0
            self.velocidade_movimento_base = 4 + self.nivel_motor; self.max_vida = 4 + self.nivel_max_vida; self.vida_atual = self.max_vida
            self.alvo_selecionado = None; self.posicao_alvo_mouse = None; self.tempo_fim_lentidao = 0; self.rastro_particulas = []
            print(f"[{self.nome}] Resetando estado da IA para VAGANDO.")
            self.estado_ia = "VAGANDO"; self.alvo_atual = None; self.virando_aleatoriamente_timer = 0; self.angulo_alvo_borda = 0
            print(f"[{self.nome}] Readicionando auxiliar padrão."); self.comprar_auxiliar()
        return morreu
    def mover(self):
        # ... (mover code with wrap-around remains the same) ...
        agora = pygame.time.get_ticks(); velocidade_atual = self.velocidade_movimento_base
        if agora < self.tempo_fim_lentidao: velocidade_atual *= 0.4
        nova_pos = pygame.math.Vector2(self.posicao.x, self.posicao.y); movendo_frente = False
        radianos = math.radians(self.angulo)
        if self.quer_mover_frente: nova_pos.x += -math.sin(radianos) * velocidade_atual; nova_pos.y += -math.cos(radianos) * velocidade_atual; movendo_frente = True
        if self.quer_mover_tras: nova_pos.x -= -math.sin(radianos) * velocidade_atual; nova_pos.y -= -math.cos(radianos) * velocidade_atual
        meia_largura = self.largura_base / 2; meia_altura = self.altura / 2
        if nova_pos.x > MAP_WIDTH + meia_largura: nova_pos.x = -meia_largura
        elif nova_pos.x < -meia_largura: nova_pos.x = MAP_WIDTH + meia_largura
        if nova_pos.y > MAP_HEIGHT + meia_altura: nova_pos.y = -meia_altura
        elif nova_pos.y < -meia_altura: nova_pos.y = MAP_HEIGHT + meia_altura
        self.posicao = nova_pos; self.rect.center = self.posicao
        if self.nivel_motor == MAX_NIVEL_MOTOR and movendo_frente:
            agora = pygame.time.get_ticks(); radianos_oposto = math.radians(self.angulo + 180); offset_rastro = self.altura * 0.6
            pos_rastro_x = self.posicao.x + (-math.sin(radianos_oposto) * offset_rastro); pos_rastro_y = self.posicao.y + (-math.cos(radianos_oposto) * offset_rastro)
            self.rastro_particulas.append([pos_rastro_x, pos_rastro_y, agora])
            if len(self.rastro_particulas) > RASTRO_MAX_PARTICULAS: self.rastro_particulas.pop(0)

    def update(self, player_ref, grupo_projeteis_bots, grupo_bots_ref, grupo_inimigos_ref, grupo_obstaculos_ref):
        if self.estado_ia != "EVITANDO_BORDA" and (self.alvo_atual is None or not self.alvo_atual.groups()):
            # --- INÍCIO CORREÇÃO 1.1 ---
            # Cria a lista de alvos naves (Player + outros Bots)
            lista_alvos_naves = [player_ref] + list(grupo_bots_ref.sprites())
            self.encontrar_alvo(grupo_inimigos_ref, grupo_obstaculos_ref, lista_alvos_naves)
            # --- FIM CORREÇÃO 1.1 ---
        self.processar_input_ia(); self.rotacionar(); self.mover(); self.lidar_com_tiros(grupo_projeteis_bots); self.processar_upgrades_ia()

    def encontrar_alvo(self, grupo_inimigos, grupo_obstaculos, lista_alvos_naves):
        self.alvo_atual = None
        dist_min = float('inf')
        
        # --- CORREÇÃO 1: Procura NAVES (Player e outros Bots) ---
        for nave_alvo in lista_alvos_naves:
            if nave_alvo == self or not nave_alvo.groups(): # Pula a si mesmo ou naves mortas
                continue
            dist = self.posicao.distance_to(nave_alvo.posicao)
            if dist < self.distancia_scan_inimigo and dist < dist_min: # Usa a distancia de inimigo
                dist_min = dist
                self.alvo_atual = nave_alvo
        
        if self.alvo_atual: 
            self.estado_ia = "ATACANDO"
            return
        # --- FIM CORREÇÃO 1 ---

        # --- CORREÇÃO 2: Procura INIMIGOS (Minions, Motherships, etc.) ---
        # (Resetamos dist_min para procurar o inimigo mais próximo,
        # caso nenhuma nave tenha sido encontrada)
        dist_min = float('inf') 
        for inimigo in grupo_inimigos:
            if not inimigo.groups(): 
                continue
            
            dist = self.posicao.distance_to(inimigo.posicao) # <-- Usa 'inimigo'
            if dist < self.distancia_scan_inimigo and dist < dist_min: # <-- Usa 'distancia_scan_inimigo'
                 dist_min = dist
                 self.alvo_atual = inimigo # <-- Usa 'inimigo'

        if self.alvo_atual: 
            self.estado_ia = "ATACANDO" # <-- Estado é ATACANDO
            return
        # --- FIM CORREÇÃO 2 ---

        # --- CORREÇÃO 3: Procura OBSTÁCULOS (Lógica que estava faltando) ---
        dist_min = float('inf') 
        for obst in grupo_obstaculos:
            if not obst.groups(): 
                continue
            dist = self.posicao.distance_to(obst.posicao)
            if dist < self.distancia_scan_obstaculo and dist < dist_min:
                 dist_min = dist
                 self.alvo_atual = obst
        
        if self.alvo_atual: 
            self.estado_ia = "COLETANDO" # <-- Estado para obstáculo é COLETANDO
            return
        # --- FIM CORREÇÃO 3 ---

        # Se não achou nada, vaga
        self.estado_ia = "VAGANDO"

    def processar_input_ia(self):
        # ... (processar_input_ia code) ...
        # --- MODIFICAÇÃO: Checa tipo por nome ---
        if self.estado_ia == "VAGANDO":
            if self.alvo_atual:
                 # Verifica se é um inimigo (não Obstáculo/Vida)
                 if type(self.alvo_atual).__name__ not in ['Obstaculo', 'VidaColetavel']:
                     self.estado_ia = "ATACANDO"
                 # Verifica se é Obstáculo
                 elif type(self.alvo_atual).__name__ == 'Obstaculo':
                     self.estado_ia = "COLETANDO" # Ou ATACANDO se quiser atirar
            # ... (resto da lógica de VAGANDO) ...
        # --- FIM MODIFICAÇÃO ---
        # (O resto da lógica de processar_input_ia permanece igual, pois já usa self.estado_ia)
        self.quer_virar_esquerda = False; self.quer_virar_direita = False; self.quer_mover_frente = False; self.quer_mover_tras = False; self.quer_atirar = False
        perto_da_borda = False; dist_reacao = self.distancia_borda_virar
        if self.posicao.x < dist_reacao: self.angulo_alvo_borda = -90; perto_da_borda = True
        elif self.posicao.x > MAP_WIDTH - dist_reacao: self.angulo_alvo_borda = 90; perto_da_borda = True
        if self.posicao.y < dist_reacao:
            if perto_da_borda and self.angulo_alvo_borda == -90: self.angulo_alvo_borda = -135
            elif perto_da_borda and self.angulo_alvo_borda == 90: self.angulo_alvo_borda = 135
            else: self.angulo_alvo_borda = 180
            perto_da_borda = True
        elif self.posicao.y > MAP_HEIGHT - dist_reacao:
            if perto_da_borda and self.angulo_alvo_borda == -90: self.angulo_alvo_borda = -45
            elif perto_da_borda and self.angulo_alvo_borda == 90: self.angulo_alvo_borda = 45
            else: self.angulo_alvo_borda = 0
            perto_da_borda = True
        if perto_da_borda and self.estado_ia != "EVITANDO_BORDA": self.estado_ia = "EVITANDO_BORDA"
        if self.estado_ia == "EVITANDO_BORDA":
            if not perto_da_borda: self.estado_ia = "VAGANDO"
            else:
                diff_angulo = (self.angulo_alvo_borda - self.angulo + 180) % 360 - 180
                if diff_angulo > 5: self.quer_virar_direita = True
                elif diff_angulo < -5: self.quer_virar_esquerda = True
                self.quer_mover_frente = True
        elif self.estado_ia == "ATACANDO":
            if self.alvo_atual is None or not self.alvo_atual.groups(): self.estado_ia = "VAGANDO"
            else:
                try: direcao_alvo_vec = (self.alvo_atual.posicao - self.posicao); distancia_alvo = direcao_alvo_vec.length(); angulo_alvo = pygame.math.Vector2(0, -1).angle_to(direcao_alvo_vec.normalize()) if distancia_alvo > 0 else self.angulo
                except ValueError: distancia_alvo = 0; angulo_alvo = self.angulo
                diff_angulo = (angulo_alvo - self.angulo + 180) % 360 - 180
                if diff_angulo > 5: self.quer_virar_direita = True
                elif diff_angulo < -5: self.quer_virar_esquerda = True
                if distancia_alvo > self.distancia_parar_ia: self.quer_mover_frente = True
                elif distancia_alvo < self.distancia_parar_ia - 50: self.quer_mover_tras = True
                if distancia_alvo < self.distancia_tiro_ia: self.quer_atirar = True
        elif self.estado_ia == "COLETANDO":
             if self.alvo_atual is None or not self.alvo_atual.groups(): self.estado_ia = "VAGANDO"
             else:
                 self.quer_mover_frente = True
                 try: direcao_alvo_vec = (self.alvo_atual.posicao - self.posicao); angulo_alvo = pygame.math.Vector2(0, -1).angle_to(direcao_alvo_vec.normalize()) if direcao_alvo_vec.length() > 0 else self.angulo
                 except ValueError: angulo_alvo = self.angulo
                 diff_angulo = (angulo_alvo - self.angulo + 180) % 360 - 180
                 if diff_angulo > 5: self.quer_virar_direita = True
                 elif diff_angulo < -5: self.quer_virar_esquerda = True
        elif self.estado_ia == "VAGANDO":
             # Correção aqui também
            if self.alvo_atual:
                 if type(self.alvo_atual).__name__ not in ['Obstaculo', 'VidaColetavel']: self.estado_ia = "ATACANDO"
                 elif type(self.alvo_atual).__name__ == 'Obstaculo': self.estado_ia = "COLETANDO"
            else: # Lógica de vagar
                self.quer_mover_frente = True
                if self.virando_aleatoriamente_timer > 0:
                    if self.direcao_virada_aleatoria == "esquerda": self.quer_virar_esquerda = True
                    else: self.quer_virar_direita = True
                    self.virando_aleatoriamente_timer -= 1
                elif random.random() < 0.01:
                    self.virando_aleatoriamente_timer = random.randint(30, 90); self.direcao_virada_aleatoria = random.choice(["esquerda", "direita"])

    def processar_upgrades_ia(self):
        # ... (processar_upgrades_ia code remains the same) ...
        if self.pontos >= CUSTO_BASE_MOTOR * self.nivel_motor and self.nivel_motor < MAX_NIVEL_MOTOR: self.comprar_upgrade("motor")
        elif self.pontos >= CUSTO_BASE_MAX_VIDA * self.nivel_max_vida: self.comprar_upgrade("max_health")
        elif self.pontos >= CUSTO_BASE_DANO * self.nivel_dano and self.nivel_dano < MAX_NIVEL_DANO: self.comprar_upgrade("dano")
        elif self.pontos >= CUSTO_BASE_ESCUDO * (self.nivel_escudo + 1) and self.nivel_escudo < MAX_NIVEL_ESCUDO : self.comprar_upgrade("escudo")