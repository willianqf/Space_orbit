# enemies.py
import pygame
import math
import random
from settings import (VERMELHO_VIDA_FUNDO, VERDE_VIDA, MAP_WIDTH, MAP_HEIGHT,
                      VERMELHO_PERSEGUIDOR, ROXO_ATIRADOR_RAPIDO, AMARELO_BOMBA, CIANO_MINION, CIANO_MOTHERSHIP,
                      LARANJA_RAPIDO, AZUL_TIRO_RAPIDO, ROXO_ATORDOADOR)
# Importa as classes de projéteis necessárias
from projectiles import ProjetilInimigo, ProjetilInimigoRapido, ProjetilTeleguiadoLento
# Importa a classe Explosao
from effects import Explosao

# Referências globais que serão definidas no main.py (necessário para adicionar minions/explosões)
grupo_explosoes = None
grupo_inimigos_global_ref = None # Para Mothership adicionar Minions

# Função para definir as referências globais (chamada no main.py)
def set_global_enemy_references(explosions_group, enemies_group):
    global grupo_explosoes, grupo_inimigos_global_ref
    grupo_explosoes = explosions_group
    grupo_inimigos_global_ref = enemies_group

# Classe Base para Inimigos
class InimigoBase(pygame.sprite.Sprite):
    def __init__(self, x, y, tamanho, cor, vida):
        super().__init__()
        self.tamanho = tamanho
        self.image = pygame.Surface((self.tamanho, self.tamanho))
        self.image.fill(cor)
        self.posicao = pygame.math.Vector2(x, y)
        self.rect = self.image.get_rect(center=self.posicao)
        self.max_vida = vida
        self.vida_atual = self.max_vida
        self.pontos_por_morte = 0
        self.tempo_barra_visivel = 1500  # ms
        self.ultimo_hit_tempo = 0

    def foi_atingido(self, dano):
        agora = pygame.time.get_ticks()
        # Cooldown rápido para evitar múltiplos hits do mesmo tiro rápido/explosão
        if agora - self.ultimo_hit_tempo < 100:
             return False

        self.vida_atual -= dano
        self.ultimo_hit_tempo = agora
        if self.vida_atual <= 0:
            if grupo_explosoes is not None:
                explosao = Explosao(self.rect.center, self.tamanho // 2 + 5)
                grupo_explosoes.add(explosao)
            self.kill()
            return True # Morreu
        return False # Apenas tomou dano

    def update_base(self, pos_alvo_generico, dist_despawn):
        # Lógica comum de despawn (pode ser sobrescrita se necessário)
        # Assume que pos_alvo_generico é a posição do jogador ou do alvo mais próximo
        # Retorna False se deve parar o update (despawnou)
        # if self.posicao.distance_to(pos_alvo_generico) > dist_despawn:
        #     self.kill()
        #     return False
        return True # Continua update

    def desenhar_vida(self, surface, camera):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_hit_tempo < self.tempo_barra_visivel:
            LARGURA_BARRA = self.tamanho
            ALTURA_BARRA = 4
            OFFSET_Y = (self.tamanho / 2) + 10

            pos_x_mundo = self.posicao.x - LARGURA_BARRA / 2
            pos_y_mundo = self.posicao.y - OFFSET_Y # Barra acima do inimigo

            percentual = max(0, self.vida_atual / self.max_vida)
            largura_vida_atual = LARGURA_BARRA * percentual

            rect_fundo_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, LARGURA_BARRA, ALTURA_BARRA)
            rect_vida_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, largura_vida_atual, ALTURA_BARRA)

            # Aplica a câmera aos Rects para desenhar na tela
            pygame.draw.rect(surface, VERMELHO_VIDA_FUNDO, camera.apply(rect_fundo_mundo))
            pygame.draw.rect(surface, VERDE_VIDA, camera.apply(rect_vida_mundo))

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        # Método a ser sobrescrito pelas subclasses
        pass

# Inimigo Perseguidor Padrão (Vermelho)
class InimigoPerseguidor(InimigoBase):
    def __init__(self, x, y):
        super().__init__(x, y, tamanho=30, cor=VERMELHO_PERSEGUIDOR, vida=3)
        self.velocidade = 2
        self.distancia_parar = 200 # Distância que tenta manter do alvo
        self.cooldown_tiro = 2000 # ms
        self.ultimo_tiro_tempo = 0
        self.distancia_tiro = 500 # Começa a atirar a esta distância
        self.pontos_por_morte = 5

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        alvo_mais_proximo = None
        dist_min = float('inf')
        for alvo in lista_alvos_naves:
            if alvo is None or not alvo.groups(): continue # Verifica se o alvo ainda existe
            dist = self.posicao.distance_to(alvo.posicao)
            if dist < dist_min:
                dist_min = dist
                alvo_mais_proximo = alvo

        if not alvo_mais_proximo: return # Sem alvos válidos

        pos_alvo = alvo_mais_proximo.posicao
        if not self.update_base(pos_alvo, dist_despawn): return # Despawn check

        distancia_alvo = dist_min # Já calculamos

        # Move-se em direção ao alvo se estiver longe
        if distancia_alvo > self.distancia_parar:
            try:
                direcao = (pos_alvo - self.posicao).normalize()
                self.posicao += direcao * self.velocidade
                self.rect.center = self.posicao
            except ValueError:
                pass # Pode acontecer se estiver exatamente na mesma posição

        # Atira se estiver perto o suficiente
        if distancia_alvo < self.distancia_tiro:
            self.atirar(pos_alvo, grupo_projeteis_inimigos) # Passa a posição

    def atirar(self, pos_alvo, grupo_projeteis_inimigos):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora
            proj = ProjetilInimigo(self.posicao.x, self.posicao.y, pos_alvo)
            grupo_projeteis_inimigos.add(proj)

# Inimigo Atirador Rápido (Roxo - antigo)
class InimigoAtiradorRapido(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(ROXO_ATIRADOR_RAPIDO)
        self.max_vida = 1 # Mais frágil
        self.vida_atual = 1
        self.cooldown_tiro = 500 # Atira muito mais rápido
        self.distancia_parar = 300 # Para um pouco mais longe
        self.pontos_por_morte = 10

# Inimigo Bomba (Amarelo)
class InimigoBomba(InimigoBase):
    def __init__(self, x, y):
        super().__init__(x, y, tamanho=25, cor=AMARELO_BOMBA, vida=1)
        self.velocidade = 3
        self.DANO_EXPLOSAO = 3 # Dano causado na colisão RAM
        self.pontos_por_morte = 3

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        alvo_mais_proximo = None
        dist_min = float('inf')
        for alvo in lista_alvos_naves:
            if alvo is None or not alvo.groups(): continue
            dist = self.posicao.distance_to(alvo.posicao)
            if dist < dist_min:
                dist_min = dist
                alvo_mais_proximo = alvo

        if not alvo_mais_proximo: return

        pos_alvo = alvo_mais_proximo.posicao
        if not self.update_base(pos_alvo, dist_despawn): return

        # Simplesmente persegue o alvo mais próximo
        try:
            direcao = (pos_alvo - self.posicao).normalize()
            self.posicao += direcao * self.velocidade
            self.rect.center = self.posicao
        except ValueError:
            pass

# --- NOVOS INIMIGOS ---

# Inimigo Rápido (Laranja)
class InimigoRapido(InimigoPerseguidor): # Herda de Perseguidor, mas não atira
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(LARANJA_RAPIDO)
        self.max_vida = 3 # Vida normal
        self.vida_atual = 3
        self.velocidade = 4.5 # BEM RÁPIDO
        self.pontos_por_morte = 7

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        # Sobrescreve update para apenas perseguir, sem atirar
        alvo_mais_proximo = None
        dist_min = float('inf')
        for alvo in lista_alvos_naves:
            if alvo is None or not alvo.groups(): continue
            dist = self.posicao.distance_to(alvo.posicao)
            if dist < dist_min:
                dist_min = dist
                alvo_mais_proximo = alvo

        if not alvo_mais_proximo: return

        pos_alvo = alvo_mais_proximo.posicao
        if not self.update_base(pos_alvo, dist_despawn): return

        # Persegue sem parar
        try:
            direcao = (pos_alvo - self.posicao).normalize()
            self.posicao += direcao * self.velocidade
            self.rect.center = self.posicao
        except ValueError:
            pass
        # Não chama self.atirar()

# Inimigo Tiro Rápido (Azul)
class InimigoTiroRapido(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(AZUL_TIRO_RAPIDO)
        self.max_vida = 10 # Vida maior
        self.vida_atual = 10
        self.velocidade = 1.5 # Um pouco mais lento que o padrão
        self.cooldown_tiro = 1500 # Atira um pouco mais rápido que o padrão
        self.pontos_por_morte = 20 # Mais pontos

    def atirar(self, pos_alvo, grupo_projeteis_inimigos):
        # Sobrescreve o método 'atirar' para usar o projétil rápido
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora
            proj = ProjetilInimigoRapido(self.posicao.x, self.posicao.y, pos_alvo)
            grupo_projeteis_inimigos.add(proj)

# Inimigo Atordoador (Roxo)
class InimigoAtordoador(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(ROXO_ATORDOADOR)
        self.max_vida = 5 # Vida média
        self.vida_atual = 5
        self.velocidade = 1.0 # Bem lento
        self.cooldown_tiro = 5000 # Atira raramente (tiro forte)
        self.pontos_por_morte = 25 # Bastante pontos

    # Precisa sobrescrever o UPDATE para passar o ALVO (sprite) para o 'atirar'
    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        alvo_mais_proximo = None
        dist_min = float('inf')
        for alvo in lista_alvos_naves:
            if alvo is None or not alvo.groups(): continue
            dist = self.posicao.distance_to(alvo.posicao)
            if dist < dist_min:
                dist_min = dist
                alvo_mais_proximo = alvo # Salva o sprite do alvo

        if not alvo_mais_proximo: return

        pos_alvo_para_mov = alvo_mais_proximo.posicao # Posição para mover
        if not self.update_base(pos_alvo_para_mov, dist_despawn): return

        distancia_alvo = dist_min

        if distancia_alvo > self.distancia_parar:
            try:
                direcao = (pos_alvo_para_mov - self.posicao).normalize()
                self.posicao += direcao * self.velocidade
                self.rect.center = self.posicao
            except ValueError:
                pass

        if distancia_alvo < self.distancia_tiro:
            # A MUDANÇA ESTÁ AQUI: Passa o sprite do alvo, não a posição
            self.atirar(alvo_mais_proximo, grupo_projeteis_inimigos)

    # Assinatura do método 'atirar' ligeiramente diferente (recebe o sprite do alvo)
    def atirar(self, alvo_sprite, grupo_projeteis_inimigos):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora
            proj = ProjetilTeleguiadoLento(self.posicao.x, self.posicao.y, alvo_sprite)
            grupo_projeteis_inimigos.add(proj)

# --- MINION E MOTHERSHIP ---
# (Precisam ser definidos depois das outras classes de inimigos se dependerem delas,
# mas aqui dependem mais das classes Nave/NaveBot que estarão em ships.py)

class InimigoMinion(InimigoBase):
    def __init__(self, x, y, owner, target, index, max_minions):
        super().__init__(x, y, tamanho=15, cor=CIANO_MINION, vida=2)
        self.owner = owner # A Mothership
        self.target = target # Nave ou NaveBot
        self.velocidade = 3
        self.cooldown_tiro = 1000
        self.distancia_tiro = 500
        self.pontos_por_morte = 1
        self.ultimo_tiro_tempo = 0
        self.distancia_despawn_minion = 1000 # Se o alvo ficar muito longe

        # Lógica de órbita
        self.raio_orbita = self.owner.tamanho * 0.8 + random.randint(30, 60)
        # Define ângulo inicial baseado no índice para espalhar os minions
        self.angulo_orbita_atual = (index / max_minions) * 360
        self.velocidade_orbita = random.uniform(0.5, 1.0) # Velocidade angular

        self.angulo_mira = 0 # Ângulo para desenhar a imagem

        # Cria a imagem original (triângulo)
        self.imagem_original = pygame.Surface((self.tamanho + 5, self.tamanho + 5), pygame.SRCALPHA)
        centro = (self.tamanho + 5) / 2
        ponto_topo = (centro, centro - self.tamanho / 2)
        ponto_base_esq = (centro - self.tamanho / 2, centro + self.tamanho / 2)
        ponto_base_dir = (centro + self.tamanho / 2, centro + self.tamanho / 2)
        pygame.draw.polygon(self.imagem_original, CIANO_MINION, [ponto_topo, ponto_base_esq, ponto_base_dir])
        self.image = self.imagem_original # Imagem atual começa como a original

    def atirar(self, pos_alvo, grupo_projeteis_inimigos):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora
            proj = ProjetilInimigo(self.posicao.x, self.posicao.y, pos_alvo)
            grupo_projeteis_inimigos.add(proj)

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        # Minion não usa lista_alvos_naves, ele foca no self.target
        deve_morrer = False

        # Verifica se o dono (Mothership) ou o alvo ainda existem
        if self.target is None or self.owner is None or not self.owner.groups():
            deve_morrer = True
        elif not self.target.groups(): # Se o alvo não está mais em nenhum grupo
             deve_morrer = True
        # Verifica se o alvo se afastou demais
        elif self.owner.posicao.distance_to(self.target.posicao) > self.distancia_despawn_minion:
             deve_morrer = True

        if deve_morrer:
            self.kill()
            return

        # --- Lógica de Órbita ---
        self.angulo_orbita_atual = (self.angulo_orbita_atual + self.velocidade_orbita) % 360
        rad = math.radians(self.angulo_orbita_atual)
        pos_alvo_x = self.owner.posicao.x + math.cos(rad) * self.raio_orbita
        pos_alvo_y = self.owner.posicao.y + math.sin(rad) * self.raio_orbita
        posicao_alvo_orbita = pygame.math.Vector2(pos_alvo_x, pos_alvo_y)
        # Interpola suavemente para a posição alvo na órbita
        self.posicao = self.posicao.lerp(posicao_alvo_orbita, 0.05)

        # --- Lógica de Mira e Tiro ---
        dist_para_alvo = self.posicao.distance_to(self.target.posicao)

        # Calcula o ângulo para mirar no alvo (para rotação da imagem)
        try:
            direcao_vetor = (self.target.posicao - self.posicao)
            if direcao_vetor.length() > 0: # Evita erro de divisão por zero
                radianos = math.atan2(direcao_vetor.y, direcao_vetor.x)
                # Converte radianos para graus e ajusta para o sistema do Pygame (0 é para cima)
                self.angulo_mira = -math.degrees(radianos) - 90
        except ValueError:
            pass # Mantém o ângulo anterior se o vetor for zero

        # Atira se o alvo estiver dentro do alcance
        if dist_para_alvo < self.distancia_tiro:
            self.atirar(self.target.posicao, grupo_projeteis_inimigos)

        # Rotaciona a imagem e atualiza o rect
        self.image = pygame.transform.rotate(self.imagem_original, self.angulo_mira)
        self.rect = self.image.get_rect(center = self.posicao)


class InimigoMothership(InimigoPerseguidor): # Herda de Perseguidor para ter movimento básico e vida
    def __init__(self, x, y): # Removido grupo_inimigos_global do init, será pego pela referência
        super().__init__(x, y) # Chama init do InimigoPerseguidor
        self.tamanho = 80
        self.image = pygame.Surface((self.tamanho, self.tamanho))
        self.image.fill(CIANO_MOTHERSHIP)
        self.rect = self.image.get_rect(center=(x,y)) # Redefine o rect com novo tamanho
        self.max_vida = 200
        self.vida_atual = 200
        self.velocidade = 1 # Mais lenta
        self.pontos_por_morte = 100
        self.nome = f"Mothership {random.randint(1, 99)}"

        # Estado da IA
        self.estado_ia = "VAGANDO" # Pode ser "VAGANDO" ou "RETALIANDO"
        self.alvo_retaliacao = None # Nave/Bot que a atacou

        # Gerenciamento de Minions
        self.distancia_despawn_minion = 1000 # Se o alvo se afastar demais, minions somem
        self.max_minions = 8
        self.grupo_minions = pygame.sprite.Group() # Grupo interno para gerenciar minions

    def encontrar_atacante_mais_proximo(self, lista_alvos_naves):
        # Encontra a nave/bot mais próxima que poderia ter atacado
        dist_min = float('inf')
        alvo_prox = None
        for alvo in lista_alvos_naves:
            if alvo is None or not alvo.groups(): continue
            dist = self.posicao.distance_to(alvo.posicao)
            if dist < dist_min:
                dist_min = dist
                alvo_prox = alvo
        return alvo_prox

    def spawnar_minions(self):
        # Só spawna se estiver retaliando e não tiver minions ativos
        if self.alvo_retaliacao and len(self.grupo_minions) == 0 and grupo_inimigos_global_ref is not None:
            print(f"[{self.nome}] Gerando {self.max_minions} minions!")
            for i in range(self.max_minions):
                # Calcula posição de spawn em círculo ao redor da mothership
                angulo_rad = (i / self.max_minions) * 2 * math.pi
                raio_spawn = self.tamanho * 0.8 # Um pouco dentro da borda
                spawn_x = self.posicao.x + math.cos(angulo_rad) * raio_spawn
                spawn_y = self.posicao.y + math.sin(angulo_rad) * raio_spawn

                minion = InimigoMinion(spawn_x, spawn_y, self, self.alvo_retaliacao, i, self.max_minions)
                self.grupo_minions.add(minion)
                grupo_inimigos_global_ref.add(minion) # Adiciona ao grupo principal do jogo

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        # Lógica de encontrar um alvo para referência de despawn (como em update_base)
        pos_referencia = self.posicao # Padrão se não houver alvos
        for alvo in lista_alvos_naves:
            if alvo is not None and alvo.groups():
                pos_referencia = alvo.posicao
                break
        if not self.update_base(pos_referencia, dist_despawn): return

        agora = pygame.time.get_ticks()

        # Verifica se foi atingida recentemente para iniciar retaliação
        if (agora - self.ultimo_hit_tempo < 1000) and self.alvo_retaliacao is None:
            self.alvo_retaliacao = self.encontrar_atacante_mais_proximo(lista_alvos_naves)
            if self.alvo_retaliacao:
                print(f"[{self.nome}] Fui atacado! Retaliando contra {self.alvo_retaliacao.nome}")
                self.estado_ia = "RETALIANDO"

        # Comportamento baseado no estado
        if self.estado_ia == "VAGANDO":
            # Move-se lentamente em direção ao centro do mapa (ou outro ponto)
            try:
                direcao = (pygame.math.Vector2(MAP_WIDTH/2, MAP_HEIGHT/2) - self.posicao).normalize()
                self.posicao += direcao * (self.velocidade * 0.5) # Metade da velocidade
                self.rect.center = self.posicao
            except ValueError:
                pass # Já está no centro
        elif self.estado_ia == "RETALIANDO":
            # Verifica se perdeu o alvo
            perdeu_alvo = False
            if self.alvo_retaliacao is None: perdeu_alvo = True
            elif not self.alvo_retaliacao.groups(): perdeu_alvo = True # Alvo morreu/despawnou
            elif self.posicao.distance_to(self.alvo_retaliacao.posicao) > self.distancia_despawn_minion:
                perdeu_alvo = True # Alvo se afastou demais

            if perdeu_alvo:
                print(f"[{self.nome}] Alvo perdido. Voltando a vagar.")
                self.alvo_retaliacao = None
                self.estado_ia = "VAGANDO"
                self.grupo_minions.empty() # Manda minions pararem (eles vão se autodestruir)
            else:
                # Tenta spawnar minions
                self.spawnar_minions()
                # Afasta-se lentamente do alvo enquanto os minions atacam
                try:
                    direcao = (self.alvo_retaliacao.posicao - self.posicao).normalize()
                    self.posicao -= direcao * self.velocidade # Move na direção oposta
                    self.rect.center = self.posicao
                except ValueError:
                    pass