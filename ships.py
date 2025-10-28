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
                      VERMELHO_VIDA_FUNDO, VERDE_VIDA) # <-- Adicionadas aqui
# Importa classes necessárias
from projectiles import Projetil
from effects import Explosao
# Importa classes de inimigos/entidades para checagem de tipo na IA e alvo
from enemies import InimigoBase, InimigoMinion, InimigoMothership
from entities import Obstaculo


# Referência global para o grupo de explosões (definido no main.py)
grupo_explosoes_ref = None
def set_global_ship_references(explosions_group):
    global grupo_explosoes_ref
    grupo_explosoes_ref = explosions_group

# Nave Auxiliar (Drones)
class NaveAuxiliar(pygame.sprite.Sprite):
    def __init__(self, owner_nave, offset_pos):
        super().__init__()
        self.owner = owner_nave # A Nave ou NaveBot a que pertence
        self.offset_pos = offset_pos # Posição relativa ao dono
        self.tamanho = 15

        # Cria a imagem original (triângulo verde)
        self.imagem_original = pygame.Surface((self.tamanho + 5, self.tamanho + 5), pygame.SRCALPHA)
        centro = (self.tamanho + 5) / 2
        ponto_topo = (centro, centro - self.tamanho / 2)
        ponto_base_esq = (centro - self.tamanho / 2, centro + self.tamanho / 2)
        ponto_base_dir = (centro + self.tamanho / 2, centro + self.tamanho / 2)
        pygame.draw.polygon(self.imagem_original, VERDE_AUXILIAR, [ponto_topo, ponto_base_esq, ponto_base_dir])

        # Posição inicial e rect
        self.posicao = self.owner.posicao + self.offset_pos.rotate(-self.owner.angulo) # Posição inicial correta
        self.rect = self.imagem_original.get_rect(center=self.posicao)

        # Atributos de combate
        self.angulo = self.owner.angulo
        self.alvo_atual = None
        self.distancia_tiro = 600
        self.cooldown_tiro = 1000 # ms
        self.ultimo_tiro_tempo = 0

    def update(self, lista_alvos, grupo_projeteis_destino, estado_jogo_atual, nave_player_ref):
        # Verifica se deve parar de atacar (se for do jogador e o jogo acabou)
        parar_ataque = (self.owner == nave_player_ref and estado_jogo_atual == "GAME_OVER")

        # --- Lógica de Seguir o Dono ---
        # Rotaciona o offset de acordo com o ângulo do dono
        offset_rotacionado = self.offset_pos.rotate(-self.owner.angulo)
        posicao_alvo_seguir = self.owner.posicao + offset_rotacionado
        # Interpola suavemente para a posição alvo
        self.posicao = self.posicao.lerp(posicao_alvo_seguir, 0.1)

        # --- Lógica de Mira e Tiro ---
        self.alvo_atual = None
        if not parar_ataque:
            dist_min = self.distancia_tiro
            for alvo in lista_alvos:
                # Não atirar no próprio dono ou em alvos inválidos
                if alvo == self.owner or alvo is None or not alvo.groups():
                    continue
                dist = self.posicao.distance_to(alvo.posicao)
                if dist < dist_min:
                    dist_min = dist
                    self.alvo_atual = alvo

            if self.alvo_atual:
                # Mira no alvo
                try:
                    direcao = (self.alvo_atual.posicao - self.posicao).normalize()
                    # Calcula ângulo em relação ao vetor (0, -1) (para cima)
                    self.angulo = direcao.angle_to(pygame.math.Vector2(0, -1))
                except ValueError:
                    self.angulo = self.owner.angulo # Mantém ângulo do dono se der erro

                # Atira se o cooldown permitir
                agora = pygame.time.get_ticks()
                if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
                    self.ultimo_tiro_tempo = agora
                    radianos = math.radians(self.angulo)
                    # Cria projétil usando o nível de dano do dono
                    proj = Projetil(self.posicao.x, self.posicao.y, radianos, self.owner.nivel_dano)
                    grupo_projeteis_destino.add(proj)
            else:
                # Se não tem alvo, alinha com o dono
                self.angulo = self.owner.angulo
        else:
             # Se ataque parado, alinha com o dono
             self.angulo = self.owner.angulo

        # Atualiza o rect para colisões e desenho
        self.rect.center = self.posicao

    def desenhar(self, surface, camera):
        # Rotaciona a imagem original e obtém o novo rect para desenho
        imagem_rotacionada = pygame.transform.rotate(self.imagem_original, self.angulo)
        rect_desenho = imagem_rotacionada.get_rect(center = self.posicao)
        # Desenha a imagem na posição correta da câmera
        surface.blit(imagem_rotacionada, camera.apply(rect_desenho))


# Classe Base para Naves (Jogador e Bots)
class Nave(pygame.sprite.Sprite):
    POSICOES_AUXILIARES = [
        pygame.math.Vector2(-40, 20), pygame.math.Vector2(40, 20),
        pygame.math.Vector2(-50, -10), pygame.math.Vector2(50, -10)
    ]

    def __init__(self, x, y, cor=AZUL_NAVE, nome="Nave"):
        super().__init__()
        self.nome = nome
        self.posicao = pygame.math.Vector2(x, y)
        self.largura_base = 30
        self.altura = 30
        self.cor = cor

        # Rotação e Movimento
        self.velocidade_rotacao = 5
        self.angulo = 0.0
        self.velocidade_movimento_base = 4 # Será atualizada pelos upgrades

        # Imagem (Triângulo com ponta)
        tamanho_surface = max(self.largura_base, self.altura) + 10
        self.imagem_original = pygame.Surface((tamanho_surface, tamanho_surface), pygame.SRCALPHA)
        centro_x = tamanho_surface / 2
        centro_y = tamanho_surface / 2
        ponto_topo = (centro_x, centro_y - self.altura / 2)
        ponto_base_esq = (centro_x - self.largura_base / 2, centro_y + self.altura / 2)
        ponto_base_dir = (centro_x + self.largura_base / 2, centro_y + self.altura / 2)
        pygame.draw.polygon(self.imagem_original, self.cor, [ponto_topo, ponto_base_esq, ponto_base_dir])
        ponta_largura = 4
        ponta_altura = 8
        pygame.draw.rect(self.imagem_original, PONTA_NAVE, (ponto_topo[0] - ponta_largura / 2, ponto_topo[1] - ponta_altura, ponta_largura, ponta_altura))
        self.image = self.imagem_original # Imagem atual começa como a original
        # Rect usado para colisões (um pouco menor que a imagem)
        self.rect = pygame.Rect(x, y, self.largura_base * 0.8, self.altura * 0.8)
        self.rect.center = self.posicao

        # Atributos de Combate e Upgrades
        self.cooldown_tiro = 250 # ms
        self.ultimo_tiro_tempo = 0
        self.pontos = 0
        self.nivel_motor = 1
        self.nivel_dano = 1
        self.nivel_max_vida = 1
        self.nivel_escudo = 0
        self.max_vida = 4 + self.nivel_max_vida
        self.vida_atual = self.max_vida
        self.velocidade_movimento_base = 4 + self.nivel_motor # Atualiza com base no nível inicial

        # Estado e Controle
        self.quer_virar_esquerda = False
        self.quer_virar_direita = False
        self.quer_mover_frente = False
        self.quer_mover_tras = False
        self.quer_atirar = False
        self.alvo_selecionado = None # Sprite alvo (inimigo, bot, obstáculo)
        self.posicao_alvo_mouse = None # Vector2 da posição alvo do clique direito

        # Efeitos Visuais
        self.tempo_barra_visivel = 2000
        self.ultimo_hit_tempo = 0
        self.mostrar_escudo_fx = False
        self.angulo_impacto_rad_pygame = 0 # Ângulo onde o escudo foi atingido
        self.tempo_escudo_fx = 0
        self.rastro_particulas = [] # Lista para partículas de rastro do motor

        # Controle de Lentidão (status effect)
        self.tempo_fim_lentidao = 0 # Timestamp de quando o efeito termina

        # Naves Auxiliares
        self.lista_todas_auxiliares = []
        self.grupo_auxiliares_ativos = pygame.sprite.Group()
        for pos in self.POSICOES_AUXILIARES:
            nova_aux = NaveAuxiliar(self, pos)
            self.lista_todas_auxiliares.append(nova_aux)

    # --- Métodos de Controle e Atualização ---
    def update(self, grupo_projeteis_destino, camera=None):
        # O método update principal varia entre Jogador e Bot
        # Deve ser implementado/sobrescrito nas subclasses
        pass

    def rotacionar(self):
        angulo_alvo = None
        # Prioridade 1: Travar no alvo selecionado
        if self.alvo_selecionado:
            # Verifica se o alvo ainda é válido
            if not self.alvo_selecionado.groups(): # Se não está em nenhum grupo, sumiu
                self.alvo_selecionado = None
            elif self.posicao.distance_to(self.alvo_selecionado.posicao) > MAX_TARGET_LOCK_DISTANCE:
                # print(f"[{self.nome}] Alvo muito distante, perdendo trava.")
                self.alvo_selecionado = None
            else:
                try: # Calcula ângulo para o alvo
                    direcao_vetor = (self.alvo_selecionado.posicao - self.posicao)
                    if direcao_vetor.length() > 0:
                        radianos = math.atan2(direcao_vetor.y, direcao_vetor.x)
                        angulo_alvo = -math.degrees(radianos) - 90
                except ValueError: pass # Mantém ângulo atual se der erro
        # Prioridade 2: Virar para o alvo do mouse (clique direito)
        elif self.posicao_alvo_mouse:
            # Só vira se estiver longe do ponto clicado
            if self.posicao.distance_to(self.posicao_alvo_mouse) > 5.0:
                try: # Calcula ângulo para o ponto
                    direcao_vetor = (self.posicao_alvo_mouse - self.posicao)
                    if direcao_vetor.length() > 0:
                        radianos = math.atan2(direcao_vetor.y, direcao_vetor.x)
                        angulo_alvo = -math.degrees(radianos) - 90
                except ValueError: pass

        # Aplica a rotação
        if angulo_alvo is not None:
            # Vira diretamente para o alvo (ou interpola para suavizar?)
            # Por enquanto, direto:
            self.angulo = angulo_alvo
        # Prioridade 3: Rotação manual (teclas A/D ou setas)
        elif self.quer_virar_esquerda:
            self.angulo += self.velocidade_rotacao
        elif self.quer_virar_direita:
            self.angulo -= self.velocidade_rotacao

        self.angulo %= 360 # Mantém o ângulo entre 0 e 359

    def mover(self):
        # Calcula a velocidade atual (considerando lentidão)
        agora = pygame.time.get_ticks()
        velocidade_atual = self.velocidade_movimento_base
        if agora < self.tempo_fim_lentidao:
            velocidade_atual *= 0.4 # Aplica 60% de lentidão

        nova_pos = pygame.math.Vector2(self.posicao.x, self.posicao.y)
        movendo_frente = False # Flag para adicionar rastro

        # Movimento baseado em input (teclas W/S ou clique direito)
        if self.quer_mover_frente or self.quer_mover_tras:
            radianos = math.radians(self.angulo)
            if self.quer_mover_frente:
                nova_pos.x += -math.sin(radianos) * velocidade_atual
                nova_pos.y += -math.cos(radianos) * velocidade_atual
                movendo_frente = True
            if self.quer_mover_tras:
                nova_pos.x -= -math.sin(radianos) * velocidade_atual
                nova_pos.y -= -math.cos(radianos) * velocidade_atual
        elif self.posicao_alvo_mouse:
            distancia = self.posicao.distance_to(self.posicao_alvo_mouse)
            if distancia > 5.0: # Só move se não estiver muito perto
                try:
                    direcao = (self.posicao_alvo_mouse - self.posicao).normalize()
                    nova_pos = self.posicao + direcao * velocidade_atual
                    movendo_frente = True
                    # Se o movimento ultrapassar o alvo, vai direto para ele
                    if self.posicao.distance_to(self.posicao_alvo_mouse) < velocidade_atual:
                        nova_pos = self.posicao_alvo_mouse
                        self.posicao_alvo_mouse = None # Chegou ao destino
                except ValueError:
                    nova_pos = self.posicao # Fica parado se der erro
            else: # Chegou ao destino
                nova_pos = self.posicao_alvo_mouse
                self.posicao_alvo_mouse = None

        # --- Lógica de Limite de Mapa (Clamping ou Wrap-around) ---
        # Este método será sobrescrito pelo NaveBot para implementar Wrap-around
        # A Nave (jogador) usa Clamping:
        meia_largura = self.largura_base / 2
        meia_altura = self.altura / 2
        nova_pos.x = max(meia_largura, min(nova_pos.x, MAP_WIDTH - meia_largura))
        nova_pos.y = max(meia_altura, min(nova_pos.y, MAP_HEIGHT - meia_altura))
        # --- FIM DO CLAMPING ---

        self.posicao = nova_pos
        self.rect.center = self.posicao

        # --- Adicionar Rastro do Motor (se nível máximo e movendo para frente) ---
        if self.nivel_motor == MAX_NIVEL_MOTOR and movendo_frente:
            agora = pygame.time.get_ticks()
            radianos_oposto = math.radians(self.angulo + 180) # Direção oposta à frente
            offset_rastro = self.altura * 0.6 # Posição atrás da nave
            pos_rastro_x = self.posicao.x + (-math.sin(radianos_oposto) * offset_rastro)
            pos_rastro_y = self.posicao.y + (-math.cos(radianos_oposto) * offset_rastro)
            # Adiciona [x, y, timestamp]
            self.rastro_particulas.append([pos_rastro_x, pos_rastro_y, agora])
            # Remove a partícula mais antiga se exceder o limite
            if len(self.rastro_particulas) > RASTRO_MAX_PARTICULAS:
                self.rastro_particulas.pop(0)

    def criar_projetil(self):
        radianos = math.radians(self.angulo)
        # Calcula a posição da ponta da nave
        offset_ponta = self.altura / 2 + 10 # Um pouco à frente da ponta visual
        pos_x = self.posicao.x + (-math.sin(radianos) * offset_ponta)
        pos_y = self.posicao.y + (-math.cos(radianos) * offset_ponta)
        return Projetil(pos_x, pos_y, radianos, self.nivel_dano)

    def lidar_com_tiros(self, grupo_destino):
        # Atira se a tecla de espaço estiver pressionada OU se houver um alvo travado
        if self.quer_atirar or self.alvo_selecionado:
            agora = pygame.time.get_ticks()
            if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
                self.ultimo_tiro_tempo = agora
                grupo_destino.add(self.criar_projetil())

    # --- Métodos de Interação e Status ---
    def foi_atingido(self, dano, estado_jogo_atual, proj_pos=None):
        # Não toma dano se já estiver morto (em GAME_OVER) - Previne múltiplos hits pós-morte
        if self.vida_atual <= 0 and estado_jogo_atual == "GAME_OVER":
            return False

        agora = pygame.time.get_ticks()
        # Cooldown curto para evitar múltiplos hits (ex: shotgun inimigo)
        if agora - self.ultimo_hit_tempo < 150: # Um pouco mais longo que o do inimigo
            return False

        # Aplica redução de dano do escudo
        reducao_percent = min(self.nivel_escudo * REDUCAO_DANO_POR_NIVEL, 75) # Máx 75%
        dano_reduzido = max(1, int(dano * (1 - reducao_percent / 100.0))) # Pelo menos 1 de dano

        vida_antes = self.vida_atual
        self.vida_atual -= dano_reduzido
        self.ultimo_hit_tempo = agora # Atualiza tempo do último hit (para barra de vida e cooldown)

        # Log e efeito visual do escudo
        if vida_antes > 0: # Só loga/mostra FX se estava vivo antes
            log_dano = f"Dano: {dano_reduzido}"
            if self.nivel_escudo > 0:
                log_dano += f" (Original: {dano}, Reduzido por Escudo Nv{self.nivel_escudo})"
            # print(f"[{self.nome}] ATINGIDO! {log_dano}. Vida: {max(0, self.vida_atual)}/{self.max_vida}")

            # Mostra efeito visual do escudo (se nível máximo)
            if self.nivel_escudo == MAX_NIVEL_ESCUDO:
                self.mostrar_escudo_fx = True
                self.tempo_escudo_fx = agora
                # Calcula ângulo do impacto se a posição do projétil foi dada
                if proj_pos:
                     vetor_para_origem = proj_pos - self.posicao
                     if vetor_para_origem.length() > 0:
                         # atan2 retorna radianos no sistema matemático padrão, converte para Pygame
                         self.angulo_impacto_rad_pygame = math.atan2(vetor_para_origem.y, vetor_para_origem.x)
                     else: # Se projétil no centro, usa ângulo da nave
                         self.angulo_impacto_rad_pygame = math.radians(90 - self.angulo) # Ajusta 90 graus
                else: # Se não sabe de onde veio o dano, usa a frente da nave
                    self.angulo_impacto_rad_pygame = math.radians(90 - self.angulo)

        # Verifica se morreu
        if self.vida_atual <= 0 and vida_antes > 0:
            print(f"[{self.nome}] MORREU!")
            if grupo_explosoes_ref is not None:
                explosao = Explosao(self.rect.center, self.altura // 2 + 10)
                grupo_explosoes_ref.add(explosao)
            # A mudança de estado_jogo para GAME_OVER é feita no loop principal
            return True # Morreu
        return False # Apenas tomou dano

    def aplicar_lentidao(self, duracao_ms):
        agora = pygame.time.get_ticks()
        # Define o timestamp em que o efeito acaba (ou estende se já estiver lento)
        self.tempo_fim_lentidao = max(self.tempo_fim_lentidao, agora + duracao_ms)
        print(f"[{self.nome}] LENTIDÃO aplicada/estendida por {duracao_ms}ms!")

    def ganhar_pontos(self, quantidade):
        self.pontos += quantidade

    def comprar_auxiliar(self):
        num_ativos = len(self.grupo_auxiliares_ativos)
        if num_ativos < len(self.lista_todas_auxiliares):
            aux_para_adicionar = self.lista_todas_auxiliares[num_ativos]
            self.grupo_auxiliares_ativos.add(aux_para_adicionar)
            print(f"[{self.nome}] Ativando auxiliar {num_ativos + 1}")
            return True # Compra bem-sucedida
        else:
            print(f"[{self.nome}] Máximo de auxiliares atingido!")
            return False

    def comprar_upgrade(self, tipo):
        comprou = False
        if tipo == "motor":
            if self.nivel_motor < MAX_NIVEL_MOTOR:
                custo = CUSTO_BASE_MOTOR * self.nivel_motor
                if self.pontos >= custo:
                    self.pontos -= custo
                    self.nivel_motor += 1
                    self.velocidade_movimento_base = 4 + self.nivel_motor # Atualiza velocidade
                    print(f"[{self.nome}] Motor comprado! Nível {self.nivel_motor}.")
                    comprou = True
            else: print(f"[{self.nome}] Nível máximo de motor atingido!")
        elif tipo == "dano":
            if self.nivel_dano < MAX_NIVEL_DANO:
                custo = CUSTO_BASE_DANO * self.nivel_dano
                if self.pontos >= custo:
                    self.pontos -= custo
                    self.nivel_dano += 1
                    print(f"[{self.nome}] Dano comprado! Nível {self.nivel_dano}.")
                    comprou = True
            else: print(f"[{self.nome}] Nível máximo de dano atingido!")
        elif tipo == "auxiliar":
            num_ativos = len(self.grupo_auxiliares_ativos)
            if num_ativos < len(self.lista_todas_auxiliares):
                custo = CUSTO_BASE_AUXILIAR * (num_ativos + 1)
                if self.pontos >= custo:
                    if self.comprar_auxiliar(): # Tenta ativar o próximo auxiliar
                        self.pontos -= custo # Só desconta se a ativação funcionou
                        comprou = True
            else: print(f"[{self.nome}] Nível máximo de auxiliares atingido!")
        elif tipo == "max_health":
            custo = CUSTO_BASE_MAX_VIDA * self.nivel_max_vida
            if self.pontos >= custo:
                self.pontos -= custo
                self.nivel_max_vida += 1
                self.max_vida = 4 + self.nivel_max_vida
                self.vida_atual += 1 # Ganha 1 de vida ao aumentar o max
                self.ultimo_hit_tempo = pygame.time.get_ticks() # Mostra barra de vida
                print(f"[{self.nome}] Vida Máx. aumentada! Nível {self.nivel_max_vida}.")
                comprou = True
        elif tipo == "escudo":
            if self.nivel_escudo < MAX_NIVEL_ESCUDO:
                custo = CUSTO_BASE_ESCUDO * (self.nivel_escudo + 1)
                if self.pontos >= custo:
                    self.pontos -= custo
                    self.nivel_escudo += 1
                    print(f"[{self.nome}] Escudo comprado! Nível {self.nivel_escudo}.")
                    comprou = True
            else: print(f"[{self.nome}] Nível máximo de escudo atingido!")
        return comprou

    def coletar_vida(self, quantidade):
        if self.vida_atual < self.max_vida:
            self.vida_atual = min(self.max_vida, self.vida_atual + quantidade)
            self.ultimo_hit_tempo = pygame.time.get_ticks() # Mostra a barra de vida
            print(f"[{self.nome}] Coletou vida! Vida: {self.vida_atual}/{self.max_vida}")
            return True
        return False

    # --- Métodos de Desenho ---
    def desenhar(self, surface, camera):
        # 1. Desenha o Rastro do Motor
        agora = pygame.time.get_ticks()
        particulas_vivas = []
        for particula in self.rastro_particulas:
            pos_x, pos_y, tempo_criacao = particula
            idade = agora - tempo_criacao
            if idade < RASTRO_DURACAO:
                particulas_vivas.append(particula)
                progresso = idade / RASTRO_DURACAO
                tamanho_atual = max(1, int(RASTRO_TAMANHO_INICIAL * (1 - progresso)))
                alpha = int(200 * (1 - progresso)) # Fade out
                cor_atual = (*COR_RASTRO_MOTOR, alpha)

                # Desenha como círculo em uma surface temporária para alpha funcionar
                pos_tela_centro = camera.apply(pygame.Rect(pos_x, pos_y, 0, 0)).topleft
                raio_desenho = tamanho_atual // 2
                temp_surf = pygame.Surface((tamanho_atual, tamanho_atual), pygame.SRCALPHA)
                pygame.draw.circle(temp_surf, cor_atual, (raio_desenho, raio_desenho), raio_desenho)
                surface.blit(temp_surf, (pos_tela_centro[0] - raio_desenho, pos_tela_centro[1] - raio_desenho))
        self.rastro_particulas = particulas_vivas # Atualiza a lista

        # 2. Desenha a Nave
        self.image = pygame.transform.rotate(self.imagem_original, self.angulo)
        rect_desenho = self.image.get_rect(center = self.posicao)
        surface.blit(self.image, camera.apply(rect_desenho))

        # 3. Desenha o Efeito do Escudo
        if self.mostrar_escudo_fx:
            agora = pygame.time.get_ticks()
            if agora - self.tempo_escudo_fx < DURACAO_FX_ESCUDO:
                raio_escudo = self.altura * 0.8 + 10 # Tamanho do arco
                largura_arco_graus = 90
                largura_arco_rad = math.radians(largura_arco_graus)
                cor_fx_com_alpha = COR_ESCUDO_FX # Já tem alpha

                # Calcula ângulos de início e fim no sistema do Pygame (0 = direita)
                angulo_inicio_pygame_rad = self.angulo_impacto_rad_pygame - (largura_arco_rad / 2)
                angulo_fim_pygame_rad = self.angulo_impacto_rad_pygame + (largura_arco_rad / 2)

                # Cria rect para o arco no mundo e aplica câmera
                rect_escudo_mundo = pygame.Rect(0, 0, raio_escudo * 2, raio_escudo * 2)
                rect_escudo_mundo.center = self.posicao
                rect_escudo_tela = camera.apply(rect_escudo_mundo)

                # Desenha o arco em uma surface temporária para alpha
                temp_surface = pygame.Surface(rect_escudo_tela.size, pygame.SRCALPHA)
                try:
                    pygame.draw.arc(temp_surface, cor_fx_com_alpha,
                                    (0, 0, rect_escudo_tela.width, rect_escudo_tela.height),
                                    angulo_inicio_pygame_rad, angulo_fim_pygame_rad, width=3)
                    surface.blit(temp_surface, rect_escudo_tela.topleft)
                except ValueError: pass # Ignora erro se ângulos forem inválidos
            else:
                self.mostrar_escudo_fx = False # Efeito terminou

    def desenhar_vida(self, surface, camera):
        agora = pygame.time.get_ticks()
        # Mostra a barra por um tempo após ser atingido ou curado
        if agora - self.ultimo_hit_tempo < self.tempo_barra_visivel:
            LARGURA_BARRA = 40
            ALTURA_BARRA = 5
            OFFSET_Y = 30 # Distância acima da nave

            pos_x_mundo = self.posicao.x - LARGURA_BARRA / 2
            pos_y_mundo = self.posicao.y - OFFSET_Y

            percentual = max(0, self.vida_atual / self.max_vida)
            largura_vida_atual = LARGURA_BARRA * percentual

            rect_fundo_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, LARGURA_BARRA, ALTURA_BARRA)
            rect_vida_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, largura_vida_atual, ALTURA_BARRA)

            # Desenha usando a câmera
            pygame.draw.rect(surface, VERMELHO_VIDA_FUNDO, camera.apply(rect_fundo_mundo))
            pygame.draw.rect(surface, VERDE_VIDA, camera.apply(rect_vida_mundo))

# --- Classe do Jogador ---
class Player(Nave):
    def __init__(self, x, y):
        super().__init__(x, y, cor=AZUL_NAVE, nome="Jogador")

    def update(self, grupo_projeteis_jogador, camera):
        self.processar_input_humano(camera)
        self.rotacionar()
        self.mover() # Usa o mover da classe base (com clamping)
        self.lidar_com_tiros(grupo_projeteis_jogador)

    def processar_input_humano(self, camera):
        teclas = pygame.key.get_pressed()
        self.quer_virar_esquerda = teclas[pygame.K_a] or teclas[pygame.K_LEFT]
        self.quer_virar_direita = teclas[pygame.K_d] or teclas[pygame.K_RIGHT]
        self.quer_mover_frente = teclas[pygame.K_w] or teclas[pygame.K_UP]
        self.quer_mover_tras = teclas[pygame.K_s] or teclas[pygame.K_DOWN]
        self.quer_atirar = teclas[pygame.K_SPACE]

        # Controle pelo mouse
        mouse_buttons = pygame.mouse.get_pressed()
        # Clique direito define alvo de movimento
        if mouse_buttons[2]: # Botão direito
            mouse_pos_tela = pygame.mouse.get_pos()
            # Converte posição da tela para posição do mundo
            camera_world_topleft = (-camera.camera_rect.left, -camera.camera_rect.top)
            mouse_pos_mundo = pygame.math.Vector2(mouse_pos_tela[0] + camera_world_topleft[0],
                                                  mouse_pos_tela[1] + camera_world_topleft[1])
            self.posicao_alvo_mouse = mouse_pos_mundo
            # Desativa movimento pelas teclas se clicar com o mouse
            self.quer_mover_frente = False
            self.quer_mover_tras = False

        # Se usar teclas W/S, cancela o movimento pelo mouse
        if self.quer_mover_frente or self.quer_mover_tras:
            self.posicao_alvo_mouse = None
        # Se usar teclas A/D, cancela a trava de alvo (para poder virar livremente)
        #if self.quer_virar_esquerda or self.quer_virar_direita:
        #    self.alvo_selecionado = None
            # Nota: Comentado para permitir ajuste manual mesmo com alvo travado? Avaliar jogabilidade.


# --- Classe do Bot Aliado ---
class NaveBot(Nave):
    def __init__(self, x, y):
        # Chama init da Nave com cor e nome específicos
        super().__init__(x, y, cor=LARANJA_BOT, nome=f"Bot {random.randint(1, 99)}")

        # Atributos específicos da IA
        self.alvo_atual = None # Alvo da IA (inimigo ou obstáculo)
        self.virando_aleatoriamente_timer = 0 # Contador para viradas aleatórias
        self.direcao_virada_aleatoria = "direita"
        self.distancia_borda_virar = 100 # Distância da borda para começar a virar

        # Distâncias de scan e comportamento
        self.distancia_scan = 800 # Distância geral para detectar coisas
        self.distancia_scan_inimigo = 600
        self.distancia_scan_obstaculo = 800 # Prioriza mais obstáculos?
        self.distancia_parar_ia = 300 # Distância que tenta manter do inimigo
        self.distancia_tiro_ia = 500 # Distância para começar a atirar

        # Estados da IA
        self.estado_ia = "VAGANDO" # Pode ser "VAGANDO", "ATACANDO", "COLETANDO", "EVITANDO_BORDA"
        self.angulo_alvo_borda = 0 # Ângulo para virar ao evitar a borda

        # --- Bloco de Upgrades Aleatórios de Spawn ---
        print(f"[{self.nome}] Gerando upgrades aleatórios...")
        # 1. Motor
        self.nivel_motor = random.randint(1, MAX_NIVEL_MOTOR)
        self.velocidade_movimento_base = 4 + self.nivel_motor # Atualiza velocidade base
        if self.nivel_motor > 1: print(f"  -> Spawn com Motor Nv. {self.nivel_motor}")
        # 2. Dano
        self.nivel_dano = random.randint(1, MAX_NIVEL_DANO)
        if self.nivel_dano > 1: print(f"  -> Spawn com Dano Nv. {self.nivel_dano}")
        # 3. Escudo
        self.nivel_escudo = random.randint(0, MAX_NIVEL_ESCUDO)
        if self.nivel_escudo > 0: print(f"  -> Spawn com Escudo Nv. {self.nivel_escudo}")
        # 4. Vida Máxima (limitado para não serem muito tanks no spawn)
        max_spawn_vida_lvl = 3
        self.nivel_max_vida = random.randint(1, max_spawn_vida_lvl)
        self.max_vida = 4 + self.nivel_max_vida
        self.vida_atual = self.max_vida
        if self.nivel_max_vida > 1: print(f"  -> Spawn com Vida Máx. Nv. {self.nivel_max_vida} ({self.max_vida} HP)")
        # 5. Auxiliares
        max_aux = len(self.lista_todas_auxiliares)
        num_auxiliares = random.randint(0, max_aux)
        if num_auxiliares > 0:
            print(f"  -> Spawn com {num_auxiliares} Auxiliares.")
            for _ in range(num_auxiliares):
                self.comprar_auxiliar() # Usa o método da classe base

    # Sobrescreve 'foi_atingido' para lógica de respawn/reset
    def foi_atingido(self, dano, estado_jogo_atual, proj_pos=None):
        vida_antes = self.vida_atual
        morreu = super().foi_atingido(dano, estado_jogo_atual, proj_pos) # Chama método da Nave

        if morreu:
            print(f"[{self.nome}] BOT MORREU! Resetando...")
            # Reposiciona no centro (ou local aleatório?)
            self.posicao = pygame.math.Vector2(MAP_WIDTH // 2, MAP_HEIGHT // 2)
            self.rect.center = self.posicao

            # Reseta atributos
            self.grupo_auxiliares_ativos.empty()
            self.pontos = 0
            self.nivel_motor = 1
            self.nivel_dano = 1
            self.nivel_max_vida = 1
            self.nivel_escudo = 0
            self.velocidade_movimento_base = 4 + self.nivel_motor
            self.max_vida = 4 + self.nivel_max_vida
            self.vida_atual = self.max_vida
            self.alvo_selecionado = None
            self.posicao_alvo_mouse = None
            self.tempo_fim_lentidao = 0
            self.rastro_particulas = [] # Limpa rastro

            # Reseta IA
            print(f"[{self.nome}] Resetando estado da IA para VAGANDO.")
            self.estado_ia = "VAGANDO"
            self.alvo_atual = None
            self.virando_aleatoriamente_timer = 0
            self.angulo_alvo_borda = 0

            # Readiciona 1 auxiliar padrão após respawn
            print(f"[{self.nome}] Readicionando auxiliar padrão.")
            self.comprar_auxiliar()
        return morreu # Retorna se morreu ou não

    # Sobrescreve 'mover' para implementar Wrap-Around
    def mover(self):
        # Calcula velocidade atual (considerando lentidão) - Copiado da Nave.mover
        agora = pygame.time.get_ticks()
        velocidade_atual = self.velocidade_movimento_base
        if agora < self.tempo_fim_lentidao:
            velocidade_atual *= 0.4

        nova_pos = pygame.math.Vector2(self.posicao.x, self.posicao.y)
        movendo_frente = False

        # Calcula nova posição (baseado em quer_mover_frente/tras da IA)
        radianos = math.radians(self.angulo)
        if self.quer_mover_frente:
            nova_pos.x += -math.sin(radianos) * velocidade_atual
            nova_pos.y += -math.cos(radianos) * velocidade_atual
            movendo_frente = True
        if self.quer_mover_tras: # Bots podem usar ré para ajustar posição
            nova_pos.x -= -math.sin(radianos) * velocidade_atual
            nova_pos.y -= -math.cos(radianos) * velocidade_atual
        # Bots não usam movimento pelo mouse (posicao_alvo_mouse)

        # --- LÓGICA DE WRAP-AROUND ---
        meia_largura = self.largura_base / 2
        meia_altura = self.altura / 2
        if nova_pos.x > MAP_WIDTH + meia_largura: nova_pos.x = -meia_largura
        elif nova_pos.x < -meia_largura: nova_pos.x = MAP_WIDTH + meia_largura
        if nova_pos.y > MAP_HEIGHT + meia_altura: nova_pos.y = -meia_altura
        elif nova_pos.y < -meia_altura: nova_pos.y = MAP_HEIGHT + meia_altura
        # --- FIM DO WRAP-AROUND ---

        self.posicao = nova_pos
        self.rect.center = self.posicao

        # Adicionar Rastro (copiado da Nave.mover)
        if self.nivel_motor == MAX_NIVEL_MOTOR and movendo_frente:
            # ... (código do rastro igual ao da Nave) ...
            agora = pygame.time.get_ticks()
            radianos_oposto = math.radians(self.angulo + 180)
            offset_rastro = self.altura * 0.6
            pos_rastro_x = self.posicao.x + (-math.sin(radianos_oposto) * offset_rastro)
            pos_rastro_y = self.posicao.y + (-math.cos(radianos_oposto) * offset_rastro)
            self.rastro_particulas.append([pos_rastro_x, pos_rastro_y, agora])
            if len(self.rastro_particulas) > RASTRO_MAX_PARTICULAS:
                self.rastro_particulas.pop(0)


    # Update principal da IA do Bot
    def update(self, player_ref, grupo_projeteis_bots, grupo_bots_ref, grupo_inimigos_ref, grupo_obstaculos_ref):
        # 1. Encontrar Alvo (se necessário)
        # Só procura novo alvo se não estiver evitando borda e não tiver um alvo válido
        if self.estado_ia != "EVITANDO_BORDA" and (self.alvo_atual is None or not self.alvo_atual.groups()):
            self.encontrar_alvo(grupo_inimigos_ref, grupo_obstaculos_ref)

        # 2. Processar Input da IA (define flags de movimento/tiro)
        self.processar_input_ia()

        # 3. Executar Ações (rotacionar, mover, atirar) - Métodos da classe base Nave
        self.rotacionar()
        self.mover() # Usa o mover sobrescrito com wrap-around
        self.lidar_com_tiros(grupo_projeteis_bots)

        # 4. Tentar comprar upgrades
        self.processar_upgrades_ia()

    def encontrar_alvo(self, grupo_inimigos, grupo_obstaculos):
        self.alvo_atual = None
        dist_min = float('inf') # Começa com infinito para garantir que o primeiro alvo seja selecionado

        # Prioridade 1: Inimigos dentro do alcance
        for inimigo in grupo_inimigos:
            # ---> ADICIONE ESTA LINHA: Verifica se o inimigo ainda existe
            if not inimigo.groups(): continue
            # <--- FIM DA ADIÇÃO

            # Ignora minions e motherships (ou define prioridades diferentes?)
            if isinstance(inimigo, InimigoMinion) or isinstance(inimigo, InimigoMothership): continue
            dist = self.posicao.distance_to(inimigo.posicao)
            # Verifica se está dentro do alcance de scan E se é mais perto que o alvo anterior
            if dist < self.distancia_scan_inimigo and dist < dist_min:
                dist_min = dist
                self.alvo_atual = inimigo

        # Se encontrou inimigo, define estado e retorna
        if self.alvo_atual:
            self.estado_ia = "ATACANDO"
            return

        # Prioridade 2: Obstáculos (se nenhum inimigo foi encontrado)
        dist_min = float('inf') # Reseta dist_min para nova busca
        for obst in grupo_obstaculos:
            # ---> ADICIONE ESTA LINHA: Verifica se o obstáculo ainda existe
            if not obst.groups(): continue
            # <--- FIM DA ADIÇÃO

            dist = self.posicao.distance_to(obst.posicao)
            if dist < self.distancia_scan_obstaculo and dist < dist_min:
                 dist_min = dist
                 self.alvo_atual = obst

        # Se encontrou obstáculo, define estado
        if self.alvo_atual:
            self.estado_ia = "COLETANDO" # Ou ATACANDO se quiserem atirar em obstáculos
            return

        # Se não encontrou nada, estado é VAGANDO (já está resetado no início)
        self.estado_ia = "VAGANDO"

    def processar_input_ia(self):
        # Reseta flags de ação
        self.quer_virar_esquerda = False; self.quer_virar_direita = False
        self.quer_mover_frente = False; self.quer_mover_tras = False; self.quer_atirar = False

        # --- Lógica de Evitar Borda (Prioridade Máxima) ---
        perto_da_borda = False
        dist_reacao = self.distancia_borda_virar
        # Checa proximidade com cada borda e define ângulo alvo para virar
        if self.posicao.x < dist_reacao: self.angulo_alvo_borda = -90; perto_da_borda = True # Virar Direita (sentido horário)
        elif self.posicao.x > MAP_WIDTH - dist_reacao: self.angulo_alvo_borda = 90; perto_da_borda = True # Virar Esquerda (anti-horário)
        if self.posicao.y < dist_reacao: # Perto da borda de cima
            if perto_da_borda and self.angulo_alvo_borda == -90: self.angulo_alvo_borda = -135 # Canto superior esquerdo -> Virar Sudeste
            elif perto_da_borda and self.angulo_alvo_borda == 90: self.angulo_alvo_borda = 135 # Canto superior direito -> Virar Sudoeste
            else: self.angulo_alvo_borda = 180 # Borda de cima -> Virar para Baixo
            perto_da_borda = True
        elif self.posicao.y > MAP_HEIGHT - dist_reacao: # Perto da borda de baixo
            if perto_da_borda and self.angulo_alvo_borda == -90: self.angulo_alvo_borda = -45 # Canto inferior esquerdo -> Virar Nordeste
            elif perto_da_borda and self.angulo_alvo_borda == 90: self.angulo_alvo_borda = 45 # Canto inferior direito -> Virar Noroeste
            else: self.angulo_alvo_borda = 0 # Borda de baixo -> Virar para Cima
            perto_da_borda = True

        # Define estado se entrou na zona de reação da borda
        if perto_da_borda and self.estado_ia != "EVITANDO_BORDA":
            self.estado_ia = "EVITANDO_BORDA"
            # print(f"[{self.nome}] Entrando em EVITANDO_BORDA (Ângulo Alvo: {self.angulo_alvo_borda})")

        # --- Lógica Baseada no Estado Atual ---
        if self.estado_ia == "EVITANDO_BORDA":
            if not perto_da_borda: # Saiu da zona de perigo?
                self.estado_ia = "VAGANDO" # Volta a vagar
                # print(f"[{self.nome}] Saindo de EVITANDO_BORDA")
            else:
                # Calcula a menor diferença angular para o ângulo alvo
                diff_angulo = (self.angulo_alvo_borda - self.angulo + 180) % 360 - 180
                # Define a direção da virada
                if diff_angulo > 5: self.quer_virar_direita = True # Pygame: negativo é horário, positivo é anti-horário? Testar! -> Ajuste: parece ser o oposto, + é anti-horário
                elif diff_angulo < -5: self.quer_virar_esquerda = True
                self.quer_mover_frente = True # Sempre tenta avançar enquanto vira

        elif self.estado_ia == "ATACANDO":
            if self.alvo_atual is None or not self.alvo_atual.groups(): # Perdeu o alvo?
                self.estado_ia = "VAGANDO"
            else:
                # Calcula ângulo e distância para o alvo
                try:
                    direcao_alvo_vec = (self.alvo_atual.posicao - self.posicao)
                    distancia_alvo = direcao_alvo_vec.length()
                    if distancia_alvo > 0:
                        angulo_alvo = pygame.math.Vector2(0, -1).angle_to(direcao_alvo_vec.normalize())
                    else: angulo_alvo = self.angulo # Evita erro se estiver no mesmo ponto
                except ValueError:
                    distancia_alvo = 0
                    angulo_alvo = self.angulo

                # Define virada
                diff_angulo = (angulo_alvo - self.angulo + 180) % 360 - 180
                if diff_angulo > 5: self.quer_virar_direita = True
                elif diff_angulo < -5: self.quer_virar_esquerda = True

                # Define movimento (tenta manter distância)
                if distancia_alvo > self.distancia_parar_ia: self.quer_mover_frente = True
                elif distancia_alvo < self.distancia_parar_ia - 50: self.quer_mover_tras = True # Recua se muito perto

                # Define tiro
                if distancia_alvo < self.distancia_tiro_ia: self.quer_atirar = True

        elif self.estado_ia == "COLETANDO": # Perseguir obstáculo/vida
             if self.alvo_atual is None or not self.alvo_atual.groups(): # Perdeu o alvo?
                 self.estado_ia = "VAGANDO"
             else:
                 self.quer_mover_frente = True # Sempre avança
                 # Calcula ângulo para o alvo
                 try:
                    direcao_alvo_vec = (self.alvo_atual.posicao - self.posicao)
                    if direcao_alvo_vec.length() > 0:
                         angulo_alvo = pygame.math.Vector2(0, -1).angle_to(direcao_alvo_vec.normalize())
                    else: angulo_alvo = self.angulo
                 except ValueError: angulo_alvo = self.angulo
                 # Vira na direção
                 diff_angulo = (angulo_alvo - self.angulo + 180) % 360 - 180
                 if diff_angulo > 5: self.quer_virar_direita = True
                 elif diff_angulo < -5: self.quer_virar_esquerda = True
                 # Não atira em obstáculos por padrão

        elif self.estado_ia == "VAGANDO":
            # Se não encontrou alvo no início do update, continua vagando
            self.quer_mover_frente = True
            # Lógica de virada aleatória
            if self.virando_aleatoriamente_timer > 0:
                if self.direcao_virada_aleatoria == "esquerda": self.quer_virar_esquerda = True
                else: self.quer_virar_direita = True
                self.virando_aleatoriamente_timer -= 1
            elif random.random() < 0.01: # Chance pequena de iniciar uma virada
                self.virando_aleatoriamente_timer = random.randint(30, 90) # Duração da virada
                self.direcao_virada_aleatoria = random.choice(["esquerda", "direita"])

    def processar_upgrades_ia(self):
        # Lógica simples para gastar pontos (pode ser melhorada)
        # Prioridade: Motor > Vida Max > Dano > Escudo
        if self.pontos >= CUSTO_BASE_MOTOR * self.nivel_motor and self.nivel_motor < MAX_NIVEL_MOTOR:
            self.comprar_upgrade("motor")
        elif self.pontos >= CUSTO_BASE_MAX_VIDA * self.nivel_max_vida:
             self.comprar_upgrade("max_health")
        elif self.pontos >= CUSTO_BASE_DANO * self.nivel_dano and self.nivel_dano < MAX_NIVEL_DANO:
            self.comprar_upgrade("dano")
        elif self.pontos >= CUSTO_BASE_ESCUDO * (self.nivel_escudo + 1) and self.nivel_escudo < MAX_NIVEL_ESCUDO :
            self.comprar_upgrade("escudo")
        # Bots não compram auxiliares sozinhos (só no spawn)