# entities.py
import pygame
import math
# --- INÍCIO: MODIFICAÇÃO IMPORTAÇÕES ---
from settings import (CINZA_OBSTACULO, BRANCO, VERMELHO_VIDA_COLETAVEL,
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

# Vida Coletável (Estrela Vermelha)
class VidaColetavel(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.raio = 12
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        self.posicao = pygame.math.Vector2(x, y)
        self.rect = self.image.get_rect(center=self.posicao)

        # Desenha uma estrela vermelha de 5 pontas
        centro = self.raio
        pontos_estrela = []
        for i in range(5):
            # Ponto externo
            angulo_ext = math.radians(i * 72 - 90) # Começa no topo
            x_ext = centro + self.raio * math.cos(angulo_ext)
            y_ext = centro + self.raio * math.sin(angulo_ext)
            pontos_estrela.append((x_ext, y_ext))
            # Ponto interno
            angulo_int = math.radians(i * 72 + 36 - 90) # 36 graus de offset
            raio_interno = self.raio * 0.5
            x_int = centro + raio_interno * math.cos(angulo_int)
            y_int = centro + raio_interno * math.sin(angulo_int)
            pontos_estrela.append((x_int, y_int))

        pygame.draw.polygon(self.image, VERMELHO_VIDA_COLETAVEL, pontos_estrela)
        pygame.draw.polygon(self.image, BRANCO, pontos_estrela, 1) # Borda branca fina

    def update(self, *args, **kwargs):
        # Vidas são estáticas, não precisam de update
        pass