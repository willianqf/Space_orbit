# entities.py
import pygame
import math
# --- INÍCIO: MODIFICAÇÃO IMPORTAÇÕES ---
from settings import (CINZA_OBSTACULO, BRANCO, LILAS_REGEN, # <-- MODIFICADO
                      OBSTACULO_RAIO_MIN, OBSTACULO_RAIO_MAX,
                      OBSTACULO_PONTOS_MIN, OBSTACULO_PONTOS_MAX)
# --- FIM: MODIFICAÇÃO IMPORTAÇÕES ---

# Obstáculo (Asteroide/Detrito)
class Obstaculo(pygame.sprite.Sprite):
    def __init__(self, x, y, raio):
        super().__init__()
        self.raio = raio
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        # Desenha o círculo cinza com borda branca
        pygame.draw.circle(self.image, CINZA_OBSTACULO, (self.raio, self.raio), self.raio)
        pygame.draw.circle(self.image, BRANCO, (self.raio, self.raio), self.raio, 2) # Borda
        self.posicao = pygame.math.Vector2(x, y)
        self.rect = self.image.get_rect(center=self.posicao)
        
        # --- INÍCIO: MODIFICAÇÃO PONTOS POR TAMANHO ---
        # Garante que o raio esteja dentro dos limites esperados para evitar divisão por zero
        raio_normalizado = max(OBSTACULO_RAIO_MIN, min(self.raio, OBSTACULO_RAIO_MAX))
        range_raio = OBSTACULO_RAIO_MAX - OBSTACULO_RAIO_MIN
        range_pontos = OBSTACULO_PONTOS_MAX - OBSTACULO_PONTOS_MIN
        
        percentual = 0.0
        # Evita divisão por zero se MIN e MAX forem iguais
        if range_raio > 0:
            percentual = (raio_normalizado - OBSTACULO_RAIO_MIN) / range_raio
        
        # Mapeia linearmente e arredonda para o inteiro mais próximo
        pontos_calculados = OBSTACULO_PONTOS_MIN + (percentual * range_pontos)
        self.pontos_por_morte = int(round(pontos_calculados))
        # --- FIM: MODIFICAÇÃO PONTOS POR TAMANHO ---

    def update(self, *args, **kwargs):
        # Obstáculos são estáticos por enquanto
        pass

# --- CLASSE 'VidaColetavel' REMOVIDA ---


# --- INÍCIO: ADIÇÃO DA NAVE DE REGENERAÇÃO ---
class NaveRegeneradora(pygame.sprite.Sprite):
    def __init__(self, owner_nave):
        super().__init__()
        self.owner = owner_nave # Referência ao jogador (ou bot)
        self.tamanho = 18
        
        # Cria a imagem da nave lilás (um triângulo)
        self.imagem_original = pygame.Surface((self.tamanho, self.tamanho), pygame.SRCALPHA)
        centro = self.tamanho / 2
        ponto_topo = (centro, centro - self.tamanho / 2)
        ponto_base_esq = (centro - self.tamanho / 2, centro + self.tamanho / 2)
        ponto_base_dir = (centro + self.tamanho / 2, centro + self.tamanho / 2)
        pygame.draw.polygon(self.imagem_original, LILAS_REGEN, [ponto_topo, ponto_base_esq, ponto_base_dir])
        
        # Posição e órbita
        self.posicao = self.owner.posicao + pygame.math.Vector2(0, -50) # Começa acima do dono
        self.rect = self.imagem_original.get_rect(center=self.posicao)
        self.angulo_nave = 0 # Rotação da própria nave (visual)
        self.angulo_orbita_atual = 0 # Ângulo ao redor do dono
        self.velocidade_orbita = 3 # Quão rápido gira ao redor do dono
        self.raio_orbita = 50 # Quão longe do dono

    def update(self):
        # 1. Gira a própria nave (efeito visual)
        self.angulo_nave = (self.angulo_nave - 5) % 360 # Gira 5 graus por frame
        
        # 2. Gira a órbita ao redor do dono
        self.angulo_orbita_atual = (self.angulo_orbita_atual + self.velocidade_orbita) % 360
        
        # 3. Calcula a nova posição na órbita
        rad = math.radians(self.angulo_orbita_atual)
        pos_alvo_orbita = self.owner.posicao + pygame.math.Vector2(math.cos(rad), math.sin(rad)) * self.raio_orbita
        
        # 4. Move-se suavemente para a posição da órbita
        self.posicao = self.posicao.lerp(pos_alvo_orbita, 0.2) 
        self.rect.center = self.posicao

    def desenhar(self, surface, camera):
        # Desenha a nave girando
        imagem_rotacionada = pygame.transform.rotate(self.imagem_original, self.angulo_nave)
        rect_desenho = imagem_rotacionada.get_rect(center = self.posicao)
        surface.blit(imagem_rotacionada, camera.apply(rect_desenho))
# --- FIM: ADIÇÃO ---