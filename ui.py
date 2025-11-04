# ui.py
import pygame
# Importa todas as constantes e fontes de settings
from settings import *

# --- Variáveis Globais de UI (Tamanho e Posição) ---
# Serão atualizadas por recalculate_ui_positions
# Tamanhos Fixos
BTN_LOJA_W, BTN_LOJA_H = 300, 50
BTN_MENU_W, BTN_MENU_H = 250, 50
BTN_REINICIAR_W, BTN_REINICIAR_H = 200, 50
BTN_HUD_UPGRADE_W, BTN_HUD_UPGRADE_H = 100, 30
TERMINAL_H = 35
PAUSE_PANEL_W, PAUSE_PANEL_H = 350, 250
BTN_PAUSE_CTRL_W, BTN_PAUSE_CTRL_H = 40, 40

# --- Bloco da Tela de Nome (Login) ---
LOGIN_PANEL_W, LOGIN_PANEL_H = 350, 250
LOGIN_INPUT_W, LOGIN_INPUT_H = 300, 40
LOGIN_BTN_W, LOGIN_BTN_H = 200, 50

# --- INÍCIO DA MODIFICAÇÃO (Adicionar Tela de Conexão) ---
CONNECT_PANEL_W, CONNECT_PANEL_H = 350, 300 # Um pouco mais alto
CONNECT_INPUT_W, CONNECT_INPUT_H = 300, 40
CONNECT_BTN_W, CONNECT_BTN_H = 200, 50
# --- FIM DA MODIFICAÇÃO ---

MINIMAP_WIDTH = 150 # Definido localmente aqui, mas poderia vir de settings
MINIMAP_HEIGHT = 150 # Definido localmente aqui, mas poderia vir de settings

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
MINIMAP_RECT = pygame.Rect(0, 0, MINIMAP_WIDTH, MINIMAP_HEIGHT) # Posição será definida
RECT_LOGO_MENU = pygame.Rect(0, 0, 0, 0)
# Novos Rects Pausa
RECT_PAUSE_FUNDO = pygame.Rect(0, 0, PAUSE_PANEL_W, PAUSE_PANEL_H)
RECT_TEXTO_BOTS = pygame.Rect(0, 0, 200, 40)
RECT_BOTAO_BOT_MENOS = pygame.Rect(0, 0, BTN_PAUSE_CTRL_W, BTN_PAUSE_CTRL_H)
RECT_BOTAO_BOT_MAIS = pygame.Rect(0, 0, BTN_PAUSE_CTRL_W, BTN_PAUSE_CTRL_H)
RECT_BOTAO_VOLTAR_MENU = pygame.Rect(0, 0, 200, 40)
RECT_TEXTO_VOLTAR = pygame.Rect(0, 0, 200, 30)
RECT_BOTAO_VOLTAR_MENU = pygame.Rect(0, 0, BTN_REINICIAR_W, BTN_REINICIAR_H)

# --- Rects da Tela de Nome (Login) ---
RECT_LOGIN_PAINEL = pygame.Rect(0, 0, LOGIN_PANEL_W, LOGIN_PANEL_H)
RECT_LOGIN_INPUT = pygame.Rect(0, 0, LOGIN_INPUT_W, LOGIN_INPUT_H)
RECT_LOGIN_BOTAO = pygame.Rect(0, 0, LOGIN_BTN_W, LOGIN_BTN_H)

# --- INÍCIO DA MODIFICAÇÃO (Rects da Tela de Conexão) ---
RECT_CONNECT_PAINEL = pygame.Rect(0, 0, CONNECT_PANEL_W, CONNECT_PANEL_H)
RECT_CONNECT_NOME = pygame.Rect(0, 0, CONNECT_INPUT_W, CONNECT_INPUT_H)
RECT_CONNECT_IP = pygame.Rect(0, 0, CONNECT_INPUT_W, CONNECT_INPUT_H)
RECT_CONNECT_BOTAO = pygame.Rect(0, 0, CONNECT_BTN_W, CONNECT_BTN_H)
# --- FIM DA MODIFICAÇÃO ---


# Variáveis para guardar posições calculadas
MINIMAP_POS_X = 0
MINIMAP_POS_Y = 0

def recalculate_ui_positions(w, h):
    global MINIMAP_POS_X, MINIMAP_POS_Y, MINIMAP_RECT, RECT_TERMINAL_INPUT
    global RECT_BOTAO_MOTOR, RECT_BOTAO_DANO, RECT_BOTAO_AUX, RECT_BOTAO_MAX_HP, RECT_BOTAO_ESCUDO
    global RECT_BOTAO_REINICIAR, RECT_BOTAO_UPGRADE_HUD
    global RECT_BOTAO_JOGAR_OFF, RECT_BOTAO_MULTIPLAYER, RECT_BOTAO_SAIR
    # Adiciona os novos Rects de Pausa
    global RECT_PAUSE_FUNDO, RECT_TEXTO_BOTS, RECT_BOTAO_BOT_MENOS, RECT_BOTAO_BOT_MAIS, RECT_TEXTO_VOLTAR, RECT_BOTAO_VOLTAR_MENU
    global RECT_BOTAO_VOLTAR_MENU, RECT_TEXTO_VOLTAR
    
    # Rects de Login
    global RECT_LOGIN_PAINEL, RECT_LOGIN_INPUT, RECT_LOGIN_BOTAO
    
    # --- INÍCIO DA MODIFICAÇÃO (Globals da Tela de Conexão) ---
    global RECT_CONNECT_PAINEL, RECT_CONNECT_NOME, RECT_CONNECT_IP, RECT_CONNECT_BOTAO
    # --- FIM DA MODIFICAÇÃO ---

    # Minimapa
    MINIMAP_POS_X = w - MINIMAP_WIDTH - 10
    MINIMAP_POS_Y = 10
    MINIMAP_RECT.topleft = (MINIMAP_POS_X, MINIMAP_POS_Y)

    # Terminal Input
    RECT_TERMINAL_INPUT.width = w - 20
    RECT_TERMINAL_INPUT.bottomleft = (10, h - 10)

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
    
    # --

    # Botões do Menu Principal (Centralizados)
    # 1. Posição da Logo
    logo_y_pos = h // 3 # Posição Y do centro da logo (igual em desenhar_menu)
    logo_height = 0
    # Declara que vamos modificar o RECT_LOGO_MENU global
    global RECT_LOGO_MENU 
    
    if LOGO_JOGO:
        # Pega a altura da logo para calcular a posição dos botões
        logo_height = LOGO_JOGO.get_height()
        RECT_LOGO_MENU = LOGO_JOGO.get_rect(center=(w // 2, logo_y_pos))
    else:
        # Fallback se a logo não carregou (usa a fonte)
        fallback_text = FONT_TITULO.render("Nosso Jogo de Nave", True, BRANCO)
        logo_height = fallback_text.get_height()
        RECT_LOGO_MENU = fallback_text.get_rect(center=(w // 2, logo_y_pos))

    # 2. Posição dos Botões (baseado na logo)
    # Posição Y inicial = centro_logo_y + metade_altura_logo + espaçamento
    menu_btn_y_start = logo_y_pos + (logo_height // 2) + 50 # 50px de espaço
    
    menu_btn_x = w // 2 - BTN_MENU_W // 2
    menu_btn_spacing = 70
    RECT_BOTAO_JOGAR_OFF.topleft = (menu_btn_x, menu_btn_y_start)
    RECT_BOTAO_MULTIPLAYER.topleft = (menu_btn_x, menu_btn_y_start + menu_btn_spacing)
    RECT_BOTAO_SAIR.topleft = (menu_btn_x, menu_btn_y_start + menu_btn_spacing * 2)

    # --- Posições do Menu de Pausa (Centralizado) ---
    RECT_PAUSE_FUNDO.center = (w // 2, h // 2)
    
    # Y inicial para o primeiro item
    base_y_pause = RECT_PAUSE_FUNDO.top + 60
    
    # Espaçamentos
    spacing_pause_items = 25 # Espaço vertical entre o botão e os controles
    spacing_pause_buttons = 15 # Espaço horizontal para +/-
    
    # 1. Botão Voltar ao Menu (Primeiro item)
    RECT_BOTAO_VOLTAR_MENU.midtop = (RECT_PAUSE_FUNDO.centerx, base_y_pause)
    
    # 2. Controles de Bots (Segundo item, abaixo do botão "Voltar ao Menu")
    # Posição Y = Ponto inferior (bottom) do botão + espaçamento
    y_pos_bots = RECT_BOTAO_VOLTAR_MENU.bottom + spacing_pause_items
    
    RECT_TEXTO_BOTS.midtop = (RECT_PAUSE_FUNDO.centerx, y_pos_bots)
    RECT_BOTAO_BOT_MENOS.midright = (RECT_TEXTO_BOTS.left - spacing_pause_buttons, RECT_TEXTO_BOTS.centery)
    RECT_BOTAO_BOT_MAIS.midleft = (RECT_TEXTO_BOTS.right + spacing_pause_buttons, RECT_TEXTO_BOTS.centery)
    
    # 3. Texto "ESC para Voltar" (Último item)
    RECT_TEXTO_VOLTAR.midbottom = (RECT_PAUSE_FUNDO.centerx, RECT_PAUSE_FUNDO.bottom - 20)
    
    # --- Posições da Tela de Nome (Login) ---
    RECT_LOGIN_PAINEL.center = (w // 2, h // 2)
    
    # Posição Y do Input (um pouco abaixo do título, que será desenhado em + 40)
    input_y_pos = RECT_LOGIN_PAINEL.top + 100
    RECT_LOGIN_INPUT.center = (RECT_LOGIN_PAINEL.centerx, input_y_pos)
    
    # Posição Y do Botão (abaixo do input)
    btn_y_pos = RECT_LOGIN_INPUT.bottom + 30
    RECT_LOGIN_BOTAO.center = (RECT_LOGIN_PAINEL.centerx, btn_y_pos)

    # --- INÍCIO DA MODIFICAÇÃO (Posições da Tela de Conexão) ---
    # --- Posições da Tela de Conexão ---
    RECT_CONNECT_PAINEL.center = (w // 2, h // 2)
    
    # Posição Y do Input de Nome (abaixo do título)
    nome_y_pos = RECT_CONNECT_PAINEL.top + 100
    RECT_CONNECT_NOME.center = (RECT_CONNECT_PAINEL.centerx, nome_y_pos)
    
    # Posição Y do Input de IP (abaixo do nome)
    ip_y_pos = RECT_CONNECT_NOME.bottom + 50 # Mais espaço para o label
    RECT_CONNECT_IP.center = (RECT_CONNECT_PAINEL.centerx, ip_y_pos)

    # Posição Y do Botão (abaixo do IP)
    btn_connect_y_pos = RECT_CONNECT_IP.bottom + 30
    RECT_CONNECT_BOTAO.center = (RECT_CONNECT_PAINEL.centerx, btn_connect_y_pos)
    # --- FIM DA MODIFICAÇÃO ---


# --- Funções de Desenho ---

def desenhar_menu(surface, largura_tela, altura_tela):
    """ Desenha a tela do menu principal. """
    surface.fill(PRETO) # Fundo preto simples

    # --- INÍCIO DA MODIFICAÇÃO: DESENHAR LOGO ---
    # Verifica se a logo foi carregada com sucesso
    if LOGO_JOGO:
        # Calcula a posição da logo (centralizada, 1/3 abaixo do topo)
        logo_rect = LOGO_JOGO.get_rect(center=(largura_tela // 2, altura_tela // 3))
        # Desenha a logo na tela
        surface.blit(LOGO_JOGO, logo_rect)
    else:
        # Se a logo falhou (ex: arquivo não encontrado), desenha o texto antigo
        texto_titulo = FONT_TITULO.render("Nosso Jogo de Nave", True, BRANCO)
        titulo_rect = texto_titulo.get_rect(center=(largura_tela // 2, altura_tela // 3))
        surface.blit(texto_titulo, titulo_rect)
    # --- FIM DA MODIFICAÇÃO ---


    # Função auxiliar para desenhar botões
    def draw_menu_button(rect, text, text_color=PRETO, button_color=BRANCO):
        pygame.draw.rect(surface, button_color, rect, border_radius=5)
        text_surf = FONT_PADRAO.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

    # Desenha os Botões
    draw_menu_button(RECT_BOTAO_JOGAR_OFF, "Jogar Offline")
    
    # --- INÍCIO DA MODIFICAÇÃO (Ativar Botão) ---
    draw_menu_button(RECT_BOTAO_MULTIPLAYER, "Multijogador") # Botão agora está ativo (cores padrão)
    # --- FIM DA MODIFICAÇÃO ---
    
    draw_menu_button(RECT_BOTAO_SAIR, "Sair")

def desenhar_tela_nome(surface, nome_jogador_atual, input_nome_ativo):
    """ Desenha a tela de entrada de nome. """
    
    # 1. Fundo (Pode desenhar o menu atrás, ou apenas um fundo preto)
    # Vamos desenhar o logo e o fundo preto para consistência
    surface.fill(PRETO)
    if LOGO_JOGO:
        logo_rect = LOGO_JOGO.get_rect(center=(surface.get_width() // 2, surface.get_height() // 3))
        surface.blit(LOGO_JOGO, logo_rect)
        
    # 2. Painel de fundo
    # (Opcional, mas ajuda a destacar. Vamos pular por enquanto e desenhar direto)
    # pygame.draw.rect(surface, CINZA_LOJA_FUNDO, RECT_LOGIN_PAINEL, border_radius=10)
    
    # 3. Título
    texto_titulo = FONT_TITULO.render("Digite seu nome", True, BRANCO)
    titulo_rect = texto_titulo.get_rect(center=(RECT_LOGIN_PAINEL.centerx, RECT_LOGIN_PAINEL.top + 40))
    surface.blit(texto_titulo, titulo_rect)

    # 4. Caixa de Input de Nome
    cor_borda_input = BRANCO if input_nome_ativo else CINZA_BOTAO_DESLIGADO
    pygame.draw.rect(surface, PRETO, RECT_LOGIN_INPUT, border_radius=5)
    pygame.draw.rect(surface, cor_borda_input, RECT_LOGIN_INPUT, 2, border_radius=5)

    # Texto e Cursor
    cursor = "_" if input_nome_ativo and pygame.time.get_ticks() % 1000 < 500 else ""
    texto_renderizado = FONT_PADRAO.render(f"{nome_jogador_atual}{cursor}", True, BRANCO)
    texto_rect = texto_renderizado.get_rect(midleft=(RECT_LOGIN_INPUT.x + 15, RECT_LOGIN_INPUT.centery))
    surface.blit(texto_renderizado, texto_rect)

    # Placeholder
    if not input_nome_ativo and not nome_jogador_atual:
        placeholder_surf = FONT_PADRAO.render("Nome...", True, CINZA_BOTAO_DESLIGADO)
        placeholder_rect = placeholder_surf.get_rect(midleft=(RECT_LOGIN_INPUT.x + 15, RECT_LOGIN_INPUT.centery))
        surface.blit(placeholder_surf, placeholder_rect)
        
    # 5. Botão "Respawn"
    pygame.draw.rect(surface, BRANCO, RECT_LOGIN_BOTAO, border_radius=5)
    texto_botao = FONT_PADRAO.render("Respawn", True, PRETO)
    texto_botao_rect = texto_botao.get_rect(center=RECT_LOGIN_BOTAO.center)
    surface.blit(texto_botao, texto_botao_rect)

# --- Função Desenhar Pausa ---
def desenhar_pause(surface, max_bots_atual, max_bots_limite, num_bots_ativos):
    """ Desenha o menu de pausa sobre a tela do jogo. """
    # Desenha um fundo semi-transparente escuro sobre toda a tela
    fundo_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    fundo_overlay.fill(PRETO_TRANSPARENTE_PAUSA) # Usa nova constante
    surface.blit(fundo_overlay, (0, 0))

    # Desenha o painel de fundo do menu de pausa
    pygame.draw.rect(surface, CINZA_LOJA_FUNDO, RECT_PAUSE_FUNDO, border_radius=10)
    pygame.draw.rect(surface, BRANCO, RECT_PAUSE_FUNDO, 2, border_radius=10)

    # Título "PAUSADO"
    texto_titulo = FONT_TITULO.render("PAUSADO", True, BRANCO)
    titulo_rect = texto_titulo.get_rect(midtop=(RECT_PAUSE_FUNDO.centerx, RECT_PAUSE_FUNDO.top + 15))
    surface.blit(texto_titulo, titulo_rect)

    # --- Controles de Bots ---
    # Botão Menos (-)
    cor_menos = BRANCO if max_bots_atual > 0 else CINZA_BOTAO_DESLIGADO # Desabilita se for 0
    pygame.draw.rect(surface, cor_menos, RECT_BOTAO_BOT_MENOS, border_radius=5)
    texto_menos = FONT_TITULO.render("-", True, PRETO)
    menos_rect = texto_menos.get_rect(center=RECT_BOTAO_BOT_MENOS.center)
    surface.blit(texto_menos, menos_rect)

    # Texto de Contagem
    texto_contagem = FONT_PADRAO.render(f"Max Bots: {max_bots_atual} (Ativos: {num_bots_ativos})", True, BRANCO)
    contagem_rect = texto_contagem.get_rect(center=RECT_TEXTO_BOTS.center)
    surface.blit(texto_contagem, contagem_rect)

    # Botão Mais (+)
    cor_mais = BRANCO if max_bots_atual < max_bots_limite else CINZA_BOTAO_DESLIGADO # Desabilita se no limite
    pygame.draw.rect(surface, cor_mais, RECT_BOTAO_BOT_MAIS, border_radius=5)
    texto_mais = FONT_TITULO.render("+", True, PRETO)
    mais_rect = texto_mais.get_rect(center=RECT_BOTAO_BOT_MAIS.center)
    surface.blit(texto_mais, mais_rect)
    # --- Fim Controles de Bots ---
    pygame.draw.rect(surface, BRANCO, RECT_BOTAO_VOLTAR_MENU, border_radius=5)
    texto_voltar_menu_surf = FONT_PADRAO.render("Voltar ao Menu", True, PRETO)
    texto_voltar_menu_rect = texto_voltar_menu_surf.get_rect(center=RECT_BOTAO_VOLTAR_MENU.center)
    surface.blit(texto_voltar_menu_surf, texto_voltar_menu_rect)

    # Texto "ESC para voltar"
    texto_voltar = FONT_PADRAO.render("ESC para Voltar", True, BRANCO)
    voltar_rect = texto_voltar.get_rect(center=RECT_TEXTO_VOLTAR.center)
    surface.blit(texto_voltar, voltar_rect)
# --- FIM Função Desenhar Pausa ---

def desenhar_loja(surface, nave, largura_tela, altura_tela):
    # Fundo semi-transparente
    fundo_loja = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
    fundo_loja.fill(CINZA_LOJA_FUNDO)
    surface.blit(fundo_loja, (0, 0))

    # Título e Pontos de Upgrade
    texto_titulo = FONT_TITULO.render("LOJA DE UPGRADES", True, BRANCO)
    surface.blit(texto_titulo, (largura_tela // 2 - texto_titulo.get_width() // 2, 50))
    # --- ALTERAÇÃO AQUI ---
    texto_pontos = FONT_PADRAO.render(f"Pontos de Upgrade: {nave.pontos_upgrade_disponiveis}", True, BRANCO)
    surface.blit(texto_pontos, (largura_tela // 2 - texto_pontos.get_width() // 2, 100))
    texto_limite = FONT_PADRAO.render(f"Upgrades Feitos: {nave.total_upgrades_feitos} / {MAX_TOTAL_UPGRADES}", True, CINZA_BOTAO_DESLIGADO)
    surface.blit(texto_limite, (largura_tela // 2 - texto_limite.get_width() // 2, 130))
    # --- FIM ALTERAÇÃO ---

    # Função auxiliar para texto no botão
    def draw_text_on_button(rect, text, font, text_color):
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

    # --- INÍCIO: ALTERAÇÕES BOTÕES LOJA ---
    pode_comprar_geral = nave.pontos_upgrade_disponiveis > 0 and nave.total_upgrades_feitos < MAX_TOTAL_UPGRADES
    custo_padrao = 1 # Custo padrão para a maioria dos upgrades

    # Botão Motor
    pode_motor = pode_comprar_geral and nave.nivel_motor < MAX_NIVEL_MOTOR
    cor_motor = BRANCO if pode_motor else CINZA_BOTAO_DESLIGADO
    pygame.draw.rect(surface, cor_motor, RECT_BOTAO_MOTOR, border_radius=5)
    if nave.nivel_motor < MAX_NIVEL_MOTOR:
        txt_motor = f"Motor Nv. {nave.nivel_motor + 1}/{MAX_NIVEL_MOTOR} (Custo: {custo_padrao} Pt)"
    else: txt_motor = f"Motor Nv. {nave.nivel_motor} (MAX)"
    draw_text_on_button(RECT_BOTAO_MOTOR, txt_motor, FONT_PADRAO, PRETO)

    # Botão Dano
    pode_dano = pode_comprar_geral and nave.nivel_dano < MAX_NIVEL_DANO
    cor_dano = BRANCO if pode_dano else CINZA_BOTAO_DESLIGADO
    pygame.draw.rect(surface, cor_dano, RECT_BOTAO_DANO, border_radius=5)
    if nave.nivel_dano < MAX_NIVEL_DANO:
        txt_dano = f"Dano Nv. {nave.nivel_dano + 1}/{MAX_NIVEL_DANO} (Custo: {custo_padrao} Pt)"
    else: txt_dano = f"Dano Nv. {nave.nivel_dano} (MAX)"
    draw_text_on_button(RECT_BOTAO_DANO, txt_dano, FONT_PADRAO, PRETO)

    # --- INÍCIO: MODIFICAÇÃO BOTÃO AUXILIAR ---
    num_ativos = len(nave.grupo_auxiliares_ativos)
    max_aux = len(nave.lista_todas_auxiliares) # Geralmente 4
    
    # Verifica se ainda pode comprar auxiliares
    if num_ativos < max_aux:
        # Pega o custo da lista CUSTOS_AUXILIARES (de settings.py)
        # num_ativos = 0 -> CUSTOS_AUXILIARES[0] (custo 1)
        # num_ativos = 1 -> CUSTOS_AUXILIARES[1] (custo 2)
        custo_atual_aux = CUSTOS_AUXILIARES[num_ativos]
        
        txt_aux = f"Comprar Auxiliar {num_ativos + 1}/{max_aux} (Custo: {custo_atual_aux} Pts)"
        
        # Verifica se pode comprar (limite total E se tem pontos suficientes para ESTE custo)
        pode_aux = pode_comprar_geral and nave.pontos_upgrade_disponiveis >= custo_atual_aux
    else:
        txt_aux = "Máx. Auxiliares"
        pode_aux = False # Não pode comprar mais
        
    cor_aux = BRANCO if pode_aux else CINZA_BOTAO_DESLIGADO
    pygame.draw.rect(surface, cor_aux, RECT_BOTAO_AUX, border_radius=5)
    draw_text_on_button(RECT_BOTAO_AUX, txt_aux, FONT_PADRAO, PRETO)
    # --- FIM: MODIFICAÇÃO BOTÃO AUXILIAR ---

    # Botão Max HP
    pode_maxhp = pode_comprar_geral # Sem limite específico de nível
    cor_maxhp = BRANCO if pode_maxhp else CINZA_BOTAO_DESLIGADO
    pygame.draw.rect(surface, cor_maxhp, RECT_BOTAO_MAX_HP, border_radius=5)
    draw_text_on_button(RECT_BOTAO_MAX_HP, f"Vida Max Nv. {nave.nivel_max_vida + 1} (Custo: {custo_padrao} Pt)", FONT_PADRAO, PRETO)

    # Botão Escudo
    pode_escudo = pode_comprar_geral and nave.nivel_escudo < MAX_NIVEL_ESCUDO
    cor_escudo = BRANCO if pode_escudo else CINZA_BOTAO_DESLIGADO
    pygame.draw.rect(surface, cor_escudo, RECT_BOTAO_ESCUDO, border_radius=5)
    if nave.nivel_escudo < MAX_NIVEL_ESCUDO:
        txt_escudo = f"Escudo Nv. {nave.nivel_escudo + 1}/{MAX_NIVEL_ESCUDO} (Custo: {custo_padrao} Pt)"
    else: txt_escudo = f"Escudo Nv. {nave.nivel_escudo} (MAX)"
    draw_text_on_button(RECT_BOTAO_ESCUDO, txt_escudo, FONT_PADRAO, PRETO)
    # --- FIM: ALTERAÇÕES BOTÕES LOJA ---

    # Instrução para fechar
    texto_fechar = FONT_PADRAO.render("Aperte 'V' para fechar a loja", True, BRANCO)
    surface.blit(texto_fechar, (largura_tela // 2 - texto_fechar.get_width() // 2, altura_tela - 60))

def desenhar_hud(surface, nave, estado_jogo):
    # Posição Y inicial para os detalhes (abaixo do botão Upgrade)
    pos_x_detalhes = 10
    pos_y_atual_detalhes = 10 # Começa abaixo dos pontos normais
    hud_line_height = FONT_HUD.get_height() + 5

    # Desenha Pontos (Ranking) e Vida
    texto_pontos = FONT_HUD.render(f"Pontos: {nave.pontos}", True, BRANCO)
    surface.blit(texto_pontos, (pos_x_detalhes, pos_y_atual_detalhes))
    pos_y_atual_detalhes += hud_line_height

    # --- INÍCIO DA MODIFICAÇÃO (Bug do Escudo Decimal) ---
    # Arredonda a vida atual para 1 casa decimal ANTES de desenhar
    vida_display = round(max(0, nave.vida_atual), 1)
    texto_vida = FONT_HUD.render(f"Vida: {vida_display} / {nave.max_vida}", True, VERDE_VIDA)
    # --- FIM DA MODIFICAÇÃO ---
    
    surface.blit(texto_vida, (pos_x_detalhes, pos_y_atual_detalhes))
    pos_y_atual_detalhes += hud_line_height

    # Desenha Pontos de Upgrade e Botão (apenas se não estiver no Game Over)
    if estado_jogo != "GAME_OVER":
        # Pontos de Upgrade
        cor_pts_upgrade = AMARELO_BOMBA if nave.pontos_upgrade_disponiveis > 0 else BRANCO
        texto_pts_up = FONT_HUD.render(f"Pts Upgrade: {nave.pontos_upgrade_disponiveis}", True, cor_pts_upgrade)
        surface.blit(texto_pts_up, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += hud_line_height

        # Botão Upgrade (posição ajustada)
        RECT_BOTAO_UPGRADE_HUD.topleft = (pos_x_detalhes, pos_y_atual_detalhes) # Botão abaixo dos pontos
        pygame.draw.rect(surface, BRANCO, RECT_BOTAO_UPGRADE_HUD, border_radius=5)
        texto_botao_surf = FONT_RANKING.render("UPGRADE (V)", True, PRETO)
        texto_botao_rect = texto_botao_surf.get_rect(center=RECT_BOTAO_UPGRADE_HUD.center)
        surface.blit(texto_botao_surf, texto_botao_rect)
        pos_y_atual_detalhes = RECT_BOTAO_UPGRADE_HUD.bottom + 10 # Próximo item abaixo do botão

        # --- INÍCIO DA MODIFICAÇÃO: Status da Nave ---
        line_spacing_detalhes = FONT_HUD_DETALHES.get_height() + 2
        
        # Motor
        texto_motor = FONT_HUD_DETALHES.render(f"Motor: Nv {nave.nivel_motor}/{MAX_NIVEL_MOTOR}", True, BRANCO)
        surface.blit(texto_motor, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += line_spacing_detalhes

        # Dano
        texto_dano = FONT_HUD_DETALHES.render(f"Dano: Nv {nave.nivel_dano}/{MAX_NIVEL_DANO}", True, BRANCO)
        surface.blit(texto_dano, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += line_spacing_detalhes
        
        # Escudo
        texto_escudo = FONT_HUD_DETALHES.render(f"Escudo: Nv {nave.nivel_escudo}/{MAX_NIVEL_ESCUDO}", True, BRANCO)
        surface.blit(texto_escudo, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += line_spacing_detalhes
        
        # Auxiliares
        num_aux = len(nave.grupo_auxiliares_ativos)
        max_aux = len(nave.lista_todas_auxiliares)
        texto_aux = FONT_HUD_DETALHES.render(f"Auxiliares: {num_aux}/{max_aux}", True, BRANCO)
        surface.blit(texto_aux, (pos_x_detalhes, pos_y_atual_detalhes))
        pos_y_atual_detalhes += line_spacing_detalhes
        # --- FIM DA MODIFICAÇÃO ---

def desenhar_minimapa(surface, player, bots, estado_jogo, map_width, map_height, online_players, meu_nome_rede):
    # Fundo semi-transparente
    fundo_mini = pygame.Surface((MINIMAP_WIDTH, MINIMAP_HEIGHT), pygame.SRCALPHA)
    fundo_mini.fill(MINIMAP_FUNDO)
    surface.blit(fundo_mini, (MINIMAP_POS_X, MINIMAP_POS_Y))
    # Borda
    pygame.draw.rect(surface, BRANCO, MINIMAP_RECT, 1)

    # Relação entre mapa e minimapa
    ratio_x = MINIMAP_WIDTH / map_width
    ratio_y = MINIMAP_HEIGHT / map_height

    # Função auxiliar para converter posição do mundo para minimapa
    def get_pos_minimapa(pos_mundo_vec):
        map_x = int((pos_mundo_vec.x * ratio_x) + MINIMAP_POS_X)
        map_y = int((pos_mundo_vec.y * ratio_y) + MINIMAP_POS_Y)
        # Garante que os pontos fiquem dentro da borda do minimapa
        map_x = max(MINIMAP_POS_X + 1, min(map_x, MINIMAP_POS_X + MINIMAP_WIDTH - 2))
        map_y = max(MINIMAP_POS_Y + 1, min(map_y, MINIMAP_POS_Y + MINIMAP_HEIGHT - 2))
        return (map_x, map_y)

    # --- Lógica de Desenho Atualizada ---
    if online_players:
        # Modo Online: Desenha jogadores do dicionário 'online_players'
        for nome, state in online_players.items():
            if nome == meu_nome_rede:
                continue # Não desenha o "outro" eu, o jogador principal trata disso
            
            # (Usamos a mesma cor dos bots por enquanto)
            pos_vec = pygame.math.Vector2(state['x'], state['y'])
            pygame.draw.circle(surface, LARANJA_BOT, get_pos_minimapa(pos_vec), 2)
    else:
        # Modo Offline: Desenha Bots
        for bot in bots:
            pygame.draw.circle(surface, LARANJA_BOT, get_pos_minimapa(bot.posicao), 2)

    # Desenha Jogador (sempre)
    if estado_jogo != "GAME_OVER":
        pygame.draw.circle(surface, AZUL_NAVE, get_pos_minimapa(player.posicao), 3)
# --- FIM DA MODIFICAÇÃO (desenhar_minimapa) ---

def desenhar_ranking(surface, lista_top_5, nave_player):
    # Posição inicial (abaixo do minimapa)
    pos_x_base = MINIMAP_POS_X
    pos_y_base = MINIMAP_POS_Y + MINIMAP_HEIGHT + 10 # 10px de margem
    ranking_width = MINIMAP_WIDTH

    # Título
    titulo_surf = FONT_HUD.render("RANKING", True, BRANCO)
    titulo_x = pos_x_base + (ranking_width - titulo_surf.get_width()) // 2
    surface.blit(titulo_surf, (titulo_x, pos_y_base))

    # Lista
    pos_y_linha_atual = pos_y_base + titulo_surf.get_height() + 5
    for i, nave in enumerate(lista_top_5):
        cor_texto = LARANJA_BOT if nave != nave_player else VERDE_VIDA # Destaque para jogador

        # Nome (truncado se necessário)
        nome_nave = nave.nome
        if len(nome_nave) > 12: nome_nave = nome_nave[:11] + "."
        texto_nome = f"{i + 1}. {nome_nave}"
        nome_surf = FONT_RANKING.render(texto_nome, True, cor_texto)
        surface.blit(nome_surf, (pos_x_base + 5, pos_y_linha_atual))

        # Pontos (alinhado à direita)
        texto_pontos = f"{nave.pontos}"
        pontos_surf = FONT_RANKING.render(texto_pontos, True, cor_texto)
        pontos_x = pos_x_base + ranking_width - pontos_surf.get_width() - 5
        surface.blit(pontos_surf, (pontos_x, pos_y_linha_atual))

        pos_y_linha_atual += FONT_RANKING.get_height() + 2


def desenhar_terminal(surface, texto_atual, largura_tela, altura_tela):
    # Fundo semi-transparente
    fundo_terminal = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
    fundo_terminal.fill(CINZA_LOJA_FUNDO)
    surface.blit(fundo_terminal, (0, 0))

    # Instrução
    texto_instrucao = FONT_PADRAO.render("Aperte ENTER para executar ou ' para fechar", True, BRANCO)
    surface.blit(texto_instrucao, (largura_tela // 2 - texto_instrucao.get_width() // 2, RECT_TERMINAL_INPUT.y - 40))

    # Caixa de Input
    pygame.draw.rect(surface, PRETO, RECT_TERMINAL_INPUT)
    pygame.draw.rect(surface, BRANCO, RECT_TERMINAL_INPUT, 2) # Borda

    # Texto e Cursor
    cursor = "_" if pygame.time.get_ticks() % 1000 < 500 else ""
    texto_renderizado = FONT_TERMINAL.render(f"> {texto_atual}{cursor}", True, BRANCO)
    surface.blit(texto_renderizado, (RECT_TERMINAL_INPUT.x + 10, RECT_TERMINAL_INPUT.y + (RECT_TERMINAL_INPUT.height - texto_renderizado.get_height()) // 2))


def desenhar_game_over(surface, largura_tela, altura_tela):
    # Fundo escuro
    fundo_escuro = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
    fundo_escuro.fill(CINZA_LOJA_FUNDO)
    surface.blit(fundo_escuro, (0, 0))

    # Texto "Você Morreu!"
    texto_game_over = FONT_TITULO.render("Você Morreu!", True, VERMELHO_VIDA_FUNDO)
    surface.blit(texto_game_over, (largura_tela // 2 - texto_game_over.get_width() // 2, altura_tela // 2 - 50))

    # Botão Reiniciar
    pygame.draw.rect(surface, BRANCO, RECT_BOTAO_REINICIAR, border_radius=5)
    texto_botao = FONT_PADRAO.render("Reiniciar", True, PRETO)
    surface.blit(texto_botao, (RECT_BOTAO_REINICIAR.centerx - texto_botao.get_width() // 2, RECT_BOTAO_REINICIAR.centery - texto_botao.get_height() // 2))

# --- INÍCIO DA MODIFICAÇÃO (Adicionar Tela de Conexão) ---
def desenhar_tela_conexao(surface, nome_str, ip_str, input_ativo_key):
    """ Desenha a tela de conexão multiplayer. """
    
    # 1. Fundo (Mesmo do menu/login)
    surface.fill(PRETO)
    if LOGO_JOGO:
        logo_rect = LOGO_JOGO.get_rect(center=(surface.get_width() // 2, surface.get_height() // 3))
        surface.blit(LOGO_JOGO, logo_rect)
    
    # 2. Título do Painel
    texto_titulo = FONT_TITULO.render("Conectar ao Servidor", True, BRANCO)
    titulo_rect = texto_titulo.get_rect(center=(RECT_CONNECT_PAINEL.centerx, RECT_CONNECT_PAINEL.top + 40))
    surface.blit(texto_titulo, titulo_rect)

    # --- Helper para desenhar input (label + caixa) ---
    def draw_input_box(rect, label_text, text_str, is_active):
        # Label
        label_surf = FONT_PADRAO.render(label_text, True, BRANCO)
        label_rect = label_surf.get_rect(midbottom=(rect.centerx, rect.top - 5))
        surface.blit(label_surf, label_rect)
        
        # Caixa
        cor_borda = BRANCO if is_active else CINZA_BOTAO_DESLIGADO
        pygame.draw.rect(surface, PRETO, rect, border_radius=5)
        pygame.draw.rect(surface, cor_borda, rect, 2, border_radius=5)

        # Texto e Cursor
        cursor = "_" if is_active and pygame.time.get_ticks() % 1000 < 500 else ""
        texto_renderizado = FONT_PADRAO.render(f"{text_str}{cursor}", True, BRANCO)
        texto_rect = texto_renderizado.get_rect(midleft=(rect.x + 15, rect.centery))
        surface.blit(texto_renderizado, texto_rect)

    # 3. Desenha Input "Seu Nome"
    draw_input_box(RECT_CONNECT_NOME, "Seu Nome:", nome_str, input_ativo_key == "nome")
    
    # 4. Desenha Input "IP do Servidor"
    draw_input_box(RECT_CONNECT_IP, "IP do Servidor:", ip_str, input_ativo_key == "ip")

    # 5. Botão "Conectar"
    pygame.draw.rect(surface, BRANCO, RECT_CONNECT_BOTAO, border_radius=5)
    texto_botao = FONT_PADRAO.render("Conectar", True, PRETO)
    texto_botao_rect = texto_botao.get_rect(center=RECT_CONNECT_BOTAO.center)
    surface.blit(texto_botao, texto_botao_rect)
# --- FIM DA MODIFICAÇÃO ---