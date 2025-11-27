# game_logic.py
import pygame
import random
import settings as s
import multi.pvp_settings as pvp_s 
from ships import (Player, NaveBot, NaveAuxiliar, Nave, 
                   tocar_som_posicional) 
from projectiles import ProjetilCongelante, ProjetilTeleguiadoLento
from enemies import (InimigoMothership, BossCongelante, InimigoMinion, 
                     MinionCongelante, InimigoBomba)
from settings import (VOLUME_BASE_EXPLOSAO_BOSS, VOLUME_BASE_EXPLOSAO_NPC, 
                      VIDA_POR_NIVEL)

class GameLogic:
    def __init__(self, main_callbacks: dict):
        self.cb_spawnar_bot = main_callbacks["spawnar_bot"]
        self.cb_spawnar_obstaculo = main_callbacks["spawnar_obstaculo"]
        self.cb_spawnar_inimigo_aleatorio = main_callbacks["spawnar_inimigo_aleatorio"]
        self.cb_spawnar_mothership = main_callbacks["spawnar_mothership"]
        self.cb_spawnar_boss_congelante = main_callbacks["spawnar_boss_congelante"]

    def update_offline_logic(self, game_state: dict, game_groups: dict, pos_ouvinte: pygame.math.Vector2):
        if s.MAP_WIDTH < 5000: 
            return game_state["estado_jogo"]
        
        estado_jogo = game_state["estado_jogo"]
        if estado_jogo.startswith("PVP_"):
            return estado_jogo
        
        nave_player = game_state["nave_player"]
        dificuldade_jogo_atual = game_state["dificuldade_jogo_atual"]
        max_bots_atual = game_state["max_bots_atual"]
        
        grupo_bots = game_groups["grupo_bots"]
        grupo_inimigos = game_groups["grupo_inimigos"]
        grupo_efeitos_visuais = game_groups["grupo_efeitos_visuais"]
        grupo_projeteis_bots = game_groups["grupo_projeteis_bots"]
        grupo_projeteis_inimigos = game_groups["grupo_projeteis_inimigos"]
        grupo_projeteis_player = game_groups["grupo_projeteis_player"]
        grupo_obstaculos = game_groups["grupo_obstaculos"]
        grupo_motherships = game_groups["grupo_motherships"]
        grupo_boss_congelante = game_groups["grupo_boss_congelante"]

        lista_alvos_naves = game_state["lista_alvos_naves"]

        # --- INÍCIO DA CORREÇÃO ---
        # Cria uma lista com TODOS os projéteis que podem machucar os bots
        lista_projeteis_hostis = list(grupo_projeteis_player) + list(grupo_projeteis_inimigos)
        
        # Passa essa lista para o update dos bots
        grupo_bots.update(
            player_ref=nave_player, 
            grupo_projeteis_bots=grupo_projeteis_bots, 
            grupo_bots_ref=grupo_bots, 
            grupo_inimigos_ref=grupo_inimigos, 
            grupo_obstaculos_ref=grupo_obstaculos, 
            grupo_efeitos_visuais_ref=grupo_efeitos_visuais, 
            pos_ouvinte=pos_ouvinte, 
            map_width=s.MAP_WIDTH, 
            map_height=s.MAP_HEIGHT,
            lista_projeteis_hostis=lista_projeteis_hostis # <--- NOVO ARGUMENTO
        )
        # --- FIM DA CORREÇÃO ---

        grupo_inimigos.update(lista_alvos_naves, grupo_projeteis_inimigos, s.DESPAWN_DIST, pos_ouvinte)
        
        grupo_projeteis_player.update()
        grupo_projeteis_bots.update()
        grupo_projeteis_inimigos.update()

        # --- 2. Lógica de Spawn ---
        lista_spawn_anchors = lista_alvos_naves
        if lista_spawn_anchors:
            ponto_referencia_sprite = random.choice(lista_spawn_anchors)
            ponto_referencia = ponto_referencia_sprite.posicao
            
            if len(grupo_bots) < max_bots_atual:
                self.cb_spawnar_bot(ponto_referencia, dificuldade_jogo_atual)

            if len(grupo_obstaculos) < s.MAX_OBSTACULOS:
                self.cb_spawnar_obstaculo(ponto_referencia)
            
            contagem_inimigos_normais = sum(1 for inimigo in grupo_inimigos if not isinstance(inimigo, (InimigoMinion, InimigoMothership, MinionCongelante, BossCongelante)))
            
            if contagem_inimigos_normais < s.MAX_INIMIGOS:
                self.cb_spawnar_inimigo_aleatorio(ponto_referencia)
            
            if len(grupo_motherships) < s.MAX_MOTHERSHIPS:
                self.cb_spawnar_mothership(ponto_referencia)
            
            if len(grupo_boss_congelante) < s.MAX_BOSS_CONGELANTE:
                self.cb_spawnar_boss_congelante(ponto_referencia)

        # --- 3. Lógica de Colisão ---
        self._handle_bot_projectile_collisions(nave_player, grupo_projeteis_bots, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo, pos_ouvinte)
        self._handle_enemy_projectile_collisions_vs_bots(grupo_bots, grupo_projeteis_inimigos, estado_jogo)
        self._handle_ramming_collisions_bots_vs_enemies(grupo_bots, grupo_inimigos, estado_jogo, nave_player, pos_ouvinte)
        
        if (estado_jogo == "JOGANDO" or estado_jogo == "LOJA" or estado_jogo == "TERMINAL"):
            self._handle_player_projectile_collisions(nave_player, grupo_projeteis_player, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo, pos_ouvinte)
            self._handle_enemy_projectile_collisions_vs_player(nave_player, grupo_projeteis_inimigos, estado_jogo)
            self._handle_ramming_collisions_player_vs_enemies(nave_player, grupo_inimigos, estado_jogo, pos_ouvinte)
            self._handle_ramming_collisions_player_vs_bots(nave_player, grupo_bots, estado_jogo)

            if nave_player.vida_atual <= 0 and estado_jogo == "JOGANDO": 
                print("[LOGIC] Morte do jogador detectada por colisões.")
                if hasattr(nave_player, 'ultimo_atacante') and nave_player.ultimo_atacante:
                    if hasattr(nave_player.ultimo_atacante, 'ganhar_pontos'):
                        pontos_ganhos = int(nave_player.pontos * 0.75)
                        nave_player.ultimo_atacante.ganhar_pontos(pontos_ganhos)
                
                estado_jogo = "ESPECTADOR"
                game_state["estado_jogo"] = "ESPECTADOR"
                game_state["jogador_esta_vivo_espectador"] = False
                game_state["alvo_espectador"] = None
                game_state["alvo_espectador_nome"] = None
                game_state["spectator_overlay_hidden"] = False
                espectador_dummy_alvo = game_state.get("espectador_dummy_alvo")
                if espectador_dummy_alvo:
                    espectador_dummy_alvo.posicao = nave_player.posicao.copy()
            
        return estado_jogo

    def update_pvp_logic(self, game_state: dict, game_groups: dict, pos_ouvinte: pygame.math.Vector2):
        estado_jogo = game_state["estado_jogo"]
        nave_player = game_state["nave_player"]
        agora = pygame.time.get_ticks()
        map_width = s.MAP_WIDTH
        map_height = s.MAP_HEIGHT

        grupo_bots = game_groups["grupo_bots"]
        grupo_player = game_groups["grupo_player"]
        grupo_projeteis_player = game_groups["grupo_projeteis_player"]
        grupo_projeteis_bots = game_groups["grupo_projeteis_bots"]
        grupo_obstaculos = game_groups["grupo_obstaculos"]
        grupo_efeitos_visuais = game_groups["grupo_efeitos_visuais"]

        grupo_pvp_jogadores = pygame.sprite.Group(grupo_player, grupo_bots)
        is_pvp_map_check = (s.MAP_WIDTH < 5000) 
        
        if estado_jogo == "PVP_PLAYING" or (estado_jogo == "ESPECTADOR" and is_pvp_map_check):
            jogadores_vivos = [p for p in grupo_pvp_jogadores if p.vida_atual > 0]
            if len(jogadores_vivos) <= 1:
                estado_jogo = "PVP_GAME_OVER"
                game_state["estado_jogo"] = "PVP_GAME_OVER"
                if len(jogadores_vivos) == 1: game_state["pvp_vencedor_nome"] = jogadores_vivos[0].nome
                else: game_state["pvp_vencedor_nome"] = "Empate" 
            elif agora > game_state.get("pvp_partida_timer_fim", 0):
                estado_jogo = "PVP_GAME_OVER"
                game_state["estado_jogo"] = "PVP_GAME_OVER"
                jogadores_vivos.sort(key=lambda p: p.vida_atual, reverse=True)
                if jogadores_vivos: game_state["pvp_vencedor_nome"] = jogadores_vivos[0].nome
                else: game_state["pvp_vencedor_nome"] = "Empate"

        if estado_jogo == "PVP_LOBBY":
            if len(grupo_pvp_jogadores) >= pvp_s.MAX_JOGADORES_PVP:
                estado_jogo = "PVP_COUNTDOWN"; game_state["estado_jogo"] = "PVP_COUNTDOWN"
                game_state["pvp_lobby_timer_fim"] = agora + (pvp_s.PVP_LOBBY_COUNTDOWN_SEGUNDOS * 1000)

        elif estado_jogo == "PVP_COUNTDOWN":
            if agora > game_state["pvp_lobby_timer_fim"]:
                estado_jogo = "PVP_PRE_MATCH"; game_state["estado_jogo"] = "PVP_PRE_MATCH"
                game_state["pvp_pre_match_timer_fim"] = agora + (5 * 1000) 
                jogadores_para_spawnar = [p for p in grupo_pvp_jogadores if p.vida_atual > 0]
                for i, nave in enumerate(jogadores_para_spawnar):
                    if i < len(pvp_s.SPAWN_POSICOES):
                        pos_canto = pvp_s.SPAWN_POSICOES[i]
                        nave.posicao = pos_canto.copy(); nave.rect.center = nave.posicao
                        nave.vida_atual = nave.max_vida; nave.parar_regeneracao()
                        nave.alvo_selecionado = None; nave.posicao_alvo_mouse = None
                    else: nave.kill()
        
        elif estado_jogo == "PVP_PRE_MATCH":
            if agora > game_state["pvp_pre_match_timer_fim"]:
                estado_jogo = "PVP_PLAYING"; game_state["estado_jogo"] = "PVP_PLAYING"
                game_state["pvp_partida_timer_fim"] = agora + (pvp_s.PVP_PARTIDA_DURACAO_SEGUNDOS * 1000)
        
        if estado_jogo != "PVP_GAME_OVER":
            if estado_jogo == "PVP_PLAYING" or (estado_jogo == "ESPECTADOR" and is_pvp_map_check):
                
                # --- INÍCIO DA CORREÇÃO PVP ---
                # Lista de todos os projéteis no PVP (Player + Bots)
                lista_projeteis_hostis_pvp = list(grupo_projeteis_player) + list(grupo_projeteis_bots)
                
                for bot in grupo_bots:
                    if bot.vida_atual > 0:
                        bot.update(
                            player_ref=nave_player, 
                            grupo_projeteis_bots=grupo_projeteis_bots,
                            grupo_bots_ref=grupo_pvp_jogadores,
                            grupo_inimigos_ref=grupo_pvp_jogadores,
                            grupo_obstaculos_ref=grupo_obstaculos,
                            grupo_efeitos_visuais_ref=grupo_efeitos_visuais,
                            pos_ouvinte=pos_ouvinte,
                            map_width=map_width,
                            map_height=map_height,
                            lista_projeteis_hostis=lista_projeteis_hostis_pvp # <--- NOVO ARGUMENTO PVP
                        )
                # --- FIM DA CORREÇÃO PVP ---
                        
                colisoes_player_vs_bot = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_bots, True, False)
                for proj, bots_atingidos in colisoes_player_vs_bot.items():
                    for bot in bots_atingidos: bot.foi_atingido(proj.dano, estado_jogo, proj.posicao, atacante=nave_player)

                pygame.sprite.groupcollide(grupo_projeteis_player, grupo_obstaculos, True, True)

                colisoes_bot_vs_player = pygame.sprite.spritecollide(nave_player, grupo_projeteis_bots, True)
                for proj in colisoes_bot_vs_player:
                    if nave_player.vida_atual > 0: nave_player.foi_atingido(proj.dano, estado_jogo, proj.posicao, atacante=proj.owner)
                
                colisoes_bot_vs_bot = pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_bots, True, False)
                for proj, bots_atingidos in colisoes_bot_vs_bot.items():
                    owner = proj.owner
                    for bot in bots_atingidos:
                        if bot != owner: bot.foi_atingido(proj.dano, estado_jogo, proj.posicao, atacante=owner)

                pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_obstaculos, True, True)

                colisoes_ramming = pygame.sprite.groupcollide(grupo_pvp_jogadores, grupo_pvp_jogadores, False, False)
                for nave_a, naves_colididas in colisoes_ramming.items():
                    for nave_b in naves_colididas:
                        if nave_a != nave_b and nave_a.vida_atual > 0 and nave_b.vida_atual > 0: 
                            nave_a.foi_atingido(0.1, estado_jogo, nave_b.posicao, atacante=nave_b)
            
            if nave_player.vida_atual <= 0 and game_state["estado_jogo"] == "PVP_PLAYING":
                estado_jogo = "ESPECTADOR"; game_state["estado_jogo"] = "ESPECTADOR"
                game_state["jogador_esta_vivo_espectador"] = False
                game_state["alvo_espectador"] = None; game_state["alvo_espectador_nome"] = None
                game_state["spectator_overlay_hidden"] = False
                espectador_dummy_alvo = game_state.get("espectador_dummy_alvo")
                if espectador_dummy_alvo: espectador_dummy_alvo.posicao = nave_player.posicao.copy()

            grupo_projeteis_player.update()
            grupo_projeteis_bots.update()

        return estado_jogo

    def _tocar_som_explosao(self, inimigo, pos_ouvinte):
        if isinstance(inimigo, (InimigoMothership, BossCongelante)):
            if isinstance(inimigo, InimigoMothership): inimigo.grupo_minions.empty()
            if isinstance(inimigo, BossCongelante): inimigo.grupo_minions_congelantes.empty()
            if tocar_som_posicional and s.SOM_EXPLOSAO_BOSS: tocar_som_posicional(s.SOM_EXPLOSAO_BOSS, inimigo.posicao, pos_ouvinte, VOLUME_BASE_EXPLOSAO_BOSS)
        else:
            if tocar_som_posicional and s.SOM_EXPLOSAO_NPC: tocar_som_posicional(s.SOM_EXPLOSAO_NPC, inimigo.posicao, pos_ouvinte, VOLUME_BASE_EXPLOSAO_NPC)

    def _handle_player_projectile_collisions(self, nave_player, grupo_projeteis_player, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo, pos_ouvinte): 
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_obstaculos, True, True)
        for _, obst_list in colisoes.items():
            for obst in obst_list: nave_player.ganhar_pontos(obst.pontos_por_morte)
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_inimigos, True, False)
        for proj, inim_list in colisoes.items():
            for inimigo in inim_list:
                morreu = inimigo.foi_atingido(proj.dano)
                if morreu:
                    nave_player.ganhar_pontos(inimigo.pontos_por_morte); self._tocar_som_explosao(inimigo, pos_ouvinte)
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_bots, True, False)
        for proj, bot_list in colisoes.items():
            for bot in bot_list:
                pontos_da_vitima = bot.pontos 
                morreu = bot.foi_atingido(proj.dano, estado_jogo, proj.posicao, atacante=nave_player)
                if morreu:
                    pontos_ganhos = int(pontos_da_vitima * 0.75) 
                    nave_player.ganhar_pontos(pontos_ganhos)
                    
    def _handle_enemy_projectile_collisions_vs_player(self, nave_player, grupo_projeteis_inimigos, estado_jogo):
        colisoes_proj_inimigo_player = pygame.sprite.spritecollide(nave_player, grupo_projeteis_inimigos, False)
        for proj in colisoes_proj_inimigo_player:
            atacante = getattr(proj, 'owner', None) 
            if isinstance(proj, ProjetilCongelante): nave_player.aplicar_congelamento(s.DURACAO_CONGELAMENTO) 
            elif isinstance(proj, ProjetilTeleguiadoLento): nave_player.aplicar_lentidao(6000)
            else: nave_player.foi_atingido(1, estado_jogo, proj.posicao, atacante=atacante)
            proj.kill()

    def _handle_ramming_collisions_player_vs_enemies(self, nave_player, grupo_inimigos, estado_jogo, pos_ouvinte): 
        colisoes_ram_inimigo_player = pygame.sprite.spritecollide(nave_player, grupo_inimigos, False)
        for inimigo in colisoes_ram_inimigo_player:
            dano = 1 if not isinstance(inimigo, InimigoBomba) else inimigo.DANO_EXPLOSAO
            nave_player.foi_atingido(dano, estado_jogo, inimigo.posicao, atacante=inimigo) 
            morreu = inimigo.foi_atingido(1)
            if morreu: nave_player.ganhar_pontos(inimigo.pontos_por_morte); self._tocar_som_explosao(inimigo, pos_ouvinte) 

    def _handle_ramming_collisions_player_vs_bots(self, nave_player, grupo_bots, estado_jogo):
        colisoes_ram_bot_player = pygame.sprite.spritecollide(nave_player, grupo_bots, False)
        for bot in colisoes_ram_bot_player:
            pontos_do_bot = bot.pontos 
            morreu_player = nave_player.foi_atingido(1, estado_jogo, bot.posicao, atacante=bot)
            morreu_bot = bot.foi_atingido(1, estado_jogo, nave_player.posicao, atacante=nave_player)
            if morreu_bot:
                pontos_ganhos = int(pontos_do_bot * 0.75) 
                nave_player.ganhar_pontos(pontos_ganhos)

    def _handle_bot_projectile_collisions(self, nave_player, grupo_projeteis_bots, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo, pos_ouvinte): 
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_obstaculos, True, True)
        for proj, obst_list in colisoes.items():
            owner_do_tiro = proj.owner
            if owner_do_tiro:
                for obst in obst_list: owner_do_tiro.ganhar_pontos(obst.pontos_por_morte)
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_inimigos, True, False)
        for proj, inim_list in colisoes.items():
            owner_do_tiro = proj.owner
            if owner_do_tiro:
                for inimigo in inim_list:
                    morreu = inimigo.foi_atingido(proj.dano)
                    if morreu: owner_do_tiro.ganhar_pontos(inimigo.pontos_por_morte); self._tocar_som_explosao(inimigo, pos_ouvinte) 
        colisoes_bot_vs_bot = pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_bots, True, False)
        for proj, bots_atingidos in colisoes_bot_vs_bot.items():
            owner_do_tiro = proj.owner
            if not owner_do_tiro: continue
            for bot_atingido in bots_atingidos:
                if bot_atingido != owner_do_tiro:
                    pontos_da_vitima = bot_atingido.pontos 
                    dano_do_tiro = proj.dano
                    morreu = bot_atingido.foi_atingido(dano_do_tiro, estado_jogo, proj.posicao, atacante=owner_do_tiro)
                    if morreu:
                        if isinstance(owner_do_tiro, Nave):
                            pontos_ganhos = int(pontos_da_vitima * 0.75) 
                            owner_do_tiro.ganhar_pontos(pontos_ganhos)
        
        if estado_jogo == "JOGANDO" or estado_jogo == "LOJA" or estado_jogo == "TERMINAL":
            colisoes_proj_bot_player = pygame.sprite.spritecollide(nave_player, grupo_projeteis_bots, True)
            for proj in colisoes_proj_bot_player:
                if proj.owner != nave_player: nave_player.foi_atingido(proj.dano, estado_jogo, proj.posicao, atacante=proj.owner)
                    
    def _handle_enemy_projectile_collisions_vs_bots(self, grupo_bots, grupo_projeteis_inimigos, estado_jogo):
        colisoes = pygame.sprite.groupcollide(grupo_bots, grupo_projeteis_inimigos, False, False)
        for bot, proj_list in colisoes.items():
            for proj in proj_list:
                atacante = getattr(proj, 'owner', None)
                if isinstance(proj, ProjetilCongelante): bot.aplicar_congelamento(s.DURACAO_CONGELAMENTO)
                elif isinstance(proj, ProjetilTeleguiadoLento): bot.aplicar_lentidao(6000)
                else: bot.foi_atingido(1, estado_jogo, proj.posicao, atacante=atacante)
                proj.kill()
                
    def _handle_ramming_collisions_bots_vs_enemies(self, grupo_bots, grupo_inimigos, estado_jogo, nave_player, pos_ouvinte): 
        for bot in grupo_bots:
            inimigos_colididos = pygame.sprite.spritecollide(bot, grupo_inimigos, False)
            for inimigo in inimigos_colididos:
                dano = 1 if not isinstance(inimigo, InimigoBomba) else inimigo.DANO_EXPLOSAO
                bot.foi_atingido(dano, estado_jogo, inimigo.posicao, atacante=inimigo)
                morreu = inimigo.foi_atingido(1)
                if morreu: 
                    bot.ganhar_pontos(inimigo.pontos_por_morte); self._tocar_som_explosao(inimigo, pos_ouvinte)