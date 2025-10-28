# camera.py
import pygame
from settings import MAP_WIDTH, MAP_HEIGHT

class Camera:
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        self.camera_rect = pygame.Rect(0, 0, self.largura, self.altura)

    def apply(self, rect_alvo):
        return rect_alvo.move(self.camera_rect.topleft)

    def update(self, alvo):
        # O alvo deve ter um atributo 'posicao' (pygame.math.Vector2)
        x = -alvo.posicao.x + int(self.largura / 2)
        y = -alvo.posicao.y + int(self.altura / 2)

        # Limita o scroll às bordas do mapa
        x = min(0, x)  # Borda esquerda
        x = max(-(MAP_WIDTH - self.largura), x)  # Borda direita
        y = min(0, y)  # Borda superior
        y = max(-(MAP_HEIGHT - self.altura), y)  # Borda inferior

        self.camera_rect.topleft = (x, y)

    def get_world_view_rect(self):
        # Retorna o retângulo que a câmera está vendo no mundo
        return pygame.Rect(-self.camera_rect.left, -self.camera_rect.top, self.largura, self.altura)

    def resize(self, nova_largura, nova_altura):
        self.largura = nova_largura
        self.altura = nova_altura