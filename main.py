# main.py
import pygame
import sys
import random
import math

# 1. Importações dos Módulos
import settings as s # Importa tudo de settings com alias 's'
from camera import Camera
# from effects import Explosao # Importado via enemies e ships
from projectiles import Projetil, ProjetilInimigo, ProjetilInimigoRapido, ProjetilTeleguiadoLento
from entities import Obstaculo, VidaColetavel
# Importa as classes de inimigos
from enemies import (InimigoPerseguidor, InimigoAtiradorRapido, InimigoBomba, InimigoMinion,
                     InimigoMothership, InimigoRapido, InimigoTiroRapido, InimigoAtordoador,
                     set_global_enemy_references)
# Importa as classes de naves
from ships import Player, NaveBot, NaveAuxiliar, Nave, set_global_ship_references # Importa Nave base também
# Importa as funções e Rects da UI
import ui

# 2. Inicialização do Pygame e Tela
pygame.init()
LARGURA_TELA = s.LARGURA_TELA_INICIAL
ALTURA_TELA = s.ALTURA_TELA_INICIAL
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.RESIZABLE)
pygame.display.set_caption("Nosso Jogo de Nave Refatorado")
clock = pygame.time.Clock()

# 3. Variáveis Globais do Jogo
estado_jogo = "MENU" # Começa no Menu
variavel_texto_terminal = ""
rodando = True
max_bots_atual = s.MAX_BOTS # Controla o limite de bots dinamicamente

# 4. Criação da Câmera
camera = Camera(LARGURA_TELA, ALTURA_TELA)

# 5. Grupos de Sprites
grupo_projeteis_player = pygame.sprite.Group()
grupo_projeteis_bots = pygame.sprite.Group()
grupo_projeteis_inimigos = pygame.sprite.Group()
grupo_obstaculos = pygame.sprite.Group()
grupo_vidas_coletaveis = pygame.sprite.Group()
grupo_inimigos = pygame.sprite.Group() # Grupo geral de inimigos
grupo_motherships = pygame.sprite.Group() # Específico para contar motherships
grupo_bots = pygame.sprite.Group()
grupo_explosoes = pygame.sprite.Group()
grupo_player = pygame.sprite.GroupSingle()
# grupo_todos_sprites = pygame.sprite.Group() # Opcional

# 6. Criação do Jogador
nave_player = Player(s.MAP_WIDTH // 2, s.MAP_HEIGHT // 2)
grupo_player.add(nave_player)
# grupo_todos_sprites.add(nave_player)

# 7. Define Referências Globais para Módulos
set_global_enemy_references(grupo_explosoes, grupo_inimigos)
set_global_ship_references(grupo_explosoes)

# 8. Fundo Estrelado
lista_estrelas = []
for _ in range(s.NUM_ESTRELAS):
    pos_base = pygame.math.Vector2(random.randint(0, LARGURA_TELA), random.randint(0, ALTURA_TELA))
    raio = random.randint(1, 2)
    parallax_fator = raio * 0.1
    lista_estrelas.append((pos_base, raio, parallax_fator))

# 9. Funções Auxiliares (Spawners, Cheats, Reiniciar)

def calcular_posicao_spawn(pos_referencia, dist_min_do_jogador=s.SPAWN_DIST_MIN): # Adiciona parâmetro opcional
    """ Calcula uma posição aleatória no mapa, garantindo uma distância mínima do jogador. """
    while True:
        # Escolhe x e y aleatórios dentro de todo o mapa
        x = random.uniform(0, s.MAP_WIDTH)
        y = random.uniform(0, s.MAP_HEIGHT)
        
        # Cria um Vector2 com a posição gerada
        pos_spawn = pygame.math.Vector2(x, y)
        
        # Verifica se a posição gerada está longe o suficiente da referência (jogador)
        # Usa a distância mínima de spawn definida em settings como segurança
        if pos_referencia.distance_to(pos_spawn) > dist_min_do_jogador:
            return (x, y) # Retorna a posição válida
        # Se estiver muito perto, o loop continua e gera outra posição

def spawnar_inimigo_aleatorio(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia)
    chance = random.random()
    inimigo = None
    if chance < 0.05: inimigo = InimigoBomba(x, y)
    elif chance < 0.10: inimigo = InimigoTiroRapido(x, y)
    elif chance < 0.15: inimigo = InimigoAtordoador(x, y)
    elif chance < 0.35: inimigo = InimigoAtiradorRapido(x, y)
    elif chance < 0.55: inimigo = InimigoRapido(x, y)
    else: inimigo = InimigoPerseguidor(x, y)

    if inimigo:
        grupo_inimigos.add(inimigo)
        # grupo_todos_sprites.add(inimigo)

def spawnar_bot(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia)
    novo_bot = NaveBot(x, y)
    grupo_bots.add(novo_bot)
    # grupo_todos_sprites.add(novo_bot)

def spawnar_mothership(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia)
    nova_mothership = InimigoMothership(x, y)
    grupo_inimigos.add(nova_mothership)
    grupo_motherships.add(nova_mothership)
    # grupo_todos_sprites.add(nova_mothership)

def spawnar_vida(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia)
    nova_vida = VidaColetavel(x, y)
    grupo_vidas_coletaveis.add(nova_vida)
    # grupo_todos_sprites.add(nova_vida)

def spawnar_obstaculo(pos_referencia):
    x, y = calcular_posicao_spawn(pos_referencia)
    raio = random.randint(20, 40)
    novo_obstaculo = Obstaculo(x, y, raio)
    grupo_obstaculos.add(novo_obstaculo)
    # grupo_todos_sprites.add(novo_obstaculo)

def processar_cheat(comando, nave):
    global variavel_texto_terminal
    comando_limpo = comando.strip().lower()
    if comando_limpo == "maxpoint":
        nave.ganhar_pontos(9999)
        print("[CHEAT] +9999 pontos adicionados!")
    else:
        print(f"[CHEAT] Comando desconhecido: '{comando_limpo}'")
    variavel_texto_terminal = ""

def reiniciar_jogo():
    global estado_jogo, nave_player, max_bots_atual

    print("Reiniciando o Jogo...")

    # Limpa grupos
    grupo_projeteis_player.empty()
    grupo_projeteis_bots.empty()
    grupo_projeteis_inimigos.empty()
    grupo_obstaculos.empty()
    grupo_vidas_coletaveis.empty()
    grupo_inimigos.empty()
    grupo_motherships.empty()
    grupo_bots.empty()
    grupo_explosoes.empty()

    # Reseta jogador
    margem_spawn = 100
    spawn_x = random.randint(margem_spawn, s.MAP_WIDTH - margem_spawn)
    spawn_y = random.randint(margem_spawn, s.MAP_HEIGHT - margem_spawn)
    nave_player.posicao = pygame.math.Vector2(spawn_x, spawn_y)
    nave_player.rect.center = nave_player.posicao
    nave_player.grupo_auxiliares_ativos.empty()
    nave_player.lista_todas_auxiliares = [] # Recria lista de auxiliares
    for pos in Nave.POSICOES_AUXILIARES: # Usa Nave base importada
        nova_aux = NaveAuxiliar(nave_player, pos)
        nave_player.lista_todas_auxiliares.append(nova_aux)
    nave_player.pontos = 0
    nave_player.nivel_motor = 1
    nave_player.nivel_dano = 1
    nave_player.nivel_max_vida = 1
    nave_player.nivel_escudo = 0
    nave_player.velocidade_movimento_base = 4 + nave_player.nivel_motor
    nave_player.max_vida = 4 + nave_player.nivel_max_vida
    nave_player.vida_atual = nave_player.max_vida
    nave_player.alvo_selecionado = None
    nave_player.posicao_alvo_mouse = None
    nave_player.ultimo_hit_tempo = 0
    nave_player.tempo_fim_lentidao = 0
    nave_player.rastro_particulas = []

    # Reset max_bots_atual para o padrão? Ou mantém a configuração? Manteremos por enquanto.
    # max_bots_atual = s.MAX_BOTS

    # Spawn inicial
    for _ in range(20): spawnar_obstaculo(nave_player.posicao) # Mais obstáculos iniciais
    for _ in range(5): spawnar_vida(nave_player.posicao)     # Mais vidas iniciais
    # Limpa bots antes de spawnar novos (caso reiniciar_jogo seja chamado de outro estado)
    grupo_bots.empty()
    for _ in range(max_bots_atual): spawnar_bot(nave_player.posicao) # Spawna a quantidade configurada

    estado_jogo = "JOGANDO"

# 10. Recalcula Posições Iniciais da UI (após inicializar Pygame)
ui.recalculate_ui_positions(LARGURA_TELA, ALTURA_TELA)

# --- LOOP PRINCIPAL DO JOGO ---
while rodando:
    # 11. Tratamento de Eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False
        elif event.type == pygame.VIDEORESIZE:
            LARGURA_TELA = event.w
            ALTURA_TELA = event.h
            tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.RESIZABLE)
            ui.recalculate_ui_positions(LARGURA_TELA, ALTURA_TELA)
            camera.resize(LARGURA_TELA, ALTURA_TELA)
            print(f"Tela redimensionada para: {LARGURA_TELA}x{ALTURA_TELA}")

        # --- Eventos por Estado ---
        if estado_jogo == "MENU":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if ui.RECT_BOTAO_JOGAR_OFF.collidepoint(mouse_pos):
                    reiniciar_jogo()
                elif ui.RECT_BOTAO_MULTIPLAYER.collidepoint(mouse_pos):
                    print("Modo Multijogador ainda não implementado.")
                elif ui.RECT_BOTAO_SAIR.collidepoint(mouse_pos):
                    rodando = False

        elif estado_jogo == "JOGANDO":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_v: estado_jogo = "LOJA"; print("Abrindo loja...")
                elif event.key == pygame.K_QUOTE: estado_jogo = "TERMINAL"; variavel_texto_terminal = ""; print("Abrindo terminal de cheats...")
                elif event.key == pygame.K_ESCAPE: estado_jogo = "PAUSE"; print("Jogo Pausado.")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos_tela = pygame.mouse.get_pos()
                if ui.RECT_BOTAO_VOLTAR_MENU.collidepoint(mouse_pos):
                    # Limpa todos os bots e inimigos para não continuarem no menu
                    grupo_bots.empty()
                    grupo_inimigos.empty()
                    grupo_motherships.empty()
                    grupo_projeteis_bots.empty()
                    grupo_projeteis_inimigos.empty()
                    estado_jogo = "MENU"
                    print("Voltando ao Menu Principal.")
                if event.button == 1: # Esquerdo
                    if ui.RECT_BOTAO_UPGRADE_HUD.collidepoint(mouse_pos_tela):
                         estado_jogo = "LOJA"; print("Abrindo loja via clique no botão HUD...")
                    else: # Clique no mapa
                        camera_world_topleft = (-camera.camera_rect.left, -camera.camera_rect.top)
                        mouse_pos_mundo = pygame.math.Vector2(mouse_pos_tela[0] + camera_world_topleft[0],
                                                              mouse_pos_tela[1] + camera_world_topleft[1])
                        alvo_clicado = None
                        todos_alvos_clicaveis = list(grupo_inimigos) + list(grupo_bots) + list(grupo_obstaculos)
                        for alvo in todos_alvos_clicaveis:
                            target_click_rect = pygame.Rect(0, 0, s.TARGET_CLICK_SIZE, s.TARGET_CLICK_SIZE)
                            target_click_rect.center = alvo.posicao
                            if target_click_rect.collidepoint(mouse_pos_mundo):
                                alvo_clicado = alvo
                                break
                        nave_player.alvo_selecionado = alvo_clicado
                # Botão direito é tratado em Player.processar_input_humano

        elif estado_jogo == "PAUSE":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: estado_jogo = "JOGANDO"; print("Jogo Retomado.")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if ui.RECT_BOTAO_VOLTAR_MENU.collidepoint(mouse_pos):
                    estado_jogo = "MENU"
                    print("Voltando ao Menu Principal...")
                if ui.RECT_BOTAO_BOT_MENOS.collidepoint(mouse_pos):
                    if max_bots_atual > 0:
                        max_bots_atual -= 1
                        print(f"Máximo de Bots reduzido para: {max_bots_atual}")
                        if len(grupo_bots) > max_bots_atual:
                             # Tenta remover um bot aleatório ou o último
                             try:
                                 bot_para_remover = random.choice(grupo_bots.sprites())
                                 bot_para_remover.kill()
                                 print(f"Bot {bot_para_remover.nome} removido.")
                             except IndexError: # Caso o grupo esteja vazio inesperadamente
                                 pass
                elif ui.RECT_BOTAO_BOT_MAIS.collidepoint(mouse_pos):
                    if max_bots_atual < s.MAX_BOTS_LIMITE_SUPERIOR:
                        max_bots_atual += 1
                        print(f"Máximo de Bots aumentado para: {max_bots_atual}")

        elif estado_jogo == "LOJA":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_v: estado_jogo = "JOGANDO"; print("Fechando loja...")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if ui.RECT_BOTAO_MOTOR.collidepoint(mouse_pos): nave_player.comprar_upgrade("motor")
                elif ui.RECT_BOTAO_DANO.collidepoint(mouse_pos): nave_player.comprar_upgrade("dano")
                elif ui.RECT_BOTAO_AUX.collidepoint(mouse_pos): nave_player.comprar_upgrade("auxiliar")
                elif ui.RECT_BOTAO_MAX_HP.collidepoint(mouse_pos): nave_player.comprar_upgrade("max_health")
                elif ui.RECT_BOTAO_ESCUDO.collidepoint(mouse_pos): nave_player.comprar_upgrade("escudo")

        elif estado_jogo == "TERMINAL":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    processar_cheat(variavel_texto_terminal, nave_player)
                    estado_jogo = "JOGANDO"
                elif event.key == pygame.K_BACKSPACE: variavel_texto_terminal = variavel_texto_terminal[:-1]
                elif event.key == pygame.K_QUOTE: estado_jogo = "JOGANDO"; print("Fechando terminal.")
                else:
                    if len(variavel_texto_terminal) < 50: variavel_texto_terminal += event.unicode

        elif estado_jogo == "GAME_OVER":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if ui.RECT_BOTAO_REINICIAR.collidepoint(mouse_pos):
                    reiniciar_jogo()

    # 12. Lógica de Atualização
    # --- Atualizações que rodam exceto no Menu e Pausa ---
    if estado_jogo not in ["MENU", "PAUSE"]:
        # Atualiza Câmera
        camera.update(nave_player)

        # Define listas de alvos
        if estado_jogo == "GAME_OVER": lista_alvos_naves = list(grupo_bots)
        else: lista_alvos_naves = [nave_player] + list(grupo_bots)
        lista_todos_alvos_para_aux = list(grupo_inimigos) + list(grupo_obstaculos) + lista_alvos_naves

        # Atualiza Bots e Auxiliares
        grupo_bots.update(nave_player, grupo_projeteis_bots, grupo_bots, grupo_inimigos, grupo_obstaculos)
        for bot in grupo_bots:
            bot.grupo_auxiliares_ativos.update(lista_todos_alvos_para_aux, grupo_projeteis_bots, estado_jogo, nave_player)

        # Atualiza Inimigos
        grupo_inimigos.update(lista_alvos_naves, grupo_projeteis_inimigos, s.DESPAWN_DIST)

        # Atualiza Projéteis
        grupo_projeteis_player.update()
        grupo_projeteis_bots.update()
        grupo_projeteis_inimigos.update()

        # Atualiza Auxiliares do Jogador
        nave_player.grupo_auxiliares_ativos.update(lista_todos_alvos_para_aux, grupo_projeteis_player, estado_jogo, nave_player)

        # Atualiza Efeitos
        grupo_explosoes.update()

        # --- Lógica de Spawn ---
        if len(grupo_vidas_coletaveis) < s.MAX_VIDAS_COLETAVEIS: spawnar_vida(nave_player.posicao)
        if len(grupo_obstaculos) < s.MAX_OBSTACULOS: spawnar_obstaculo(nave_player.posicao)
        contagem_inimigos_normais = sum(1 for inimigo in grupo_inimigos if not isinstance(inimigo, (InimigoMinion, InimigoMothership)))
        if contagem_inimigos_normais < s.MAX_INIMIGOS: spawnar_inimigo_aleatorio(nave_player.posicao)
        if len(grupo_motherships) < s.MAX_MOTHERSHIPS: spawnar_mothership(nave_player.posicao)
        # Spawna bots apenas se estiver JOGANDO (evita spawn na tela de game over)
        if estado_jogo == "JOGANDO" and len(grupo_bots) < max_bots_atual: spawnar_bot(nave_player.posicao)

        # --- Lógica de Colisões (Geral - exceto colisões diretas com jogador) ---
        # Projéteis Player vs ...
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_obstaculos, True, True)
        for _, obst_list in colisoes.items(): nave_player.ganhar_pontos(len(obst_list)) # Jogador ganha pontos
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_inimigos, True, False)
        for _, inim_list in colisoes.items():
            for inimigo in inim_list:
                if inimigo.foi_atingido(nave_player.nivel_dano):
                    nave_player.ganhar_pontos(inimigo.pontos_por_morte);
                    if isinstance(inimigo, InimigoMothership): inimigo.grupo_minions.empty()
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_bots, True, False)
        for _, bot_list in colisoes.items():
            for bot in bot_list: bot.foi_atingido(nave_player.nivel_dano, estado_jogo) # Tiro amigo!

        # Projéteis Bots vs ...
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_obstaculos, True, True)
        for proj, obst_list in colisoes.items():
            for bot in grupo_bots:
                if bot.posicao.distance_to(proj.posicao) < bot.distancia_scan: bot.ganhar_pontos(len(obst_list)); break
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_inimigos, True, False)
        for proj, inim_list in colisoes.items():
            bot_que_acertou = None; dano_bot = 1
            for bot_ in grupo_bots:
                if bot_.posicao.distance_to(proj.posicao) < bot_.distancia_scan: bot_que_acertou = bot_; dano_bot = bot_.nivel_dano; break
            if bot_que_acertou:
                for inimigo in inim_list:
                    if inimigo.foi_atingido(dano_bot):
                        bot_que_acertou.ganhar_pontos(inimigo.pontos_por_morte);
                        if isinstance(inimigo, InimigoMothership): inimigo.grupo_minions.empty()

        # Projéteis Inimigos vs Bots
        colisoes = pygame.sprite.groupcollide(grupo_bots, grupo_projeteis_inimigos, False, False)
        for bot, proj_list in colisoes.items():
            for proj in proj_list:
                if isinstance(proj, ProjetilTeleguiadoLento): bot.aplicar_lentidao(6000)
                else: bot.foi_atingido(1, estado_jogo, proj.posicao)
                proj.kill()

        # Coleta de Vida (Bots)
        colisoes = pygame.sprite.groupcollide(grupo_bots, grupo_vidas_coletaveis, False, True)
        for bot, vida_list in colisoes.items():
            if vida_list: bot.coletar_vida(s.VIDA_COLETADA_CURA)

        # Colisões de Corpo (RAM) - Bot vs Inimigo
        for bot in grupo_bots:
            inimigos_colididos = pygame.sprite.spritecollide(bot, grupo_inimigos, False)
            for inimigo in inimigos_colididos:
                dano = 1 if not isinstance(inimigo, InimigoBomba) else inimigo.DANO_EXPLOSAO
                bot.foi_atingido(dano, estado_jogo, inimigo.posicao)
                if inimigo.foi_atingido(1): # Inimigo também toma dano RAM
                    bot.ganhar_pontos(inimigo.pontos_por_morte)
                    if isinstance(inimigo, InimigoMothership): inimigo.grupo_minions.empty()

    # --- Atualizações e Colisões Específicas do Jogador (Só quando JOGANDO) ---
    if estado_jogo == "JOGANDO":
        # Atualiza Input, Movimento, Tiro do Jogador
        nave_player.update(grupo_projeteis_player, camera)

        # Colisões QUE AFETAM O JOGADOR DIRETAMENTE
        # Projéteis Inimigos vs Jogador
        colisoes_proj_inimigo_player = pygame.sprite.spritecollide(nave_player, grupo_projeteis_inimigos, False)
        for proj in colisoes_proj_inimigo_player:
            if isinstance(proj, ProjetilTeleguiadoLento): nave_player.aplicar_lentidao(6000)
            else:
                # Passa estado_jogo para foi_atingido saber se já está em game over
                if nave_player.foi_atingido(1, estado_jogo, proj.posicao):
                     estado_jogo = "GAME_OVER" # Muda estado se jogador morreu
            proj.kill()
            
        colisoes_proj_bot_player = pygame.sprite.spritecollide(nave_player, grupo_projeteis_bots, True) # True: Projéteis são destruídos
        for proj in colisoes_proj_bot_player:
            # A classe Projetil não armazena o dano (apenas a cor)
            # Vamos assumir dano 1, assim como os projéteis inimigos.
            if nave_player.foi_atingido(1, estado_jogo, proj.posicao):
                 estado_jogo = "GAME_OVER" # Muda estado se jogador morreu

        # Coleta de Vida (Jogador)
        colisoes_vida_player = pygame.sprite.spritecollide(nave_player, grupo_vidas_coletaveis, True)
        for _ in colisoes_vida_player: nave_player.coletar_vida(s.VIDA_COLETADA_CURA)

        # Colisões de Corpo (RAM) vs Jogador
        colisoes_ram_inimigo_player = pygame.sprite.spritecollide(nave_player, grupo_inimigos, False)
        for inimigo in colisoes_ram_inimigo_player:
            dano = 1 if not isinstance(inimigo, InimigoBomba) else inimigo.DANO_EXPLOSAO
            if nave_player.foi_atingido(dano, estado_jogo, inimigo.posicao):
                estado_jogo = "GAME_OVER"
            # Inimigo também toma dano na colisão e jogador ganha pontos se matar
            if inimigo.foi_atingido(1):
                nave_player.ganhar_pontos(inimigo.pontos_por_morte)
                if isinstance(inimigo, InimigoMothership): inimigo.grupo_minions.empty()
        colisoes_ram_bot_player = pygame.sprite.spritecollide(nave_player, grupo_bots, False)
        for bot in colisoes_ram_bot_player:
            if nave_player.foi_atingido(1, estado_jogo, bot.posicao): # Jogador toma dano
                estado_jogo = "GAME_OVER"
            bot.foi_atingido(1, estado_jogo, nave_player.posicao) # Bot também toma dano

    # 13. Desenho
    if estado_jogo == "MENU":
        ui.desenhar_menu(tela, LARGURA_TELA, ALTURA_TELA)
    else: # Desenha o jogo e as UIs sobrepostas
        # Fundo estrelado
        tela.fill(s.PRETO)
        for pos_base, raio, parallax_fator in lista_estrelas:
            pos_jogador = nave_player.posicao
            pos_tela_x = (pos_base.x - (pos_jogador.x * parallax_fator)) % LARGURA_TELA
            pos_tela_y = (pos_base.y - (pos_jogador.y * parallax_fator)) % ALTURA_TELA
            pygame.draw.circle(tela, s.CORES_ESTRELAS[raio - 1], (int(pos_tela_x), int(pos_tela_y)), raio)

        # Sprites do Jogo
        for obst in grupo_obstaculos: tela.blit(obst.image, camera.apply(obst.rect))
        for vida in grupo_vidas_coletaveis: tela.blit(vida.image, camera.apply(vida.rect))
        for inimigo in grupo_inimigos: inimigo.desenhar_vida(tela, camera); tela.blit(inimigo.image, camera.apply(inimigo.rect)) # Desenha vida primeiro
        for bot in grupo_bots:
            bot.desenhar(tela, camera); bot.desenhar_vida(tela, camera)
            for aux in bot.grupo_auxiliares_ativos: aux.desenhar(tela, camera)
        for proj in grupo_projeteis_player: tela.blit(proj.image, camera.apply(proj.rect))
        for proj in grupo_projeteis_bots: tela.blit(proj.image, camera.apply(proj.rect))
        for proj in grupo_projeteis_inimigos: tela.blit(proj.image, camera.apply(proj.rect))
        if estado_jogo != "GAME_OVER": # Só desenha jogador se não morreu
            nave_player.desenhar(tela, camera); nave_player.desenhar_vida(tela, camera)
            for aux in nave_player.grupo_auxiliares_ativos: aux.desenhar(tela, camera)
        for explosao in grupo_explosoes: explosao.draw(tela, camera)

        # UI Estática
        ui.desenhar_hud(tela, nave_player, estado_jogo)
        ui.desenhar_minimapa(tela, nave_player, grupo_bots, estado_jogo, s.MAP_WIDTH, s.MAP_HEIGHT)
        todos_os_jogadores = [nave_player] + list(grupo_bots.sprites())
        lista_ordenada = sorted(todos_os_jogadores, key=lambda n: n.pontos, reverse=True); top_5 = lista_ordenada[:5]
        ui.desenhar_ranking(tela, top_5, nave_player)

        # Overlays (Pausa desenha antes dos outros para ficar por baixo)
        if estado_jogo == "PAUSE":
            ui.desenhar_pause(tela, max_bots_atual, s.MAX_BOTS_LIMITE_SUPERIOR, len(grupo_bots))
        elif estado_jogo == "LOJA":
            ui.desenhar_loja(tela, nave_player, LARGURA_TELA, ALTURA_TELA)
        elif estado_jogo == "TERMINAL":
            ui.desenhar_terminal(tela, variavel_texto_terminal, LARGURA_TELA, ALTURA_TELA)
        elif estado_jogo == "GAME_OVER":
            ui.desenhar_game_over(tela, LARGURA_TELA, ALTURA_TELA)

    # 14. Atualiza a Tela e Controla FPS
    pygame.display.flip()
    clock.tick(60)

# 15. Finalização
pygame.quit()
sys.exit()