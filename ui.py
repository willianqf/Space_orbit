# ui.py
import pygame
# Importa todas as constantes e fontes de settings
from settings import *
import multi.pvp_settings as pvp_s # <-- MODIFICAÇÃO: CORREÇÃO DO BUG (importação)

# --- Variáveis Globais de UI (Tamanho e Posição) ---
# Tamanhos Fixos
BTN_LOJA_W, BTN_LOJA_H = 300, 50
BTN_MENU_W, BTN_MENU_H = 250, 50
BTN_REINICIAR_W, BTN_REINICIAR_H = 200, 50
BTN_HUD_UPGRADE_W, BTN_HUD_UPGRADE_H = 100, 30
TERMINAL_H = 35
# --- INÍCIO: MODIFICAÇÃO (Tamanho Painel Pausa) ---
PAUSE_PANEL_W, PAUSE_PANEL_H = 350, 400 # Aumentado para caber novos botões
# --- FIM: MODIFICAÇÃO ---
BTN_PAUSE_CTRL_W, BTN_PAUSE_CTRL_H = 40, 40

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

# --- (Botão Regenerar - Sem alteração) ---
BTN_HUD_REGEN_W, BTN_HUD_REGEN_H = 160, 30

# --- INÍCIO: MODIFICAÇÃO (Novos Tamanhos de Botão de Pausa) ---
BTN_PAUSA_MENU_W, BTN_PAUSA_MENU_H = 250, 40
# --- FIM: MODIFICAÇÃO ---


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

# --- INÍCIO: MODIFICAÇÃO (Novos Rects Seleção Multiplayer) ---
RECT_BOTAO_PVE_ONLINE = pygame.Rect(0, 0, BTN_MENU_W, BTN_MENU_H)
RECT_BOTAO_PVP_ONLINE = pygame.Rect(0, 0, BTN_MENU_W, BTN_MENU_H)
# --- FIM: MODIFICAÇÃO ---

# --- INÍCIO: MODIFICAÇÃO (Novos Rects Pausa) ---
RECT_PAUSE_FUNDO = pygame.Rect(0, 0, PAUSE_PANEL_W, PAUSE_PANEL_H)
RECT_TEXTO_BOTS = pygame.Rect(0, 0, 200, 40)
RECT_BOTAO_BOT_MENOS = pygame.Rect(0, 0, BTN_PAUSE_CTRL_W, BTN_PAUSE_CTRL_H)
RECT_BOTAO_BOT_MAIS = pygame.Rect(0, 0, BTN_PAUSE_CTRL_W, BTN_PAUSE_CTRL_H)
RECT_BOTAO_VOLTAR_MENU = pygame.Rect(0, 0, BTN_PAUSA_MENU_W, BTN_PAUSA_MENU_H)
RECT_BOTAO_ESPECTADOR = pygame.Rect(0, 0, BTN_PAUSA_MENU_W, BTN_PAUSA_MENU_H)
RECT_BOTAO_VOLTAR_NAVE = pygame.Rect(0, 0, BTN_PAUSA_MENU_W, BTN_PAUSA_MENU_H)
RECT_BOTAO_RESPAWN_PAUSA = pygame.Rect(0, 0, BTN_PAUSA_MENU_W, BTN_PAUSA_MENU_H)
RECT_TEXTO_VOLTAR = pygame.Rect(0, 0, 200, 30)
# --- FIM: MODIFICAÇÃO ---

# Rects Login
RECT_LOGIN_PAINEL = pygame.Rect(0, 0, LOGIN_PANEL_W, LOGIN_PANEL_H)
RECT_LOGIN_INPUT = pygame.Rect(0, 0, LOGIN_INPUT_W, LOGIN_INPUT_H)
RECT_LOGIN_BOTAO = pygame.Rect(0, 0, LOGIN_BTN_W, LOGIN_BTN_H)
RECT_LOGIN_DIFICULDADE_TEXT = pygame.Rect(0, 0, LOGIN_DIFICULDADE_W, LOGIN_DIFICULDADE_H)
RECT_LOGIN_DIFICULDADE_LEFT = pygame.Rect(0, 0, LOGIN_ARROW_W, LOGIN_ARROW_H)
RECT_LOGIN_DIFICULDADE_RIGHT = pygame.Rect(0, 0, LOGIN_ARROW_W, LOGIN_ARROW_H)
# Rects Conexão
RECT_CONNECT_PAINEL = pygame.Rect(0, 0, CONNECT_PANEL_W, CONNECT_PANEL_H)
RECT_CONNECT_NOME = pygame.Rect(0, 0, CONNECT_INPUT_W, CONNECT_INPUT_H)
RECT_CONNECT_IP = pygame.Rect(0, 0, CONNECT_INPUT_W, CONNECT_INPUT_H)
RECT_CONNECT_BOTAO = pygame.Rect(0, 0, CONNECT_BTN_W, CONNECT_BTN_H)

# --- (Rect Regenerar - Sem alteração) ---
RECT_BOTAO_REGEN_HUD = pygame.Rect(0, 0, BTN_HUD_REGEN_W, BTN_HUD_REGEN_H)


# Variáveis para guardar posições calculadas
MINIMAP_POS_X = 0
MINIMAP_POS_Y = 0

def recalculate_ui_positions(w, h):
    global MINIMAP_POS_X, MINIMAP_POS_Y, MINIMAP_RECT, RECT_TERMINAL_INPUT
    global RECT_BOTAO_MOTOR, RECT_BOTAO_DANO, RECT_BOTAO_AUX, RECT_BOTAO_MAX_HP, RECT_BOTAO_ESCUDO
    global RECT_BOTAO_REINICIAR, RECT_BOTAO_UPGRADE_HUD
    global RECT_BOTAO_JOGAR_OFF, RECT_BOTAO_MULTIPLAYER, RECT_BOTAO_SAIR
    # --- INÍCIO: MODIFICAÇÃO (Globais Seleção Multiplayer) ---
    global RECT_BOTAO_PVE_ONLINE, RECT_BOTAO_PVP_ONLINE
    # --- FIM: MODIFICAÇÃO ---
    # --- INÍCIO: MODIFICAÇÃO (Globais Pausa) ---
    global RECT_PAUSE_FUNDO, RECT_TEXTO_BOTS, RECT_BOTAO_BOT_MENOS, RECT_BOTAO_BOT_MAIS
    global RECT_BOTAO_VOLTAR_MENU, RECT_BOTAO_ESPECTADOR, RECT_BOTAO_VOLTAR_NAVE
    global RECT_BOTAO_RESPAWN_PAUSA, RECT_TEXTO_VOLTAR
    # --- FIM: MODIFICAÇÃO ---
    global RECT_LOGIN_PAINEL, RECT_LOGIN_INPUT, RECT_LOGIN_BOTAO
    global RECT_LOGIN_DIFICULDADE_TEXT, RECT_LOGIN_DIFICULDADE_LEFT, RECT_LOGIN_DIFICULDADE_RIGHT
    global RECT_CONNECT_PAINEL, RECT_CONNECT_NOME, RECT_CONNECT_IP, RECT_CONNECT_BOTAO
    global RECT_BOTAO_REGEN_HUD

    # Minimapa
    MINIMAP_POS_X = w - MINIMAP_WIDTH - 10
    MINIMAP_POS_Y = 10
    MINIMAP_RECT.topleft = (MINIMAP_POS_X, MINIMAP_POS_Y)

    # Terminal Input
    RECT_TERMINAL_INPUT.width = w - 20
    RECT_TERMINAL_INPUT.bottomleft = (10, h - 10)
    
    # Posição Botão Regenerar
    RECT_BOTAO_REGEN_HUD.bottomleft = (10, RECT_TERMINAL_INPUT.top - 10)

    # Botões da Loja (Centralizados)
    btn_y_start_loja = 180
    btn_y_spacing_loja = 70
    btn_x_loja = w // 2 - BTN_LOJA_W // 2
    RECT_BOTAO_MOTOR.topleft = (btn_x_loja, btn_y_start_loja)
    RECT_BOTAO_DANO.topleft = (btn_x_loja, btn_y_start_loja + btn_y_spacing_loja * 1)
    RECT_BOTAO_AUX.topleft = (btn_x_loja, btn_y_start_loja + btn_y_spacing_loja * 2)
    RECT_BOTAO_MAX_HP.topleft = (btn_x_loja, btn_y_start_loja + btn_y_spacing_loja * 3)
    RECT_BOTAO_ESCUDO.topleft = (btn_x_loja, btn_y_start_loja + btn_y_spacing_loja * 4)
   
    # Botão Reiniciar (Game Over - Centralizado)
    RECT_BOTAO_REINICIAR.center = (w // 2, h // 2 + 50)

    # Botão Upgrade no HUD (Canto superior esquerdo)
    hud_y_spacing = FONT_HUD.get_height() + 10
    RECT_BOTAO_UPGRADE_HUD.topleft = (10, 35 + hud_y_spacing)
    
    # Botões do Menu Principal (Centralizados)
    global RECT_LOGO_MENU 
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
    # --- INÍCIO: CORREÇÃO DO ERRO ---
    RECT_BOTAO_SAIR.topleft = (menu_btn_x, menu_btn_y_start + menu_btn_spacing * 2)
    # --- FIM: CORREÇÃO DO ERRO ---

    # --- INÍCIO: MODIFICAÇÃO (Posições Tela Seleção Multiplayer) ---
    # Centraliza os dois botões na tela
    multiplayer_btn_y_start = h // 2 - BTN_MENU_H - menu_btn_spacing // 2
    RECT_BOTAO_PVE_ONLINE.topleft = (menu_btn_x, multiplayer_btn_y_start)
    RECT_BOTAO_PVP_ONLINE.topleft = (menu_btn_x, multiplayer_btn_y_start + menu_btn_spacing)
    # --- FIM: MODIFICAÇÃO ---

    # --- INÍCIO: MODIFICAÇÃO (Posições do Menu de Pausa) ---
    RECT_PAUSE_FUNDO.center = (w // 2, h // 2)
    
    # Posição Y inicial para os botões
    base_y_pause = RECT_PAUSE_FUNDO.top + 60
    # Espaçamento vertical entre os botões
    spacing_pause_items = 15
    # Espaçamento entre o botão e o texto
    btn_height_with_spacing = BTN_PAUSA_MENU_H + spacing_pause_items 
    
    # Posições dos botões (de cima para baixo)
    y_pos_voltar_nave = base_y_pause
    RECT_BOTAO_VOLTAR_NAVE.midtop = (RECT_PAUSE_FUNDO.centerx, y_pos_voltar_nave)
    
    y_pos_respawn = y_pos_voltar_nave
    RECT_BOTAO_RESPAWN_PAUSA.midtop = (RECT_PAUSE_FUNDO.centerx, y_pos_respawn)
    
    y_pos_espectador = y_pos_voltar_nave + btn_height_with_spacing
    RECT_BOTAO_ESPECTADOR.midtop = (RECT_PAUSE_FUNDO.centerx, y_pos_espectador)
    
    y_pos_voltar_menu = y_pos_espectador + btn_height_with_spacing
    RECT_BOTAO_VOLTAR_MENU.midtop = (RECT_PAUSE_FUNDO.centerx, y_pos_voltar_menu)
    
    # Controles de Bots (abaixo dos botões principais)
    y_pos_bots = RECT_BOTAO_VOLTAR_MENU.bottom + 25 # Mais espaço
    RECT_TEXTO_BOTS.midtop = (RECT_PAUSE_FUNDO.centerx, y_pos_bots)
    
    spacing_pause_buttons_ctrl = 15 # Espaçamento dos botões +/-
    RECT_BOTAO_BOT_MENOS.midright = (RECT_TEXTO_BOTS.left - spacing_pause_buttons_ctrl, RECT_TEXTO_BOTS.centery)
    RECT_BOTAO_BOT_MAIS.midleft = (RECT_TEXTO_BOTS.right + spacing_pause_buttons_ctrl, RECT_TEXTO_BOTS.centery)
    
    # Texto "ESC" na parte inferior
    RECT_TEXTO_VOLTAR.midbottom = (RECT_PAUSE_FUNDO.centerx, RECT_PAUSE_FUNDO.bottom - 20)
    # --- FIM: MODIFICAÇÃO ---

    
    # Posições da Tela de Nome (Login)
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

    # Posições da Tela de Conexão
    RECT_CONNECT_PAINEL.center = (w // 2, h // 2)
    nome_y_pos = RECT_CONNECT_PAINEL.top + 100
    RECT_CONNECT_NOME.center = (RECT_CONNECT_PAINEL.centerx, nome_y_pos)
    ip_y_pos = RECT_CONNECT_NOME.bottom + 50
    RECT_CONNECT_IP.center = (RECT_CONNECT_PAINEL.centerx, ip_y_pos)
    btn_connect_y_pos = RECT_CONNECT_IP.bottom + 30
    RECT_CONNECT_BOTAO.center = (RECT_CONNECT_PAINEL.centerx, btn_connect_y_pos)


# --- Funções de Desenho ---

def desenhar_menu(surface, largura_tela, altura_tela):
    surface.fill(PRETO) 

    if LOGO_JOGO:
        logo_rect = LOGO_JOGO.get_rect(center=(largura_tela // 2, altura_tela // 3))
        surface.blit(LOGO_JOGO, logo_rect)
    else:
        texto_titulo = FONT_TITULO.render("Nosso Jogo de Nave", True, BRANCO)
        titulo_rect = texto_titulo.get_rect(center=(largura_tela // 2, altura_tela // 3))
        surface.blit(texto_titulo, titulo_rect)

    def draw_menu_button(rect, text, text_color=PRETO, button_color=BRANCO):
        pygame.draw.rect(surface, button_color, rect, border_radius=5)
        text_surf = FONT_PADRAO.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

    draw_menu_button(RECT_BOTAO_JOGAR_OFF, "Jogar Offline")
    draw_menu_button(RECT_BOTAO_MULTIPLAYER, "Multijogador")
    draw_menu_button(RECT_BOTAO_SAIR, "Sair")

def desenhar_tela_nome(surface, nome_jogador_atual, input_nome_ativo, dificuldade_atual):
    """ Desenha a tela de entrada de nome. """
    
    surface.fill(PRETO)
    if LOGO_JOGO:
        logo_rect = LOGO_JOGO.get_rect(center=(surface.get_width() // 2, surface.get_height() // 3))
        surface.blit(LOGO_JOGO, logo_rect)
        
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
        
    # Desenho da Dificuldade
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
    texto_botao = FONT_PADRAO.render("Respawn", True, PRETO)
    texto_botao_rect = texto_botao.get_rect(center=RECT_LOGIN_BOTAO.center)
    surface.blit(texto_botao, texto_botao_rect)

# --- INÍCIO: MODIFICAÇÃO (Assinatura da Função) ---
def desenhar_tela_modo_multiplayer(surface, largura_tela, altura_tela, pvp_disponivel=False):
    """ Desenha a tela de seleção de modo multiplayer (PVE vs PVP). """
# --- FIM: MODIFICAÇÃO ---
    surface.fill(PRETO) 

    # Desenha o logo ou título
    if LOGO_JOGO:
        logo_rect = LOGO_JOGO.get_rect(center=(largura_tela // 2, altura_tela // 3))
        surface.blit(LOGO_JOGO, logo_rect)
    
    texto_titulo = FONT_TITULO.render("Modo Multijogador", True, BRANCO)
    # Posiciona o título acima dos botões
    titulo_rect = texto_titulo.get_rect(midbottom=(largura_tela // 2, RECT_BOTAO_PVE_ONLINE.top - 50))
    surface.blit(texto_titulo, titulo_rect)

    # Função helper para desenhar botões (copiada de desenhar_menu)
    def draw_menu_button(rect, text, text_color=PRETO, button_color=BRANCO):
        pygame.draw.rect(surface, button_color, rect, border_radius=5)
        text_surf = FONT_PADRAO.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

    # Botão 1: Jogador VS Todos (Modo PVE Online)
    draw_menu_button(RECT_BOTAO_PVE_ONLINE, "Jogador VS Todos")
    
    # --- INÍCIO: MODIFICAÇÃO (Cor do Botão PVP) ---
    # Botão 2: Jogador VS Jogador (Modo PVP Online) - Agora dinâmico
    if pvp_disponivel:
        draw_menu_button(RECT_BOTAO_PVP_ONLINE, "Jogador VS Jogador", text_color=PRETO, button_color=BRANCO)
    else:
        draw_menu_button(RECT_BOTAO_PVP_ONLINE, "Jogador VS Jogador", text_color=PRETO, button_color=CINZA_BOTAO_DESLIGADO)
    # --- FIM: MODIFICAÇÃO ---
    
    # Instrução para voltar
    texto_voltar = FONT_PADRAO.render("ESC para Voltar", True, CINZA_BOTAO_DESLIGADO)
    voltar_rect = texto_voltar.get_rect(midbottom=(largura_tela // 2, altura_tela - 50))
    surface.blit(texto_voltar, voltar_rect)
# --- FIM: MODIFICAÇÃO ---


# --- INÍCIO: MODIFICAÇÃO (Remoção da função desenhar_pause) ---
# A função 'desenhar_pause' (linhas 309-380 do arquivo original) foi removida.
# Ela agora vive dentro do 'pause_menu.py'
# --- FIM: MODIFICAÇÃO ---


def desenhar_loja(surface, nave, largura_tela, altura_tela, client_socket=None):
    fundo_loja = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
    fundo_loja.fill(CINZA_LOJA_FUNDO)
    surface.blit(fundo_loja, (0, 0))
    texto_titulo = FONT_TITULO.render("LOJA DE UPGRADES", True, BRANCO)
    surface.blit(texto_titulo, (largura_tela // 2 - texto_titulo.get_width() // 2, 50))
    texto_pontos = FONT_PADRAO.render(f"Pontos de Upgrade: {nave.pontos_upgrade_disponiveis}", True, BRANCO)
    surface.blit(texto_pontos, (largura_tela // 2 - texto_pontos.get_width() // 2, 100))
    
    # --- INÍCIO: MODIFICAÇÃO (Não mostra limite no PVP) ---
    # (No PVE, o limite é MAX_TOTAL_UPGRADES)
    # (No PVP, o limite são os 10 pontos iniciais)
    limite_texto = f"Upgrades Feitos: {nave.total_upgrades_feitos} / {MAX_TOTAL_UPGRADES}"
    if nave.pontos > 0: # Se tem pontos, é PVE
        pass # Usa o limite_texto padrão
    elif nave.pontos_upgrade_disponiveis > 0 or nave.total_upgrades_feitos > 0: # Se não tem pontos, mas tem upgrades, é PVP
        limite_texto = f"Upgrades Feitos: {nave.total_upgrades_feitos} / {pvp_s.PONTOS_ATRIBUTOS_INICIAIS}"
    
    texto_limite = FONT_PADRAO.render(limite_texto, True, CINZA_BOTAO_DESLIGADO)
    surface.blit(texto_limite, (largura_tela // 2 - texto_limite.get_width() // 2, 130))
    # --- FIM: MODIFICAÇÃO ---


    def draw_text_on_button(rect, text, font, text_color):
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

    # --- INÍCIO: MODIFICAÇÃO (Lógica de Custo PVP) ---
    # Verifica se estamos em PVE (tem pontos de score) ou PVP (score 0, mas tem pontos de upgrade)
    is_pve = nave.pontos > 0
    
    if is_pve:
        pode_comprar_geral = nave.pontos_upgrade_disponiveis > 0 and nave.total_upgrades_feitos < MAX_TOTAL_UPGRADES
    else: # É PVP
        # No PVP, o único limite é ter pontos
        pode_comprar_geral = nave.pontos_upgrade_disponiveis > 0
    # --- FIM: MODIFICAÇÃO ---

    custo_padrao = 1
    pode_motor = pode_comprar_geral and nave.nivel_motor < MAX_NIVEL_MOTOR
    cor_motor = BRANCO if pode_motor else CINZA_BOTAO_DESLIGADO
    pygame.draw.rect(surface, cor_motor, RECT_BOTAO_MOTOR, border_radius=5)
    if nave.nivel_motor < MAX_NIVEL_MOTOR:
        txt_motor = f"Motor Nv. {nave.nivel_motor + 1}/{MAX_NIVEL_MOTOR} (Custo: {custo_padrao} Pt)"
    else: txt_motor = f"Motor Nv. {nave.nivel_motor} (MAX)"
    draw_text_on_button(RECT_BOTAO_MOTOR, txt_motor, FONT_PADRAO, PRETO)
    pode_dano = pode_comprar_geral and nave.nivel_dano < MAX_NIVEL_DANO
    cor_dano = BRANCO if pode_dano else CINZA_BOTAO_DESLIGADO
    pygame.draw.rect(surface, cor_dano, RECT_BOTAO_DANO, border_radius=5)
    if nave.nivel_dano < MAX_NIVEL_DANO:
        txt_dano = f"Dano Nv. {nave.nivel_dano + 1}/{MAX_NIVEL_DANO} (Custo: {custo_padrao} Pt)"
    else: txt_dano = f"Dano Nv. {nave.nivel_dano} (MAX)"
    draw_text_on_button(RECT_BOTAO_DANO, txt_dano, FONT_PADRAO, PRETO)
    
    if client_socket:
        num_ativos = nave.nivel_aux # Lê o número do estado sincronizado
    else:
        num_ativos = len(nave.grupo_auxiliares_ativos) # Lê os sprites locais

    max_aux = len(nave.lista_todas_auxiliares) # Assume 4
    if num_ativos < max_aux:
        custo_atual_aux = CUSTOS_AUXILIARES[num_ativos]
        txt_aux = f"Comprar Auxiliar {num_ativos + 1}/{max_aux} (Custo: {custo_atual_aux} Pts)"
        pode_aux = pode_comprar_geral and nave.pontos_upgrade_disponiveis >= custo_atual_aux
    else:
        txt_aux = "Máx. Auxiliares"
        pode_aux = False
    cor_aux = BRANCO if pode_aux else CINZA_BOTAO_DESLIGADO
    pygame.draw.rect(surface, cor_aux, RECT_BOTAO_AUX, border_radius=5)
    draw_text_on_button(RECT_BOTAO_AUX, txt_aux, FONT_PADRAO, PRETO)

    # --- INÍCIO: MODIFICAÇÃO (Lógica Botão Vida Máx) ---
    MAX_NIVEL_VIDA = len(VIDA_POR_NIVEL) - 1 # (Isso será 5)
    
    pode_maxhp = pode_comprar_geral and nave.nivel_max_vida < MAX_NIVEL_VIDA
    cor_maxhp = BRANCO if pode_maxhp else CINZA_BOTAO_DESLIGADO
    pygame.draw.rect(surface, cor_maxhp, RECT_BOTAO_MAX_HP, border_radius=5)
    
    if nave.nivel_max_vida < MAX_NIVEL_VIDA:
        txt_maxhp = f"Vida Max Nv. {nave.nivel_max_vida + 1} (Custo: {custo_padrao} Pt)"
    else:
        txt_maxhp = f"Vida Max Nv. {nave.nivel_max_vida} (MAX)"
        
    draw_text_on_button(RECT_BOTAO_MAX_HP, txt_maxhp, FONT_PADRAO, PRETO)
    # --- FIM: MODIFICAÇÃO ---
    
    pode_escudo = pode_comprar_geral and nave.nivel_escudo < MAX_NIVEL_ESCUDO
    cor_escudo = BRANCO if pode_escudo else CINZA_BOTAO_DESLIGADO
    pygame.draw.rect(surface, cor_escudo, RECT_BOTAO_ESCUDO, border_radius=5)
    if nave.nivel_escudo < MAX_NIVEL_ESCUDO:
        txt_escudo = f"Escudo Nv. {nave.nivel_escudo + 1}/{MAX_NIVEL_ESCUDO} (Custo: {custo_padrao} Pt)"
    else: txt_escudo = f"Escudo Nv. {nave.nivel_escudo} (MAX)"
    draw_text_on_button(RECT_BOTAO_ESCUDO, txt_escudo, FONT_PADRAO, PRETO)
    texto_fechar = FONT_PADRAO.render("Aperte 'V' para fechar a loja", True, BRANCO)
    surface.blit(texto_fechar, (largura_tela // 2 - texto_fechar.get_width() // 2, altura_tela - 60))

def desenhar_hud(surface, nave, estado_jogo):
    # --- INÍCIO: MODIFICAÇÃO (Não desenha HUD no modo espectador) ---
    if estado_jogo == "ESPECTADOR":
        return
    # --- FIM: MODIFICAÇÃO ---

    pos_x_detalhes = 10
    pos_y_atual_detalhes = 10
    hud_line_height = FONT_HUD.get_height() + 5
    
    # --- INÍCIO: MODIFICAÇÃO (PVP não mostra pontos) ---
    if estado_jogo != "JOGANDO": # Se não for PVE
        # Em PVP_LOBBY, PVP_COUNTDOWN, etc., não mostramos pontos de score
        pass
    else:
        texto_pontos = FONT_HUD.render(f"Pontos: {nave.pontos}", True, BRANCO)
        surface.blit(texto_pontos, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += hud_line_height
    # --- FIM: MODIFICAÇÃO ---
    
    vida_display = round(max(0, nave.vida_atual), 1)
    texto_vida = FONT_HUD.render(f"Vida: {vida_display} / {nave.max_vida}", True, VERDE_VIDA)
    surface.blit(texto_vida, (pos_x_detalhes, pos_y_atual_detalhes))
    pos_y_atual_detalhes += hud_line_height
    
    # --- INÍCIO: MODIFICAÇÃO (Não desenha se estiver morto) ---
    if estado_jogo != "GAME_OVER" and nave.vida_atual > 0:
    # --- FIM: MODIFICAÇÃO ---
        cor_pts_upgrade = AMARELO_BOMBA if nave.pontos_upgrade_disponiveis > 0 else BRANCO
        texto_pts_up = FONT_HUD.render(f"Pts Upgrade: {nave.pontos_upgrade_disponiveis}", True, cor_pts_upgrade)
        surface.blit(texto_pts_up, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += hud_line_height
        RECT_BOTAO_UPGRADE_HUD.topleft = (pos_x_detalhes, pos_y_atual_detalhes)
        
        # --- INÍCIO: MODIFICAÇÃO (Botão Upgrade no PVP) ---
        # Só mostra o botão se puder usar a loja
        if estado_jogo in ["JOGANDO", "PVP_LOBBY", "PVP_COUNTDOWN"]:
            pygame.draw.rect(surface, BRANCO, RECT_BOTAO_UPGRADE_HUD, border_radius=5)
            texto_botao_surf = FONT_RANKING.render("UPGRADE (V)", True, PRETO)
            texto_botao_rect = texto_botao_surf.get_rect(center=RECT_BOTAO_UPGRADE_HUD.center)
            surface.blit(texto_botao_surf, texto_botao_rect)
        
        pos_y_atual_detalhes = RECT_BOTAO_UPGRADE_HUD.bottom + 10
        # --- FIM: MODIFICAÇÃO ---

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
        
        if hasattr(nave, 'nivel_aux'): 
            num_aux = nave.nivel_aux
        else: 
            num_aux = len(nave.grupo_auxiliares_ativos)
            
        max_aux = len(nave.lista_todas_auxiliares)
        texto_aux = FONT_HUD_DETALHES.render(f"Auxiliares: {num_aux}/{max_aux}", True, BRANCO)
        surface.blit(texto_aux, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += line_spacing_detalhes

        # --- INÍCIO: MODIFICAÇÃO (Botão Regenerar apenas PVE) ---
        # Desenhar Botão Regenerar (Apenas no modo PVE "JOGANDO")
        if estado_jogo == "JOGANDO":
            is_regenerando = getattr(nave, 'esta_regenerando', False) 
            
            if is_regenerando:
                cor_botao = LILAS_REGEN
                texto_botao = "Regenerando..."
            elif nave.vida_atual >= nave.max_vida:
                cor_botao = CINZA_BOTAO_DESLIGADO
                texto_botao = "Vida Cheia"
            else:
                cor_botao = BRANCO
                texto_botao = "Regenerar Vida (R)"
                
            pygame.draw.rect(surface, cor_botao, RECT_BOTAO_REGEN_HUD, border_radius=5)
            texto_surf = FONT_RANKING.render(texto_botao, True, PRETO) 
            texto_rect = texto_surf.get_rect(center=RECT_BOTAO_REGEN_HUD.center)
            surface.blit(texto_surf, texto_rect)
        # --- FIM: MODIFICAÇÃO ---


# --- MODIFICAÇÃO 1: Mudar a assinatura da função ---
def desenhar_minimapa(surface, player, bots, estado_jogo, map_width, map_height, online_players, meu_nome_rede, 
                         alvo_camera_atual, camera_zoom, jogador_esta_vivo_espectador=False):
# --- FIM DA MODIFICAÇÃO 1 ---
    fundo_mini = pygame.Surface((MINIMAP_WIDTH, MINIMAP_HEIGHT), pygame.SRCALPHA)
    fundo_mini.fill(MINIMAP_FUNDO)
    surface.blit(fundo_mini, (MINIMAP_POS_X, MINIMAP_POS_Y))
    pygame.draw.rect(surface, BRANCO, MINIMAP_RECT, 1)
    
    # --- INÍCIO: MODIFICAÇÃO (Usa map_width/height passados) ---
    # Garante que não haja divisão por zero se o mapa for 0
    if map_width == 0 or map_height == 0:
        return # Não pode desenhar o minimapa
        
    ratio_x = MINIMAP_WIDTH / map_width
    ratio_y = MINIMAP_HEIGHT / map_height
    # --- FIM: MODIFICAÇÃO ---
    
    def get_pos_minimapa(pos_mundo_vec):
        # Proteção contra pos_mundo_vec None
        if pos_mundo_vec is None:
            return (0, 0) # Posição inválida
        try:
            map_x = int((pos_mundo_vec.x * ratio_x) + MINIMAP_POS_X)
            map_y = int((pos_mundo_vec.y * ratio_y) + MINIMAP_POS_Y)
            map_x = max(MINIMAP_POS_X + 1, min(map_x, MINIMAP_POS_X + MINIMAP_WIDTH - 2))
            map_y = max(MINIMAP_POS_Y + 1, min(map_y, MINIMAP_POS_Y + MINIMAP_HEIGHT - 2))
            return (map_x, map_y)
        except (AttributeError, TypeError):
             return (0, 0) # Retorno seguro

    # --- MODIFICAÇÃO 2: Adicionar lógica da visão ampla ---
    # --- INÍCIO DA NOVA LÓGICA DE ZOOM (VISÃO AMPLA) ---
    if camera_zoom < 1.0 and alvo_camera_atual: # Se o zoom "amplo" estiver ativo
        # Calcula o tamanho da visão da câmera no mundo
        largura_tela, altura_tela = surface.get_size()
        view_width_mundo = largura_tela / camera_zoom
        view_height_mundo = altura_tela / camera_zoom
        
        # Posição do centro da câmera (que é o alvo)
        cam_center_pos = alvo_camera_atual.posicao
        
        # Top-left da visão no mundo
        view_top_left_mundo = pygame.math.Vector2(
            cam_center_pos.x - (view_width_mundo / 2),
            cam_center_pos.y - (view_height_mundo / 2)
        )

        # Converte para posições do minimapa
        view_top_left_mini = get_pos_minimapa(view_top_left_mundo)
        
        # Calcula largura e altura no minimapa
        view_width_mini = int(view_width_mundo * ratio_x)
        view_height_mini = int(view_height_mundo * ratio_y)
        
        # Desenha o retângulo da visão
        rect_visao = pygame.Rect(view_top_left_mini[0], view_top_left_mini[1], view_width_mini, view_height_mini)
        pygame.draw.rect(surface, BRANCO, rect_visao, 1) # Desenha uma caixa branca
    
    # --- FIM DA NOVA LÓGICA DE ZOOM ---
    # --- FIM DA MODIFICAÇÃO 2 ---

    if online_players:
        for nome, state in online_players.items():
            if nome == meu_nome_rede:
                continue
            if state.get('hp', 0) <= 0:
                continue
            pos_vec = pygame.math.Vector2(state['x'], state['y'])
            pygame.draw.circle(surface, LARANJA_BOT, get_pos_minimapa(pos_vec), 2)
    else:
        for bot in bots:
            # --- MODIFICAÇÃO PVP: Não desenha o player (que está no grupo 'bots' no pvp) como laranja ---
            if bot == player:
                continue
            pygame.draw.circle(surface, LARANJA_BOT, get_pos_minimapa(bot.posicao), 2)
            
            
    # --- INÍCIO DA MODIFICAÇÃO: Desenhar Trilha "Serrilhada" ---
    # Verifica se o jogador tem um alvo de clique (posicao_alvo_mouse) e está vivo
    if (estado_jogo == "JOGANDO" or estado_jogo.startswith("PVP_")) and player.posicao_alvo_mouse and player.vida_atual > 0: # <-- MODIFICAÇÃO PVP
        
        start_mini_v = pygame.math.Vector2(get_pos_minimapa(player.posicao))
        end_mini_v = pygame.math.Vector2(get_pos_minimapa(player.posicao_alvo_mouse))
        
        vec = end_mini_v - start_mini_v
        length = vec.length()
        
        if length > 0:
            try:
                direction = vec.normalize()
                dash_len = 4  # Comprimento do traço
                gap_len = 3   # Comprimento do espaço
                total_step = dash_len + gap_len
                current_dist = 0
                
                # Desenha a linha tracejada
                while current_dist < length:
                    start_dash = start_mini_v + direction * current_dist
                    end_dist = min(current_dist + dash_len, length)
                    end_dash = start_mini_v + direction * end_dist
                    
                    # Desenha o segmento
                    pygame.draw.line(surface, BRANCO, (start_dash.x, start_dash.y), (end_dash.x, end_dash.y), 1)
                    
                    current_dist += total_step
            except ValueError:
                pass # Evita crash se o vetor for (0,0)
    # --- FIM DA MODIFICAÇÃO ---

    
    # --- INÍCIO DA MODIFICAÇÃO (Foco do Espectador no Minimapa) ---
    # O ponto azul (AZUL_NAVE) agora representa o 'alvo_camera_atual'.
    
    if estado_jogo == "JOGANDO" or estado_jogo.startswith("PVP_"): # <-- MODIFICAÇÃO PVP
        if player.vida_atual > 0:
            # alvo_camera_atual == player, então usamos sua posição
            pygame.draw.circle(surface, AZUL_NAVE, get_pos_minimapa(alvo_camera_atual.posicao), 3)
            
    # No modo ESPECTADOR, sempre desenhamos o 'alvo_camera_atual'
    elif estado_jogo == "ESPECTADOR":
        # Verifica se o alvo_camera_atual não é None (pode acontecer brevemente)
        if alvo_camera_atual:
            pygame.draw.circle(surface, AZUL_NAVE, get_pos_minimapa(alvo_camera_atual.posicao), 3)

    # --- FIM DA MODIFICAÇÃO ---

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
        
        # --- INÍCIO: MODIFICAÇÃO (Ranking PVP por Vida) ---
        # Se os pontos forem 0, assume que é PVP e mostra a vida
        if hasattr(nave, 'max_vida'):
            # Se for 'Nave' (Offline) E tiver 0 pontos, é PVP, mostra HP
            if nave.pontos == 0:
                 texto_pontos = f"{int(nave.vida_atual)} HP"
            # Se for 'Nave' (Offline) E tiver >0 pontos, é PVE, mostra Pontos
            else:
                 texto_pontos = f"{nave.pontos}"
        # Senão, é um 'RankingEntry' (Online), SEMPRE mostra pontos
        else:
            texto_pontos = f"{nave.pontos}"
        # --- FIM: MODIFICAÇÃO ---
        
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

# --- INÍCIO: MODIFICAÇÃO (desenhar_game_over) ---
# Esta função agora é chamada no estado ESPECTADOR se o jogador estiver morto
def desenhar_game_over(surface, largura_tela, altura_tela):
    # Não desenha mais o fundo escuro, pois o jogo está visível por baixo
    
    # Desenha o texto "Você Morreu!"
    texto_game_over = FONT_TITULO.render("Você Morreu!", True, VERMELHO_VIDA_FUNDO)
    surface.blit(texto_game_over, (largura_tela // 2 - texto_game_over.get_width() // 2, altura_tela // 2 - 50))
    
    # Desenha o botão "Reiniciar"
    pygame.draw.rect(surface, BRANCO, RECT_BOTAO_REINICIAR, border_radius=5)
    texto_botao = FONT_PADRAO.render("Respawnar", True, PRETO) # Texto mudado
    surface.blit(texto_botao, (RECT_BOTAO_REINICIAR.centerx - texto_botao.get_width() // 2, RECT_BOTAO_REINICIAR.centery - texto_botao.get_height() // 2))
# --- FIM: MODIFICAÇÃO ---


def desenhar_tela_conexao(surface, nome_str, ip_str, input_ativo_key):
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
    pygame.draw.rect(surface, BRANCO, RECT_CONNECT_BOTAO, border_radius=5)
    texto_botao = FONT_PADRAO.render("Conectar", True, PRETO)
    texto_botao_rect = texto_botao.get_rect(center=RECT_CONNECT_BOTAO.center)
    surface.blit(texto_botao, texto_botao_rect)