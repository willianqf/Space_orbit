# renderer.py
import pygame
import math
import settings as s
import ui
from camera import Camera
from pause_menu import PauseMenu
from Redes.network_client import NetworkClient
# --- INÍCIO: MODIFICAÇÃO (Importação corrigida) ---
from ships import Player, NaveBot, NaveAuxiliar, Nave, NaveRegeneradora, tocar_som_posicional
# --- FIM: MODIFICAÇÃO ---
from effects import Explosao
from entities import Obstaculo
from multi import pvp_settings as pvp_s

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
        
        # O módulo 'ui' é importado diretamente, pois contém funções estáticas
        self.ui = ui 

    def draw(self, estado_jogo: str, game_globals: dict, game_groups: dict, 
             online_data: dict, online_trackers: dict, alvo_camera_final: pygame.sprite.Sprite,
             pos_ouvinte: pygame.math.Vector2): # <-- MODIFICADO
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
        
        # --- Extrair Grupos ---
        grupo_obstaculos = game_groups["grupo_obstaculos"]
        grupo_inimigos = game_groups["grupo_inimigos"]
        grupo_bots = game_groups["grupo_bots"]
        grupo_projeteis_player = game_groups["grupo_projeteis_player"]
        grupo_projeteis_bots = game_groups["grupo_projeteis_bots"]
        grupo_projeteis_inimigos = game_groups["grupo_projeteis_inimigos"]
        grupo_efeitos_visuais = game_groups["grupo_efeitos_visuais"]
        grupo_explosoes = game_groups["grupo_explosoes"]

        # --- Início do Bloco de Desenho (Movido do main.py) ---
        
        if estado_jogo == "MENU":
            self.ui.desenhar_menu(self.tela, LARGURA_TELA, ALTURA_TELA)
            
        elif estado_jogo == "GET_NAME":
            self.ui.desenhar_tela_nome(self.tela, game_globals["nome_jogador_input"], game_globals["input_nome_ativo"], game_globals["dificuldade_selecionada"])
            
        elif estado_jogo == "GET_SERVER_INFO":
            self.ui.desenhar_tela_conexao(self.tela, game_globals["nome_jogador_input"], game_globals["ip_servidor_input"], game_globals["input_connect_ativo"])
        
        # --- INÍCIO: MODIFICAÇÃO (Adiciona o novo estado) ---
        elif estado_jogo == "MULTIPLAYER_MODE_SELECT":
            self.ui.desenhar_tela_modo_multiplayer(self.tela, LARGURA_TELA, ALTURA_TELA)
        # --- FIM: MODIFICAÇÃO ---

        else: 
            # --- Desenho do Jogo (JOGANDO, PAUSE, LOJA, etc.) ---
            self.tela.fill(s.PRETO)
            
            # 1. Fundo Parallax
            pos_camera = alvo_camera_final.posicao
            for pos_base, raio, parallax_fator in self.lista_estrelas:
                pos_tela_x = (pos_base.x - (pos_camera.x * parallax_fator)) % LARGURA_TELA
                pos_tela_y = (pos_base.y - (pos_camera.y * parallax_fator)) % ALTURA_TELA
                pygame.draw.circle(self.tela, s.CORES_ESTRELAS[raio - 1], (int(pos_tela_x), int(pos_tela_y)), raio)

            # 2. Sprites Estáticos
            for obst in grupo_obstaculos: 
                self.tela.blit(obst.image, self.camera.apply(obst.rect))
            
            # 3. Entidades (Online vs Offline)
            if is_online:
                # 3a. Desenho Online
                # --- MODIFICADO: Passa pos_ouvinte ---
                self._draw_online_entities(nave_player, online_players_copy, online_npcs_copy, online_projectiles_copy,
                                           online_players_last_frame, online_npcs_last_frame, online_projectile_ids_last_frame,
                                           grupo_explosoes, pos_ouvinte)
            else:
                # 3b. Desenho Offline
                self._draw_offline_entities(grupo_inimigos, grupo_bots, grupo_projeteis_player,
                                            grupo_projeteis_bots, grupo_projeteis_inimigos)
            
            # 4. Desenho do Jogador (e seus auxiliares)
            self._draw_player(nave_player, estado_jogo, is_online, game_globals["jogador_esta_vivo_espectador"])
            
            # 5. Efeitos Visuais (Explosões, Regeneração)
            for efeito in grupo_efeitos_visuais:
                if isinstance(efeito, NaveRegeneradora):
                    efeito.desenhar(self.tela, self.camera)
                else: 
                    efeito.draw(self.tela, self.camera) # Explosões

            # 6. UI (HUD, Minimapa, Ranking)
            self._draw_ui_elements(estado_jogo, nave_player, game_globals, online_players_copy,
                                   grupo_bots, alvo_camera_final)
                
            # 7. Overlays (Menus por cima do jogo)
            self._draw_overlays(estado_jogo, nave_player, game_globals, is_online, len(grupo_bots),
                                LARGURA_TELA, ALTURA_TELA)

        # --- Fim do Bloco de Desenho ---

        # 14. Atualiza a Tela (Movido do main.py)
        pygame.display.flip()

    
    def _draw_online_entities(self, nave_player, online_players_copy, online_npcs_copy, online_projectiles_copy,
                              online_players_last_frame, online_npcs_last_frame, online_projectile_ids_last_frame,
                              grupo_explosoes, pos_ouvinte: pygame.math.Vector2): # <-- MODIFICADO
        """ Desenha todas as entidades de rede (outros players, NPCs, projéteis). """
        
        # --- Lógica de Som/Efeitos de Morte (amarrada ao desenho) ---
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
            else: 
                som_a_tocar = s.SOM_TIRO_PLAYER; vol_base = s.VOLUME_BASE_TIRO_PLAYER
            
            # --- MODIFICADO: Usa pos_ouvinte ---
            tocar_som_posicional(som_a_tocar, pos_som, pos_ouvinte, vol_base)

        
        current_npc_ids = set(online_npcs_copy.keys())
        ids_desaparecidos = set(online_npcs_last_frame.keys()) - current_npc_ids
        ids_mortos_pelo_hp = {npc_id for npc_id, state in online_npcs_copy.items() if state.get('hp', 0) <= 0}
        ids_npcs_mortos_neste_tick = ids_desaparecidos.union(ids_mortos_pelo_hp)

        if ids_npcs_mortos_neste_tick:
            if nave_player.alvo_selecionado and isinstance(nave_player.alvo_selecionado, str):
                if nave_player.alvo_selecionado in ids_npcs_mortos_neste_tick: 
                    nave_player.alvo_selecionado = None # Limpa a mira local
            
            for npc_id in ids_npcs_mortos_neste_tick:
                if npc_id in online_npcs_last_frame:
                    npc = online_npcs_last_frame[npc_id]
                    pos_npc = pygame.math.Vector2(npc['x'], npc['y'])
                    tamanho_padrao_explosao = npc['tamanho'] // 2 + 5
                    
                    if npc['tipo'] == 'bomba': tamanho_padrao_explosao = npc['tamanho'] + 75 
                    
                    explosao = Explosao(pos_npc, tamanho_padrao_explosao)
                    grupo_explosoes.add(explosao)
                    
                    if npc['tipo'] in ['mothership', 'boss_congelante']:
                        # --- MODIFICADO: Usa pos_ouvinte ---
                        tocar_som_posicional(s.SOM_EXPLOSAO_BOSS, pos_npc, pos_ouvinte, s.VOLUME_BASE_EXPLOSAO_BOSS)
                    else:
                        # --- MODIFICADO: Usa pos_ouvinte ---
                        tocar_som_posicional(s.SOM_EXPLOSAO_NPC, pos_npc, pos_ouvinte, s.VOLUME_BASE_EXPLOSAO_NPC)
        
        current_player_names = set(online_players_copy.keys())
        dead_player_states = [player for name, player in online_players_last_frame.items() if name not in current_player_names]
        
        for player in dead_player_states:
             pos_player = pygame.math.Vector2(player['x'], player['y'])
             explosao = Explosao(pos_player, 30 // 2 + 10) 
             grupo_explosoes.add(explosao)
             # --- MODIFICADO: Usa pos_ouvinte ---
             tocar_som_posicional(s.SOM_EXPLOSAO_NPC, pos_player, pos_ouvinte, s.VOLUME_BASE_EXPLOSAO_NPC)

        # --- Desenho das Entidades de Rede ---
        MEU_NOME_REDE = self.network_client.get_my_name()

        # 1. Desenhar outros jogadores (e bots)
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
            
            # --- INÍCIO DA CORREÇÃO (BUG ONLINE: Desenhar Vida do Jogador) ---
            player_hp = state.get('hp', 0)
            player_max_hp = state.get('max_hp', player_hp if player_hp > 0 else 5) # Usa 5 como padrão se max_hp for 0
            
            # (Usando a mesma lógica do offline: mostrar se a vida não estiver cheia)
            # (Não podemos usar 'ultimo_hit_tempo' pois não é enviado pela rede)
            if player_hp < player_max_hp: 
                LARGURA_BARRA = 40; ALTURA_BARRA = 5; OFFSET_Y = 30 # (Valores de 'ships.py')
                
                # (Posicionamento da barra de vida do 'ships.py')
                pos_x_mundo = state['x'] - LARGURA_BARRA / 2
                pos_y_mundo = state['y'] - OFFSET_Y 
                
                percentual = max(0, player_hp / player_max_hp)
                largura_vida_atual = LARGURA_BARRA * percentual
                
                rect_fundo_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, LARGURA_BARRA, ALTURA_BARRA)
                rect_vida_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, largura_vida_atual, ALTURA_BARRA)
                
                pygame.draw.rect(self.tela, s.VERMELHO_VIDA_FUNDO, self.camera.apply(rect_fundo_mundo))
                pygame.draw.rect(self.tela, s.VERDE_VIDA, self.camera.apply(rect_vida_mundo))
            # --- FIM DA CORREÇÃO ---
        
        # 2. Desenhar projéteis de rede
        for proj_dict in online_projectiles_copy: 
            x, y, tipo, tipo_proj = proj_dict['x'], proj_dict['y'], proj_dict['tipo'], proj_dict['tipo_proj']
            cor = s.VERMELHO_TIRO; raio = 5
            if tipo == 'npc':
                if tipo_proj == 'congelante': cor = s.AZUL_TIRO_CONGELANTE; raio = 6
                elif tipo_proj == 'teleguiado_lento': cor = s.ROXO_TIRO_LENTO; raio = 5
                else: cor = s.LARANJA_TIRO_INIMIGO; raio = 4
            elif tipo == 'player': cor = s.VERMELHO_TIRO; raio = 5
            rect_proj = pygame.Rect(x-raio, y-raio, raio*2, raio*2)
            rect_proj_tela = self.camera.apply(rect_proj)
            pygame.draw.circle(self.tela, cor, rect_proj_tela.center, max(1, int(raio * self.camera.zoom))) 
        
        # 3. Desenhar NPCs de rede
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
        
        # --- MODIFICAÇÃO PVP: Trata estados PVP como "JOGANDO" ---
        if estado_jogo in ["JOGANDO", "PAUSE", "LOJA", "TERMINAL", "PVP_LOBBY", "PVP_COUNTDOWN", "PVP_PLAYING"]:
            if nave_player.vida_atual > 0:
                jogador_visivel = True
        # --- FIM MODIFICAÇÃO PVP ---
        
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
                          grupo_bots, alvo_camera_final):
        """ Desenha os elementos de UI (HUD, Minimapa, Ranking). """
        
        # --- MODIFICAÇÃO PVP: Determina se está em modo PVP ---
        em_modo_pvp = estado_jogo in ["PVP_LOBBY", "PVP_COUNTDOWN", "PVP_PLAYING", "PVP_GAME_OVER"]
        # --- FIM MODIFICAÇÃO PVP ---
        
        # HUD
        if estado_jogo in ["JOGANDO", "LOJA", "TERMINAL", "PVP_LOBBY", "PVP_COUNTDOWN", "PVP_PLAYING"]:
             self.ui.desenhar_hud(self.tela, nave_player, estado_jogo)
        
        # Minimapa e Ranking
        if estado_jogo in ["JOGANDO", "LOJA", "TERMINAL", "ESPECTADOR", "PVP_LOBBY", "PVP_COUNTDOWN", "PVP_PLAYING"]:
            MEU_NOME_REDE = self.network_client.get_my_name()
            
            # --- MODIFICAÇÃO PVP: Usa dimensões corretas do mapa ---
            map_width = s.MAP_WIDTH
            map_height = s.MAP_HEIGHT
            # --- FIM MODIFICAÇÃO PVP ---
            
            self.ui.desenhar_minimapa(self.tela, nave_player, grupo_bots, estado_jogo, map_width, map_height, 
                                 online_players_copy, MEU_NOME_REDE, alvo_camera_final, self.camera.zoom,
                                 game_globals["jogador_esta_vivo_espectador"]) 
            
            # --- MODIFICAÇÃO PVP: Lógica do Ranking ---
            if em_modo_pvp:
                # No PVP, ranking é baseado em VIDA, não pontos
                todos_os_jogadores = []
                if nave_player.vida_atual > 0:
                    todos_os_jogadores.append(nave_player)
                todos_os_jogadores.extend([bot for bot in grupo_bots.sprites() if bot.vida_atual > 0])
                
                # Ordena por vida (maior vida primeiro)
                lista_ordenada = sorted(todos_os_jogadores, key=lambda n: n.vida_atual, reverse=True)
                top_5 = lista_ordenada[:5]
                
                # Desenha ranking PVP (mostra vida ao invés de pontos)
                self.ui.desenhar_ranking_pvp(self.tela, top_5, nave_player)
            else:
                # Ranking PVE (baseado em pontos)
                if self.network_client.is_connected():
                    class RankingEntry: # Helper class
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
                
                self.ui.desenhar_ranking(self.tela, top_5, nave_player)
            # --- FIM MODIFICAÇÃO PVP ---

    def _draw_overlays(self, estado_jogo, nave_player, game_globals, is_online, num_bots_ativos,
                       LARGURA_TELA, ALTURA_TELA):
        """ Desenha os menus que ficam por cima do jogo (Pause, Loja, etc.). """
        
        if estado_jogo == "PAUSE":
            self.pause_manager.draw(self.tela, game_globals["max_bots_atual"], s.MAX_BOTS_LIMITE_SUPERIOR, num_bots_ativos,
                                    nave_player.vida_atual <= 0, game_globals["jogador_esta_vivo_espectador"], is_online)
            
        elif estado_jogo == "LOJA":
            self.ui.desenhar_loja(self.tela, nave_player, LARGURA_TELA, ALTURA_TELA, is_online)
            
        elif estado_jogo == "TERMINAL":
            self.ui.desenhar_terminal(self.tela, game_globals["variavel_texto_terminal"], LARGURA_TELA, ALTURA_TELA)
            
        elif estado_jogo == "ESPECTADOR":
            
            # --- INÍCIO DA CORREÇÃO (BUG 2) ---
            # O jogador está morto E NÃO está vivo-espectador?
            is_dead_spectator = (nave_player.vida_atual <= 0 and not game_globals["jogador_esta_vivo_espectador"])
            
            # 1. Botão de Respawn (se morto E flag NÃO está ativa)
            # Só desenha o overlay "Você Morreu" se o jogador estiver morto
            # E a flag 'spectator_overlay_hidden' for Falsa.
            if is_dead_spectator and not game_globals.get("spectator_overlay_hidden", False):
                 self.ui.desenhar_game_over(self.tela, LARGURA_TELA, ALTURA_TELA)
            # --- FIM DA CORREÇÃO ---
                 
            # 2. HUD de Espectador (Sempre desenha)
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
        
        # --- INÍCIO: MODIFICAÇÃO (Overlays PVP) ---
        elif estado_jogo == "PVP_LOBBY":
            # Overlay de Lobby
            overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
            overlay.fill(pvp_s.PVP_COR_OVERLAY)
            self.tela.blit(overlay, (0, 0))
            
            # Título
            texto_titulo = pvp_s.PVP_FONT_TITULO.render(pvp_s.PVP_MSG_AGUARDANDO, True, pvp_s.PVP_COR_TEXTO_DESTAQUE)
            rect_titulo = texto_titulo.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 3))
            self.tela.blit(texto_titulo, rect_titulo)
            
            # Instruções
            texto_instrucoes = pvp_s.PVP_FONT_INSTRUCOES.render(pvp_s.PVP_MSG_INSTRUCOES_LOBBY, True, pvp_s.PVP_COR_TEXTO_PRINCIPAL)
            rect_instrucoes = texto_instrucoes.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2))
            self.tela.blit(texto_instrucoes, rect_instrucoes)
        
        elif estado_jogo == "PVP_COUNTDOWN":
            # Overlay de Countdown
            overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
            overlay.fill(pvp_s.PVP_COR_OVERLAY)
            self.tela.blit(overlay, (0, 0))
            
            # Calcula tempo restante
            countdown_inicio = game_globals.get("pvp_countdown_inicio", pygame.time.get_ticks())
            tempo_decorrido = pygame.time.get_ticks() - countdown_inicio
            segundos_restantes = max(0, (pvp_s.PVP_TEMPO_LOBBY - tempo_decorrido) // 1000)
            
            # Mensagem
            texto_msg = pvp_s.PVP_FONT_SUBTITULO.render(pvp_s.PVP_MSG_CONTAGEM, True, pvp_s.PVP_COR_TEXTO_PRINCIPAL)
            rect_msg = texto_msg.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 3))
            self.tela.blit(texto_msg, rect_msg)
            
            # Timer
            texto_timer = pvp_s.PVP_FONT_TIMER.render(str(segundos_restantes), True, pvp_s.PVP_COR_CONTAGEM)
            rect_timer = texto_timer.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2))
            self.tela.blit(texto_timer, rect_timer)
        
        elif estado_jogo == "PVP_PLAYING":
            # Timer da partida (no topo da tela)
            tempo_fim = game_globals.get("pvp_partida_timer_fim", 0)
            agora = pygame.time.get_ticks()
            tempo_restante_ms = max(0, tempo_fim - agora)
            minutos = tempo_restante_ms // 60000
            segundos = (tempo_restante_ms % 60000) // 1000
            
            texto_timer = pvp_s.PVP_FONT_TIMER.render(f"{minutos}:{segundos:02d}", True, pvp_s.PVP_COR_TEXTO_DESTAQUE)
            rect_timer = texto_timer.get_rect(center=(LARGURA_TELA // 2, 30))
            
            # Fundo semi-transparente para o timer
            padding = 10
            fundo_rect = pygame.Rect(rect_timer.left - padding, rect_timer.top - padding,
                                     rect_timer.width + 2*padding, rect_timer.height + 2*padding)
            pygame.draw.rect(self.tela, (0, 0, 0, 180), fundo_rect)
            
            self.tela.blit(texto_timer, rect_timer)
        
        elif estado_jogo == "PVP_GAME_OVER":
            # Overlay de Game Over
            overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
            overlay.fill(pvp_s.PVP_COR_OVERLAY)
            self.tela.blit(overlay, (0, 0))
            
            vencedor_nome = game_globals.get("pvp_vencedor_nome", None)
            
            if vencedor_nome:
                # Há um vencedor
                texto_vencedor = pvp_s.PVP_FONT_TITULO.render(pvp_s.PVP_MSG_VENCEDOR, True, pvp_s.PVP_COR_TEXTO_PRINCIPAL)
                rect_vencedor = texto_vencedor.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 3))
                self.tela.blit(texto_vencedor, rect_vencedor)
                
                texto_nome = pvp_s.PVP_FONT_SUBTITULO.render(vencedor_nome, True, pvp_s.PVP_COR_VENCEDOR)
                rect_nome = texto_nome.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2))
                self.tela.blit(texto_nome, rect_nome)
            else:
                # Empate
                texto_empate = pvp_s.PVP_FONT_TITULO.render(pvp_s.PVP_MSG_EMPATE, True, pvp_s.PVP_COR_TEXTO_DESTAQUE)
                rect_empate = texto_empate.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2))
                self.tela.blit(texto_empate, rect_empate)
            
            # Instruções
            texto_instrucoes = pvp_s.PVP_FONT_INSTRUCOES.render(pvp_s.PVP_MSG_INSTRUCOES_FIM, True, pvp_s.PVP_COR_TEXTO_PRINCIPAL)
            rect_instrucoes = texto_instrucoes.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA * 2 // 3))
            self.tela.blit(texto_instrucoes, rect_instrucoes)
        # --- FIM: MODIFICAÇÃO (Overlays PVP) ---