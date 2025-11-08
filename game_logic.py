# game_logic.py
import pygame
import random
import settings as s
from ships import (Player, NaveBot, NaveAuxiliar, Nave, 
                   tocar_som_posicional) 
from projectiles import ProjetilCongelante, ProjetilTeleguiadoLento
from enemies import (InimigoMothership, BossCongelante, InimigoMinion, 
                     MinionCongelante, InimigoBomba)
from settings import (VOLUME_BASE_EXPLOSAO_BOSS, VOLUME_BASE_EXPLOSAO_NPC, 
                      VIDA_POR_NIVEL)

class GameLogic:
    def __init__(self, main_callbacks: dict):
        """
        Inicializa o gerenciador de lógica de jogo offline.

        Args:
            main_callbacks: Dicionário de funções do main.py (spawners).
        """
        self.cb_spawnar_bot = main_callbacks["spawnar_bot"]
        self.cb_spawnar_obstaculo = main_callbacks["spawnar_obstaculo"]
        self.cb_spawnar_inimigo_aleatorio = main_callbacks["spawnar_inimigo_aleatorio"]
        self.cb_spawnar_mothership = main_callbacks["spawnar_mothership"]
        self.cb_spawnar_boss_congelante = main_callbacks["spawnar_boss_congelante"]

    def update_offline_logic(self, game_state: dict, game_groups: dict):
        """
        Processa toda a lógica de jogo offline (spawns, updates, colisões).
        Substitui o bloco 'if not is_online:' no main.py.

        Args:
            game_state: Dicionário com o estado atual do jogo.
            game_groups: Dicionário com todos os grupos de sprites.
        
        Returns:
            String: O novo estado_jogo (ex: "ESPECTADOR" se o jogador morrer).
        """
        
        # Extrai variáveis de estado
        estado_jogo = game_state["estado_jogo"]
        nave_player = game_state["nave_player"]
        dificuldade_jogo_atual = game_state["dificuldade_jogo_atual"]
        max_bots_atual = game_state["max_bots_atual"]
        
        # Extrai grupos de sprites
        grupo_bots = game_groups["grupo_bots"]
        grupo_inimigos = game_groups["grupo_inimigos"]
        grupo_efeitos_visuais = game_groups["grupo_efeitos_visuais"]
        grupo_projeteis_bots = game_groups["grupo_projeteis_bots"]
        grupo_projeteis_inimigos = game_groups["grupo_projeteis_inimigos"]
        grupo_projeteis_player = game_groups["grupo_projeteis_player"]
        grupo_obstaculos = game_groups["grupo_obstaculos"]
        grupo_motherships = game_groups["grupo_motherships"]
        grupo_boss_congelante = game_groups["grupo_boss_congelante"]

        # --- 1. Atualização de Grupos ---
        lista_alvos_naves = game_state["lista_alvos_naves"] # Pega a lista já filtrada

        grupo_bots.update(nave_player, grupo_projeteis_bots, grupo_bots, grupo_inimigos, grupo_obstaculos, grupo_efeitos_visuais)
        grupo_inimigos.update(lista_alvos_naves, grupo_projeteis_inimigos, s.DESPAWN_DIST)
        
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
        
        # Colisões de Projéteis de Jogador/Bots
        self._handle_player_projectile_collisions(nave_player, grupo_projeteis_player, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo)
        self._handle_bot_projectile_collisions(nave_player, grupo_projeteis_bots, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo)
        
        # Colisões de Projéteis Inimigos
        self._handle_enemy_projectile_collisions(nave_player, grupo_bots, grupo_projeteis_inimigos, estado_jogo)
        
        # Colisões de Ramming (Corpo a Corpo)
        self._handle_ramming_collisions(nave_player, grupo_bots, grupo_inimigos, estado_jogo)

        # --- 4. Checagem de Morte do Jogador (após todas as colisões) ---
        if (estado_jogo == "JOGANDO" or estado_jogo == "LOJA" or estado_jogo == "TERMINAL"):
            if nave_player.vida_atual <= 0:
                print("[LOGIC] Morte do jogador detectada por colisões.")
                # Retorna o novo estado
                return "ESPECTADOR" 
        
        return estado_jogo # Retorna o estado atual se não houver mudança

    
    def _tocar_som_explosao(self, inimigo, pos_ouvinte):
        """Helper para tocar som de explosão."""
        if isinstance(inimigo, (InimigoMothership, BossCongelante)):
            if isinstance(inimigo, InimigoMothership): inimigo.grupo_minions.empty()
            if isinstance(inimigo, BossCongelante): inimigo.grupo_minions_congelantes.empty()
            if tocar_som_posicional and s.SOM_EXPLOSAO_BOSS:
                tocar_som_posicional(s.SOM_EXPLOSAO_BOSS, inimigo.posicao, pos_ouvinte, VOLUME_BASE_EXPLOSAO_BOSS)
        else:
            if tocar_som_posicional and s.SOM_EXPLOSAO_NPC:
                tocar_som_posicional(s.SOM_EXPLOSAO_NPC, inimigo.posicao, pos_ouvinte, VOLUME_BASE_EXPLOSAO_NPC)

    def _handle_player_projectile_collisions(self, nave_player, grupo_projeteis_player, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo):
        """ Processa colisões dos projéteis do jogador. """
        
        # Só processa se o jogador estiver jogando
        if estado_jogo != "JOGANDO":
            return

        # Player Proj vs Obstáculos
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_obstaculos, True, True)
        for _, obst_list in colisoes.items():
            for obst in obst_list:
                nave_player.ganhar_pontos(obst.pontos_por_morte)
        
        # Player Proj vs Inimigos
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_inimigos, True, False)
        for proj, inim_list in colisoes.items():
            for inimigo in inim_list:
                morreu = inimigo.foi_atingido(proj.dano)
                if morreu:
                    nave_player.ganhar_pontos(inimigo.pontos_por_morte)
                    self._tocar_som_explosao(inimigo, nave_player.posicao)
        
        # Player Proj vs Bots (PVP Amigável)
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_bots, True, False)
        for proj, bot_list in colisoes.items():
            for bot in bot_list:
                morreu = bot.foi_atingido(proj.dano, estado_jogo, proj.posicao)
                if morreu:
                    nave_player.ganhar_pontos(10) # Pontos por matar bot

    def _handle_bot_projectile_collisions(self, nave_player, grupo_projeteis_bots, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo):
        """ Processa colisões dos projéteis dos bots. """

        # Bot Proj vs Obstáculos
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_obstaculos, True, True)
        for proj, obst_list in colisoes.items():
            owner_do_tiro = proj.owner
            if owner_do_tiro:
                for obst in obst_list:
                    owner_do_tiro.ganhar_pontos(obst.pontos_por_morte)

        # Bot Proj vs Inimigos
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_inimigos, True, False)
        for proj, inim_list in colisoes.items():
            owner_do_tiro = proj.owner
            if owner_do_tiro:
                for inimigo in inim_list:
                    morreu = inimigo.foi_atingido(proj.dano)
                    if morreu:
                        owner_do_tiro.ganhar_pontos(inimigo.pontos_por_morte)
                        self._tocar_som_explosao(inimigo, nave_player.posicao)

        # Bot Proj vs Bots (PVP Amigável)
        colisoes_bot_vs_bot = pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_bots, True, False)
        for proj, bots_atingidos in colisoes_bot_vs_bot.items():
            owner_do_tiro = proj.owner
            if not owner_do_tiro:
                continue
            for bot_atingido in bots_atingidos:
                if bot_atingido != owner_do_tiro:
                    dano_do_tiro = proj.dano
                    morreu = bot_atingido.foi_atingido(dano_do_tiro, estado_jogo, proj.posicao)
                    if morreu:
                        if isinstance(owner_do_tiro, Nave):
                            owner_do_tiro.ganhar_pontos(10)
                            print(f"[{owner_do_tiro.nome}] destruiu [{bot_atingido.nome}]!")
        
        # Bot Proj vs Player
        colisoes_proj_bot_player = pygame.sprite.spritecollide(nave_player, grupo_projeteis_bots, True)
        for proj in colisoes_proj_bot_player:
            if proj.owner != nave_player: 
                nave_player.foi_atingido(proj.dano, estado_jogo, proj.posicao)
                # (A checagem de morte do player acontece no final)

    def _handle_enemy_projectile_collisions(self, nave_player, grupo_bots, grupo_projeteis_inimigos, estado_jogo):
        """ Processa colisões dos projéteis inimigos contra aliados. """
        
        # Inimigo Proj vs Bots
        colisoes = pygame.sprite.groupcollide(grupo_bots, grupo_projeteis_inimigos, False, False)
        for bot, proj_list in colisoes.items():
            for proj in proj_list:
                if isinstance(proj, ProjetilCongelante):
                    bot.aplicar_congelamento(s.DURACAO_CONGELAMENTO)
                elif isinstance(proj, ProjetilTeleguiadoLento):
                    bot.aplicar_lentidao(6000)
                else: 
                    bot.foi_atingido(1, estado_jogo, proj.posicao)
                proj.kill()
                
        # Inimigo Proj vs Player
        colisoes_proj_inimigo_player = pygame.sprite.spritecollide(nave_player, grupo_projeteis_inimigos, False)
        for proj in colisoes_proj_inimigo_player:
            if isinstance(proj, ProjetilCongelante):
                nave_player.aplicar_congelamento(s.DURACAO_CONGELAMENTO) 
            elif isinstance(proj, ProjetilTeleguiadoLento):
                nave_player.aplicar_lentidao(6000)
            else:
                nave_player.foi_atingido(1, estado_jogo, proj.posicao)
            proj.kill()
            # (A checagem de morte do player acontece no final)

    def _handle_ramming_collisions(self, nave_player, grupo_bots, grupo_inimigos, estado_jogo):
        """ Processa colisões de corpo a corpo (ramming). """
        
        # Bots vs Inimigos
        for bot in grupo_bots:
            inimigos_colididos = pygame.sprite.spritecollide(bot, grupo_inimigos, False)
            for inimigo in inimigos_colididos:
                dano = 1 if not isinstance(inimigo, InimigoBomba) else inimigo.DANO_EXPLOSAO
                bot.foi_atingido(dano, estado_jogo, inimigo.posicao)
                morreu = inimigo.foi_atingido(1)
                if morreu: 
                    bot.ganhar_pontos(inimigo.pontos_por_morte)
                    self._tocar_som_explosao(inimigo, nave_player.posicao)
        
        # Player vs Inimigos
        colisoes_ram_inimigo_player = pygame.sprite.spritecollide(nave_player, grupo_inimigos, False)
        for inimigo in colisoes_ram_inimigo_player:
            dano = 1 if not isinstance(inimigo, InimigoBomba) else inimigo.DANO_EXPLOSAO
            nave_player.foi_atingido(dano, estado_jogo, inimigo.posicao)
                
            morreu = inimigo.foi_atingido(1)
            if morreu:
                nave_player.ganhar_pontos(inimigo.pontos_por_morte)
                self._tocar_som_explosao(inimigo, nave_player.posicao)
            # (A checagem de morte do player acontece no final)
        
        # Player vs Bots
        colisoes_ram_bot_player = pygame.sprite.spritecollide(nave_player, grupo_bots, False)
        for bot in colisoes_ram_bot_player:
            nave_player.foi_atingido(1, estado_jogo, bot.posicao)
            bot.foi_atingido(1, estado_jogo, nave_player.posicao)
            # (A checagem de morte do player acontece no final)