# projectiles.py
import pygame
import math
from settings import (MAP_RECT, MAX_DISTANCIA_TIRO, VERMELHO_TIRO, VERDE_TIRO_MAX,
                      MAX_NIVEL_DANO, LARANJA_TIRO_INIMIGO, ROXO_TIRO_LENTO,
                      AZUL_TIRO_CONGELANTE) # <-- Importar nova cor

# Projétil do Jogador/Bots Aliados
class Projetil(pygame.sprite.Sprite):
    def __init__(self, x, y, angulo_radianos, nivel_dano_owner=1):
        super().__init__()
        self.raio = 5
        # Define a cor baseada no nível de dano
        if nivel_dano_owner >= MAX_NIVEL_DANO:
            cor_tiro_atual = VERDE_TIRO_MAX
        else:
            cor_tiro_atual = VERMELHO_TIRO

        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, cor_tiro_atual, (self.raio, self.raio), self.raio)
        self.posicao_inicial = pygame.math.Vector2(x, y)
        self.posicao = pygame.math.Vector2(x, y) # Posição como Vector2
        self.rect = self.image.get_rect(center = self.posicao)
        self.velocidade = 10
        self.angulo_radianos = angulo_radianos

    def update(self, *args, **kwargs):
        # Movimento baseado no ângulo
        self.posicao.x += -math.sin(self.angulo_radianos) * self.velocidade
        self.posicao.y += -math.cos(self.angulo_radianos) * self.velocidade
        self.rect.center = self.posicao # Atualiza o rect

        # Remove se sair do mapa ou atingir distância máxima
        distancia_percorrida = self.posicao.distance_to(self.posicao_inicial)
        if distancia_percorrida > MAX_DISTANCIA_TIRO:
            self.kill()
            return
        if not MAP_RECT.colliderect(self.rect):
            self.kill()

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
        # Calcula a direção inicial
        try:
            self.direcao = (pos_alvo - self.posicao).normalize()
        except ValueError: # Alvo está na mesma posição
            self.direcao = pygame.math.Vector2(0, -1) # Padrão para cima
        self.velocidade_vetor = self.direcao * self.velocidade_valor

    def update(self, *args, **kwargs):
        # Move na direção calculada
        self.posicao += self.velocidade_vetor
        self.rect.center = self.posicao

        # Remove se sair do mapa ou atingir distância máxima
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
        # --- MODIFICAÇÃO AQUI ---
        self.velocidade_valor = 22 # O padrão era 15
        # --- FIM DA MODIFICAÇÃO ---
        self.velocidade_vetor = self.direcao * self.velocidade_valor

# Projétil Teleguiado Lento (Roxo)
class ProjetilTeleguiadoLento(ProjetilInimigo):
    def __init__(self, x, y, alvo_sprite):
        # Chama o init da classe base, passando a posição ATUAL do alvo
        super().__init__(x, y, alvo_sprite.posicao)

        self.alvo_sprite = alvo_sprite # Armazena a REFERÊNCIA do alvo

        # --- INÍCIO DAS MODIFICAÇÕES ---
        # Problema 2: Aumenta a velocidade
        self.velocidade_valor = 9.0 # Aumentado de 3.5 para 9.0 (mais rápido que o tiro normal)
        
        # Problema 1: Adiciona limite de tempo
        self.tempo_criacao = pygame.time.get_ticks()
        self.duracao_vida = 5000 # 5000ms = 5 segundos de perseguição
        # --- FIM DAS MODIFICAÇÕES ---

        self.raio = 5 # Um pouco maior

        # Redesenha a imagem com a nova cor
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, ROXO_TIRO_LENTO, (self.raio, self.raio), self.raio)
        
        # --- INÍCIO MODIFICAÇÃO: Recalcula vetor velocidade após mudar valor ---
        self.velocidade_vetor = self.direcao * self.velocidade_valor
        # --- FIM MODIFICAÇÃO ---


    def update(self, *args, **kwargs):
        
        # --- INÍCIO DAS MODIFICAÇÕES (Problema 1: Verifica o tempo de vida) ---
        agora = pygame.time.get_ticks()
        if agora - self.tempo_criacao > self.duracao_vida:
            self.kill() # Projétil "morre" após 5 segundos
            return
        # --- FIM DAS MODIFICAÇÕES ---

        # Lógica de "Homing" (Teleguiado)
        # Verifica se o alvo ainda existe (está em algum grupo)
        if self.alvo_sprite and self.alvo_sprite.groups():
            # Se o alvo ainda existe, recalcula a direção
            try:
                self.direcao = (self.alvo_sprite.posicao - self.posicao).normalize()
                self.velocidade_vetor = self.direcao * self.velocidade_valor
            except ValueError:
                # Alvo pode estar exatamente na mesma posição, mantém direção antiga
                pass
        # Se o alvo não existe mais, continua na última direção calculada

        # Move o projétil
        self.posicao += self.velocidade_vetor
        self.rect.center = self.posicao

        # Verifica distância (copiado da classe base)
        distancia_percorrida = self.posicao.distance_to(self.posicao_inicial)
        if distancia_percorrida > MAX_DISTANCIA_TIRO:
            self.kill()
            return
        if not MAP_RECT.colliderect(self.rect):
            self.kill()
            
class ProjetilInimigoRapidoCurto(ProjetilInimigo):
    def __init__(self, x, y, pos_alvo):
        super().__init__(x, y, pos_alvo) # Chama o init base (cor laranja padrão)
        
        # Atributos específicos
        self.velocidade_valor = 12 # Mais rápido que o padrão (7) e que o azul (15)? Ajuste conforme necessário.
        self.max_distancia = 400 # Alcance menor que o padrão (MAX_DISTANCIA_TIRO = 1000)
        
        # Recalcula o vetor de velocidade com a nova velocidade_valor
        self.velocidade_vetor = self.direcao * self.velocidade_valor

    def update(self, *args, **kwargs):
        # Move na direção calculada
        self.posicao += self.velocidade_vetor
        self.rect.center = self.posicao

        # Remove se sair do mapa ou atingir a distância MÁXIMA ESPECÍFICA desta classe
        distancia_percorrida = self.posicao.distance_to(self.posicao_inicial)
        if distancia_percorrida > self.max_distancia: # Usa o max_distancia da classe
            self.kill()
            return
        if not MAP_RECT.colliderect(self.rect):
            self.kill()

# --- INÍCIO DA MODIFICAÇÃO (Projétil Congelante Teleguiado) ---
class ProjetilCongelante(ProjetilTeleguiadoLento): # Herda de TeleguiadoLento
    def __init__(self, x, y, alvo_sprite):
        # Chama o __init__ de ProjetilTeleguiadoLento
        super().__init__(x, y, alvo_sprite) 
        
        # Mantém a cor azul e o raio maior
        self.raio = 6
        self.image = pygame.Surface((self.raio * 2, self.raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, AZUL_TIRO_CONGELANTE, (self.raio, self.raio), self.raio)
        
        # Ajusta a velocidade (pode ser a mesma do TeleguiadoLento ou um pouco diferente)
        self.velocidade_valor = 8.0 # Um pouco mais lento que o roxo (9.0)
        self.velocidade_vetor = self.direcao * self.velocidade_valor
        
        # Define uma distância máxima específica para este projétil
        self.max_distancia = 700 # Menor que MAX_DISTANCIA_TIRO (1000)

    def update(self, *args, **kwargs):
        # Chama o update da classe pai (ProjetilTeleguiadoLento)
        # Isso já inclui a lógica de homing e o limite de tempo (duracao_vida)
        super().update(*args, **kwargs)

        # Adiciona a verificação de distância máxima específica
        distancia_percorrida = self.posicao.distance_to(self.posicao_inicial)
        if distancia_percorrida > self.max_distancia:
            self.kill()
            return
        # A verificação de sair do mapa (MAP_RECT) já está no update pai
# --- FIM DA MODIFICAÇÃO ---