# event_handler.py
import pygame
import ui
import random
import settings as s
from ships import Player, NaveBot, NaveAuxiliar, Nave
from camera import Camera
from pause_menu import PauseMenu
from Redes.network_client import NetworkClient 

class EventHandler:
    def __init__(self, network_client: NetworkClient, camera: Camera, pause_manager: PauseMenu, main_callbacks: dict):
        """
        Inicializa o gerenciador de eventos.
        
        Args:
            network_client: A instância do NetworkClient.
            camera: A instância da Câmera (para cliques do mouse).
            pause_manager: A instância do PauseMenu.
            main_callbacks: Um dicionário de funções do main.py (ex: "reiniciar_jogo").
        """
        self.network_client = network_client
        self.camera = camera
        self.pause_manager = pause_manager
        
        self.cb_reiniciar_jogo = main_callbacks["reiniciar_jogo"]
        self.cb_resetar_para_menu = main_callbacks["resetar_para_menu"]
        self.cb_processar_cheat = main_callbacks["processar_cheat"]
        self.cb_ciclar_alvo_espectador = main_callbacks["ciclar_alvo_espectador"]
        self.cb_respawn_player_offline = main_callbacks["respawn_player_offline"]
        self.cb_reiniciar_jogo_pvp = main_callbacks.get("reiniciar_jogo_pvp", lambda: print("[ERRO] cb_reiniciar_jogo_pvp não foi definido no event_handler."))
        
    def processar_eventos(self, game_state: dict):
        """
        Processa todos os eventos pendentes do Pygame e atualiza o game_state.
        Este método SUBSTITUI o loop 'for event...' do main.py.
        
        Args:
            game_state: Um dicionário contendo o estado atual do jogo.
        
        Returns:
            Um dicionário com o estado do jogo atualizado.
        """
        
        novos_estados = game_state.copy()
        
        estado_jogo = novos_estados["estado_jogo"]
        nave_player = novos_estados["nave_player"]
        is_online = novos_estados["is_online"]
        agora = novos_estados["agora"]
        
        if estado_jogo == "JOGANDO" and is_online and agora > nave_player.tempo_spawn_protecao_input:
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0]:
                mouse_pos_tela = pygame.mouse.get_pos()
                if not ui.RECT_BOTAO_UPGRADE_HUD.collidepoint(mouse_pos_tela) and not ui.RECT_BOTAO_REGEN_HUD.collidepoint(mouse_pos_tela):
                    mouse_pos_mundo = self.camera.get_mouse_world_pos(mouse_pos_tela)
                    self.network_client.send(f"CLICK_MOVE|{int(mouse_pos_mundo.x)}|{int(mouse_pos_mundo.y)}")
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                novos_estados["rodando"] = False
                
            elif event.type == pygame.VIDEORESIZE:
                novos_estados["LARGURA_TELA"] = event.w
                novos_estados["ALTURA_TELA"] = event.h
                
            if estado_jogo == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if ui.RECT_BOTAO_JOGAR_OFF.collidepoint(mouse_pos):
                        novos_estados["estado_jogo"] = "GET_NAME"
                        novos_estados["input_nome_ativo"] = True
                    elif ui.RECT_BOTAO_MULTIPLAYER.collidepoint(mouse_pos):
                        novos_estados["estado_jogo"] = "MULTIPLAYER_MODE_SELECT" 
                    elif ui.RECT_BOTAO_SAIR.collidepoint(mouse_pos):
                        novos_estados["rodando"] = False

            elif estado_jogo == "GET_NAME":
                if event.type == pygame.KEYDOWN:
                    if novos_estados["input_nome_ativo"]:
                        if event.key == pygame.K_RETURN:
                            novos_estados["estado_jogo"] = "OFFLINE_MODE_SELECT" 
                        elif event.key == pygame.K_BACKSPACE:
                            novos_estados["nome_jogador_input"] = novos_estados["nome_jogador_input"][:-1]
                        else:
                            if len(novos_estados["nome_jogador_input"]) < s.LIMITE_MAX_NOME and event.unicode.isprintable():
                                novos_estados["nome_jogador_input"] += event.unicode
                
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if ui.RECT_LOGIN_BOTAO.collidepoint(mouse_pos):
                        novos_estados["estado_jogo"] = "OFFLINE_MODE_SELECT" 
                    elif ui.RECT_LOGIN_INPUT.collidepoint(mouse_pos):
                        novos_estados["input_nome_ativo"] = True
                    elif ui.RECT_LOGIN_DIFICULDADE_LEFT.collidepoint(mouse_pos):
                        novos_estados["dificuldade_selecionada"] = "Normal"
                    elif ui.RECT_LOGIN_DIFICULDADE_RIGHT.collidepoint(mouse_pos):
                        novos_estados["dificuldade_selecionada"] = "Dificil"
                    else:
                        novos_estados["input_nome_ativo"] = False
            
            elif estado_jogo == "GET_SERVER_INFO":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        novos_estados["input_connect_ativo"] = "ip" if novos_estados["input_connect_ativo"] == "nome" else "nome"
                    elif event.key == pygame.K_RETURN:
                        if novos_estados["input_connect_ativo"] == "nome":
                            novos_estados["input_connect_ativo"] = "ip"
                        elif novos_estados["input_connect_ativo"] == "ip":
                            novos_estados["input_connect_ativo"] = "none"
                            
                            # --- INÍCIO: MODIFICAÇÃO (Lógica de Conexão PVE/PVP) ---
                            modo_de_jogo_desejado = novos_estados.get("multiplayer_mode_to_join", "PVE")
                            
                            sucesso, modo_retornado, nome_rede, pos_spawn = self.network_client.connect(
                                novos_estados["ip_servidor_input"], 5555, 
                                novos_estados["nome_jogador_input"], 
                                modo_de_jogo_desejado 
                            )
                            
                            if sucesso:
                                if modo_retornado == "PVE":
                                    self.cb_reiniciar_jogo(pos_spawn=pos_spawn)
                                    novos_estados["estado_jogo"] = "JOGANDO"
                                elif modo_retornado == "PVP":
                                    # Chama o setup PVP (que usa o mapa PVP)
                                    # (Teremos que modificar cb_reiniciar_jogo_pvp no main.py)
                                    self.cb_reiniciar_jogo_pvp(is_online=True, pos_spawn=pos_spawn)
                                    novos_estados["estado_jogo"] = "PVP_LOBBY"
                            else:
                                print(f"Falha ao conectar: {self.network_client.connection_error_message}")
                                novos_estados["estado_jogo"] = "MENU"
                            # --- FIM: MODIFICAÇÃO ---

                    elif novos_estados["input_connect_ativo"] == "nome":
                        if event.key == pygame.K_BACKSPACE:
                            novos_estados["nome_jogador_input"] = novos_estados["nome_jogador_input"][:-1]
                        elif len(novos_estados["nome_jogador_input"]) < s.LIMITE_MAX_NOME and event.unicode.isprintable():
                            novos_estados["nome_jogador_input"] += event.unicode
                    elif novos_estados["input_connect_ativo"] == "ip":
                        if event.key == pygame.K_BACKSPACE:
                            novos_estados["ip_servidor_input"] = novos_estados["ip_servidor_input"][:-1]
                        elif len(novos_estados["ip_servidor_input"]) < s.LIMITE_MAX_IP and event.unicode.isprintable():
                            novos_estados["ip_servidor_input"] += event.unicode
                
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if ui.RECT_CONNECT_BOTAO.collidepoint(mouse_pos):
                        novos_estados["input_connect_ativo"] = "none"

                        # --- INÍCIO: MODIFICAÇÃO (Lógica de Conexão PVE/PVP) ---
                        modo_de_jogo_desejado = novos_estados.get("multiplayer_mode_to_join", "PVE")
                        sucesso, modo_retornado, nome_rede, pos_spawn = self.network_client.connect(
                            novos_estados["ip_servidor_input"], 5555, 
                            novos_estados["nome_jogador_input"],
                            modo_de_jogo_desejado
                        )
                        
                        if sucesso:
                            if modo_retornado == "PVE":
                                self.cb_reiniciar_jogo(pos_spawn=pos_spawn)
                                novos_estados["estado_jogo"] = "JOGANDO"
                            elif modo_retornado == "PVP":
                                self.cb_reiniciar_jogo_pvp(is_online=True, pos_spawn=pos_spawn)
                                novos_estados["estado_jogo"] = "PVP_LOBBY"
                        else:
                            print(f"Falha ao conectar: {self.network_client.connection_error_message}")
                            novos_estados["estado_jogo"] = "MENU"
                        # --- FIM: MODIFICAÇÃO ---
                        
                    elif ui.RECT_CONNECT_NOME.collidepoint(mouse_pos):
                        novos_estados["input_connect_ativo"] = "nome"
                    elif ui.RECT_CONNECT_IP.collidepoint(mouse_pos):
                        novos_estados["input_connect_ativo"] = "ip"
                    else:
                        novos_estados["input_connect_ativo"] = "none"
            
            elif estado_jogo == "OFFLINE_MODE_SELECT":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        novos_estados["estado_jogo"] = "GET_NAME" 
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if ui.RECT_BOTAO_PVE_OFFLINE.collidepoint(mouse_pos):
                        novos_estados["estado_jogo"] = "PVE_OFFLINE_START"
                    
                    elif ui.RECT_BOTAO_PVP_OFFLINE.collidepoint(mouse_pos):
                        novos_estados["estado_jogo"] = "PVP_OFFLINE_START"

            elif estado_jogo == "MULTIPLAYER_MODE_SELECT":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        novos_estados["estado_jogo"] = "MENU"
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if ui.RECT_BOTAO_PVE_ONLINE.collidepoint(mouse_pos):
                        novos_estados["estado_jogo"] = "GET_SERVER_INFO"
                        novos_estados["input_connect_ativo"] = "nome"
                        novos_estados["multiplayer_mode_to_join"] = "PVE"
                    
                    elif ui.RECT_BOTAO_PVP_ONLINE.collidepoint(mouse_pos):
                        pvp_disponivel = novos_estados.get("pvp_disponivel", True) # Assumindo que está disponível
                        if pvp_disponivel:
                            novos_estados["estado_jogo"] = "GET_SERVER_INFO"
                            novos_estados["input_connect_ativo"] = "nome"
                            novos_estados["multiplayer_mode_to_join"] = "PVP"
                        else:
                            print("[AVISO] Modo PVP clicado, mas não está disponível.")
            
            elif estado_jogo in ["JOGANDO", "PVP_LOBBY", "PVP_COUNTDOWN", "PVP_PLAYING", "PVP_PRE_MATCH"]:
                if event.type == pygame.KEYDOWN:
                    
                    if event.key == pygame.K_v and estado_jogo in ["JOGANDO", "PVP_LOBBY", "PVP_COUNTDOWN"]: 
                        novos_estados["estado_anterior_loja"] = estado_jogo 
                        novos_estados["estado_jogo"] = "LOJA"; print("Abrindo loja...")
                    
                    elif event.key == pygame.K_QUOTE: 
                        if estado_jogo == "JOGANDO": 
                            novos_estados["estado_anterior_terminal"] = estado_jogo 
                            novos_estados["estado_jogo"] = "TERMINAL"; novos_estados["variavel_texto_terminal"] = ""; print("Abrindo terminal de cheats...")
                        else:
                            print("[PVP] Terminal desabilitado no modo PVP.") 
                    
                    elif event.key == pygame.K_ESCAPE: 
                        novos_estados["estado_anterior_pause"] = estado_jogo 
                        novos_estados["estado_jogo"] = "PAUSE"; print("Jogo Pausado.")
                    
                    elif event.key == pygame.K_r and estado_jogo == "JOGANDO":
                        if is_online:
                            self.network_client.send("TOGGLE_REGEN")
                        else:
                            grupo_fx = novos_estados.get("grupo_efeitos_visuais")
                            if grupo_fx is not None:
                                nave_player.toggle_regeneracao(grupo_fx)
                            else:
                                print("[AVISO] grupo_efeitos_visuais não encontrado para regeneração offline.")

                    elif is_online: # Controles de rede
                        if event.key == pygame.K_w or event.key == pygame.K_UP: self.network_client.send("W_DOWN")
                        elif event.key == pygame.K_a or event.key == pygame.K_LEFT: self.network_client.send("A_DOWN")
                        elif event.key == pygame.K_s or event.key == pygame.K_DOWN: self.network_client.send("S_DOWN")
                        elif event.key == pygame.K_d or event.key == pygame.K_RIGHT: self.network_client.send("D_DOWN")
                        elif event.key == pygame.K_SPACE: self.network_client.send("SPACE_DOWN")
                
                elif event.type == pygame.KEYUP:
                    if is_online:
                        if event.key == pygame.K_w or event.key == pygame.K_UP: self.network_client.send("W_UP")
                        elif event.key == pygame.K_a or event.key == pygame.K_LEFT: self.network_client.send("A_UP")
                        elif event.key == pygame.K_s or event.key == pygame.K_DOWN: self.network_client.send("S_UP")
                        elif event.key == pygame.K_d or event.key == pygame.K_RIGHT: self.network_client.send("D_UP")
                        elif event.key == pygame.K_SPACE: self.network_client.send("SPACE_UP")

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos_tela = pygame.mouse.get_pos()
                    
                    if event.button == 1: 
                        if ui.RECT_BOTAO_UPGRADE_HUD.collidepoint(mouse_pos_tela) and estado_jogo in ["JOGANDO", "PVP_LOBBY", "PVP_COUNTDOWN"]:
                             novos_estados["estado_anterior_loja"] = estado_jogo 
                             novos_estados["estado_jogo"] = "LOJA"; print("Abrindo loja via clique no botão HUD...")
                        
                        elif ui.RECT_BOTAO_REGEN_HUD.collidepoint(mouse_pos_tela) and estado_jogo == "JOGANDO":
                            if is_online:
                                self.network_client.send("TOGGLE_REGEN")
                            else: 
                                grupo_fx = novos_estados.get("grupo_efeitos_visuais")
                                if grupo_fx is not None:
                                    nave_player.toggle_regeneracao(grupo_fx)
                        
                        elif not is_online and agora > nave_player.tempo_spawn_protecao_input:
                            mouse_pos_mundo = self.camera.get_mouse_world_pos(mouse_pos_tela)
                            nave_player.posicao_alvo_mouse = mouse_pos_mundo
                            nave_player.quer_mover_frente = False 
                            nave_player.quer_mover_tras = False

                    elif event.button == 3: 
                        mouse_pos_tela = pygame.mouse.get_pos() 

                        if (agora > nave_player.tempo_spawn_protecao_input and 
                            ui.MINIMAP_RECT.collidepoint(mouse_pos_tela) and
                            not is_online): 
                            
                            click_x_rel = mouse_pos_tela[0] - ui.MINIMAP_RECT.left
                            click_y_rel = mouse_pos_tela[1] - ui.MINIMAP_RECT.top
                            
                            map_w = s.MAP_WIDTH
                            map_h = s.MAP_HEIGHT

                            ratio_x = map_w / ui.MINIMAP_WIDTH
                            ratio_y = map_h / ui.MINIMAP_HEIGHT
                            
                            world_x = click_x_rel * ratio_x
                            world_y = click_y_rel * ratio_y
                            
                            destino = pygame.math.Vector2(world_x, world_y)
                            nave_player.posicao_alvo_mouse = destino
                            
                            nave_player.quer_mover_frente = False 
                            nave_player.quer_mover_tras = False
                            nave_player.alvo_selecionado = None
                        
                        elif agora > nave_player.tempo_spawn_protecao_input: 
                            mouse_pos_mundo = self.camera.get_mouse_world_pos(mouse_pos_tela)
                            
                            if is_online:
                                self.network_client.send(f"CLICK_TARGET|{int(mouse_pos_mundo.x)}|{int(mouse_pos_mundo.y)}")
                                
                                alvo_clicado_id = None
                                dist_min_sq = (s.TARGET_CLICK_SIZE / 2)**2
                                
                                game_state_rede = self.network_client.get_state()
                                # --- INÍCIO: MODIFICAÇÃO (Mira Online PVP) ---
                                # No PVP, miramos em Jogadores, não em NPCs
                                if estado_jogo.startswith("PVP_"):
                                    online_players_copy = game_state_rede['players']
                                    meu_nome = self.network_client.get_my_name()
                                    for nome, state in online_players_copy.items():
                                        if nome == meu_nome: continue
                                        if state.get('hp', 0) <= 0: continue
                                        dist_sq = (state['x'] - mouse_pos_mundo.x)**2 + (state['y'] - mouse_pos_mundo.y)**2
                                        if dist_sq < dist_min_sq:
                                            dist_min_sq = dist_sq
                                            alvo_clicado_id = nome
                                else: # Lógica PVE (original)
                                    online_npcs_copy = game_state_rede['npcs']
                                    for npc_id, state in online_npcs_copy.items():
                                        if state.get('hp', 0) <= 0: continue
                                        dist_sq = (state['x'] - mouse_pos_mundo.x)**2 + (state['y'] - mouse_pos_mundo.y)**2
                                        if dist_sq < dist_min_sq:
                                            dist_min_sq = dist_sq
                                            alvo_clicado_id = npc_id 
                                # --- FIM: MODIFICAÇÃO ---
                                
                                nave_player.alvo_selecionado = alvo_clicado_id 
                                
                            else: # Offline
                                alvo_clicado = None
                                grupo_inimigos = novos_estados.get("grupo_inimigos")
                                grupo_bots = novos_estados.get("grupo_bots")
                                grupo_obstaculos = novos_estados.get("grupo_obstaculos")
                                
                                todos_alvos_clicaveis = []
                                if estado_jogo.startswith("PVP_"):
                                    if grupo_bots:
                                        todos_alvos_clicaveis.extend(list(grupo_bots))
                                    if grupo_obstaculos:
                                        todos_alvos_clicaveis.extend(list(grupo_obstaculos))
                                else:
                                    if grupo_inimigos: todos_alvos_clicaveis.extend(list(grupo_inimigos))
                                    if grupo_bots: todos_alvos_clicaveis.extend(list(grupo_bots))
                                    if grupo_obstaculos: todos_alvos_clicaveis.extend(list(grupo_obstaculos))
                                    
                                dist_min_sq = (s.TARGET_CLICK_SIZE / 2)**2
                                for alvo in todos_alvos_clicaveis:
                                    if alvo == nave_player:
                                        continue
                                    dist_sq = alvo.posicao.distance_squared_to(mouse_pos_mundo)
                                    if dist_sq < dist_min_sq:
                                        dist_min_sq = dist_sq
                                        alvo_clicado = alvo
                                nave_player.alvo_selecionado = alvo_clicado
            
            elif estado_jogo == "PAUSE":
                action = self.pause_manager.handle_event(event, is_online)

                if action == "RESUME_GAME":
                    estado_anterior = game_state.get("estado_anterior_pause", "JOGANDO")
                    novos_estados["estado_jogo"] = estado_anterior
                
                elif action == "GOTO_MENU":
                    self.cb_resetar_para_menu() 
                    novos_estados["estado_jogo"] = "MENU" 

                elif action == "REQ_SPECTATOR":
                    if not game_state.get("estado_anterior_pause", "").startswith("PVP_"):
                        if is_online:
                            novos_estados["jogador_pediu_para_espectar"] = True
                            novos_estados["jogador_esta_vivo_espectador"] = True
                            self.network_client.send("ENTER_SPECTATOR")
                            novos_estados["estado_jogo"] = "JOGANDO" 
                        else:
                            nave_player.vida_atual = 0 
                            novos_estados["estado_jogo"] = "ESPECTADOR"
                            novos_estados["jogador_esta_vivo_espectador"] = True
                            novos_estados["alvo_espectador"] = None
                            novos_estados["alvo_espectador_nome"] = None
                            novos_estados["espectador_dummy_alvo"].posicao = nave_player.posicao.copy()
                        
                        zoom_w = novos_estados["LARGURA_TELA"] / s.MAP_WIDTH
                        zoom_h = novos_estados["ALTURA_TELA"] / s.MAP_HEIGHT
                        self.camera.set_zoom(min(zoom_w, zoom_h))
                        novos_estados["alvo_espectador"] = None
                        novos_estados["alvo_espectador_nome"] = None
                    else:
                        print("[PVP] Modo espectador desabilitado durante partida PVP.")

                elif action == "REQ_RESPAWN":
                    is_pvp_map = (s.MAP_WIDTH < 5000)

                    if is_pvp_map:
                        print("[PVP] Respawn manual desabilitado no modo PVP.")
                    
                    elif (nave_player.vida_atual <= 0 or novos_estados["jogador_esta_vivo_espectador"]):
                        if is_online:
                            self.network_client.send("RESPAWN_ME")
                        else:
                            self.cb_respawn_player_offline(nave_player)
                            novos_estados["estado_jogo"] = "JOGANDO"
                            novos_estados["jogador_esta_vivo_espectador"] = False
                
                estado_antes_de_pausar = game_state.get("estado_anterior_pause", "JOGANDO")
                if not is_online and not estado_antes_de_pausar.startswith("PVP_"):
                    if action == "BOT_MENOS":
                        if novos_estados["max_bots_atual"] > 0:
                            novos_estados["max_bots_atual"] -= 1
                            grupo_bots = novos_estados.get("grupo_bots")
                            if grupo_bots and len(grupo_bots) > novos_estados["max_bots_atual"]:
                                 try:
                                     bot_para_remover = random.choice(grupo_bots.sprites())
                                     bot_para_remover.kill()
                                 except IndexError:
                                     pass
                                     
                    elif action == "BOT_MAIS":
                        if novos_estados["max_bots_atual"] < s.MAX_BOTS_LIMITE_SUPERIOR:
                            novos_estados["max_bots_atual"] += 1
            
            elif estado_jogo == "LOJA":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_v:
                    estado_para_retornar = game_state.get("estado_anterior_loja", "JOGANDO")
                    novos_estados["estado_jogo"] = estado_para_retornar
                    print(f"Fechando loja, retornando para: {estado_para_retornar}")
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if ui.RECT_BOTAO_MOTOR.collidepoint(mouse_pos):
                        if is_online: self.network_client.send("BUY_UPGRADE|motor")
                        else: nave_player.comprar_upgrade("motor")
                    elif ui.RECT_BOTAO_DANO.collidepoint(mouse_pos):
                        if is_online: self.network_client.send("BUY_UPGRADE|dano")
                        else: nave_player.comprar_upgrade("dano")
                    elif ui.RECT_BOTAO_AUX.collidepoint(mouse_pos):
                        if is_online: self.network_client.send("BUY_UPGRADE|auxiliar")
                        else: nave_player.comprar_upgrade("auxiliar")
                    elif ui.RECT_BOTAO_MAX_HP.collidepoint(mouse_pos):
                        if is_online: self.network_client.send("BUY_UPGRADE|max_health")
                        else: nave_player.comprar_upgrade("max_health")
                    elif ui.RECT_BOTAO_ESCUDO.collidepoint(mouse_pos):
                        if is_online: self.network_client.send("BUY_UPGRADE|escudo")
                        else: nave_player.comprar_upgrade("escudo")

            elif estado_jogo == "TERMINAL":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.cb_processar_cheat(novos_estados["variavel_texto_terminal"], nave_player)
                        novos_estados["estado_jogo"] = game_state.get("estado_anterior_terminal", "JOGANDO") 
                    elif event.key == pygame.K_BACKSPACE: novos_estados["variavel_texto_terminal"] = novos_estados["variavel_texto_terminal"][:-1]
                    elif event.key == pygame.K_QUOTE: 
                        novos_estados["estado_jogo"] = game_state.get("estado_anterior_terminal", "JOGANDO") 
                    else:
                        if len(novos_estados["variavel_texto_terminal"]) < 50: novos_estados["variavel_texto_terminal"] += event.unicode
            
            elif estado_jogo == "PVP_GAME_OVER":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        self.cb_resetar_para_menu() 
                        novos_estados["estado_jogo"] = "MENU"

            elif estado_jogo == "ESPECTADOR":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: 
                        novos_estados["estado_anterior_pause"] = estado_jogo 
                        novos_estados["estado_jogo"] = "PAUSE"
                        self.camera.set_zoom(1.0)
                    
                    elif event.key == pygame.K_z:
                         novos_estados["spectator_overlay_hidden"] = True 
                         if self.camera.zoom < 1.0:
                             self.camera.set_zoom(1.0)
                         else:
                             zoom_w = novos_estados["LARGURA_TELA"] / s.MAP_WIDTH
                             zoom_h = novos_estados["ALTURA_TELA"] / s.MAP_HEIGHT
                             self.camera.set_zoom(min(zoom_w, zoom_h))
                         novos_estados["alvo_espectador"] = None
                         novos_estados["alvo_espectador_nome"] = None
                    
                    elif event.key == pygame.K_e or event.key == pygame.K_q:
                        novos_estados["spectator_overlay_hidden"] = True 
                        self.cb_ciclar_alvo_espectador(novos_estados, avancar=(event.key == pygame.K_e))
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos_tela = pygame.mouse.get_pos()
                    
                    is_pve_map = s.MAP_WIDTH > 5000 
                    
                    if (is_pve_map and 
                        not novos_estados["jogador_esta_vivo_espectador"] and 
                        nave_player.vida_atual <= 0 and 
                        ui.RECT_BOTAO_REINICIAR.collidepoint(mouse_pos_tela)):
                        
                        if is_online:
                            self.network_client.send("RESPAWN_ME")
                        else:
                            self.cb_respawn_player_offline(nave_player)
                            novos_estados["estado_jogo"] = "JOGANDO" 
                            novos_estados["jogador_esta_vivo_espectador"] = False

                    elif event.button == 1:
                        novos_estados["spectator_overlay_hidden"] = True 
                        self.camera.set_zoom(1.0) 
                        mouse_pos_mundo = self.camera.get_mouse_world_pos(mouse_pos_tela)
                        
                        alvo_clicado_sprite = None
                        alvo_clicado_nome = None

                        if is_online:
                            game_state_rede = self.network_client.get_state()
                            online_players_copy = game_state_rede['players']
                            
                            dist_min_sq = (s.TARGET_CLICK_SIZE * 2)**2
                            for nome, state in online_players_copy.items():
                                if state.get('hp', 0) <= 0: continue
                                dist_sq = (state['x'] - mouse_pos_mundo.x)**2 + (state['y'] - mouse_pos_mundo.y)**2
                                if dist_sq < dist_min_sq:
                                    dist_min_sq = dist_sq
                                    alvo_clicado_nome = nome
                            if alvo_clicado_nome:
                                novos_estados["alvo_espectador_nome"] = alvo_clicado_nome
                                novos_estados["alvo_espectador"] = None
                        
                        else: # Modo Offline
                            grupo_bots = novos_estados.get("grupo_bots")
                            alvos_offline_vivos = []
                            if novos_estados["jogador_esta_vivo_espectador"]:
                                 alvos_offline_vivos.append(nave_player)
                            if grupo_bots:
                                alvos_offline_vivos.extend([bot for bot in grupo_bots if bot.vida_atual > 0])
                            
                            dist_min_sq = (s.TARGET_CLICK_SIZE * 2)**2
                            for alvo in alvos_offline_vivos:
                                dist_sq = alvo.posicao.distance_squared_to(mouse_pos_mundo)
                                if dist_sq < dist_min_sq:
                                    dist_min_sq = dist_sq
                                    alvo_clicado_sprite = alvo
                            
                            if alvo_clicado_sprite:
                                novos_estados["alvo_espectador"] = alvo_clicado_sprite
                                novos_estados["alvo_espectador_nome"] = None

                    elif event.button == 3:
                        novos_estados["spectator_overlay_hidden"] = True 
                        self.camera.set_zoom(1.0)
                        novos_estados["alvo_espectador"] = None
                        novos_estados["alvo_espectador_nome"] = None

        return novos_estados