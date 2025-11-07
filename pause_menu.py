# pause_menu.py
import pygame
import settings as s
# Importa os RECTs e constantes de tamanho de ui.py
from ui import (
    RECT_PAUSE_FUNDO, RECT_BOTAO_RESPAWN_PAUSA, RECT_BOTAO_ESPECTADOR,
    RECT_BOTAO_VOLTAR_MENU, RECT_BOTAO_BOT_MENOS, RECT_BOTAO_BOT_MAIS,
    RECT_TEXTO_BOTS, RECT_TEXTO_VOLTAR, BTN_PAUSA_MENU_H, BTN_PAUSE_CTRL_H,
    PAUSE_PANEL_H, PAUSE_PANEL_W
)

class PauseMenu:
    def __init__(self):
        """
        Inicializa o gerenciador do menu de pausa.
        Este objeto não guarda estado, ele o recebe através dos métodos.
        """
        pass

    def handle_event(self, event, is_online):
        """
        Processa um único evento (mouse click ou tecla).
        Retorna uma string de "ação" se o evento for tratado.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "RESUME_GAME"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()

            if RECT_BOTAO_VOLTAR_MENU.collidepoint(mouse_pos):
                return "GOTO_MENU"

            if RECT_BOTAO_ESPECTADOR.collidepoint(mouse_pos):
                return "REQ_SPECTATOR"

            if RECT_BOTAO_RESPAWN_PAUSA.collidepoint(mouse_pos):
                return "REQ_RESPAWN"

            # Controles de Bot (só funcionam se estiver offline)
            if not is_online:
                if RECT_BOTAO_BOT_MENOS.collidepoint(mouse_pos):
                    return "BOT_MENOS"
                if RECT_BOTAO_BOT_MAIS.collidepoint(mouse_pos):
                    return "BOT_MAIS"
        
        return None # Nenhum evento tratado

    def draw(self, surface, max_bots_atual, max_bots_limite, num_bots_ativos,
             jogador_esta_morto, jogador_esta_vivo_espectador, is_online):
        """
        Desenha o menu de pausa completo com base no estado atual do jogo.
        Esta é a lógica de 'desenhar_pause' movida de ui.py
        """
        
        fundo_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        fundo_overlay.fill(s.PRETO_TRANSPARENTE_PAUSA)
        surface.blit(fundo_overlay, (0, 0))
        
        # Desenha o fundo do painel
        pygame.draw.rect(surface, s.CINZA_LOJA_FUNDO, RECT_PAUSE_FUNDO, border_radius=10)
        pygame.draw.rect(surface, s.BRANCO, RECT_PAUSE_FUNDO, 2, border_radius=10)
        
        # Título "PAUSADO"
        texto_titulo = s.FONT_TITULO.render("PAUSADO", True, s.BRANCO)
        titulo_rect = texto_titulo.get_rect(midtop=(RECT_PAUSE_FUNDO.centerx, RECT_PAUSE_FUNDO.top + 15))
        surface.blit(texto_titulo, titulo_rect)

        # Lógica dos Botões de Pausa
        
        # Botão 1: "Respawnar" (Se morto OU vivo-espectador)
        if jogador_esta_vivo_espectador or jogador_esta_morto:
            pygame.draw.rect(surface, s.BRANCO, RECT_BOTAO_RESPAWN_PAUSA, border_radius=5)
            texto_surf = s.FONT_PADRAO.render("Respawnar", True, s.PRETO)
            texto_rect = texto_surf.get_rect(center=RECT_BOTAO_RESPAWN_PAUSA.center)
            surface.blit(texto_surf, texto_rect)

        # Botão 2: "Modo Espectador" (Se vivo, não espectador)
        if not jogador_esta_vivo_espectador and not jogador_esta_morto:
            pygame.draw.rect(surface, s.BRANCO, RECT_BOTAO_ESPECTADOR, border_radius=5)
            texto_surf = s.FONT_PADRAO.render("Modo Espectador", True, s.PRETO)
            texto_rect = texto_surf.get_rect(center=RECT_BOTAO_ESPECTADOR.center)
            surface.blit(texto_surf, texto_rect)

        # Botão 3: "Voltar ao Menu" (Sempre visível)
        pygame.draw.rect(surface, s.BRANCO, RECT_BOTAO_VOLTAR_MENU, border_radius=5)
        texto_voltar_menu_surf = s.FONT_PADRAO.render("Voltar ao Menu", True, s.PRETO)
        texto_voltar_menu_rect = texto_voltar_menu_surf.get_rect(center=RECT_BOTAO_VOLTAR_MENU.center)
        surface.blit(texto_voltar_menu_surf, texto_voltar_menu_rect)
        
        # Controles de Bot (Ocultos se Online)
        if not is_online:
            cor_menos = s.BRANCO if max_bots_atual > 0 else s.CINZA_BOTAO_DESLIGADO
            pygame.draw.rect(surface, cor_menos, RECT_BOTAO_BOT_MENOS, border_radius=5)
            texto_menos = s.FONT_TITULO.render("-", True, s.PRETO)
            menos_rect = texto_menos.get_rect(center=RECT_BOTAO_BOT_MENOS.center)
            surface.blit(texto_menos, menos_rect)
            
            texto_contagem = s.FONT_PADRAO.render(f"Max Bots: {max_bots_atual} (Ativos: {num_bots_ativos})", True, s.BRANCO)
            contagem_rect = texto_contagem.get_rect(center=RECT_TEXTO_BOTS.center)
            surface.blit(texto_contagem, contagem_rect)
            
            cor_mais = s.BRANCO if max_bots_atual < s.MAX_BOTS_LIMITE_SUPERIOR else s.CINZA_BOTAO_DESLIGADO
            pygame.draw.rect(surface, cor_mais, RECT_BOTAO_BOT_MAIS, border_radius=5)
            texto_mais = s.FONT_TITULO.render("+", True, s.PRETO)
            mais_rect = texto_mais.get_rect(center=RECT_BOTAO_BOT_MAIS.center)
            surface.blit(texto_mais, mais_rect)

        # Texto "ESC para Voltar"
        texto_voltar = s.FONT_PADRAO.render("ESC para Voltar", True, s.BRANCO)
        voltar_rect = texto_voltar.get_rect(center=RECT_TEXTO_VOLTAR.center)
        surface.blit(texto_voltar, voltar_rect)