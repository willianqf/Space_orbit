# camera.py
import pygame
from settings import MAP_WIDTH, MAP_HEIGHT

class Camera:
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        self.camera_rect = pygame.Rect(0, 0, self.largura, self.altura)
        self.zoom = 1.0 # NEW

    def set_zoom(self, zoom_level):
        """ Define o nível de zoom. 1.0 = normal, < 1.0 = zoom out. """
        self.zoom = max(0.01, zoom_level) # Evita zoom 0

    def apply(self, rect_alvo):
        """ Aplica o offset da câmera E o zoom a um Rect. """
        
        # 1. Obter o offset da câmera (calculado em update)
        offset_x = self.camera_rect.left
        offset_y = self.camera_rect.top
        
        # 2. Calcular a posição do centro do alvo na tela (com zoom 1.0)
        center_x_nozoom = rect_alvo.centerx + offset_x
        center_y_nozoom = rect_alvo.centery + offset_y
        
        # 3. Vetor do centro da tela para o centro do alvo
        vec_x = center_x_nozoom - (self.largura / 2)
        vec_y = center_y_nozoom - (self.altura / 2)
        
        # 4. Vetor escalado (posição do centro do alvo na tela com zoom)
        center_x_zoomed = (self.largura / 2) + (vec_x * self.zoom)
        center_y_zoomed = (self.altura / 2) + (vec_y * self.zoom)
        
        # 5. Escalar o tamanho
        scaled_w = max(1, int(rect_alvo.width * self.zoom))
        scaled_h = max(1, int(rect_alvo.height * self.zoom))
        
        # 6. Calcular o novo top-left
        final_x = center_x_zoomed - (scaled_w / 2)
        final_y = center_y_zoomed - (scaled_h / 2)
        
        return pygame.Rect(final_x, final_y, scaled_w, scaled_h)


    def update(self, alvo, map_width=None, map_height=None):
        """ Atualiza o offset da câmera para centralizar o 'alvo'. """
        
        # Usa MAP_WIDTH e MAP_HEIGHT de settings se não forem fornecidos
        if map_width is None:
            map_width = MAP_WIDTH
        if map_height is None:
            map_height = MAP_HEIGHT
        
        # O alvo deve ter um atributo 'posicao' (pygame.math.Vector2)
        x = -alvo.posicao.x + int(self.largura / 2)
        y = -alvo.posicao.y + int(self.altura / 2)

        # --- MODIFICAÇÃO: Limites do zoom ---
        if self.zoom < 1.0:
            # Quando com zoom out, queremos que o 'alvo' (centro do mapa)
            # fique no centro da tela. A lógica acima (x = ...) já faz isso.
            # Não aplicamos limites de borda, pois queremos ver o mapa todo.
            pass
        else:
            # Limita o scroll às bordas do mapa (lógica original)
            x = min(0, x)  # Borda esquerda
            x = max(-(map_width - self.largura), x)  # Borda direita
            y = min(0, y)  # Borda superior
            y = max(-(map_height - self.altura), y)  # Borda inferior

        self.camera_rect.topleft = (x, y)

    def get_world_view_rect(self):
        """ Retorna o retângulo que a câmera está vendo no mundo (usado para cliques). """
        
        # Posição do centro da câmera no mundo (com zoom 1.0)
        cam_center_x = -self.camera_rect.left + (self.largura / 2)
        cam_center_y = -self.camera_rect.top + (self.altura / 2)
        
        # Largura/Altura do mundo visível
        world_view_width = self.largura / self.zoom
        world_view_height = self.altura / self.zoom
        
        world_left = cam_center_x - (world_view_width / 2)
        world_top = cam_center_y - (world_view_height / 2)
        
        return pygame.Rect(world_left, world_top, world_view_width, world_view_height)

    # --- INÍCIO: NOVA FUNÇÃO ---
    def get_mouse_world_pos(self, mouse_pos_tela):
        """ Converte a posição do mouse na tela para a posição no mundo, considerando o zoom. """
        
        # 1. Posição do mouse relativa ao centro da tela
        vec_x = mouse_pos_tela[0] - (self.largura / 2)
        vec_y = mouse_pos_tela[1] - (self.altura / 2)
        
        # 2. Des-escalar o vetor
        vec_x_nozoom = vec_x / self.zoom
        vec_y_nozoom = vec_y / self.zoom
        
        # 3. Posição do centro da câmera no mundo (o ponto que está no centro da tela)
        # (self.camera_rect.left é o offset, ex: -3600. -(-3600) = 3600)
        # (3600 + 400 = 4000, que é o centro do mapa, correto)
        cam_center_x = -self.camera_rect.left + (self.largura / 2)
        cam_center_y = -self.camera_rect.top + (self.altura / 2)
        
        # 4. Posição final no mundo
        world_x = cam_center_x + vec_x_nozoom
        world_y = cam_center_y + vec_y_nozoom
        
        return pygame.math.Vector2(world_x, world_y)
    # --- FIM: NOVA FUNÇÃO ---

    def resize(self, nova_largura, nova_altura):
        self.largura = nova_largura
        self.altura = nova_altura