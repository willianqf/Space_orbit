# effects.py
import pygame
import math

class Explosao(pygame.sprite.Sprite):
    def __init__(self, center, size):
        super().__init__()
        self.size = size
        self.center = center
        self.tempo_criacao = pygame.time.get_ticks()
        self.duracao = 300  # Duração da explosão em milissegundos
        # Cria uma surface transparente
        self.image = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center)
        self.raio_atual = 0

    def update(self):
        agora = pygame.time.get_ticks()
        tempo_decorrido = agora - self.tempo_criacao
        if tempo_decorrido > self.duracao:
            self.kill()  # Remove o sprite do grupo quando a animação termina
            return

        progresso = tempo_decorrido / self.duracao
        # Usa seno para fazer o raio crescer e depois diminuir
        self.raio_atual = int(self.size * math.sin(progresso * math.pi))

        # Redesenha o círculo na surface
        self.image.fill((0, 0, 0, 0)) # Limpa a surface (transparente)
        # Cor muda de amarelo para vermelho/laranja
        cor = (255, int(200 - progresso * 150), 0)
        if self.raio_atual > 0:
            # Desenha um círculo oco (largura variável)
            largura_linha = max(1, int(4 - progresso * 4))
            pygame.draw.circle(self.image, cor, (self.size, self.size), self.raio_atual, width=largura_linha)

    def draw(self, surface, camera):
        # Método auxiliar para desenhar usando a câmera
        surface.blit(self.image, camera.apply(self.rect))