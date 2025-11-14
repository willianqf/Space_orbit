# renderer.py
import pygame
import math
import settings as s
import multi.pvp_settings as pvp_s 
import ui
from camera import Camera
from pause_menu import PauseMenu
from Redes.network_client import NetworkClient
# --- INÍCIO: MODIFICAÇÃO (Importação corrigida) ---
from ships import Player, NaveBot, NaveAuxiliar, Nave, NaveRegeneradora, tocar_som_posicional
# --- FIM: MODIFICAÇÃO ---
from effects import Explosao
from entities import Obstaculo

class Renderer:
    def __init__(self, tela: pygame.Surface, camera: Camera, pause_manager: PauseMenu, 
                 network_client: NetworkClient, lista_estrelas: list):
        """
        Inicializa o gerenciador de renderização.

        Args:
            tela: A superfície principal do Pygame.
            camera: A instância da Câmera.
            pause_manager: A instância do PauseMenu.
            network_client: A instância do NetworkClient.
            lista_estrelas: A lista de estrelas para o parallax.
        """
        self.tela = tela
        self.camera = camera
        self.pause_manager = pause_manager
        self.network_client = network_client
        self.lista_estrelas = lista_estrelas
        
        self.ui = ui 

    def draw(self, estado_jogo: str, game_globals: dict, game_groups: dict, 
             online_data: dict, online_trackers: dict, alvo_camera_final: pygame.sprite.Sprite,
             pos_ouvinte: pygame.math.Vector2): 
        """
        Desenha um único frame completo do jogo.
        Substitui todo o bloco "13. Desenho" do main.py.

        Args:
            estado_jogo: O estado atual (ex: "MENU", "JOGANDO").
            game_globals: O dicionário de estado global do main.py.
            game_groups: O dicionário de grupos de sprites.
            online_data: Dicionário com os estados atuais de rede (players, npcs, projectiles).
            online_trackers: Dicionário com os estados da rede do frame anterior (last_frame).
            alvo_camera_final: O sprite que a câmera deve seguir.
            pos_ouvinte: A posição do "ouvinte" de áudio (câmera).
        """
        
        # --- Extrair dados necessários ---
        LARGURA_TELA = game_globals["LARGURA_TELA"]
        ALTURA_TELA = game_globals["ALTURA_TELA"]
        nave_player = game_globals["nave_player"]
        is_online = self.network_client.is_connected()
        
        online_players_copy = online_data["players"]
        online_npcs_copy = online_data["npcs"]
        online_projectiles_copy = online_data["projectiles"]
        
        online_projectile_ids_last_frame = online_trackers["proj_last_frame"]
        online_npcs_last_frame = online_trackers["npcs_last_frame"]
        online_players_last_frame = online_trackers["players_last_frame"]
        
        grupo_obstaculos = game_groups["grupo_obstaculos"]
        grupo_inimigos = game_groups["grupo_inimigos"]
        grupo_bots = game_groups["grupo_bots"]
        grupo_projeteis_player = game_groups["grupo_projeteis_player"]
        grupo_projeteis_bots = game_groups["grupo_projeteis_bots"]
        grupo_projeteis_inimigos = game_groups["grupo_projeteis_inimigos"]
        grupo_efeitos_visuais = game_groups["grupo_efeitos_visuais"]
        grupo_explosoes = game_groups["grupo_explosoes"]

        # --- Início do Bloco de Desenho ---
        
        if estado_jogo == "MENU":
            self.ui.desenhar_menu(self.tela, LARGURA_TELA, ALTURA_TELA)
            
        elif estado_jogo == "GET_NAME":
            self.ui.desenhar_tela_nome(self.tela, game_globals["nome_jogador_input"], game_globals["input_nome_ativo"], game_globals["dificuldade_selecionada"])
            
        elif estado_jogo == "GET_SERVER_INFO":
            self.ui.desenhar_tela_conexao(self.tela, game_globals["nome_jogador_input"], game_globals["ip_servidor_input"], game_globals["input_connect_ativo"])
        
        elif estado_jogo == "MULTIPLAYER_MODE_SELECT":
            pvp_disponivel = game_globals.get("pvp_disponivel", False) 
            self.ui.desenhar_tela_modo_multiplayer(self.tela, LARGURA_TELA, ALTURA_TELA, pvp_disponivel) 
        
        elif estado_jogo == "OFFLINE_MODE_SELECT":
            self.ui.desenhar_tela_modo_offline(self.tela, LARGURA_TELA, ALTURA_TELA)

        else: 
            # --- Desenho do Jogo (JOGANDO, PAUSE, LOJA, etc.) ---
            self.tela.fill(s.PRETO)
            
            # 1. Fundo Parallax
            # --- INÍCIO: MODIFICAÇÃO (Problema 1: Tamanho do Mapa) ---
            # Esta lógica garante que o mapa correto seja usado para renderizar as estrelas
            # (1500x1500 se for PVP, 8000x8000 se for PVE)
            map_w = pvp_s.MAP_WIDTH if estado_jogo.startswith("PVP_") else s.MAP_WIDTH
            map_h = pvp_s.MAP_HEIGHT if estado_jogo.startswith("PVP_") else s.MAP_HEIGHT
            # --- FIM: MODIFICAÇÃO ---

            pos_camera = alvo_camera_final.posicao
            for pos_base, raio, parallax_fator in self.lista_estrelas:
                pos_tela_x = (pos_base.x - (pos_camera.x * parallax_fator)) % map_w
                pos_tela_y = (pos_base.y - (pos_camera.y * parallax_fator)) % map_h
                pygame.draw.circle(self.tela, s.CORES_ESTRELAS[raio - 1], (int(pos_tela_x), int(pos_tela_y)), raio)

            # 2. Sprites Estáticos
            for obst in grupo_obstaculos: 
                self.tela.blit(obst.image, self.camera.apply(obst.rect))
            
            # 3. Entidades (Online vs Offline)
            if is_online:
                self._draw_online_entities(nave_player, online_players_copy, online_npcs_copy, online_projectiles_copy,
                                           online_players_last_frame, online_npcs_last_frame, online_projectile_ids_last_frame,
                                           grupo_explosoes, pos_ouvinte)
            else:
                if not estado_jogo.startswith("PVP_"):
                    self._draw_offline_entities(grupo_inimigos, grupo_bots, grupo_projeteis_player,
                                                grupo_projeteis_bots, grupo_projeteis_inimigos)
                else:
                    self._draw_offline_entities(pygame.sprite.Group(), grupo_bots, grupo_projeteis_player,
                                                grupo_projeteis_bots, pygame.sprite.Group())
            
            # 4. Desenho do Jogador (e seus auxiliares)
            if estado_jogo.startswith("PVP_"):
                 self._draw_player(nave_player, "JOGANDO", is_online, False) 
            else:
                 self._draw_player(nave_player, estado_jogo, is_online, game_globals["jogador_esta_vivo_espectador"])
            
            # 5. Efeitos Visuais (Explosões, Regeneração)
            for efeito in grupo_efeitos_visuais:
                if isinstance(efeito, NaveRegeneradora):
                    efeito.desenhar(self.tela, self.camera)
                else: 
                    efeito.draw(self.tela, self.camera) 

            # 6. UI (HUD, Minimapa, Ranking)
            # --- INÍCIO: MODIFICAÇÃO (Problema 1: Tamanho do Mapa) ---
            # Passa o tamanho correto do mapa (PVP ou PVE) para o minimapa
            map_w_ui = pvp_s.MAP_WIDTH if estado_jogo.startswith("PVP_") else s.MAP_WIDTH
            map_h_ui = pvp_s.MAP_HEIGHT if estado_jogo.startswith("PVP_") else s.MAP_HEIGHT
            # --- FIM: MODIFICAÇÃO ---
            self._draw_ui_elements(estado_jogo, nave_player, game_globals, online_players_copy,
                                   grupo_bots, alvo_camera_final, map_w_ui, map_h_ui)
                
            # 7. Overlays (Menus por cima do jogo)
            self._draw_overlays(estado_jogo, nave_player, game_globals, is_online, len(grupo_bots),
                                LARGURA_TELA, ALTURA_TELA)

        # --- Fim do Bloco de Desenho ---
        pygame.display.flip()

    
    def _draw_online_entities(self, nave_player, online_players_copy, online_npcs_copy, online_projectiles_copy,
                              online_players_last_frame, online_npcs_last_frame, online_projectile_ids_last_frame,
                              grupo_explosoes, pos_ouvinte: pygame.math.Vector2): 
        """ Desenha todas as entidades de rede (outros players, NPCs, projéteis). """
        
        current_projectile_ids = {proj['id'] for proj in online_projectiles_copy}
        new_projectiles = [proj for proj in online_projectiles_copy if proj['id'] not in online_projectile_ids_last_frame]
        
        for proj in new_projectiles:
            pos_som = pygame.math.Vector2(proj['x'], proj['y'])
            tipo_som = proj.get('tipo_proj', 'normal')
            som_a_tocar = None
            vol_base = 0.4

            if proj['tipo'] == 'npc':
                if tipo_som == 'congelante': som_a_tocar = s.SOM_TIRO_CONGELANTE; vol_base = s.VOLUME_BASE_TIRO_CONGELANTE
                elif tipo_som == 'teleguiado_lento': som_a_tocar = s.SOM_TIRO_INIMIGO_SIMPLES; vol_base = s.VOLUME_BASE_TIRO_INIMIGO
                else: som_a_tocar = s.SOM_TIRO_INIMIGO_SIMPLES; vol_base = s.VOLUME_BASE_TIRO_INIMIGO
            else: # player_pve ou player_pvp
                som_a_tocar = s.SOM_TIRO_PLAYER; vol_base = s.VOLUME_BASE_TIRO_PLAYER
            
            tocar_som_posicional(som_a_tocar, pos_som, pos_ouvinte, vol_base)

        
        current_npc_ids = set(online_npcs_copy.keys())
        ids_desaparecidos = set(online_npcs_last_frame.keys()) - current_npc_ids
        ids_mortos_pelo_hp = {npc_id for npc_id, state in online_npcs_copy.items() if state.get('hp', 0) <= 0}
        ids_npcs_mortos_neste_tick = ids_desaparecidos.union(ids_mortos_pelo_hp)

        if ids_npcs_mortos_neste_tick:
            if nave_player.alvo_selecionado and isinstance(nave_player.alvo_selecionado, str):
                if nave_player.alvo_selecionado in ids_npcs_mortos_neste_tick: 
                    nave_player.alvo_selecionado = None 
            
            for npc_id in ids_npcs_mortos_neste_tick:
                if npc_id in online_npcs_last_frame:
                    npc = online_npcs_last_frame[npc_id]
                    pos_npc = pygame.math.Vector2(npc['x'], npc['y'])
                    tamanho_padrao_explosao = npc['tamanho'] // 2 + 5
                    
                    if npc['tipo'] == 'bomba': tamanho_padrao_explosao = npc['tamanho'] + 75 
                    
                    explosao = Explosao(pos_npc, tamanho_padrao_explosao)
                    grupo_explosoes.add(explosao)
                    
                    if npc['tipo'] in ['mothership', 'boss_congelante']:
                        tocar_som_posicional(s.SOM_EXPLOSAO_BOSS, pos_npc, pos_ouvinte, s.VOLUME_BASE_EXPLOSAO_BOSS)
                    else:
                        tocar_som_posicional(s.SOM_EXPLOSAO_NPC, pos_npc, pos_ouvinte, s.VOLUME_BASE_EXPLOSAO_NPC)
        
        current_player_names = set(online_players_copy.keys())
        dead_player_states = [player for name, player in online_players_last_frame.items() if name not in current_player_names]
        
        for player in dead_player_states:
             pos_player = pygame.math.Vector2(player['x'], player['y'])
             explosao = Explosao(pos_player, 30 // 2 + 10) 
             grupo_explosoes.add(explosao)
             tocar_som_posicional(s.SOM_EXPLOSAO_NPC, pos_player, pos_ouvinte, s.VOLUME_BASE_EXPLOSAO_NPC)

        MEU_NOME_REDE = self.network_client.get_my_name()

        for nome, state in online_players_copy.items():
            if nome == MEU_NOME_REDE: continue
            if state.get('hp', 0) <= 0: continue
                
            imagem_base_outro = nave_player.imagem_original
            if "Bot_" in nome: 
                temp_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
                centro_x = 20; centro_y = 20;
                ponto_topo = (centro_x, centro_y - 15); ponto_base_esq = (centro_x - 15, centro_y + 15); ponto_base_dir = (centro_x + 15, centro_y + 15)
                pygame.draw.polygon(temp_surf, s.LARANJA_BOT, [ponto_topo, ponto_base_esq, ponto_base_dir])
                ponta_largura = 4; ponta_altura = 8;
                pygame.draw.rect(temp_surf, s.PONTA_NAVE, (ponto_topo[0] - ponta_largura / 2, ponto_topo[1] - ponta_altura, ponta_largura, ponta_altura))
                imagem_base_outro = temp_surf
                
            img_rotacionada = pygame.transform.rotate(imagem_base_outro, state['angulo'])
            pos_rect = img_rotacionada.get_rect(center=(state['x'], state['y']))
            
            if state.get('is_congelado', False): img_rotacionada.fill(s.AZUL_CONGELANTE, special_flags=pygame.BLEND_RGB_ADD)
            elif state.get('is_lento', False): img_rotacionada.fill(s.ROXO_TIRO_LENTO, special_flags=pygame.BLEND_RGB_MULT)
            
            self.tela.blit(img_rotacionada, self.camera.apply(pos_rect))
            
            if state.get('esta_regenerando', False):
                angulo_orbita_simples = (pygame.time.get_ticks() / 10) % 360
                rad = math.radians(angulo_orbita_simples); raio_orbita = 50
                pos_regen_x = state['x'] + math.cos(rad) * raio_orbita; pos_regen_y = state['y'] + math.sin(rad) * raio_orbita
                pos_tela_regen = self.camera.apply(pygame.Rect(pos_regen_x, pos_regen_y, 0, 0)).topleft
                pygame.draw.circle(self.tela, s.LILAS_REGEN, pos_tela_regen, 9, 2)
            
            num_aux_outro = state.get('nivel_aux', 0)
            if num_aux_outro > 0:
                for i in range(num_aux_outro):
                    if i < len(Nave.POSICOES_AUXILIARES): 
                        offset_pos = Nave.POSICOES_AUXILIARES[i]
                        offset_rotacionado = offset_pos.rotate(-state['angulo']) 
                        posicao_alvo_seguir = pygame.math.Vector2(state['x'], state['y']) + offset_rotacionado
                        rect_fantasma = pygame.Rect(0, 0, 15, 15); rect_fantasma.center = posicao_alvo_seguir
                        pos_tela = self.camera.apply(rect_fantasma).center
                        pygame.draw.circle(self.tela, s.VERDE_AUXILIAR, pos_tela, 8, 2)

            nome_surf = s.FONT_NOME_JOGADOR.render(nome, True, s.BRANCO)
            nome_rect = nome_surf.get_rect(midbottom=(state['x'], state['y'] - 33))
            self.tela.blit(nome_surf, self.camera.apply(nome_rect))
            
            player_hp = state.get('hp', 0)
            player_max_hp = state.get('max_hp', player_hp if player_hp > 0 else 5) 
            
            if player_hp < player_max_hp: 
                LARGURA_BARRA = 40; ALTURA_BARRA = 5; OFFSET_Y = 30 
                
                pos_x_mundo = state['x'] - LARGURA_BARRA / 2
                pos_y_mundo = state['y'] - OFFSET_Y 
                
                percentual = max(0, player_hp / player_max_hp)
                largura_vida_atual = LARGURA_BARRA * percentual
                
                rect_fundo_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, LARGURA_BARRA, ALTURA_BARRA)
                rect_vida_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, largura_vida_atual, ALTURA_BARRA)
                
                pygame.draw.rect(self.tela, s.VERMELHO_VIDA_FUNDO, self.camera.apply(rect_fundo_mundo))
                pygame.draw.rect(self.tela, s.VERDE_VIDA, self.camera.apply(rect_vida_mundo))
        
        for proj_dict in online_projectiles_copy: 
            x, y, tipo, tipo_proj = proj_dict['x'], proj_dict['y'], proj_dict['tipo'], proj_dict['tipo_proj']
            cor = s.VERMELHO_TIRO; raio = 5
            if tipo == 'npc':
                if tipo_proj == 'congelante': cor = s.AZUL_TIRO_CONGELANTE; raio = 6
                elif tipo_proj == 'teleguiado_lento': cor = s.ROXO_TIRO_LENTO; raio = 5
                else: cor = s.LARANJA_TIRO_INIMIGO; raio = 4
            elif tipo.startswith('player_'): cor = s.VERMELHO_TIRO; raio = 5 # PVE ou PVP
            rect_proj = pygame.Rect(x-raio, y-raio, raio*2, raio*2)
            rect_proj_tela = self.camera.apply(rect_proj)
            pygame.draw.circle(self.tela, cor, rect_proj_tela.center, max(1, int(raio * self.camera.zoom))) 
        
        for npc_id, state in online_npcs_copy.items():
            if state.get('hp', 0) <= 0: continue 
            tamanho = state.get('tamanho', 30); tipo = state.get('tipo')
            base_img = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
            cor = s.VERMELHO_PERSEGUIDOR 
            if tipo == 'boss_congelante':
                cor = s.AZUL_CONGELANTE; centro = tamanho // 2
                pygame.draw.circle(base_img, cor, (centro, centro), centro)
                pygame.draw.circle(base_img, s.BRANCO, (centro, centro), centro, 2) 
            elif tipo == 'minion_congelante':
                cor = s.AZUL_MINION_CONGELANTE; centro = tamanho // 2
                pygame.draw.circle(base_img, cor, (centro, centro), centro)
            elif tipo == 'mothership': cor = s.CIANO_MOTHERSHIP; base_img.fill(cor) 
            elif tipo == 'minion_mothership':
                cor = s.CIANO_MINION; centro = tamanho // 2
                ponto_topo = (centro, centro - tamanho / 2); ponto_base_esq = (centro - tamanho / 2, centro + tamanho / 2); ponto_base_dir = (centro + tamanho / 2, centro + tamanho / 2)
                pygame.draw.polygon(base_img, cor, [ponto_topo, ponto_base_esq, ponto_base_dir])
            elif tipo == 'bomba': cor = s.AMARELO_BOMBA; base_img.fill(cor)
            elif tipo == 'tiro_rapido': cor = s.AZUL_TIRO_RAPIDO; base_img.fill(cor)
            elif tipo == 'atordoador': cor = s.ROXO_ATORDOADOR; base_img.fill(cor)
            elif tipo == 'atirador_rapido': cor = s.ROXO_ATIRADOR_RAPIDO; base_img.fill(cor)
            elif tipo == 'rapido': cor = s.LARANJA_RAPIDO; base_img.fill(cor)
            else: base_img.fill(cor)
            img_rotacionada = pygame.transform.rotate(base_img, state['angulo'])
            pos_rect = img_rotacionada.get_rect(center=(state['x'], state['y']))
            self.tela.blit(img_rotacionada, self.camera.apply(pos_rect))
            
            npc_hp = state.get('hp', 0); npc_max_hp = state.get('max_hp', npc_hp if npc_hp > 0 else 3) 
            if npc_hp < npc_max_hp: 
                LARGURA_BARRA = tamanho; ALTURA_BARRA = 4; OFFSET_Y = (tamanho / 2) + 10
                pos_x_mundo = state['x'] - LARGURA_BARRA / 2; pos_y_mundo = state['y'] + OFFSET_Y 
                percentual = max(0, npc_hp / npc_max_hp); largura_vida_atual = LARGURA_BARRA * percentual
                rect_fundo_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, LARGURA_BARRA, ALTURA_BARRA)
                rect_vida_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, largura_vida_atual, ALTURA_BARRA)
                pygame.draw.rect(self.tela, s.VERMELHO_VIDA_FUNDO, self.camera.apply(rect_fundo_mundo))
                pygame.draw.rect(self.tela, s.VERDE_VIDA, self.camera.apply(rect_vida_mundo))
    
    def _draw_offline_entities(self, grupo_inimigos, grupo_bots, grupo_projeteis_player,
                               grupo_projeteis_bots, grupo_projeteis_inimigos):
        """ Desenha todas as entidades locais (sprites) para o modo offline. """
        for inimigo in grupo_inimigos: 
            inimigo.desenhar_vida(self.tela, self.camera)
            self.tela.blit(inimigo.image, self.camera.apply(inimigo.rect))
        for bot in grupo_bots:
            bot.desenhar(self.tela, self.camera)
            bot.desenhar_vida(self.tela, self.camera)
            bot.desenhar_nome(self.tela, self.camera)
            for aux in bot.grupo_auxiliares_ativos: aux.desenhar(self.tela, self.camera)
        
        for proj in grupo_projeteis_player: self.tela.blit(proj.image, self.camera.apply(proj.rect))
        for proj in grupo_projeteis_bots: self.tela.blit(proj.image, self.camera.apply(proj.rect))
        for proj in grupo_projeteis_inimigos: self.tela.blit(proj.image, self.camera.apply(proj.rect))

    def _draw_player(self, nave_player, estado_jogo, is_online, jogador_esta_vivo_espectador):
        """ Desenha o sprite do jogador principal, se aplicável. """
        jogador_visivel = False
        
        if estado_jogo in ["JOGANDO", "PAUSE", "LOJA", "TERMINAL", 
                           "PVP_LOBBY", "PVP_COUNTDOWN", "PVP_PLAYING", "PVP_PRE_MATCH"]: 
            if nave_player.vida_atual > 0:
                jogador_visivel = True
        
        elif estado_jogo == "ESPECTADOR" and jogador_esta_vivo_espectador:
            if is_online and nave_player.vida_atual > 0:
                jogador_visivel = True
        
        if jogador_visivel: 
            nave_player.desenhar(self.tela, self.camera, is_online) 
            nave_player.desenhar_vida(self.tela, self.camera)
            nave_player.desenhar_nome(self.tela, self.camera)
            
            for aux in nave_player.grupo_auxiliares_ativos: 
                aux.desenhar(self.tela, self.camera)

    def _draw_ui_elements(self, estado_jogo, nave_player, game_globals, online_players_copy,
                          grupo_bots, alvo_camera_final, map_width, map_height):
        """ Desenha os elementos de UI (HUD, Minimapa, Ranking). """
        
        if estado_jogo in ["JOGANDO", "LOJA", "TERMINAL", 
                           "PVP_LOBBY", "PVP_COUNTDOWN", "PVP_PLAYING", "PVP_PRE_MATCH"]:
             self.ui.desenhar_hud(self.tela, nave_player, estado_jogo)
        
        if estado_jogo in ["JOGANDO", "LOJA", "TERMINAL", "ESPECTADOR",
                           "PVP_LOBBY", "PVP_COUNTDOWN", "PVP_PLAYING", "PVP_GAME_OVER", "PVP_PRE_MATCH"]:
            MEU_NOME_REDE = self.network_client.get_my_name()
            
            self.ui.desenhar_minimapa(self.tela, nave_player, grupo_bots, estado_jogo, map_width, map_height, 
                                 online_players_copy, MEU_NOME_REDE, alvo_camera_final, self.camera.zoom,
                                 game_globals["jogador_esta_vivo_espectador"]) 
            
            top_5 = [] 
            if estado_jogo.startswith("PVP_"):
                if self.network_client.is_connected():
                    class RankingEntry: 
                        def __init__(self, nome, hp, max_hp): self.nome = nome; self.vida_atual = hp; self.max_vida = max_hp; self.pontos = 0
                    
                    lista_ranking_pvp = []
                    for nome, state in online_players_copy.items():
                        if state.get('hp', 0) > 0:
                            lista_ranking_pvp.append(RankingEntry(nome, state.get('hp', 0), state.get('max_hp', 5)))
                    
                    lista_ordenada = sorted(lista_ranking_pvp, key=lambda entry: entry.vida_atual, reverse=True)
                    top_5 = lista_ordenada[:pvp_s.MAX_JOGADORES_PVP] 
                else:
                    todos_os_jogadores = []
                    if nave_player.vida_atual > 0:
                        todos_os_jogadores.append(nave_player)
                    todos_os_jogadores.extend([bot for bot in grupo_bots.sprites() if bot.vida_atual > 0])
                    lista_ordenada = sorted(todos_os_jogadores, key=lambda n: n.vida_atual, reverse=True)
                    top_5 = lista_ordenada[:pvp_s.MAX_JOGADORES_PVP]
            elif self.network_client.is_connected():
                class RankingEntry: 
                    def __init__(self, nome, pontos): self.nome = nome; self.pontos = pontos
                lista_ranking = []
                for nome, state in online_players_copy.items():
                    if state.get('hp', 0) <= 0: continue
                    lista_ranking.append(RankingEntry(nome, state.get('pontos', 0)))
                lista_ordenada = sorted(lista_ranking, key=lambda entry: entry.pontos, reverse=True); top_5 = lista_ordenada[:5]
            else: 
                todos_os_jogadores = []
                if nave_player.vida_atual > 0 and not game_globals["jogador_esta_vivo_espectador"]:
                    todos_os_jogadores.append(nave_player)
                todos_os_jogadores.extend([bot for bot in grupo_bots.sprites() if bot.vida_atual > 0])
                lista_ordenada = sorted(todos_os_jogadores, key=lambda n: n.pontos, reverse=True); top_5 = lista_ordenada[:5]
            
            if estado_jogo.startswith("PVP_"):
                self.ui.desenhar_lista_vivos_pvp(self.tela, top_5) 
            elif estado_jogo in ["JOGANDO", "LOJA", "TERMINAL", "ESPECTADOR"]:
                self.ui.desenhar_ranking(self.tela, top_5, nave_player)


    def _draw_overlays(self, estado_jogo, nave_player, game_globals, is_online, num_bots_ativos,
                       LARGURA_TELA, ALTURA_TELA):
        """ Desenha os menus que ficam por cima do jogo (Pause, Loja, etc.). """
        is_pvp_map = (s.MAP_WIDTH < 5000)
        if estado_jogo == "PAUSE":
            estado_antes_de_pausar = game_globals.get("estado_anterior_pause", "JOGANDO")
            
            self.pause_manager.draw(self.tela, game_globals["max_bots_atual"], s.MAX_BOTS_LIMITE_SUPERIOR, num_bots_ativos,
                                    nave_player.vida_atual <= 0, game_globals["jogador_esta_vivo_espectador"], is_online,
                                    estado_antes_de_pausar) 
            
        elif estado_jogo == "LOJA":
            self.ui.desenhar_loja(self.tela, nave_player, LARGURA_TELA, ALTURA_TELA, is_online)
            
        elif estado_jogo == "TERMINAL":
            self.ui.desenhar_terminal(self.tela, game_globals["variavel_texto_terminal"], LARGURA_TELA, ALTURA_TELA)
            
        elif estado_jogo == "PVP_LOBBY":
            # --- INÍCIO: MODIFICAÇÃO (Problema 2: Mensagem de Lobby Online/Offline) ---
            num_players = 0
            if is_online:
                num_players = game_globals.get("pvp_lobby_num_players", 0)
            else:
                num_players = len(game_globals.get("grupo_bots")) + 1 # Bots + Player
            
            texto_lobby = pvp_s.FONT_TITULO_PVP.render(f"Aguardando Jogadores... ({num_players}/{pvp_s.MAX_JOGADORES_PVP})", True, pvp_s.BRANCO)
            pos_x = (LARGURA_TELA - texto_lobby.get_width()) // 2
            self.tela.blit(texto_lobby, (pos_x, 50))
            
            texto_instr = pvp_s.FONT_TITULO_PVP.render("Use 'V' para distribuir seus 10 pontos!", True, pvp_s.AMARELO)
            pos_x_instr = (LARGURA_TELA - texto_instr.get_width()) // 2
            self.tela.blit(texto_instr, (pos_x_instr, 100))
            # --- FIM: MODIFICAÇÃO ---

        elif estado_jogo == "PVP_COUNTDOWN":
            # --- INÍCIO: MODIFICAÇÃO (Problema 3: Contagem Online/Offline) ---
            tempo_s = 0
            if is_online:
                # Se online, usa o tempo vindo do servidor
                tempo_s = game_globals.get("pvp_lobby_countdown_sec", 0)
            else:
                # Se offline, calcula localmente
                tempo_restante_ms = game_globals.get("pvp_lobby_timer_fim", 0) - pygame.time.get_ticks()
                if tempo_restante_ms < 0: tempo_restante_ms = 0
                tempo_s = math.ceil(tempo_restante_ms / 1000)
            # --- FIM: MODIFICAÇÃO ---
            
            texto_timer = pvp_s.FONT_TITULO_PVP.render(f"Iniciando em {tempo_s}", True, pvp_s.AMARELO)
            pos_x = (LARGURA_TELA - texto_timer.get_width()) // 2
            self.tela.blit(texto_timer, (pos_x, 50))

        elif estado_jogo == "PVP_PRE_MATCH":
            tempo_restante_ms = 0
            tempo_s = 0
            texto_render = "PREPARAR!"
            
            if is_online:
                # O estado é controlado pelo 'my_state' no main.py.
                # O servidor ainda não envia o *timer* de pre-match, só o estado.
                # Então, apenas mostramos "PREPARAR!"
                texto_render = "PREPARAR!"
            else:
                # Offline, calculamos o timer
                tempo_restante_ms = game_globals.get("pvp_pre_match_timer_fim", 0) - pygame.time.get_ticks()
                if tempo_restante_ms < 0: tempo_restante_ms = 0
                tempo_s = math.ceil(tempo_restante_ms / 1000) 
                texto_render = f"{tempo_s}"
            
            texto_timer = pvp_s.FONT_TITULO_PVP.render(texto_render, True, pvp_s.VERMELHO)
            pos_x = (LARGURA_TELA - texto_timer.get_width()) // 2
            pos_y = (ALTURA_TELA - texto_timer.get_height()) // 2
            self.tela.blit(texto_timer, (pos_x, pos_y))

        elif estado_jogo == "PVP_PLAYING" or (estado_jogo == "ESPECTADOR" and is_pvp_map):
            tempo_restante_ms = 0
            # --- INÍCIO: MODIFICAÇÃO (Timer Partida Online/Offline) ---
            if is_online:
                # (O servidor ainda não envia este timer, então ficará 00:00)
                # (Isso precisará ser adicionado ao STATE ou a uma nova msg)
                tempo_restante_ms = game_globals.get("pvp_match_countdown_sec", 0) * 1000 
            else:
                tempo_restante_ms = game_globals.get("pvp_partida_timer_fim", 0) - pygame.time.get_ticks()
            # --- FIM: MODIFICAÇÃO ---
                
            if tempo_restante_ms < 0: tempo_restante_ms = 0
            minutos = int(tempo_restante_ms / 60000)
            segundos = int((tempo_restante_ms % 60000) / 1000)
            cor_timer = pvp_s.BRANCO if tempo_restante_ms > 10000 else pvp_s.VERMELHO
            
            texto_timer = pvp_s.FONT_TIMER_PVP.render(f"{minutos:02d}:{segundos:02d}", True, cor_timer)
            pos_x = (LARGURA_TELA - texto_timer.get_width()) // 2
            self.tela.blit(texto_timer, (pos_x, 20))

        elif estado_jogo == "PVP_GAME_OVER":
            fundo_overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
            fundo_overlay.fill(s.PRETO_TRANSPARENTE_PAUSA)
            self.tela.blit(fundo_overlay, (0, 0))
            
            vencedor = game_globals.get("pvp_vencedor_nome", "Ninguém")
            texto_fim = pvp_s.FONT_TITULO_PVP.render("Fim de Jogo!", True, pvp_s.VERMELHO)
            pos_x_fim = (LARGURA_TELA - texto_fim.get_width()) // 2
            self.tela.blit(texto_fim, (pos_x_fim, ALTURA_TELA // 3))
            
            texto_venc = pvp_s.FONT_VENCEDOR_PVP.render(f"Vencedor: {vencedor}", True, pvp_s.VERDE)
            pos_x_venc = (LARGURA_TELA - texto_venc.get_width()) // 2
            self.tela.blit(texto_venc, (pos_x_venc, ALTURA_TELA // 2))
            
            texto_instr = s.FONT_PADRAO.render("Pressione ESC para voltar ao Menu", True, pvp_s.BRANCO)
            pos_x_instr = (LARGURA_TELA - texto_instr.get_width()) // 2
            self.tela.blit(texto_instr, (pos_x_instr, ALTURA_TELA * 0.7))
            
        elif estado_jogo == "ESPECTADOR":
            
            is_pve_map = s.MAP_WIDTH > 5000 
            is_dead_spectator = (nave_player.vida_atual <= 0 and not game_globals["jogador_esta_vivo_espectador"])
            
            if is_pve_map and is_dead_spectator and not game_globals.get("spectator_overlay_hidden", False):
                 self.ui.desenhar_game_over(self.tela, LARGURA_TELA, ALTURA_TELA)
                 
            texto_titulo_spec = s.FONT_TITULO.render("MODO ESPECTADOR", True, s.BRANCO)
            pos_x_spec = 10; pos_y_spec = 10
            self.tela.blit(texto_titulo_spec, (pos_x_spec, pos_y_spec)); pos_y_spec += texto_titulo_spec.get_height() + 5
            
            nome_alvo_hud = game_globals["alvo_espectador_nome"] or (game_globals["alvo_espectador"].nome if game_globals["alvo_espectador"] else None)
            
            if self.camera.zoom < 1.0: texto_alvo = s.FONT_HUD.render("Visão do Mapa (Z)", True, s.AMARELO_BOMBA)
            elif nome_alvo_hud: texto_alvo = s.FONT_HUD.render(f"Seguindo: {nome_alvo_hud}", True, s.VERDE_VIDA)
            else: texto_alvo = s.FONT_HUD.render("Câmera Livre (WASD)", True, s.AZUL_NAVE)
            self.tela.blit(texto_alvo, (pos_x_spec, pos_y_spec)); pos_y_spec += texto_alvo.get_height() + 2
            
            texto_ajuda1 = s.FONT_HUD_DETALHES.render("Q/E: Ciclar Alvos | Z: Visão Mapa", True, s.BRANCO)
            self.tela.blit(texto_ajuda1, (pos_x_spec, pos_y_spec)); pos_y_spec += texto_ajuda1.get_height() + 2
            texto_ajuda2 = s.FONT_HUD_DETALHES.render("LMB: Seguir Alvo | RMB: Câmera Livre", True, s.BRANCO)
            self.tela.blit(texto_ajuda2, (pos_x_spec, pos_y_spec)); pos_y_spec += texto_ajuda2.get_height() + 2
            texto_ajuda3 = s.FONT_HUD_DETALHES.render("ESC: Menu de Pausa", True, s.BRANCO)
            self.tela.blit(texto_ajuda3, (pos_x_spec, pos_y_spec))