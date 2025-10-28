# enemies.py
import pygame
import math
import random
from settings import (VERMELHO_VIDA_FUNDO, VERDE_VIDA, MAP_WIDTH, MAP_HEIGHT,
                      VERMELHO_PERSEGUIDOR, ROXO_ATIRADOR_RAPIDO, AMARELO_BOMBA, CIANO_MINION, CIANO_MOTHERSHIP,
                      LARANJA_RAPIDO, AZUL_TIRO_RAPIDO, ROXO_ATORDOADOR, BRANCO, AZUL_MINION_CONGELANTE, HP_MINION_CONGELANTE, PONTOS_MINION_CONGELANTE,
                        VELOCIDADE_MINION_CONGELANTE, COOLDOWN_TIRO_MINION_CONGELANTE, AZUL_CONGELANTE, HP_BOSS_CONGELANTE, PONTOS_BOSS_CONGELANTE,
    COOLDOWN_TIRO_CONGELANTE, COOLDOWN_SPAWN_MINION_CONGELANTE,
    MAX_MINIONS_CONGELANTE)
# Importa as classes de projéteis necessárias
from projectiles import ProjetilInimigo, ProjetilInimigoRapido, ProjetilTeleguiadoLento, ProjetilInimigoRapidoCurto, ProjetilCongelante # Importa ProjetilCongelante
# Importa a classe Explosao
from effects import Explosao

# Referências globais que serão definidas no main.py
grupo_explosoes = None
grupo_inimigos_global_ref = None

# Função para definir as referências globais
def set_global_enemy_references(explosions_group, enemies_group):
    global grupo_explosoes, grupo_inimigos_global_ref
    grupo_explosoes = explosions_group
    grupo_inimigos_global_ref = enemies_group

# Classe Base para Inimigos
class InimigoBase(pygame.sprite.Sprite):
    def __init__(self, x, y, tamanho, cor, vida):
        super().__init__()
        self.tamanho = tamanho
        # --- CORREÇÃO IMPORTANTE: Definir 'cor' ANTES de usar ---
        self.cor = cor # Define o atributo cor
        # --- FIM CORREÇÃO ---
        self.image = pygame.Surface((self.tamanho, self.tamanho))
        self.image.fill(self.cor) # Agora self.cor existe
        self.posicao = pygame.math.Vector2(x, y); self.rect = self.image.get_rect(center=self.posicao)
        self.max_vida = vida; self.vida_atual = self.max_vida; self.pontos_por_morte = 0
        self.tempo_barra_visivel = 1500; self.ultimo_hit_tempo = 0

    def foi_atingido(self, dano):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_hit_tempo < 100: return False
        self.vida_atual -= dano; self.ultimo_hit_tempo = agora
        if self.vida_atual <= 0:
            if grupo_explosoes is not None:
                explosao = Explosao(self.rect.center, self.tamanho // 2 + 5); grupo_explosoes.add(explosao)
            self.kill(); return True
        return False

    def update_base(self, pos_alvo_generico, dist_despawn):
         # Lógica de despawn simples
         try:
             if self.posicao.distance_to(pos_alvo_generico) > dist_despawn:
                 self.kill()
                 return False # Indica que foi despawnado
         except ValueError:
             pass
         return True # Continua ativo

    def desenhar_vida(self, surface, camera):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_hit_tempo < self.tempo_barra_visivel:
            LARGURA_BARRA = self.tamanho; ALTURA_BARRA = 4; OFFSET_Y = (self.tamanho / 2) + 10 # Barra abaixo
            pos_x_mundo = self.posicao.x - LARGURA_BARRA / 2; pos_y_mundo = self.posicao.y + OFFSET_Y # CORREÇÃO: Barra abaixo
            percentual = max(0, self.vida_atual / self.max_vida); largura_vida_atual = LARGURA_BARRA * percentual
            rect_fundo_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, LARGURA_BARRA, ALTURA_BARRA); rect_vida_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, largura_vida_atual, ALTURA_BARRA)
            # --- CORREÇÃO: Aplicar câmera ---
            pygame.draw.rect(surface, VERMELHO_VIDA_FUNDO, camera.apply(rect_fundo_mundo));
            pygame.draw.rect(surface, VERDE_VIDA, camera.apply(rect_vida_mundo))
            # --- FIM CORREÇÃO ---

    # Método update padrão (será sobrescrito pelas classes filhas)
    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn): pass


# --- Minion Congelante --- (Definido ANTES do Boss)
class MinionCongelante(InimigoBase):
    def __init__(self, x, y, owner_boss):
        # Chama o init base com stats corretos do minion
        super().__init__(x, y, tamanho=18, cor=AZUL_MINION_CONGELANTE, vida=HP_MINION_CONGELANTE)
        self.owner = owner_boss # Referência ao boss que o criou
        self.velocidade = VELOCIDADE_MINION_CONGELANTE
        self.pontos_por_morte = PONTOS_MINION_CONGELANTE
        self.cooldown_tiro = COOLDOWN_TIRO_MINION_CONGELANTE
        self.distancia_parar = 150 # Para perto antes de atirar
        self.distancia_tiro = 400  # Começa a atirar mais de perto
        self.ultimo_tiro_tempo = 0

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        # --- Lógica de Alvo ---
        alvo_mais_proximo = None
        dist_min = float('inf')

        atacante_do_boss = None
        # Tenta focar no último atacante do boss, se existir e estiver vivo
        if self.owner and self.owner.groups() and hasattr(self.owner, 'ultimo_atacante') and self.owner.ultimo_atacante and self.owner.ultimo_atacante.groups():
             atacante_do_boss = self.owner.ultimo_atacante
             try:
                 dist = self.posicao.distance_to(atacante_do_boss.posicao)
                 if dist < self.distancia_tiro * 1.5:
                     alvo_mais_proximo = atacante_do_boss
                     dist_min = dist
             except ValueError:
                 pass

        # Se não tem alvo do boss, procura o mais próximo geral
        if not alvo_mais_proximo:
            for alvo in lista_alvos_naves:
                is_player = type(alvo).__name__ == 'Player'
                is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
                if not is_player and not is_active_bot: continue
                try:
                    dist = self.posicao.distance_to(alvo.posicao)
                    if dist < dist_min:
                        dist_min = dist
                        alvo_mais_proximo = alvo
                except ValueError:
                    continue

        # Se o dono morreu, ou não achou alvo, verifica despawn e para
        if not self.owner or not self.owner.groups() or not alvo_mais_proximo:
            ref_pos = self.posicao if not alvo_mais_proximo else alvo_mais_proximo.posicao
            if not self.update_base(ref_pos, dist_despawn * 0.8): return # Despawn mais rápido
            # Poderia vagar aqui
            return

        pos_alvo = alvo_mais_proximo.posicao

        # --- Despawn básico ---
        if not self.update_base(pos_alvo, dist_despawn * 0.8):
             return

        # --- Movimento e Tiro ---
        distancia_alvo = dist_min
        if distancia_alvo > self.distancia_parar:
            try:
                direcao = (pos_alvo - self.posicao).normalize()
                self.posicao += direcao * self.velocidade
                self.rect.center = self.posicao
            except ValueError:
                pass

        if distancia_alvo < self.distancia_tiro:
            self.atirar(pos_alvo, grupo_projeteis_inimigos)

    def atirar(self, pos_alvo, grupo_projeteis_inimigos):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora
            proj = ProjetilInimigo(self.posicao.x, self.posicao.y, pos_alvo) # Tiro normal
            grupo_projeteis_inimigos.add(proj)

# --- FIM Minion Congelante ---


# --- Boss Congelante ---
class BossCongelante(InimigoBase):
    def __init__(self, x, y):
        # Chama super().__init__ PRIMEIRO para definir self.cor etc.
        super().__init__(x, y, tamanho=100, cor=AZUL_CONGELANTE, vida=HP_BOSS_CONGELANTE)

        # Desenho Circular
        self.image = pygame.Surface((self.tamanho, self.tamanho), pygame.SRCALPHA)
        centro = self.tamanho // 2
        pygame.draw.circle(self.image, self.cor, (centro, centro), centro) # self.cor já existe
        pygame.draw.circle(self.image, BRANCO, (centro, centro), centro, 2)
        self.rect = self.image.get_rect(center=self.posicao)

        # Atributos específicos
        self.velocidade = 1
        self.pontos_por_morte = PONTOS_BOSS_CONGELANTE
        self.nome = f"Boss Congelante {random.randint(1, 9)}"
        self.cooldown_tiro = COOLDOWN_TIRO_CONGELANTE
        self.ultimo_tiro_tempo = 0
        self.alvo_ataque = None
        self.cooldown_spawn_minion = COOLDOWN_SPAWN_MINION_CONGELANTE
        self.ultimo_spawn_minion_tempo = 0
        self.max_minions = MAX_MINIONS_CONGELANTE
        self.grupo_minions_congelantes = pygame.sprite.Group()
        self.ultimo_atacante = None # Ainda não implementado como receber isso
        self.foi_atacado_recentemente = False

    def foi_atingido(self, dano):
        vida_antes = self.vida_atual
        morreu = super().foi_atingido(dano)
        if not morreu and vida_antes > 0:
             self.foi_atacado_recentemente = True
        elif morreu: # Se morreu, limpa os minions que pertencem a ele
             print(f"[{self.nome}] Boss derrotado! Limpando minions...")
             self.grupo_minions_congelantes.empty() # Remove os minions dos grupos
        return morreu

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        # Lógica base de despawn
        pos_referencia = self.posicao
        alvo_mais_proximo_geral = None
        dist_min_geral = float('inf')
        for alvo in lista_alvos_naves:
             is_player = type(alvo).__name__ == 'Player'
             is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
             if is_player or is_active_bot:
                 try:
                     dist = self.posicao.distance_to(alvo.posicao)
                     if dist < dist_min_geral:
                         dist_min_geral = dist
                         alvo_mais_proximo_geral = alvo
                         pos_referencia = alvo.posicao
                 except ValueError:
                     continue

        if not self.update_base(pos_referencia, dist_despawn):
            self.grupo_minions_congelantes.empty()
            return

        self.alvo_ataque = alvo_mais_proximo_geral
        # print(f"[{self.nome}] Alvo: {self.alvo_ataque.nome if self.alvo_ataque else 'Nenhum'}") # DEBUG

        agora = pygame.time.get_ticks()

        # Ataque
        if self.alvo_ataque:
            if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
                print(f"[{self.nome}] Atirando!") # DEBUG
                self.atirar(self.alvo_ataque.posicao, grupo_projeteis_inimigos)
                self.ultimo_tiro_tempo = agora
            # else: print(f"[{self.nome}] Tiro em cooldown...") # DEBUG

        # Spawn
        if self.foi_atacado_recentemente and (agora - self.ultimo_spawn_minion_tempo > self.cooldown_spawn_minion):
             if len(self.grupo_minions_congelantes) < self.max_minions:
                 print(f"[{self.nome}] Gerando Minion!") # DEBUG
                 self.spawnar_minion()
                 self.ultimo_spawn_minion_tempo = agora
             self.foi_atacado_recentemente = False # Reseta flag
        # elif self.foi_atacado_recentemente: print(f"[{self.nome}] Foi atacado, spawn em cooldown...") # DEBUG

        # Movimento
        try:
             vetor_para_centro = pygame.math.Vector2(MAP_WIDTH/2, MAP_HEIGHT/2) - self.posicao
             if vetor_para_centro.length() > 50:
                 self.posicao += vetor_para_centro.normalize() * self.velocidade # Velocidade normal (1.0)
                 self.rect.center = self.posicao
                 # print(f"[{self.nome}] Movendo...") # DEBUG
        except ValueError:
             pass

    def atirar(self, pos_alvo, grupo_projeteis_inimigos):
        # Este método agora pertence ao BossCongelante
        proj = ProjetilCongelante(self.posicao.x, self.posicao.y, pos_alvo)
        grupo_projeteis_inimigos.add(proj)

    def spawnar_minion(self):
        # Este método agora pertence ao BossCongelante
        angulo_rad = random.uniform(0, 2 * math.pi)
        raio_spawn = self.tamanho * 0.7
        spawn_x = self.posicao.x + math.cos(angulo_rad) * raio_spawn
        spawn_y = self.posicao.y + math.sin(angulo_rad) * raio_spawn

        minion = MinionCongelante(spawn_x, spawn_y, self)
        self.grupo_minions_congelantes.add(minion)

        if grupo_inimigos_global_ref is not None:
            grupo_inimigos_global_ref.add(minion)
        else:
             print("[ERRO] grupo_inimigos_global_ref não definido!")

# --- FIM Boss Congelante ---


# --- Outros Inimigos ---

# Inimigo Perseguidor Padrão (Vermelho)
class InimigoPerseguidor(InimigoBase):
    def __init__(self, x, y):
        super().__init__(x, y, tamanho=30, cor=VERMELHO_PERSEGUIDOR, vida=3)
        self.velocidade = 2; self.distancia_parar = 200; self.cooldown_tiro = 2000
        self.ultimo_tiro_tempo = 0; self.distancia_tiro = 500; self.pontos_por_morte = 5

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        alvo_mais_proximo = None; dist_min = float('inf')
        for alvo in lista_alvos_naves:
            is_player = type(alvo).__name__ == 'Player'
            is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
            if not is_player and not is_active_bot: continue
            try: dist = self.posicao.distance_to(alvo.posicao)
            except ValueError: continue
            if dist < dist_min: dist_min = dist; alvo_mais_proximo = alvo

        if not alvo_mais_proximo:
             if not self.update_base(self.posicao, dist_despawn): return # Verifica despawn mesmo sem alvo
             return

        pos_alvo = alvo_mais_proximo.posicao
        if not self.update_base(pos_alvo, dist_despawn): return
        distancia_alvo = dist_min

        if distancia_alvo > self.distancia_parar:
            try: direcao = (pos_alvo - self.posicao).normalize(); self.posicao += direcao * self.velocidade; self.rect.center = self.posicao
            except ValueError: pass
        if distancia_alvo < self.distancia_tiro: self.atirar(pos_alvo, grupo_projeteis_inimigos)

    def atirar(self, pos_alvo, grupo_projeteis_inimigos):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora; proj = ProjetilInimigo(self.posicao.x, self.posicao.y, pos_alvo); grupo_projeteis_inimigos.add(proj)

# Inimigo Atirador Rápido (Roxo - antigo, mantido por referência)
class InimigoAtiradorRapido(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.cor = ROXO_ATIRADOR_RAPIDO # Atualiza a cor
        self.image.fill(self.cor)
        self.max_vida = 1; self.vida_atual = 1
        self.cooldown_tiro = 500; self.distancia_parar = 300; self.pontos_por_morte = 10
    # O método 'atirar' é herdado e usa ProjetilInimigo normal

# Inimigo Bomba (Amarelo)
class InimigoBomba(InimigoBase):
    def __init__(self, x, y):
        super().__init__(x, y, tamanho=25, cor=AMARELO_BOMBA, vida=1)
        self.velocidade = 3; self.DANO_EXPLOSAO = 3; self.pontos_por_morte = 3

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        alvo_mais_proximo = None; dist_min = float('inf')
        for alvo in lista_alvos_naves:
            is_player = type(alvo).__name__ == 'Player'
            is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
            if not is_player and not is_active_bot: continue
            try: dist = self.posicao.distance_to(alvo.posicao)
            except ValueError: continue
            if dist < dist_min: dist_min = dist; alvo_mais_proximo = alvo

        if not alvo_mais_proximo:
            if not self.update_base(self.posicao, dist_despawn): return
            return

        pos_alvo = alvo_mais_proximo.posicao
        if not self.update_base(pos_alvo, dist_despawn): return

        try: direcao = (pos_alvo - self.posicao).normalize(); self.posicao += direcao * self.velocidade; self.rect.center = self.posicao
        except ValueError: pass
        # Não atira, explode na colisão (tratado em main.py)

# Inimigo Rápido (Laranja)
class InimigoRapido(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.cor = LARANJA_RAPIDO
        self.image.fill(self.cor)
        self.max_vida = 5; self.vida_atual = 5
        self.velocidade = 4.0
        self.cooldown_tiro = 800
        self.pontos_por_morte = 9

    def atirar(self, pos_alvo, grupo_projeteis_inimigos):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora
            proj = ProjetilInimigoRapidoCurto(self.posicao.x, self.posicao.y, pos_alvo)
            grupo_projeteis_inimigos.add(proj)

# Inimigo Tiro Rápido (Azul)
class InimigoTiroRapido(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.cor = AZUL_TIRO_RAPIDO
        self.image.fill(self.cor)
        self.max_vida = 10; self.vida_atual = 10
        self.velocidade = 1.5; self.cooldown_tiro = 1500; self.pontos_por_morte = 20

    def atirar(self, pos_alvo, grupo_projeteis_inimigos):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora; proj = ProjetilInimigoRapido(self.posicao.x, self.posicao.y, pos_alvo); grupo_projeteis_inimigos.add(proj)

# Inimigo Atordoador (Roxo)
class InimigoAtordoador(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.cor = ROXO_ATORDOADOR
        self.image.fill(self.cor)
        self.max_vida = 5; self.vida_atual = 5
        self.velocidade = 1.0; self.cooldown_tiro = 5000; self.pontos_por_morte = 25

    # Update precisa passar o sprite do alvo para 'atirar'
    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        alvo_mais_proximo = None; dist_min = float('inf')
        for alvo in lista_alvos_naves:
            is_player = type(alvo).__name__ == 'Player'
            is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
            if not is_player and not is_active_bot: continue
            try: dist = self.posicao.distance_to(alvo.posicao)
            except ValueError: continue
            if dist < dist_min: dist_min = dist; alvo_mais_proximo = alvo

        if not alvo_mais_proximo:
             if not self.update_base(self.posicao, dist_despawn): return
             return

        pos_alvo_para_mov = alvo_mais_proximo.posicao
        if not self.update_base(pos_alvo_para_mov, dist_despawn): return
        distancia_alvo = dist_min

        if distancia_alvo > self.distancia_parar:
            try: direcao = (pos_alvo_para_mov - self.posicao).normalize(); self.posicao += direcao * self.velocidade; self.rect.center = self.posicao
            except ValueError: pass
        if distancia_alvo < self.distancia_tiro:
            self.atirar(alvo_mais_proximo, grupo_projeteis_inimigos) # Passa o sprite

    def atirar(self, alvo_sprite, grupo_projeteis_inimigos): # Recebe o sprite
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora; proj = ProjetilTeleguiadoLento(self.posicao.x, self.posicao.y, alvo_sprite); grupo_projeteis_inimigos.add(proj)

# --- MINION E MOTHERSHIP ---

# Minion da Mothership
class InimigoMinion(InimigoBase):
    def __init__(self, x, y, owner, target, index, max_minions):
        super().__init__(x, y, tamanho=15, cor=CIANO_MINION, vida=2);
        self.owner = owner; self.target = target
        self.velocidade = 3; self.cooldown_tiro = 1000; self.distancia_tiro = 500; self.pontos_por_morte = 1
        self.ultimo_tiro_tempo = 0; self.distancia_despawn_minion = 1000 # Distância do *dono* para o alvo
        self.raio_orbita = self.owner.tamanho * 0.8 + random.randint(30, 60); self.angulo_orbita_atual = (index / max_minions) * 360
        self.velocidade_orbita = random.uniform(0.5, 1.0); self.angulo_mira = 0

        # Desenho (triângulo)
        self.imagem_original = pygame.Surface((self.tamanho + 5, self.tamanho + 5), pygame.SRCALPHA)
        centro = (self.tamanho + 5) / 2; ponto_topo = (centro, centro - self.tamanho / 2)
        ponto_base_esq = (centro - self.tamanho / 2, centro + self.tamanho / 2); ponto_base_dir = (centro + self.tamanho / 2, centro + self.tamanho / 2)
        pygame.draw.polygon(self.imagem_original, CIANO_MINION, [ponto_topo, ponto_base_esq, ponto_base_dir])
        self.image = self.imagem_original
        self.rect = self.image.get_rect(center=self.posicao) # Atualiza rect após criar imagem

    def atirar(self, pos_alvo, grupo_projeteis_inimigos):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora; proj = ProjetilInimigo(self.posicao.x, self.posicao.y, pos_alvo); grupo_projeteis_inimigos.add(proj)

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        # Verifica se dono ou alvo ainda existem e se estão perto
        deve_morrer = False
        if self.owner is None or not self.owner.groups(): deve_morrer = True
        elif self.target is None or not self.target.groups(): deve_morrer = True # Verifica se alvo existe
        elif not (type(self.target).__name__ == 'Player' or (type(self.target).__name__ == 'NaveBot' and self.target.groups())): deve_morrer = True # Verifica tipo do alvo
        else:
            try: # Verifica distância entre dono e alvo
                if self.owner.posicao.distance_to(self.target.posicao) > self.distancia_despawn_minion: deve_morrer = True
            except ValueError: # Caso erro de distância
                deve_morrer = True

        if deve_morrer: self.kill(); return

        # Órbita
        self.angulo_orbita_atual = (self.angulo_orbita_atual + self.velocidade_orbita) % 360; rad = math.radians(self.angulo_orbita_atual)
        pos_alvo_orbita = self.owner.posicao + pygame.math.Vector2(math.cos(rad), math.sin(rad)) * self.raio_orbita
        self.posicao = self.posicao.lerp(pos_alvo_orbita, 0.05)

        # Mira e Tiro (no alvo guardado)
        try:
            dist_para_alvo = self.posicao.distance_to(self.target.posicao); direcao_vetor = (self.target.posicao - self.posicao)
            if direcao_vetor.length() > 0:
                 # Calcula ângulo para mirar
                 self.angulo_mira = pygame.math.Vector2(0, -1).angle_to(direcao_vetor)
                 if dist_para_alvo < self.distancia_tiro:
                     self.atirar(self.target.posicao, grupo_projeteis_inimigos)
            else: # Se estiver exatamente sobre o alvo, mira para cima
                self.angulo_mira = 0
        except ValueError:
             self.angulo_mira = 0 # Erro ao calcular, mira para cima

        # Rotaciona imagem
        self.image = pygame.transform.rotate(self.imagem_original, self.angulo_mira);
        self.rect = self.image.get_rect(center = self.posicao)

# Mothership
class InimigoMothership(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.tamanho = 80; self.cor = CIANO_MOTHERSHIP
        self.image = pygame.Surface((self.tamanho, self.tamanho)); self.image.fill(self.cor) # Recria imagem com tamanho certo
        self.rect = self.image.get_rect(center=(x,y));
        self.max_vida = 200; self.vida_atual = 200; self.velocidade = 1; self.pontos_por_morte = 100
        self.nome = f"Mothership {random.randint(1, 99)}"; self.estado_ia = "VAGANDO"; self.alvo_retaliacao = None
        self.distancia_despawn_minion = 1000; self.max_minions = 8; self.grupo_minions = pygame.sprite.Group()
        # Não atira diretamente

    def encontrar_atacante_mais_proximo(self, lista_alvos_naves):
        dist_min = float('inf'); alvo_prox = None
        for alvo in lista_alvos_naves:
            is_player = type(alvo).__name__ == 'Player'
            is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
            if not is_player and not is_active_bot: continue
            try: dist = self.posicao.distance_to(alvo.posicao);
            except ValueError: continue
            if dist < dist_min: dist_min = dist; alvo_prox = alvo
        return alvo_prox

    def spawnar_minions(self):
        # Spawna minions apenas se: tem alvo, grupo está vazio, e referência global existe
        if self.alvo_retaliacao and len(self.grupo_minions) == 0 and grupo_inimigos_global_ref is not None:
            is_player = type(self.alvo_retaliacao).__name__ == 'Player'
            is_active_bot = type(self.alvo_retaliacao).__name__ == 'NaveBot' and self.alvo_retaliacao.groups()
            if not is_player and not is_active_bot:
                self.alvo_retaliacao = None; self.estado_ia = "VAGANDO"; return

            print(f"[{self.nome}] Gerando {self.max_minions} minions!")
            for i in range(self.max_minions):
                angulo_rad = (i / self.max_minions) * 2 * math.pi; raio_spawn = self.tamanho * 0.8
                spawn_x = self.posicao.x + math.cos(angulo_rad) * raio_spawn; spawn_y = self.posicao.y + math.sin(angulo_rad) * raio_spawn
                # Passa a mothership (self) como dono e o alvo_retaliacao como target
                minion = InimigoMinion(spawn_x, spawn_y, self, self.alvo_retaliacao, i, self.max_minions)
                self.grupo_minions.add(minion); grupo_inimigos_global_ref.add(minion)

    def foi_atingido(self, dano):
        # Sobrescreve para limpar minions se morrer
        morreu = super().foi_atingido(dano)
        if morreu:
            print(f"[{self.nome}] Mothership derrotada! Limpando minions...")
            self.grupo_minions.empty()
        return morreu


    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        # Lógica base de despawn
        pos_referencia = self.posicao
        alvo_mais_proximo_ref = None
        dist_min_ref = float('inf')
        for alvo in lista_alvos_naves:
             is_player = type(alvo).__name__ == 'Player'
             is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
             if is_player or is_active_bot:
                 try:
                     dist = self.posicao.distance_to(alvo.posicao)
                     if dist < dist_min_ref:
                         dist_min_ref = dist
                         alvo_mais_proximo_ref = alvo
                         pos_referencia = alvo.posicao
                 except ValueError: continue

        if not self.update_base(pos_referencia, dist_despawn):
             self.grupo_minions.empty() # Limpa minions ao despawnar
             return

        agora = pygame.time.get_ticks()

        # Inicia retaliação se foi atingido recentemente e não tem alvo ainda
        if (agora - self.ultimo_hit_tempo < 1000) and self.alvo_retaliacao is None:
            self.alvo_retaliacao = self.encontrar_atacante_mais_proximo(lista_alvos_naves)
            if self.alvo_retaliacao:
                 print(f"[{self.nome}] Fui atacado! Retaliando contra {self.alvo_retaliacao.nome}")
                 self.estado_ia = "RETALIANDO"

        # Lógica de IA
        if self.estado_ia == "VAGANDO":
            # Move lentamente para o centro
            try:
                 vetor_para_centro = pygame.math.Vector2(MAP_WIDTH/2, MAP_HEIGHT/2) - self.posicao
                 if vetor_para_centro.length() > 50:
                     self.posicao += vetor_para_centro.normalize() * (self.velocidade * 0.5)
                     self.rect.center = self.posicao
            except ValueError: pass
        elif self.estado_ia == "RETALIANDO":
            perdeu_alvo = False
            if self.alvo_retaliacao is None or not self.alvo_retaliacao.groups(): perdeu_alvo = True
            else:
                is_player = type(self.alvo_retaliacao).__name__ == 'Player'
                is_active_bot = type(self.alvo_retaliacao).__name__ == 'NaveBot' and self.alvo_retaliacao.groups()
                if not is_player and not is_active_bot: perdeu_alvo = True
                else:
                    try: # Verifica distância para o alvo
                        if self.posicao.distance_to(self.alvo_retaliacao.posicao) > self.distancia_despawn_minion: perdeu_alvo = True
                    except ValueError: perdeu_alvo = True


            if perdeu_alvo:
                print(f"[{self.nome}] Alvo perdido. Voltando a vagar.")
                self.alvo_retaliacao = None; self.estado_ia = "VAGANDO"; self.grupo_minions.empty()
            else:
                self.spawnar_minions() # Tenta spawnar (só funciona se o grupo estiver vazio)
                # Foge do alvo
                try:
                     direcao_fuga = (self.posicao - self.alvo_retaliacao.posicao).normalize()
                     self.posicao += direcao_fuga * self.velocidade
                     self.rect.center = self.posicao
                except ValueError: pass # Se estiver sobreposto, fica parado