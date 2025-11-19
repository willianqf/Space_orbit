# ui.py
import pygame
# Importa todas as constantes e fontes de settings
from settings import *
import multi.pvp_settings as pvp_s 

# --- Variáveis Globais de UI (Tamanho e Posição) ---
# Tamanhos Fixos
BTN_LOJA_W, BTN_LOJA_H = 300, 50
BTN_MENU_W, BTN_MENU_H = 250, 50
BTN_REINICIAR_W, BTN_REINICIAR_H = 200, 50

# Tamanhos para os banners do HUD
BTN_HUD_UPGRADE_W, BTN_HUD_UPGRADE_H = 140, 45 
BTN_HUD_REGEN_W, BTN_HUD_REGEN_H = 140, 45

TERMINAL_H = 35
PAUSE_PANEL_W, PAUSE_PANEL_H = 350, 400 
BTN_PAUSE_CTRL_W, BTN_PAUSE_CTRL_H = 40, 40
BTN_PAUSA_MENU_W, BTN_PAUSA_MENU_H = 250, 40

# --- Bloco da Tela de Nome (Login) ---
LOGIN_PANEL_W, LOGIN_PANEL_H = 350, 250
LOGIN_INPUT_W, LOGIN_INPUT_H = 300, 40
LOGIN_BTN_W, LOGIN_BTN_H = 200, 50
LOGIN_DIFICULDADE_W, LOGIN_DIFICULDADE_H = 200, 40
LOGIN_ARROW_W, LOGIN_ARROW_H = 40, 40

# --- Bloco da Tela de Conexão ---
CONNECT_PANEL_W, CONNECT_PANEL_H = 350, 300
CONNECT_INPUT_W, CONNECT_INPUT_H = 300, 40
CONNECT_BTN_W, CONNECT_BTN_H = 200, 50

MINIMAP_WIDTH = 150 
MINIMAP_HEIGHT = 150 

# Rects (inicializados com tamanho, posição será definida depois)
RECT_TERMINAL_INPUT = pygame.Rect(0, 0, 0, TERMINAL_H)
RECT_BOTAO_MOTOR = pygame.Rect(0, 0, BTN_LOJA_W, BTN_LOJA_H)
RECT_BOTAO_DANO = pygame.Rect(0, 0, BTN_LOJA_W, BTN_LOJA_H)
RECT_BOTAO_AUX = pygame.Rect(0, 0, BTN_LOJA_W, BTN_LOJA_H)
RECT_BOTAO_MAX_HP = pygame.Rect(0, 0, BTN_LOJA_W, BTN_LOJA_H)
RECT_BOTAO_ESCUDO = pygame.Rect(0, 0, BTN_LOJA_W, BTN_LOJA_H)
RECT_BOTAO_REINICIAR = pygame.Rect(0, 0, BTN_REINICIAR_W, BTN_REINICIAR_H)
RECT_BOTAO_UPGRADE_HUD = pygame.Rect(0, 0, BTN_HUD_UPGRADE_W, BTN_HUD_UPGRADE_H)
RECT_BOTAO_JOGAR_OFF = pygame.Rect(0, 0, BTN_MENU_W, BTN_MENU_H)
RECT_BOTAO_MULTIPLAYER = pygame.Rect(0, 0, BTN_MENU_W, BTN_MENU_H)
RECT_BOTAO_SAIR = pygame.Rect(0, 0, BTN_MENU_W, BTN_MENU_H)
MINIMAP_RECT = pygame.Rect(0, 0, MINIMAP_WIDTH, MINIMAP_HEIGHT)
RECT_LOGO_MENU = pygame.Rect(0, 0, 0, 0)

RECT_BOTAO_PVE_ONLINE = pygame.Rect(0, 0, BTN_MENU_W, BTN_MENU_H)
RECT_BOTAO_PVP_ONLINE = pygame.Rect(0, 0, BTN_MENU_W, BTN_MENU_H)
RECT_BOTAO_PVE_OFFLINE = pygame.Rect(0, 0, BTN_MENU_W, BTN_MENU_H)
RECT_BOTAO_PVP_OFFLINE = pygame.Rect(0, 0, BTN_MENU_W, BTN_MENU_H)

RECT_PAUSE_FUNDO = pygame.Rect(0, 0, PAUSE_PANEL_W, PAUSE_PANEL_H)
RECT_TEXTO_BOTS = pygame.Rect(0, 0, 200, 40)
RECT_BOTAO_BOT_MENOS = pygame.Rect(0, 0, BTN_PAUSE_CTRL_W, BTN_PAUSE_CTRL_H)
RECT_BOTAO_BOT_MAIS = pygame.Rect(0, 0, BTN_PAUSE_CTRL_W, BTN_PAUSE_CTRL_H)
RECT_BOTAO_VOLTAR_MENU = pygame.Rect(0, 0, BTN_PAUSA_MENU_W, BTN_PAUSA_MENU_H)
RECT_BOTAO_ESPECTADOR = pygame.Rect(0, 0, BTN_PAUSA_MENU_W, BTN_PAUSA_MENU_H)
RECT_BOTAO_VOLTAR_NAVE = pygame.Rect(0, 0, BTN_PAUSA_MENU_W, BTN_PAUSA_MENU_H)
RECT_BOTAO_RESPAWN_PAUSA = pygame.Rect(0, 0, BTN_PAUSA_MENU_W, BTN_PAUSA_MENU_H)
RECT_TEXTO_VOLTAR = pygame.Rect(0, 0, 200, 30)

RECT_LOGIN_PAINEL = pygame.Rect(0, 0, LOGIN_PANEL_W, LOGIN_PANEL_H)
RECT_LOGIN_INPUT = pygame.Rect(0, 0, LOGIN_INPUT_W, LOGIN_INPUT_H)
RECT_LOGIN_BOTAO = pygame.Rect(0, 0, LOGIN_BTN_W, LOGIN_BTN_H)
RECT_LOGIN_DIFICULDADE_TEXT = pygame.Rect(0, 0, LOGIN_DIFICULDADE_W, LOGIN_DIFICULDADE_H)
RECT_LOGIN_DIFICULDADE_LEFT = pygame.Rect(0, 0, LOGIN_ARROW_W, LOGIN_ARROW_H)
RECT_LOGIN_DIFICULDADE_RIGHT = pygame.Rect(0, 0, LOGIN_ARROW_W, LOGIN_ARROW_H)

RECT_CONNECT_PAINEL = pygame.Rect(0, 0, CONNECT_PANEL_W, CONNECT_PANEL_H)
RECT_CONNECT_NOME = pygame.Rect(0, 0, CONNECT_INPUT_W, CONNECT_INPUT_H)
RECT_CONNECT_IP = pygame.Rect(0, 0, CONNECT_INPUT_W, CONNECT_INPUT_H)
RECT_CONNECT_BOTAO = pygame.Rect(0, 0, CONNECT_BTN_W, CONNECT_BTN_H)

RECT_BOTAO_REGEN_HUD = pygame.Rect(0, 0, BTN_HUD_REGEN_W, BTN_HUD_REGEN_H)

# --- Cache de Imagens Unificado ---
IMAGENS_LOJA = {
    "motor": None,
    "dano": None,
    "auxiliar": None,
    "max_health": None,
    "escudo": None,
    "btn_loja": None,      # Novo
    "btn_regenerar": None  # Novo
}

def _garantir_imagens_loja_carregadas():
    """Carrega as imagens da loja e do HUD se ainda não estiverem na memória."""
    if IMAGENS_LOJA["motor"] is None:
        try:
            # Carrega e converte para alpha para melhor performance e transparência
            IMAGENS_LOJA["motor"] = pygame.image.load("images/motor_btn.png").convert_alpha()
            IMAGENS_LOJA["dano"] = pygame.image.load("images/dano_btn.png").convert_alpha()
            IMAGENS_LOJA["auxiliar"] = pygame.image.load("images/aux_btn.png").convert_alpha()
            IMAGENS_LOJA["max_health"] = pygame.image.load("images/maxhp_btn.png").convert_alpha()
            IMAGENS_LOJA["escudo"] = pygame.image.load("images/escudo_btn.png").convert_alpha()
            
            # Novos botões do HUD
            IMAGENS_LOJA["btn_loja"] = pygame.image.load("images/loja.png").convert_alpha()
            IMAGENS_LOJA["btn_regenerar"] = pygame.image.load("images/regenerar.png").convert_alpha()
            
            print("[UI] Imagens da UI carregadas com sucesso.")
        except Exception as e:
            print(f"[UI] Erro ao carregar imagens da UI: {e}")
            # Define como False para evitar tentar carregar novamente em loop se falhar
            for k in IMAGENS_LOJA:
                if IMAGENS_LOJA[k] is None: IMAGENS_LOJA[k] = False

def desenhar_botao_customizado(surface, rect, imagem, nivel_atual, nivel_max, custo, pontos_jogador, ativo):
    """
    Desenha um botão da loja.
    """
    # 1. Fundo do Slot
    pygame.draw.rect(surface, (10, 10, 10), rect, border_radius=8)
    
    # Borda de destaque
    mouse_pos = pygame.mouse.get_pos()
    if rect.collidepoint(mouse_pos) and ativo:
         pygame.draw.rect(surface, AZUL_NAVE, rect, 2, border_radius=8)
    else:
         pygame.draw.rect(surface, (50, 50, 50), rect, 2, border_radius=8)

    # 2. Desenha a Imagem (Proporcional)
    if imagem:
        img_w = imagem.get_width()
        img_h = imagem.get_height()
        fator_escala_h = (rect.height - 8) / img_h
        fator_escala_w = (rect.width - 8) / img_w
        fator_final = min(fator_escala_h, fator_escala_w)
        novas_dims = (int(img_w * fator_final), int(img_h * fator_final))
        img_scaled = pygame.transform.smoothscale(imagem, novas_dims)
        img_rect = img_scaled.get_rect(center=rect.center)
        surface.blit(img_scaled, img_rect)
    else:
        cor = BRANCO if ativo else CINZA_BOTAO_DESLIGADO
        pygame.draw.rect(surface, cor, rect.inflate(-10, -10), border_radius=4)

    # 3. Efeito de Desabilitado
    if not ativo:
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        surface.blit(s, rect)

    # 4. Informações Laterais
    texto_x = rect.right + 15
    centro_y = rect.centery
    
    if nivel_atual < nivel_max:
        txt_nivel = f"Nível: {nivel_atual + 1} / {nivel_max}"
        cor_nivel = BRANCO
    else:
        txt_nivel = "NÍVEL MÁXIMO"
        cor_nivel = AZUL_NAVE 

    surf_nivel = FONT_HUD_DETALHES.render(txt_nivel, True, cor_nivel)
    rect_nivel = surf_nivel.get_rect(topleft=(texto_x, centro_y - 15))
    surface.blit(surf_nivel, rect_nivel)
    
    if nivel_atual < nivel_max:
        txt_custo = f"Custo: {custo} Pts"
        cor_custo = VERDE_VIDA if pontos_jogador >= custo else VERMELHO_VIDA_FUNDO
        surf_custo = FONT_RANKING.render(txt_custo, True, cor_custo)
        rect_custo = surf_custo.get_rect(topleft=(texto_x, centro_y + 5))
        surface.blit(surf_custo, rect_custo)

def desenhar_botao_hud(surface, rect, imagem, texto_alternativo, ativo, cor_texto=PRETO):
    """Desenha um botão simples no HUD preenchendo TODO o espaço."""
    
    # 1. Desenha Imagem
    if imagem:
        # Escala para preencher EXATAMENTE o retângulo (Pode esticar se a proporção for diferente)
        img_scaled = pygame.transform.smoothscale(imagem, (rect.width, rect.height))
        surface.blit(img_scaled, rect)
    else:
        # Fallback: Retângulo
        cor = BRANCO if ativo else CINZA_BOTAO_DESLIGADO
        pygame.draw.rect(surface, cor, rect, border_radius=5)
        texto_surf = FONT_RANKING.render(texto_alternativo, True, cor_texto)
        texto_rect = texto_surf.get_rect(center=rect.center)
        surface.blit(texto_surf, texto_rect)

    # 2. Efeito de Mouse Hover (Brilho na borda)
    if ativo and rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(surface, BRANCO, rect, 1, border_radius=5)

    # 3. Efeito de Desabilitado (Escurecer)
    if not ativo:
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        surface.blit(s, rect)

# Variáveis de Posição
MINIMAP_POS_X = 0
MINIMAP_POS_Y = 0

def recalculate_ui_positions(w, h):
    global MINIMAP_POS_X, MINIMAP_POS_Y, MINIMAP_RECT, RECT_TERMINAL_INPUT
    global RECT_BOTAO_MOTOR, RECT_BOTAO_DANO, RECT_BOTAO_AUX, RECT_BOTAO_MAX_HP, RECT_BOTAO_ESCUDO
    global RECT_BOTAO_REINICIAR, RECT_BOTAO_UPGRADE_HUD
    global RECT_BOTAO_JOGAR_OFF, RECT_BOTAO_MULTIPLAYER, RECT_BOTAO_SAIR
    global RECT_BOTAO_PVE_ONLINE, RECT_BOTAO_PVP_ONLINE
    global RECT_BOTAO_PVE_OFFLINE, RECT_BOTAO_PVP_OFFLINE
    global RECT_PAUSE_FUNDO, RECT_TEXTO_BOTS, RECT_BOTAO_BOT_MENOS, RECT_BOTAO_BOT_MAIS
    global RECT_BOTAO_VOLTAR_MENU, RECT_BOTAO_ESPECTADOR, RECT_BOTAO_VOLTAR_NAVE
    global RECT_BOTAO_RESPAWN_PAUSA, RECT_TEXTO_VOLTAR
    global RECT_LOGIN_PAINEL, RECT_LOGIN_INPUT, RECT_LOGIN_BOTAO
    global RECT_LOGIN_DIFICULDADE_TEXT, RECT_LOGIN_DIFICULDADE_LEFT, RECT_LOGIN_DIFICULDADE_RIGHT
    global RECT_CONNECT_PAINEL, RECT_CONNECT_NOME, RECT_CONNECT_IP, RECT_CONNECT_BOTAO
    global RECT_BOTAO_REGEN_HUD
    global RECT_LOGO_MENU

    # Minimapa
    MINIMAP_POS_X = w - MINIMAP_WIDTH - 10
    MINIMAP_POS_Y = 10
    MINIMAP_RECT.topleft = (MINIMAP_POS_X, MINIMAP_POS_Y)

    # Terminal Input
    RECT_TERMINAL_INPUT.width = w - 20
    RECT_TERMINAL_INPUT.bottomleft = (10, h - 10)
    
    # Posição Botão Regenerar (Agora usa o novo tamanho W/H)
    RECT_BOTAO_REGEN_HUD.size = (BTN_HUD_REGEN_W, BTN_HUD_REGEN_H)
    RECT_BOTAO_REGEN_HUD.bottomleft = (10, RECT_TERMINAL_INPUT.top - 10)

    # Botões da Loja
    btn_y_start_loja = 180
    btn_y_spacing_loja = 70
    btn_x_loja = w // 2 - BTN_LOJA_W // 2
    RECT_BOTAO_MOTOR.topleft = (btn_x_loja, btn_y_start_loja)
    RECT_BOTAO_DANO.topleft = (btn_x_loja, btn_y_start_loja + btn_y_spacing_loja * 1)
    RECT_BOTAO_AUX.topleft = (btn_x_loja, btn_y_start_loja + btn_y_spacing_loja * 2)
    RECT_BOTAO_MAX_HP.topleft = (btn_x_loja, btn_y_start_loja + btn_y_spacing_loja * 3)
    RECT_BOTAO_ESCUDO.topleft = (btn_x_loja, btn_y_start_loja + btn_y_spacing_loja * 4)
   
    # Botão Reiniciar
    RECT_BOTAO_REINICIAR.center = (w // 2, h // 2 + 50)

    # Botão Upgrade no HUD (Agora usa o novo tamanho W/H)
    hud_y_spacing = FONT_HUD.get_height() + 10
    RECT_BOTAO_UPGRADE_HUD.size = (BTN_HUD_UPGRADE_W, BTN_HUD_UPGRADE_H)
    RECT_BOTAO_UPGRADE_HUD.topleft = (10, 35 + hud_y_spacing)
    
    # Menu Principal
    logo_y_pos = h // 3
    logo_height = 0
    if LOGO_JOGO:
        logo_height = LOGO_JOGO.get_height()
        RECT_LOGO_MENU = LOGO_JOGO.get_rect(center=(w // 2, logo_y_pos))
    else:
        fallback_text = FONT_TITULO.render("Nosso Jogo de Nave", True, BRANCO)
        logo_height = fallback_text.get_height()
        RECT_LOGO_MENU = fallback_text.get_rect(center=(w // 2, logo_y_pos))

    menu_btn_y_start = logo_y_pos + (logo_height // 2) + 50
    menu_btn_x = w // 2 - BTN_MENU_W // 2
    menu_btn_spacing = 70
    RECT_BOTAO_JOGAR_OFF.topleft = (menu_btn_x, menu_btn_y_start)
    RECT_BOTAO_MULTIPLAYER.topleft = (menu_btn_x, menu_btn_y_start + menu_btn_spacing)
    RECT_BOTAO_SAIR.topleft = (menu_btn_x, menu_btn_y_start + menu_btn_spacing * 2)

    multiplayer_btn_y_start = h // 2 - BTN_MENU_H - menu_btn_spacing // 2
    RECT_BOTAO_PVE_ONLINE.topleft = (menu_btn_x, multiplayer_btn_y_start)
    RECT_BOTAO_PVP_ONLINE.topleft = (menu_btn_x, multiplayer_btn_y_start + menu_btn_spacing)
    RECT_BOTAO_PVE_OFFLINE.topleft = (menu_btn_x, multiplayer_btn_y_start)
    RECT_BOTAO_PVP_OFFLINE.topleft = (menu_btn_x, multiplayer_btn_y_start + menu_btn_spacing)

    # Pausa
    RECT_PAUSE_FUNDO.center = (w // 2, h // 2)
    base_y_pause = RECT_PAUSE_FUNDO.top + 60
    spacing_pause_items = 15
    btn_height_with_spacing = BTN_PAUSA_MENU_H + spacing_pause_items 
    y_pos_voltar_nave = base_y_pause
    RECT_BOTAO_VOLTAR_NAVE.midtop = (RECT_PAUSE_FUNDO.centerx, y_pos_voltar_nave)
    y_pos_respawn = y_pos_voltar_nave
    RECT_BOTAO_RESPAWN_PAUSA.midtop = (RECT_PAUSE_FUNDO.centerx, y_pos_respawn)
    y_pos_espectador = y_pos_voltar_nave + btn_height_with_spacing
    RECT_BOTAO_ESPECTADOR.midtop = (RECT_PAUSE_FUNDO.centerx, y_pos_espectador)
    y_pos_voltar_menu = y_pos_espectador + btn_height_with_spacing
    RECT_BOTAO_VOLTAR_MENU.midtop = (RECT_PAUSE_FUNDO.centerx, y_pos_voltar_menu)
    y_pos_bots = RECT_BOTAO_VOLTAR_MENU.bottom + 25 
    RECT_TEXTO_BOTS.midtop = (RECT_PAUSE_FUNDO.centerx, y_pos_bots)
    spacing_pause_buttons_ctrl = 15 
    RECT_BOTAO_BOT_MENOS.midright = (RECT_TEXTO_BOTS.left - spacing_pause_buttons_ctrl, RECT_TEXTO_BOTS.centery)
    RECT_BOTAO_BOT_MAIS.midleft = (RECT_TEXTO_BOTS.right + spacing_pause_buttons_ctrl, RECT_TEXTO_BOTS.centery)
    RECT_TEXTO_VOLTAR.midbottom = (RECT_PAUSE_FUNDO.centerx, RECT_PAUSE_FUNDO.bottom - 20)

    # Login
    RECT_LOGIN_PAINEL.center = (w // 2, h // 2)
    input_y_pos = RECT_LOGIN_PAINEL.top + 100
    RECT_LOGIN_INPUT.center = (RECT_LOGIN_PAINEL.centerx, input_y_pos)
    dificuldade_y_pos = RECT_LOGIN_INPUT.bottom + 40
    spacing_arrows = 10
    RECT_LOGIN_DIFICULDADE_TEXT.center = (RECT_LOGIN_PAINEL.centerx, dificuldade_y_pos)
    RECT_LOGIN_DIFICULDADE_LEFT.midright = (RECT_LOGIN_DIFICULDADE_TEXT.left - spacing_arrows, dificuldade_y_pos)
    RECT_LOGIN_DIFICULDADE_RIGHT.midleft = (RECT_LOGIN_DIFICULDADE_TEXT.right + spacing_arrows, dificuldade_y_pos)
    btn_y_pos = RECT_LOGIN_DIFICULDADE_TEXT.bottom + 30
    RECT_LOGIN_BOTAO.center = (RECT_LOGIN_PAINEL.centerx, btn_y_pos)

    # Conexão
    RECT_CONNECT_PAINEL.center = (w // 2, h // 2)
    nome_y_pos = RECT_CONNECT_PAINEL.top + 100
    RECT_CONNECT_NOME.center = (RECT_CONNECT_PAINEL.centerx, nome_y_pos)
    ip_y_pos = RECT_CONNECT_NOME.bottom + 50
    RECT_CONNECT_IP.center = (RECT_CONNECT_PAINEL.centerx, ip_y_pos)
    btn_connect_y_pos = RECT_CONNECT_IP.bottom + 30
    RECT_CONNECT_BOTAO.center = (RECT_CONNECT_PAINEL.centerx, btn_connect_y_pos)


# --- Funções de Desenho (Menu, Login, etc) - Mantidas iguais ---
def desenhar_menu(surface, largura_tela, altura_tela):
    surface.fill(PRETO) 
    if LOGO_JOGO:
        surface.blit(LOGO_JOGO, RECT_LOGO_MENU)
    else:
        texto_titulo = FONT_TITULO.render("Nosso Jogo de Nave", True, BRANCO)
        surface.blit(texto_titulo, RECT_LOGO_MENU)
    
    def draw_menu_button(rect, text, text_color=PRETO, button_color=BRANCO):
        pygame.draw.rect(surface, button_color, rect, border_radius=5)
        text_surf = FONT_PADRAO.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

    draw_menu_button(RECT_BOTAO_JOGAR_OFF, "Jogar Offline")
    draw_menu_button(RECT_BOTAO_MULTIPLAYER, "Multijogador")
    draw_menu_button(RECT_BOTAO_SAIR, "Sair")

def desenhar_tela_nome(surface, nome_jogador_atual, input_nome_ativo, dificuldade_atual):
    surface.fill(PRETO)
    if LOGO_JOGO:
        surface.blit(LOGO_JOGO, RECT_LOGO_MENU)
    texto_titulo = FONT_TITULO.render("Digite seu nome", True, BRANCO)
    titulo_rect = texto_titulo.get_rect(center=(RECT_LOGIN_PAINEL.centerx, RECT_LOGIN_PAINEL.top + 40))
    surface.blit(texto_titulo, titulo_rect)

    cor_borda_input = BRANCO if input_nome_ativo else CINZA_BOTAO_DESLIGADO
    pygame.draw.rect(surface, PRETO, RECT_LOGIN_INPUT, border_radius=5)
    pygame.draw.rect(surface, cor_borda_input, RECT_LOGIN_INPUT, 2, border_radius=5)
    cursor = "_" if input_nome_ativo and pygame.time.get_ticks() % 1000 < 500 else ""
    texto_renderizado = FONT_PADRAO.render(f"{nome_jogador_atual}{cursor}", True, BRANCO)
    texto_rect = texto_renderizado.get_rect(midleft=(RECT_LOGIN_INPUT.x + 15, RECT_LOGIN_INPUT.centery))
    surface.blit(texto_renderizado, texto_rect)
    if not input_nome_ativo and not nome_jogador_atual:
        placeholder_surf = FONT_PADRAO.render("Nome...", True, CINZA_BOTAO_DESLIGADO)
        placeholder_rect = placeholder_surf.get_rect(midleft=(RECT_LOGIN_INPUT.x + 15, RECT_LOGIN_INPUT.centery))
        surface.blit(placeholder_surf, placeholder_rect)
        
    pygame.draw.rect(surface, BRANCO, RECT_LOGIN_DIFICULDADE_LEFT, border_radius=5)
    texto_left = FONT_TITULO.render("<", True, PRETO)
    texto_left_rect = texto_left.get_rect(center=RECT_LOGIN_DIFICULDADE_LEFT.center)
    surface.blit(texto_left, texto_left_rect)
    texto_dificuldade = FONT_PADRAO.render(f"Dificuldade: {dificuldade_atual}", True, BRANCO)
    texto_dificuldade_rect = texto_dificuldade.get_rect(center=RECT_LOGIN_DIFICULDADE_TEXT.center)
    surface.blit(texto_dificuldade, texto_dificuldade_rect)
    pygame.draw.rect(surface, BRANCO, RECT_LOGIN_DIFICULDADE_RIGHT, border_radius=5)
    texto_right = FONT_TITULO.render(">", True, PRETO)
    texto_right_rect = texto_right.get_rect(center=RECT_LOGIN_DIFICULDADE_RIGHT.center)
    surface.blit(texto_right, texto_right_rect)
    pygame.draw.rect(surface, BRANCO, RECT_LOGIN_BOTAO, border_radius=5)
    texto_botao = FONT_PADRAO.render("Continuar", True, PRETO)
    texto_botao_rect = texto_botao.get_rect(center=RECT_LOGIN_BOTAO.center)
    surface.blit(texto_botao, texto_botao_rect)

def desenhar_tela_modo_multiplayer(surface, largura_tela, altura_tela, pvp_disponivel=False):
    surface.fill(PRETO) 
    if LOGO_JOGO: surface.blit(LOGO_JOGO, RECT_LOGO_MENU)
    texto_titulo = FONT_TITULO.render("Modo Multijogador", True, BRANCO)
    titulo_rect = texto_titulo.get_rect(midbottom=(largura_tela // 2, RECT_BOTAO_PVE_ONLINE.top - 50))
    surface.blit(texto_titulo, titulo_rect)

    def draw_menu_button(rect, text, text_color=PRETO, button_color=BRANCO):
        pygame.draw.rect(surface, button_color, rect, border_radius=5)
        text_surf = FONT_PADRAO.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

    draw_menu_button(RECT_BOTAO_PVE_ONLINE, "Jogador VS Todos")
    if pvp_disponivel:
        draw_menu_button(RECT_BOTAO_PVP_ONLINE, "Jogador VS Jogador", text_color=PRETO, button_color=BRANCO)
    else:
        draw_menu_button(RECT_BOTAO_PVP_ONLINE, "Jogador VS Jogador", text_color=PRETO, button_color=CINZA_BOTAO_DESLIGADO)
    texto_voltar = FONT_PADRAO.render("ESC para Voltar", True, CINZA_BOTAO_DESLIGADO)
    voltar_rect = texto_voltar.get_rect(midbottom=(largura_tela // 2, altura_tela - 50))
    surface.blit(texto_voltar, voltar_rect)

def desenhar_tela_modo_offline(surface, largura_tela, altura_tela):
    surface.fill(PRETO) 
    if LOGO_JOGO: surface.blit(LOGO_JOGO, RECT_LOGO_MENU)
    texto_titulo = FONT_TITULO.render("Modo de Jogo Offline", True, BRANCO)
    titulo_rect = texto_titulo.get_rect(midbottom=(largura_tela // 2, RECT_BOTAO_PVE_OFFLINE.top - 50))
    surface.blit(texto_titulo, titulo_rect)
    def draw_menu_button(rect, text, text_color=PRETO, button_color=BRANCO):
        pygame.draw.rect(surface, button_color, rect, border_radius=5)
        text_surf = FONT_PADRAO.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)
    draw_menu_button(RECT_BOTAO_PVE_OFFLINE, "Jogador VS Todos")
    draw_menu_button(RECT_BOTAO_PVP_OFFLINE, "Jogador VS Jogador")
    texto_voltar = FONT_PADRAO.render("ESC para Voltar", True, CINZA_BOTAO_DESLIGADO)
    voltar_rect = texto_voltar.get_rect(midbottom=(largura_tela // 2, altura_tela - 50))
    surface.blit(texto_voltar, voltar_rect)

def desenhar_loja(surface, nave, largura_tela, altura_tela, client_socket=None):
    _garantir_imagens_loja_carregadas()
    fundo_loja = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
    fundo_loja.fill(CINZA_LOJA_FUNDO)
    surface.blit(fundo_loja, (0, 0))
    texto_titulo = FONT_TITULO.render("ESTAÇÃO DE UPGRADES", True, BRANCO)
    surface.blit(texto_titulo, (largura_tela // 2 - texto_titulo.get_width() // 2, 40))
    cor_pontos = AMARELO_BOMBA if nave.pontos_upgrade_disponiveis > 0 else BRANCO
    texto_pontos = FONT_TITULO.render(f"Pontos: {nave.pontos_upgrade_disponiveis}", True, cor_pontos)
    surface.blit(texto_pontos, (largura_tela // 2 - texto_pontos.get_width() // 2, 90))
    limite_texto = f"Slots Usados: {nave.total_upgrades_feitos} / {MAX_TOTAL_UPGRADES}"
    if nave.pontos > 0: pass 
    elif nave.pontos_upgrade_disponiveis > 0 or nave.total_upgrades_feitos > 0: 
        limite_texto = f"Slots Usados: {nave.total_upgrades_feitos} / {pvp_s.PONTOS_ATRIBUTOS_INICIAIS}"
    texto_limite = FONT_HUD_DETALHES.render(limite_texto, True, CINZA_BOTAO_DESLIGADO)
    surface.blit(texto_limite, (largura_tela // 2 - texto_limite.get_width() // 2, 130))

    is_pve = nave.pontos > 0
    pode_comprar_geral = False
    if is_pve:
        pode_comprar_geral = nave.pontos_upgrade_disponiveis > 0 and nave.total_upgrades_feitos < MAX_TOTAL_UPGRADES
    else: 
        pode_comprar_geral = nave.pontos_upgrade_disponiveis > 0
    custo_padrao = 1

    ativo_motor = pode_comprar_geral and nave.nivel_motor < MAX_NIVEL_MOTOR
    desenhar_botao_customizado(
        surface, RECT_BOTAO_MOTOR, IMAGENS_LOJA["motor"], 
        nave.nivel_motor, MAX_NIVEL_MOTOR, custo_padrao, nave.pontos_upgrade_disponiveis, ativo_motor
    )
    ativo_dano = pode_comprar_geral and nave.nivel_dano < MAX_NIVEL_DANO
    desenhar_botao_customizado(
        surface, RECT_BOTAO_DANO, IMAGENS_LOJA["dano"], 
        nave.nivel_dano, MAX_NIVEL_DANO, custo_padrao, nave.pontos_upgrade_disponiveis, ativo_dano
    )
    if client_socket: num_ativos = nave.nivel_aux 
    else: num_ativos = len(nave.grupo_auxiliares_ativos) 
    max_aux = len(nave.lista_todas_auxiliares) 
    custo_aux = CUSTOS_AUXILIARES[num_ativos] if num_ativos < max_aux else 0
    ativo_aux = pode_comprar_geral and num_ativos < max_aux and nave.pontos_upgrade_disponiveis >= custo_aux
    desenhar_botao_customizado(
        surface, RECT_BOTAO_AUX, IMAGENS_LOJA["auxiliar"], 
        num_ativos, max_aux, custo_aux, nave.pontos_upgrade_disponiveis, ativo_aux
    )
    MAX_NIVEL_VIDA = len(VIDA_POR_NIVEL) - 1 
    ativo_hp = pode_comprar_geral and nave.nivel_max_vida < MAX_NIVEL_VIDA
    desenhar_botao_customizado(
        surface, RECT_BOTAO_MAX_HP, IMAGENS_LOJA["max_health"], 
        nave.nivel_max_vida, MAX_NIVEL_VIDA, custo_padrao, nave.pontos_upgrade_disponiveis, ativo_hp
    )
    ativo_escudo = pode_comprar_geral and nave.nivel_escudo < MAX_NIVEL_ESCUDO
    desenhar_botao_customizado(
        surface, RECT_BOTAO_ESCUDO, IMAGENS_LOJA["escudo"], 
        nave.nivel_escudo, MAX_NIVEL_ESCUDO, custo_padrao, nave.pontos_upgrade_disponiveis, ativo_escudo
    )
    texto_fechar = FONT_HUD_DETALHES.render("[V] Voltar ao Jogo", True, BRANCO)
    surface.blit(texto_fechar, (largura_tela // 2 - texto_fechar.get_width() // 2, altura_tela - 40))

def desenhar_hud(surface, nave, estado_jogo):
    if estado_jogo == "ESPECTADOR":
        return

    _garantir_imagens_loja_carregadas()

    pos_x_detalhes = 10
    pos_y_atual_detalhes = 10
    hud_line_height = FONT_HUD.get_height() + 5
    
    if estado_jogo == "JOGANDO":
        texto_pontos = FONT_HUD.render(f"Pontos: {nave.pontos}", True, BRANCO)
        surface.blit(texto_pontos, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += hud_line_height
    
    vida_display = round(max(0, nave.vida_atual), 1)
    texto_vida = FONT_HUD.render(f"Vida: {vida_display} / {nave.max_vida}", True, VERDE_VIDA)
    surface.blit(texto_vida, (pos_x_detalhes, pos_y_atual_detalhes))
    pos_y_atual_detalhes += hud_line_height
    
    if estado_jogo != "GAME_OVER" and nave.vida_atual > 0:
        cor_pts_upgrade = AMARELO_BOMBA if nave.pontos_upgrade_disponiveis > 0 else BRANCO
        texto_pts_up = FONT_HUD.render(f"Pts Upgrade: {nave.pontos_upgrade_disponiveis}", True, cor_pts_upgrade)
        surface.blit(texto_pts_up, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += hud_line_height + 5 
        
        RECT_BOTAO_UPGRADE_HUD.topleft = (pos_x_detalhes, pos_y_atual_detalhes)
        if estado_jogo in ["JOGANDO", "PVP_LOBBY", "PVP_COUNTDOWN"]:
            desenhar_botao_hud(
                surface, RECT_BOTAO_UPGRADE_HUD, 
                IMAGENS_LOJA["btn_loja"], "LOJA (V)", True
            )
            
            txt_atalho = FONT_RANKING.render("[ V ]", True, AMARELO_BOMBA)
            rect_atalho = txt_atalho.get_rect(midleft=(RECT_BOTAO_UPGRADE_HUD.right + 8, RECT_BOTAO_UPGRADE_HUD.centery))
            surface.blit(txt_atalho, rect_atalho)
        
        pos_y_atual_detalhes = RECT_BOTAO_UPGRADE_HUD.bottom + 15

        line_spacing_detalhes = FONT_HUD_DETALHES.get_height() + 2
        texto_motor = FONT_HUD_DETALHES.render(f"Motor: Nv {nave.nivel_motor}/{MAX_NIVEL_MOTOR}", True, BRANCO)
        surface.blit(texto_motor, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += line_spacing_detalhes
        texto_dano = FONT_HUD_DETALHES.render(f"Dano: Nv {nave.nivel_dano}/{MAX_NIVEL_DANO}", True, BRANCO)
        surface.blit(texto_dano, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += line_spacing_detalhes
        texto_escudo = FONT_HUD_DETALHES.render(f"Escudo: Nv {nave.nivel_escudo}/{MAX_NIVEL_ESCUDO}", True, BRANCO)
        surface.blit(texto_escudo, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += line_spacing_detalhes
        if hasattr(nave, 'nivel_aux'): num_aux = nave.nivel_aux
        else: num_aux = len(nave.grupo_auxiliares_ativos)
        max_aux = len(nave.lista_todas_auxiliares)
        texto_aux = FONT_HUD_DETALHES.render(f"Auxiliares: {num_aux}/{max_aux}", True, BRANCO)
        surface.blit(texto_aux, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += line_spacing_detalhes + 10 

        if estado_jogo == "JOGANDO":
            is_regenerando = getattr(nave, 'esta_regenerando', False)
            vida_cheia = nave.vida_atual >= nave.max_vida
            ativo = not is_regenerando and not vida_cheia
            txt_alt = "REGENERAR (R)"
            if is_regenerando: txt_alt = "Regenerando..."
            elif vida_cheia: txt_alt = "Vida Cheia"
            
            desenhar_botao_hud(
                surface, RECT_BOTAO_REGEN_HUD,
                IMAGENS_LOJA["btn_regenerar"], txt_alt, ativo
            )
            
            if not vida_cheia: 
                txt_atalho_r = FONT_RANKING.render("[ R ]", True, AMARELO_BOMBA)
                rect_atalho_r = txt_atalho_r.get_rect(midleft=(RECT_BOTAO_REGEN_HUD.right + 8, RECT_BOTAO_REGEN_HUD.centery))
                surface.blit(txt_atalho_r, rect_atalho_r)

def desenhar_minimapa(surface, player, bots, estado_jogo, map_width, map_height, online_players, meu_nome_rede, 
                         alvo_camera_atual, camera_zoom, jogador_esta_vivo_espectador=False):
    fundo_mini = pygame.Surface((MINIMAP_WIDTH, MINIMAP_HEIGHT), pygame.SRCALPHA)
    fundo_mini.fill(MINIMAP_FUNDO)
    surface.blit(fundo_mini, (MINIMAP_POS_X, MINIMAP_POS_Y))
    pygame.draw.rect(surface, BRANCO, MINIMAP_RECT, 1)
    if map_width == 0 or map_height == 0: return 
    ratio_x = MINIMAP_WIDTH / map_width
    ratio_y = MINIMAP_HEIGHT / map_height
    def get_pos_minimapa(pos_mundo_vec):
        if pos_mundo_vec is None: return (0, 0) 
        try:
            map_x = int((pos_mundo_vec.x * ratio_x) + MINIMAP_POS_X)
            map_y = int((pos_mundo_vec.y * ratio_y) + MINIMAP_POS_Y)
            map_x = max(MINIMAP_POS_X + 1, min(map_x, MINIMAP_POS_X + MINIMAP_WIDTH - 2))
            map_y = max(MINIMAP_POS_Y + 1, min(map_y, MINIMAP_POS_Y + MINIMAP_HEIGHT - 2))
            return (map_x, map_y)
        except (AttributeError, TypeError): return (0, 0) 
    if camera_zoom < 1.0 and alvo_camera_atual: 
        largura_tela, altura_tela = surface.get_size()
        view_width_mundo = largura_tela / camera_zoom
        view_height_mundo = altura_tela / camera_zoom
        cam_center_pos = alvo_camera_atual.posicao
        view_top_left_mundo = pygame.math.Vector2(cam_center_pos.x - (view_width_mundo / 2), cam_center_pos.y - (view_height_mundo / 2))
        view_top_left_mini = get_pos_minimapa(view_top_left_mundo)
        view_width_mini = int(view_width_mundo * ratio_x)
        view_height_mini = int(view_height_mundo * ratio_y)
        rect_visao = pygame.Rect(view_top_left_mini[0], view_top_left_mini[1], view_width_mini, view_height_mini)
        pygame.draw.rect(surface, BRANCO, rect_visao, 1) 
    if online_players:
        for nome, state in online_players.items():
            if nome == meu_nome_rede: continue
            if state.get('hp', 0) <= 0: continue
            pos_vec = pygame.math.Vector2(state['x'], state['y'])
            pygame.draw.circle(surface, LARANJA_BOT, get_pos_minimapa(pos_vec), 2)
    else:
        for bot in bots:
            if bot == player: continue
            pygame.draw.circle(surface, LARANJA_BOT, get_pos_minimapa(bot.posicao), 2)
    if (estado_jogo == "JOGANDO" or estado_jogo.startswith("PVP_")) and player.posicao_alvo_mouse and player.vida_atual > 0: 
        start_mini_v = pygame.math.Vector2(get_pos_minimapa(player.posicao))
        end_mini_v = pygame.math.Vector2(get_pos_minimapa(player.posicao_alvo_mouse))
        vec = end_mini_v - start_mini_v
        length = vec.length()
        if length > 0:
            try:
                direction = vec.normalize()
                dash_len = 4; gap_len = 3; total_step = dash_len + gap_len
                current_dist = 0
                while current_dist < length:
                    start_dash = start_mini_v + direction * current_dist
                    end_dist = min(current_dist + dash_len, length)
                    end_dash = start_mini_v + direction * end_dist
                    pygame.draw.line(surface, BRANCO, (start_dash.x, start_dash.y), (end_dash.x, end_dash.y), 1)
                    current_dist += total_step
            except ValueError: pass 
    if estado_jogo == "JOGANDO" or estado_jogo.startswith("PVP_"): 
        if player.vida_atual > 0: pygame.draw.circle(surface, AZUL_NAVE, get_pos_minimapa(alvo_camera_atual.posicao), 3)
    elif estado_jogo == "ESPECTADOR":
        if alvo_camera_atual: pygame.draw.circle(surface, AZUL_NAVE, get_pos_minimapa(alvo_camera_atual.posicao), 3)

def desenhar_ranking(surface, lista_top_5, nave_player):
    pos_x_base = MINIMAP_POS_X
    pos_y_base = MINIMAP_POS_Y + MINIMAP_HEIGHT + 10
    ranking_width = MINIMAP_WIDTH
    titulo_surf = FONT_HUD.render("RANKING", True, BRANCO)
    titulo_x = pos_x_base + (ranking_width - titulo_surf.get_width()) // 2
    surface.blit(titulo_surf, (titulo_x, pos_y_base))
    pos_y_linha_atual = pos_y_base + titulo_surf.get_height() + 5
    for i, nave in enumerate(lista_top_5):
        cor_texto = LARANJA_BOT if nave != nave_player else VERDE_VIDA
        nome_nave = nave.nome
        if len(nome_nave) > 12: nome_nave = nome_nave[:11] + "."
        texto_nome = f"{i + 1}. {nome_nave}"
        nome_surf = FONT_RANKING.render(texto_nome, True, cor_texto)
        surface.blit(nome_surf, (pos_x_base + 5, pos_y_linha_atual))
        if hasattr(nave, 'max_vida'):
            if nave.pontos == 0: texto_pontos = f"{int(nave.vida_atual)} HP"
            else: texto_pontos = f"{nave.pontos}"
        else: texto_pontos = f"{nave.pontos}"
        pontos_surf = FONT_RANKING.render(texto_pontos, True, cor_texto)
        pontos_x = pos_x_base + ranking_width - pontos_surf.get_width() - 5
        surface.blit(pontos_surf, (pontos_x, pos_y_linha_atual))
        pos_y_linha_atual += FONT_RANKING.get_height() + 2

def desenhar_terminal(surface, texto_atual, largura_tela, altura_tela):
    fundo_terminal = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
    fundo_terminal.fill(CINZA_LOJA_FUNDO)
    surface.blit(fundo_terminal, (0, 0))
    texto_instrucao = FONT_PADRAO.render("Aperte ENTER para executar ou ' para fechar", True, BRANCO)
    surface.blit(texto_instrucao, (largura_tela // 2 - texto_instrucao.get_width() // 2, RECT_TERMINAL_INPUT.y - 40))
    pygame.draw.rect(surface, PRETO, RECT_TERMINAL_INPUT)
    pygame.draw.rect(surface, BRANCO, RECT_TERMINAL_INPUT, 2)
    cursor = "_" if pygame.time.get_ticks() % 1000 < 500 else ""
    texto_renderizado = FONT_TERMINAL.render(f"> {texto_atual}{cursor}", True, BRANCO)
    surface.blit(texto_renderizado, (RECT_TERMINAL_INPUT.x + 10, RECT_TERMINAL_INPUT.y + (RECT_TERMINAL_INPUT.height - texto_renderizado.get_height()) // 2))

def desenhar_game_over(surface, largura_tela, altura_tela, 
                       winner_name=None, restart_timer=0): # Novos argumentos
    
    # Fundo escuro
    s = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
    s.fill((0,0,0, 200))
    surface.blit(s, (0,0))

    if winner_name:
        # Tela de Vitória PVP
        texto_fim = FONT_TITULO.render("FIM DE JOGO", True, VERMELHO_VIDA_FUNDO)
        texto_venc = FONT_TITULO.render(f"Vencedor: {winner_name}", True, VERDE_VIDA)
        
        surface.blit(texto_fim, (largura_tela//2 - texto_fim.get_width()//2, altura_tela//3))
        surface.blit(texto_venc, (largura_tela//2 - texto_venc.get_width()//2, altura_tela//2))
        
        if restart_timer > 0:
            texto_reinicio = FONT_PADRAO.render(f"Nova partida em {restart_timer}s...", True, BRANCO)
            surface.blit(texto_reinicio, (largura_tela//2 - texto_reinicio.get_width()//2, altura_tela * 0.7))
            
        texto_sair = FONT_HUD_DETALHES.render("[ESC] Sair para o Menu", True, CINZA_BOTAO_DESLIGADO)
        surface.blit(texto_sair, (largura_tela//2 - texto_sair.get_width()//2, altura_tela * 0.8))

    else:
        # Game Over PVE Padrão
        texto_game_over = FONT_TITULO.render("Você Morreu!", True, VERMELHO_VIDA_FUNDO)
        surface.blit(texto_game_over, (largura_tela // 2 - texto_game_over.get_width() // 2, altura_tela // 2 - 50))
        
        pygame.draw.rect(surface, BRANCO, RECT_BOTAO_REINICIAR, border_radius=5)
        texto_botao = FONT_PADRAO.render("Respawnar", True, PRETO) 
        surface.blit(texto_botao, (RECT_BOTAO_REINICIAR.centerx - texto_botao.get_width() // 2, RECT_BOTAO_REINICIAR.centery - texto_botao.get_height() // 2))
        
def desenhar_tela_conexao(surface, nome_str, ip_str, input_ativo_key, mensagem_status="", cor_status=BRANCO):
    surface.fill(PRETO)
    if LOGO_JOGO:
        logo_rect = LOGO_JOGO.get_rect(center=(surface.get_width() // 2, surface.get_height() // 3))
        surface.blit(LOGO_JOGO, logo_rect)
    texto_titulo = FONT_TITULO.render("Conectar ao Servidor", True, BRANCO)
    titulo_rect = texto_titulo.get_rect(center=(RECT_CONNECT_PAINEL.centerx, RECT_CONNECT_PAINEL.top + 40))
    surface.blit(texto_titulo, titulo_rect)
    
    def draw_input_box(rect, label_text, text_str, is_active):
        label_surf = FONT_PADRAO.render(label_text, True, BRANCO)
        label_rect = label_surf.get_rect(midbottom=(rect.centerx, rect.top - 5))
        surface.blit(label_surf, label_rect)
        cor_borda = BRANCO if is_active else CINZA_BOTAO_DESLIGADO
        pygame.draw.rect(surface, PRETO, rect, border_radius=5)
        pygame.draw.rect(surface, cor_borda, rect, 2, border_radius=5)
        cursor = "_" if is_active and pygame.time.get_ticks() % 1000 < 500 else ""
        texto_renderizado = FONT_PADRAO.render(f"{text_str}{cursor}", True, BRANCO)
        texto_rect = texto_renderizado.get_rect(midleft=(rect.x + 15, rect.centery))
        surface.blit(texto_renderizado, texto_rect)
        
    draw_input_box(RECT_CONNECT_NOME, "Seu Nome:", nome_str, input_ativo_key == "nome")
    draw_input_box(RECT_CONNECT_IP, "IP do Servidor:", ip_str, input_ativo_key == "ip")
    
    # Desenha o botão
    pygame.draw.rect(surface, BRANCO, RECT_CONNECT_BOTAO, border_radius=5)
    texto_botao = FONT_PADRAO.render("Conectar", True, PRETO)
    texto_botao_rect = texto_botao.get_rect(center=RECT_CONNECT_BOTAO.center)
    surface.blit(texto_botao, texto_botao_rect)

    # --- NOVO: Desenha mensagem de status/erro abaixo do botão ---
    if mensagem_status:
        texto_status = FONT_RANKING.render(mensagem_status, True, cor_status)
        rect_status = texto_status.get_rect(midtop=(RECT_CONNECT_PAINEL.centerx, RECT_CONNECT_BOTAO.bottom + 15))
        surface.blit(texto_status, rect_status)
        
def desenhar_tela_erro(surface, mensagem_erro):
    surface.fill(PRETO)
    
    # Título de Erro
    texto_titulo = FONT_TITULO.render("ERRO DE CONEXÃO", True, VERMELHO_VIDA_FUNDO)
    rect_titulo = texto_titulo.get_rect(center=(surface.get_width() // 2, surface.get_height() // 3))
    surface.blit(texto_titulo, rect_titulo)
    
    # Mensagem do Erro
    texto_msg = FONT_PADRAO.render(f"{mensagem_erro}", True, BRANCO)
    rect_msg = texto_msg.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
    surface.blit(texto_msg, rect_msg)
    
    # Instrução
    texto_voltar = FONT_PADRAO.render("Pressione ENTER para voltar ao Menu", True, CINZA_BOTAO_DESLIGADO)
    rect_voltar = texto_voltar.get_rect(center=(surface.get_width() // 2, surface.get_height() * 0.7))
    surface.blit(texto_voltar, rect_voltar)
    
    
def desenhar_lista_vivos_pvp(surface, lista_jogadores_vivos):
    """
    Desenha uma lista simples de jogadores vivos para o modo PVP.
    """
    pos_x_base = MINIMAP_POS_X
    pos_y_base = MINIMAP_POS_Y + MINIMAP_HEIGHT + 10
    ranking_width = MINIMAP_WIDTH
    
    # Título
    titulo_surf = FONT_HUD.render("JOGADORES VIVOS", True, BRANCO)
    titulo_x = pos_x_base + (ranking_width - titulo_surf.get_width()) // 2
    surface.blit(titulo_surf, (titulo_x, pos_y_base))
    
    pos_y_linha_atual = pos_y_base + titulo_surf.get_height() + 5
    
    # Lista de Nomes
    for i, nave in enumerate(lista_jogadores_vivos):
        cor_texto = VERDE_VIDA 
        nome_nave = nave.nome
        if len(nome_nave) > 16: nome_nave = nome_nave[:15] + "."
        
        nome_surf = FONT_RANKING.render(nome_nave, True, cor_texto)
        surface.blit(nome_surf, (pos_x_base + 5, pos_y_linha_atual))
        
        pos_y_linha_atual += FONT_RANKING.get_height() + 2