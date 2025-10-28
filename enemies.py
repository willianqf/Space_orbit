# enemies.py
import pygame
import math
import random
from settings import (VERMELHO_VIDA_FUNDO, VERDE_VIDA, MAP_WIDTH, MAP_HEIGHT,
                      VERMELHO_PERSEGUIDOR, ROXO_ATIRADOR_RAPIDO, AMARELO_BOMBA, CIANO_MINION, CIANO_MOTHERSHIP,
                      LARANJA_RAPIDO, AZUL_TIRO_RAPIDO, ROXO_ATORDOADOR, BRANCO)
# Importa as classes de projéteis necessárias
from projectiles import ProjetilInimigo, ProjetilInimigoRapido, ProjetilTeleguiadoLento, ProjetilInimigoRapidoCurto
# Importa a classe Explosao
from effects import Explosao
# REMOVED: from ships import Player, NaveBot

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
        self.tamanho = tamanho; self.image = pygame.Surface((self.tamanho, self.tamanho)); self.image.fill(cor)
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

    def update_base(self, pos_alvo_generico, dist_despawn): return True

    def desenhar_vida(self, surface, camera):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_hit_tempo < self.tempo_barra_visivel:
            LARGURA_BARRA = self.tamanho; ALTURA_BARRA = 4; OFFSET_Y = (self.tamanho / 2) + 10
            pos_x_mundo = self.posicao.x - LARGURA_BARRA / 2; pos_y_mundo = self.posicao.y - OFFSET_Y
            percentual = max(0, self.vida_atual / self.max_vida); largura_vida_atual = LARGURA_BARRA * percentual
            rect_fundo_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, LARGURA_BARRA, ALTURA_BARRA); rect_vida_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, largura_vida_atual, ALTURA_BARRA)
            pygame.draw.rect(surface, VERMELHO_VIDA_FUNDO, camera.apply(rect_fundo_mundo)); pygame.draw.rect(surface, VERDE_VIDA, camera.apply(rect_vida_mundo))

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn): pass

# Inimigo Perseguidor Padrão (Vermelho)
class InimigoPerseguidor(InimigoBase):
    def __init__(self, x, y):
        super().__init__(x, y, tamanho=30, cor=VERMELHO_PERSEGUIDOR, vida=3)
        self.velocidade = 2; self.distancia_parar = 200; self.cooldown_tiro = 2000
        self.ultimo_tiro_tempo = 0; self.distancia_tiro = 500; self.pontos_por_morte = 5

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        alvo_mais_proximo = None; dist_min = float('inf')
        for alvo in lista_alvos_naves:
            # --- MODIFICAÇÃO: Checa tipo por nome ---
            is_player = type(alvo).__name__ == 'Player'
            is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
            if not is_player and not is_active_bot: continue
            # --- FIM MODIFICAÇÃO ---
            try: dist = self.posicao.distance_to(alvo.posicao)
            except ValueError: continue
            if dist < dist_min: dist_min = dist; alvo_mais_proximo = alvo
        if not alvo_mais_proximo: return
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

# Inimigo Atirador Rápido (Roxo - antigo)
class InimigoAtiradorRapido(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y); self.image.fill(ROXO_ATIRADOR_RAPIDO); self.max_vida = 1; self.vida_atual = 1
        self.cooldown_tiro = 500; self.distancia_parar = 300; self.pontos_por_morte = 10
    # Update herdado já está corrigido

# Inimigo Bomba (Amarelo)
class InimigoBomba(InimigoBase):
    def __init__(self, x, y):
        super().__init__(x, y, tamanho=25, cor=AMARELO_BOMBA, vida=1)
        self.velocidade = 3; self.DANO_EXPLOSAO = 3; self.pontos_por_morte = 3

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        alvo_mais_proximo = None; dist_min = float('inf')
        for alvo in lista_alvos_naves:
            # --- MODIFICAÇÃO: Checa tipo por nome ---
            is_player = type(alvo).__name__ == 'Player'
            is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
            if not is_player and not is_active_bot: continue
            # --- FIM MODIFICAÇÃO ---
            try: dist = self.posicao.distance_to(alvo.posicao)
            except ValueError: continue
            if dist < dist_min: dist_min = dist; alvo_mais_proximo = alvo
        if not alvo_mais_proximo: return
        pos_alvo = alvo_mais_proximo.posicao
        if not self.update_base(pos_alvo, dist_despawn): return
        try: direcao = (pos_alvo - self.posicao).normalize(); self.posicao += direcao * self.velocidade; self.rect.center = self.posicao
        except ValueError: pass

# --- NOVOS INIMIGOS ---

# Inimigo Rápido (Laranja)
class InimigoRapido(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y) # Chama o init do InimigoPerseguidor
        self.image.fill(LARANJA_RAPIDO) # Muda a cor
        
        # Ajustes de atributos
        self.max_vida = 5 # Mais vida que o padrão (3)
        self.vida_atual = 5
        self.velocidade = 4.0 # Rápido
        self.cooldown_tiro = 800 # Atira mais rápido que o padrão (2000ms) e que o anterior (1000ms)
        self.pontos_por_morte = 9 # Um pouco mais de pontos

        # Atributos de comportamento (herdado do InimigoPerseguidor, pode ajustar se quiser)
        # self.distancia_parar = 200
        # self.distancia_tiro = 500 # Distância para COMEÇAR a atirar

    # Sobrescreve o método atirar para usar o novo projétil
    def atirar(self, pos_alvo, grupo_projeteis_inimigos):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora
            # Usa a nova classe de projétil
            proj = ProjetilInimigoRapidoCurto(self.posicao.x, self.posicao.y, pos_alvo)
            grupo_projeteis_inimigos.add(proj)
    

# Inimigo Tiro Rápido (Azul)
class InimigoTiroRapido(InimigoPerseguidor): # Update herdado já está corrigido
    def __init__(self, x, y):
        super().__init__(x, y); self.image.fill(AZUL_TIRO_RAPIDO); self.max_vida = 10; self.vida_atual = 10
        self.velocidade = 1.5; self.cooldown_tiro = 1500; self.pontos_por_morte = 20

    def atirar(self, pos_alvo, grupo_projeteis_inimigos):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora; proj = ProjetilInimigoRapido(self.posicao.x, self.posicao.y, pos_alvo); grupo_projeteis_inimigos.add(proj)

# Inimigo Atordoador (Roxo)
class InimigoAtordoador(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y); self.image.fill(ROXO_ATORDOADOR); self.max_vida = 5; self.vida_atual = 5
        self.velocidade = 1.0; self.cooldown_tiro = 5000; self.pontos_por_morte = 25

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        alvo_mais_proximo = None; dist_min = float('inf')
        for alvo in lista_alvos_naves:
            # --- MODIFICAÇÃO: Checa tipo por nome ---
            is_player = type(alvo).__name__ == 'Player'
            is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
            if not is_player and not is_active_bot: continue
            # --- FIM MODIFICAÇÃO ---
            try: dist = self.posicao.distance_to(alvo.posicao)
            except ValueError: continue
            if dist < dist_min: dist_min = dist; alvo_mais_proximo = alvo
        if not alvo_mais_proximo: return
        pos_alvo_para_mov = alvo_mais_proximo.posicao
        if not self.update_base(pos_alvo_para_mov, dist_despawn): return
        distancia_alvo = dist_min
        if distancia_alvo > self.distancia_parar:
            try: direcao = (pos_alvo_para_mov - self.posicao).normalize(); self.posicao += direcao * self.velocidade; self.rect.center = self.posicao
            except ValueError: pass
        if distancia_alvo < self.distancia_tiro: self.atirar(alvo_mais_proximo, grupo_projeteis_inimigos) # Pass sprite

    def atirar(self, alvo_sprite, grupo_projeteis_inimigos):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora; proj = ProjetilTeleguiadoLento(self.posicao.x, self.posicao.y, alvo_sprite); grupo_projeteis_inimigos.add(proj)

# --- MINION E MOTHERSHIP ---

class InimigoMinion(InimigoBase):
    def __init__(self, x, y, owner, target, index, max_minions):
        super().__init__(x, y, tamanho=15, cor=CIANO_MINION, vida=2); self.owner = owner; self.target = target
        self.velocidade = 3; self.cooldown_tiro = 1000; self.distancia_tiro = 500; self.pontos_por_morte = 1
        self.ultimo_tiro_tempo = 0; self.distancia_despawn_minion = 1000
        self.raio_orbita = self.owner.tamanho * 0.8 + random.randint(30, 60); self.angulo_orbita_atual = (index / max_minions) * 360
        self.velocidade_orbita = random.uniform(0.5, 1.0); self.angulo_mira = 0
        self.imagem_original = pygame.Surface((self.tamanho + 5, self.tamanho + 5), pygame.SRCALPHA)
        centro = (self.tamanho + 5) / 2; ponto_topo = (centro, centro - self.tamanho / 2)
        ponto_base_esq = (centro - self.tamanho / 2, centro + self.tamanho / 2); ponto_base_dir = (centro + self.tamanho / 2, centro + self.tamanho / 2)
        pygame.draw.polygon(self.imagem_original, CIANO_MINION, [ponto_topo, ponto_base_esq, ponto_base_dir])
        self.image = self.imagem_original

    def atirar(self, pos_alvo, grupo_projeteis_inimigos):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora; proj = ProjetilInimigo(self.posicao.x, self.posicao.y, pos_alvo); grupo_projeteis_inimigos.add(proj)

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        deve_morrer = False
        if self.owner is None or not self.owner.groups(): deve_morrer = True
        elif self.target is None: deve_morrer = True
        # --- MODIFICAÇÃO: Checa tipo por nome ---
        elif not (type(self.target).__name__ == 'Player' or (type(self.target).__name__ == 'NaveBot' and self.target.groups())): deve_morrer = True
        # --- FIM MODIFICAÇÃO ---
        elif self.owner.posicao.distance_to(self.target.posicao) > self.distancia_despawn_minion: deve_morrer = True
        if deve_morrer: self.kill(); return

        # Órbita
        self.angulo_orbita_atual = (self.angulo_orbita_atual + self.velocidade_orbita) % 360; rad = math.radians(self.angulo_orbita_atual)
        pos_alvo_x = self.owner.posicao.x + math.cos(rad) * self.raio_orbita; pos_alvo_y = self.owner.posicao.y + math.sin(rad) * self.raio_orbita
        self.posicao = self.posicao.lerp(pygame.math.Vector2(pos_alvo_x, pos_alvo_y), 0.05)

        # Mira e Tiro
        try:
            dist_para_alvo = self.posicao.distance_to(self.target.posicao); direcao_vetor = (self.target.posicao - self.posicao)
            if direcao_vetor.length() > 0: radianos = math.atan2(direcao_vetor.y, direcao_vetor.x); self.angulo_mira = -math.degrees(radianos) - 90
            if dist_para_alvo < self.distancia_tiro: self.atirar(self.target.posicao, grupo_projeteis_inimigos)
        except ValueError: pass

        # Rotaciona imagem
        self.image = pygame.transform.rotate(self.imagem_original, self.angulo_mira); self.rect = self.image.get_rect(center = self.posicao)


class InimigoMothership(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y); self.tamanho = 80; self.image = pygame.Surface((self.tamanho, self.tamanho)); self.image.fill(CIANO_MOTHERSHIP)
        self.rect = self.image.get_rect(center=(x,y)); self.max_vida = 200; self.vida_atual = 200; self.velocidade = 1; self.pontos_por_morte = 100
        self.nome = f"Mothership {random.randint(1, 99)}"; self.estado_ia = "VAGANDO"; self.alvo_retaliacao = None
        self.distancia_despawn_minion = 1000; self.max_minions = 8; self.grupo_minions = pygame.sprite.Group()

    def encontrar_atacante_mais_proximo(self, lista_alvos_naves):
        dist_min = float('inf'); alvo_prox = None
        for alvo in lista_alvos_naves:
            # --- MODIFICAÇÃO: Checa tipo por nome ---
            is_player = type(alvo).__name__ == 'Player'
            is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
            if not is_player and not is_active_bot: continue
            # --- FIM MODIFICAÇÃO ---
            try: dist = self.posicao.distance_to(alvo.posicao);
            except ValueError: continue
            if dist < dist_min: dist_min = dist; alvo_prox = alvo
        return alvo_prox

    def spawnar_minions(self):
        if self.alvo_retaliacao and len(self.grupo_minions) == 0 and grupo_inimigos_global_ref is not None:
            # --- MODIFICAÇÃO: Checa tipo por nome ---
            is_player = type(self.alvo_retaliacao).__name__ == 'Player'
            is_active_bot = type(self.alvo_retaliacao).__name__ == 'NaveBot' and self.alvo_retaliacao.groups()
            if not is_player and not is_active_bot:
                self.alvo_retaliacao = None; self.estado_ia = "VAGANDO"; return
            # --- FIM MODIFICAÇÃO ---

            print(f"[{self.nome}] Gerando {self.max_minions} minions!")
            for i in range(self.max_minions):
                angulo_rad = (i / self.max_minions) * 2 * math.pi; raio_spawn = self.tamanho * 0.8
                spawn_x = self.posicao.x + math.cos(angulo_rad) * raio_spawn; spawn_y = self.posicao.y + math.sin(angulo_rad) * raio_spawn
                minion = InimigoMinion(spawn_x, spawn_y, self, self.alvo_retaliacao, i, self.max_minions)
                self.grupo_minions.add(minion); grupo_inimigos_global_ref.add(minion)

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn):
        # Lógica base de despawn
        pos_referencia = self.posicao
        for alvo in lista_alvos_naves:
             # --- MODIFICAÇÃO: Checa tipo por nome ---
             is_player = type(alvo).__name__ == 'Player'
             is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
             if is_player or is_active_bot:
                 pos_referencia = alvo.posicao; break
             # --- FIM MODIFICAÇÃO ---
        if not self.update_base(pos_referencia, dist_despawn): return

        agora = pygame.time.get_ticks()

        # Inicia retaliação
        if (agora - self.ultimo_hit_tempo < 1000) and self.alvo_retaliacao is None:
            self.alvo_retaliacao = self.encontrar_atacante_mais_proximo(lista_alvos_naves)
            if self.alvo_retaliacao: print(f"[{self.nome}] Fui atacado! Retaliando contra {self.alvo_retaliacao.nome}"); self.estado_ia = "RETALIANDO"

        # Lógica de IA
        if self.estado_ia == "VAGANDO":
            try: direcao = (pygame.math.Vector2(MAP_WIDTH/2, MAP_HEIGHT/2) - self.posicao).normalize(); self.posicao += direcao * (self.velocidade * 0.5); self.rect.center = self.posicao
            except ValueError: pass
        elif self.estado_ia == "RETALIANDO":
            perdeu_alvo = False
            if self.alvo_retaliacao is None: perdeu_alvo = True
            else:
                # --- MODIFICAÇÃO: Checa tipo por nome ---
                is_player = type(self.alvo_retaliacao).__name__ == 'Player'
                is_active_bot = type(self.alvo_retaliacao).__name__ == 'NaveBot' and self.alvo_retaliacao.groups()
                if not is_player and not is_active_bot: perdeu_alvo = True
                # --- FIM MODIFICAÇÃO ---
                elif self.posicao.distance_to(self.alvo_retaliacao.posicao) > self.distancia_despawn_minion: perdeu_alvo = True

            if perdeu_alvo:
                print(f"[{self.nome}] Alvo perdido. Voltando a vagar."); self.alvo_retaliacao = None; self.estado_ia = "VAGANDO"; self.grupo_minions.empty()
            else:
                self.spawnar_minions()
                try: direcao = (self.alvo_retaliacao.posicao - self.posicao).normalize(); self.posicao -= direcao * self.velocidade; self.rect.center = self.posicao
                except ValueError: pass