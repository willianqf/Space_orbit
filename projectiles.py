# projectiles.py
import pygame
import math
from settings import (MAP_RECT, MAX_DISTANCIA_TIRO, VERMELHO_TIRO, VERDE_TIRO_MAX,
                      MAX_NIVEL_DANO, LARANJA_TIRO_INIMIGO, ROXO_TIRO_LENTO,
                      AZUL_TIRO_CONGELANTE, VELOCIDADE_TIRO, FOCO_TIRO) # <-- Importar nova cor

# Projétil do Jogador/Bots Aliados (Padrão "Burro")
class Projetil(pygame.sprite.Sprite):
    def __init__(self, x, y, angulo_radianos, nivel_dano_owner=1, owner_nave=None):
        super().__init__()
        self.raio = 5
        
        # --- INÍCIO: MODIFICAÇÃO (Correção Tiro Verde) ---
        self.owner = owner_nave # Define self.owner PRIMEIRO
        
        cor_tiro_atual = VERMELHO_TIRO # Padrão
        # Verifica o NÍVEL do dono para a cor, não o valor do dano
        if self.owner and self.owner.nivel_dano >= MAX_NIVEL_DANO:
            cor_tiro_atual = VERDE_TIRO_MAX
        # --- FIM: MODIFICAÇÃO ---

        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, cor_tiro_atual, (self.raio, self.raio), self.raio)
        self.posicao_inicial = pygame.math.Vector2(x, y)
        self.posicao = pygame.math.Vector2(x, y) 
        self.rect = self.image.get_rect(center = self.posicao)
        self.velocidade_valor = VELOCIDADE_TIRO # Renomeado de 'velocidade'
        self.angulo_radianos = angulo_radianos
        
        # self.owner = owner_nave # <-- MOVIDO PARA CIMA
        
        # 'nivel_dano_owner' agora é o DANO REAL (ex: 1.6) passado por ships.py
        self.dano = nivel_dano_owner 
        
        # Define o vetor de velocidade inicial
        self.velocidade_vetor = pygame.math.Vector2(
            -math.sin(self.angulo_radianos),
            -math.cos(self.angulo_radianos)
        ) * self.velocidade_valor

    def update(self, *args, **kwargs):
        self.posicao += self.velocidade_vetor
        self.rect.center = self.posicao 
        distancia_percorrida = self.posicao.distance_to(self.posicao_inicial)
        if distancia_percorrida > MAX_DISTANCIA_TIRO:
            self.kill()
            return
        if not MAP_RECT.colliderect(self.rect):
            self.kill()

# --- INÍCIO DAS MODIFICAÇÕES: VELOCIDADE E DURAÇÃO ---
class ProjetilTeleguiadoJogador(Projetil):
    def __init__(self, x, y, angulo_radianos, nivel_dano_owner=1, owner_nave=None, alvo_sprite=None):
        # Chama o __init__ da classe pai (Projetil)
        # O construtor pai (modificado acima) cuidará da cor e do dano
        super().__init__(x, y, angulo_radianos, nivel_dano_owner, owner_nave)
        
        self.alvo_sprite = alvo_sprite
        self.turn_speed = FOCO_TIRO # Mantém a curva suave
        
        # 1. Aumenta a velocidade (padrão do pai era 10)
        self.velocidade_valor = 14 
        # Recalcula o vetor de velocidade com o novo valor
        self.velocidade_vetor = pygame.math.Vector2(
            -math.sin(self.angulo_radianos),
            -math.cos(self.angulo_radianos)
        ) * self.velocidade_valor
        
        # 2. Adiciona tempo de vida (1.5 segundos)
        self.tempo_criacao = pygame.time.get_ticks()
        self.duracao_vida = 700 # 

    def update(self, *args, **kwargs):
        # 1. Verifica o tempo de vida
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao > self.duracao_vida:
            self.kill() # Projétil "morre" após 1.5 segundos
            return
        
        # 2. Lógica de "Homing" Suave
        if self.alvo_sprite and self.alvo_sprite.groups():
            try:
                vetor_para_alvo = (self.alvo_sprite.posicao - self.posicao).normalize()
                velocidade_ideal = vetor_para_alvo * self.velocidade_valor
                self.velocidade_vetor = self.velocidade_vetor.lerp(velocidade_ideal, self.turn_speed)
            except ValueError:
                pass
        
        # 3. Movimento e verificação de borda (copiado da classe pai)
        self.posicao += self.velocidade_vetor
        self.rect.center = self.posicao

        distancia_percorrida = self.posicao.distance_to(self.posicao_inicial)
        if distancia_percorrida > MAX_DISTANCIA_TIRO: # Mantém a distância máxima como segurança
            self.kill()
            return
        if not MAP_RECT.colliderect(self.rect):
            self.kill()
# --- FIM DAS MODIFICAÇÕES ---


# Projétil Inimigo Base
class ProjetilInimigo(pygame.sprite.Sprite):
    def __init__(self, x, y, pos_alvo):
        super().__init__()
        self.raio = 4
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, LARANJA_TIRO_INIMIGO, (self.raio, self.raio), self.raio)
        self.posicao_inicial = pygame.math.Vector2(x, y)
        self.posicao = pygame.math.Vector2(x, y)
        self.rect = self.image.get_rect(center = self.posicao)
        self.velocidade_valor = 7
        try:
            self.direcao = (pos_alvo - self.posicao).normalize()
        except ValueError: 
            self.direcao = pygame.math.Vector2(0, -1)
        self.velocidade_vetor = self.direcao * self.velocidade_valor

    def update(self, *args, **kwargs):
        self.posicao += self.velocidade_vetor
        self.rect.center = self.posicao
        distancia_percorrida = self.posicao.distance_to(self.posicao_inicial)
        if distancia_percorrida > MAX_DISTANCIA_TIRO:
            self.kill()
            return
        if not MAP_RECT.colliderect(self.rect):
            self.kill()

# Projétil Inimigo Rápido (Azul)
class ProjetilInimigoRapido(ProjetilInimigo):
    def __init__(self, x, y, pos_alvo):
        super().__init__(x, y, pos_alvo)
        self.velocidade_valor = 22
        self.velocidade_vetor = self.direcao * self.velocidade_valor

# Projétil Teleguiado Lento (Roxo)
class ProjetilTeleguiadoLento(ProjetilInimigo):
    def __init__(self, x, y, alvo_sprite):
        super().__init__(x, y, alvo_sprite.posicao)
        self.alvo_sprite = alvo_sprite
        self.velocidade_valor = 9.0 
        self.tempo_criacao = pygame.time.get_ticks()
        self.duracao_vida = 5000 
        self.raio = 5
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, ROXO_TIRO_LENTO, (self.raio, self.raio), self.raio)
        self.velocidade_vetor = self.direcao * self.velocidade_valor

    def update(self, *args, **kwargs):
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao > self.duracao_vida:
            self.kill()
            return

        if self.alvo_sprite and self.alvo_sprite.groups():
            try:
                self.direcao = (self.alvo_sprite.posicao - self.posicao).normalize()
                self.velocidade_vetor = self.direcao * self.velocidade_valor
            except ValueError:
                pass
        
        self.posicao += self.velocidade_vetor
        self.rect.center = self.posicao

        distancia_percorrida = self.posicao.distance_to(self.posicao_inicial)
        if distancia_percorrida > MAX_DISTANCIA_TIRO:
            self.kill()
            return
        if not MAP_RECT.colliderect(self.rect):
            self.kill()
            
class ProjetilInimigoRapidoCurto(ProjetilInimigo):
    def __init__(self, x, y, pos_alvo):
        super().__init__(x, y, pos_alvo)
        self.velocidade_valor = 12
        self.max_distancia = 400
        self.velocidade_vetor = self.direcao * self.velocidade_valor

    def update(self, *args, **kwargs):
        self.posicao += self.velocidade_vetor
        self.rect.center = self.posicao
        distancia_percorrida = self.posicao.distance_to(self.posicao_inicial)
        if distancia_percorrida > self.max_distancia:
            self.kill()
            return
        if not MAP_RECT.colliderect(self.rect):
            self.kill()

class ProjetilCongelante(ProjetilTeleguiadoLento):
    def __init__(self, x, y, alvo_sprite):
        super().__init__(x, y, alvo_sprite) 
        self.raio = 6
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, AZUL_TIRO_CONGELANTE, (self.raio, self.raio), self.raio)
        self.velocidade_valor = 8.0
        self.velocidade_vetor = self.direcao * self.velocidade_valor
        self.max_distancia = 700

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        distancia_percorrida = self.posicao.distance_to(self.posicao_inicial)
        if distancia_percorrida > self.max_distancia:
            self.kill()
            return