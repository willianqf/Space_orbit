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
from multi import pvp_settings as pvp_s

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

    def update_offline_logic(self, game_state: dict, game_groups: dict, pos_ouvinte: pygame.math.Vector2): # <-- MODIFICADO
        """
        Processa toda a lógica de jogo offline (spawns, updates, colisões).
        (CORRIGIDO: Colisões de Bots agora rodam fora do estado "JOGANDO")
        """
        
        # Extrai variáveis de estado
        estado_jogo = game_state["estado_jogo"]
        
        # --- MODIFICAÇÃO PVP: Retorna imediatamente se em estado PVP ---
        if estado_jogo in ["PVP_LOBBY", "PVP_COUNTDOWN", "PVP_PLAYING", "PVP_GAME_OVER"]:
            return None
        # --- FIM MODIFICAÇÃO PVP ---
        
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

        # --- MODIFICADO: Passa pos_ouvinte ---
        grupo_bots.update(nave_player, grupo_projeteis_bots, grupo_bots, grupo_inimigos, grupo_obstaculos, grupo_efeitos_visuais, pos_ouvinte)
        grupo_inimigos.update(lista_alvos_naves, grupo_projeteis_inimigos, s.DESPAWN_DIST, pos_ouvinte)
        
        grupo_projeteis_player.update()
        grupo_projeteis_bots.update()
        grupo_projeteis_inimigos.update()

        # --- 2. Lógica de Spawn ---
        # ... (lógica de spawn inalterada) ...
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
        # --- Fim da lógica de Spawn ---


        # --- 3. Lógica de Colisão ---
        
        # --- Bloco 3A: Colisões que SEMPRE OCORREM (Bots/Inimigos) ---
        # (Mesmo se o jogador estiver espectando)

        # Colisões de Projéteis de Bots (vs Obstáculos, Inimigos, e outros Bots)
        # --- MODIFICADO: Passa pos_ouvinte ---
        self._handle_bot_projectile_collisions(nave_player, grupo_projeteis_bots, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo, pos_ouvinte)
        
        # Colisões de Projéteis Inimigos (vs Bots)
        self._handle_enemy_projectile_collisions_vs_bots(grupo_bots, grupo_projeteis_inimigos, estado_jogo)
        
        # Colisões de Ramming (Bots vs Inimigos)
        # --- MODIFICADO: Passa pos_ouvinte ---
        self._handle_ramming_collisions_bots_vs_enemies(grupo_bots, grupo_inimigos, estado_jogo, nave_player, pos_ouvinte)
        
        # --- Bloco 3B: Colisões que SÓ AFETAM O JOGADOR ---
        if (estado_jogo == "JOGANDO" or estado_jogo == "LOJA" or estado_jogo == "TERMINAL"):
        
            # Colisões de Projéteis de Jogador (vs Obstáculos, Inimigos, Bots)
            # --- MODIFICADO: Passa pos_ouvinte ---
            self._handle_player_projectile_collisions(nave_player, grupo_projeteis_player, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo, pos_ouvinte)
            
            # Colisões de Projéteis Inimigos (vs Jogador)
            self._handle_enemy_projectile_collisions_vs_player(nave_player, grupo_projeteis_inimigos, estado_jogo)
            
            # Colisões de Ramming (Jogador vs Inimigos)
            # --- MODIFICADO: Passa pos_ouvinte ---
            self._handle_ramming_collisions_player_vs_enemies(nave_player, grupo_inimigos, estado_jogo, pos_ouvinte)
            
            # Colisões de Ramming (Jogador vs Bots)
            self._handle_ramming_collisions_player_vs_bots(nave_player, grupo_bots, estado_jogo)

            # --- 4. Checagem de Morte do Jogador (após todas as colisões) ---
            if nave_player.vida_atual <= 0:
                print("[LOGIC] Morte do jogador detectada por colisões.")
                
                # --- INÍCIO DA MODIFICAÇÃO (Recompensa por Abate) ---
                # Verifica se o jogador tem um 'ultimo_atacante' registrado
                if hasattr(nave_player, 'ultimo_atacante') and nave_player.ultimo_atacante:
                    # Verifica se o atacante ainda pode ganhar pontos (é uma Nave)
                    if hasattr(nave_player.ultimo_atacante, 'ganhar_pontos'):
                        pontos_ganhos = int(nave_player.pontos * 0.75)
                        nave_player.ultimo_atacante.ganhar_pontos(pontos_ganhos)
                        print(f"[{nave_player.ultimo_atacante.nome}] ganhou {pontos_ganhos} pontos por abater [{nave_player.nome}]")
                    # Limpa o atacante para evitar recompensas múltiplas
                    nave_player.ultimo_atacante = None 
                # --- FIM DA MODIFICAÇÃO ---

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

    # --- FUNÇÕES DE COLISÃO DO JOGADOR (SÓ RODAM QUANDO VIVO) ---

    def _handle_player_projectile_collisions(self, nave_player, grupo_projeteis_player, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo, pos_ouvinte): # <-- MODIFICADO
        """ Processa colisões dos projéteis do jogador. """
        
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
                    self._tocar_som_explosao(inimigo, pos_ouvinte) # <-- MODIFICADO
        
        # Player Proj vs Bots (PVP Amigável)
        colisoes = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_bots, True, False)
        for proj, bot_list in colisoes.items():
            for bot in bot_list:
                
                # --- INÍCIO DA CORREÇÃO ---
                pontos_da_vitima = bot.pontos # 1. Salva os pontos ANTES de atingir.
                # --- FIM DA CORREÇÃO ---
                
                morreu = bot.foi_atingido(proj.dano, estado_jogo, proj.posicao, atacante=nave_player)
                
                if morreu:
                    # --- INÍCIO DA CORREÇÃO ---
                    pontos_ganhos = int(pontos_da_vitima * 0.75) # 2. Usa os pontos salvos.
                    nave_player.ganhar_pontos(pontos_ganhos)
                    print(f"[{nave_player.nome}] ganhou {pontos_ganhos} pontos por abater [{bot.nome}]")
                    # --- FIM DA CORREÇÃO ---
                    
    def _handle_enemy_projectile_collisions_vs_player(self, nave_player, grupo_projeteis_inimigos, estado_jogo):
        """ Processa colisões dos projéteis inimigos contra O JOGADOR. """
        colisoes_proj_inimigo_player = pygame.sprite.spritecollide(nave_player, grupo_projeteis_inimigos, False)
        for proj in colisoes_proj_inimigo_player:
            # --- INÍCIO DA MODIFICAÇÃO (Recompensa por Abate) ---
            # Define o atacante como o 'dono' do projétil (se existir)
            atacante = getattr(proj, 'owner', None) 
            # --- FIM DA MODIFICAÇÃO ---

            if isinstance(proj, ProjetilCongelante):
                nave_player.aplicar_congelamento(s.DURACAO_CONGELAMENTO) 
            elif isinstance(proj, ProjetilTeleguiadoLento):
                nave_player.aplicar_lentidao(6000)
            else:
                # --- MODIFICADO: Passa 'atacante' ---
                nave_player.foi_atingido(1, estado_jogo, proj.posicao, atacante=atacante)
            proj.kill()
            # (A checagem de morte do player acontece no final do update_offline_logic)

    def _handle_ramming_collisions_player_vs_enemies(self, nave_player, grupo_inimigos, estado_jogo, pos_ouvinte): # <-- MODIFICADO
        """ Processa colisões de corpo a corpo (Jogador vs Inimigos). """
        colisoes_ram_inimigo_player = pygame.sprite.spritecollide(nave_player, grupo_inimigos, False)
        for inimigo in colisoes_ram_inimigo_player:
            dano = 1 if not isinstance(inimigo, InimigoBomba) else inimigo.DANO_EXPLOSAO
            nave_player.foi_atingido(dano, estado_jogo, inimigo.posicao)
                
            morreu = inimigo.foi_atingido(1)
            if morreu:
                nave_player.ganhar_pontos(inimigo.pontos_por_morte)
                self._tocar_som_explosao(inimigo, pos_ouvinte) # <-- MODIFICADO
            # (A checagem de morte do player acontece no final)

    def _handle_ramming_collisions_player_vs_bots(self, nave_player, grupo_bots, estado_jogo):
        """ Processa colisões de corpo a corpo (Jogador vs Bots). """
        colisoes_ram_bot_player = pygame.sprite.spritecollide(nave_player, grupo_bots, False)
        for bot in colisoes_ram_bot_player:
            
            # --- INÍCIO DA CORREÇÃO ---
            pontos_do_bot = bot.pontos # 1. Salva os pontos do bot ANTES de atingir.
            # (Não precisamos salvar os pontos do player, pois eles são lidos em update_offline_logic)
            # --- FIM DA CORREÇÃO ---

            morreu_player = nave_player.foi_atingido(1, estado_jogo, bot.posicao, atacante=bot)
            morreu_bot = bot.foi_atingido(1, estado_jogo, nave_player.posicao, atacante=nave_player)
            
            if morreu_bot:
                # --- INÍCIO DA CORREÇÃO ---
                pontos_ganhos = int(pontos_do_bot * 0.75) # 2. Usa os pontos salvos.
                nave_player.ganhar_pontos(pontos_ganhos)
                print(f"[{nave_player.nome}] ganhou {pontos_ganhos} pontos por abater (ram) [{bot.nome}]")
                # --- FIM DA CORREÇÃO ---

    def _handle_bot_projectile_collisions(self, nave_player, grupo_projeteis_bots, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo, pos_ouvinte): # <-- MODIFICADO
        """ Processa colisões dos projéteis dos bots (vs tudo). """

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
                        self._tocar_som_explosao(inimigo, pos_ouvinte) # <-- MODIFICADO

        # Bot Proj vs Bots (PVP Amigável)
        colisoes_bot_vs_bot = pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_bots, True, False)
        for proj, bots_atingidos in colisoes_bot_vs_bot.items():
            owner_do_tiro = proj.owner
            if not owner_do_tiro:
                continue
            for bot_atingido in bots_atingidos:
                if bot_atingido != owner_do_tiro:
                    
                    # --- INÍCIO DA CORREÇÃO ---
                    pontos_da_vitima = bot_atingido.pontos # 1. Salva os pontos ANTES de atingir.
                    # --- FIM DA CORREÇÃO ---

                    dano_do_tiro = proj.dano
                    morreu = bot_atingido.foi_atingido(dano_do_tiro, estado_jogo, proj.posicao, atacante=owner_do_tiro)
                    if morreu:
                        if isinstance(owner_do_tiro, Nave):
                            # --- INÍCIO DA CORREÇÃO ---
                            pontos_ganhos = int(pontos_da_vitima * 0.75) # 2. Usa os pontos salvos.
                            owner_do_tiro.ganhar_pontos(pontos_ganhos)
                            print(f"[{owner_do_tiro.nome}] ganhou {pontos_ganhos} pontos por abater [{bot_atingido.nome}]!")
                            # --- FIM DA CORREÇÃO ---
        
        # Bot Proj vs Player (Verificado apenas se o jogador está jogando)
        if estado_jogo == "JOGANDO" or estado_jogo == "LOJA" or estado_jogo == "TERMINAL":
            colisoes_proj_bot_player = pygame.sprite.spritecollide(nave_player, grupo_projeteis_bots, True)
            for proj in colisoes_proj_bot_player:
                if proj.owner != nave_player: 
                    nave_player.foi_atingido(proj.dano, estado_jogo, proj.posicao, atacante=proj.owner)
                    # (A checagem de morte do player acontece no final do update_offline_logic)
                    
    def _handle_enemy_projectile_collisions_vs_bots(self, grupo_bots, grupo_projeteis_inimigos, estado_jogo):
        """ Processa colisões dos projéteis inimigos contra OS BOTS. """
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
                
    def _handle_ramming_collisions_bots_vs_enemies(self, grupo_bots, grupo_inimigos, estado_jogo, nave_player, pos_ouvinte): # <-- MODIFICADO
        """ Processa colisões de corpo a corpo (Bots vs Inimigos). """
        for bot in grupo_bots:
            inimigos_colididos = pygame.sprite.spritecollide(bot, grupo_inimigos, False)
            for inimigo in inimigos_colididos:
                dano = 1 if not isinstance(inimigo, InimigoBomba) else inimigo.DANO_EXPLOSAO
                bot.foi_atingido(dano, estado_jogo, inimigo.posicao)
                morreu = inimigo.foi_atingido(1)
                if morreu: 
                    bot.ganhar_pontos(inimigo.pontos_por_morte)
    
    def update_pvp_logic(self, game_state: dict, game_groups: dict, pos_ouvinte: pygame.math.Vector2):
        """
        Processa toda a lógica do modo PVP (transições de estado, updates, colisões).
        """
        
        # Extrai variáveis de estado
        estado_jogo = game_state["estado_jogo"]
        nave_player = game_state["nave_player"]
        agora = pygame.time.get_ticks()
        
        # Extrai grupos de sprites
        grupo_bots = game_groups["grupo_bots"]
        grupo_projeteis_player = game_groups["grupo_projeteis_player"]
        grupo_projeteis_bots = game_groups["grupo_projeteis_bots"]
        grupo_obstaculos = game_groups["grupo_obstaculos"]
        
        # --- 1. Gerenciamento de Transições de Estado PVP ---
        
        if estado_jogo == "PVP_LOBBY":
            # Transição: PVP_LOBBY -> PVP_COUNTDOWN (quando atingir 4 jogadores)
            # Neste modo offline, sempre temos 4 jogadores (player + 3 bots)
            total_jogadores = 1 + len(grupo_bots)  # player + bots
            
            if total_jogadores >= pvp_s.PVP_MAX_JOGADORES:
                # Inicia countdown
                game_state["pvp_lobby_timer_fim"] = None  # Limpa timer do lobby
                game_state["pvp_countdown_inicio"] = agora
                return "PVP_COUNTDOWN"
        
        elif estado_jogo == "PVP_COUNTDOWN":
            # Transição: PVP_COUNTDOWN -> PVP_PLAYING (após 30s)
            countdown_inicio = game_state.get("pvp_countdown_inicio", agora)
            tempo_decorrido = agora - countdown_inicio
            
            if tempo_decorrido >= pvp_s.PVP_TEMPO_LOBBY:
                # Teleporta jogadores para cantos do mapa
                spawn_positions = pvp_s.PVP_SPAWN_POSITIONS[:]
                random.shuffle(spawn_positions)
                
                # Teleporta player
                if spawn_positions:
                    spawn_x, spawn_y = spawn_positions.pop(0)
                    nave_player.posicao = pygame.math.Vector2(spawn_x, spawn_y)
                    nave_player.rect.center = nave_player.posicao
                
                # Teleporta bots
                for bot in grupo_bots:
                    if spawn_positions:
                        spawn_x, spawn_y = spawn_positions.pop(0)
                        bot.posicao = pygame.math.Vector2(spawn_x, spawn_y)
                        bot.rect.center = bot.posicao
                
                # Inicia timer da partida
                game_state["pvp_partida_timer_fim"] = agora + pvp_s.PVP_TEMPO_PARTIDA
                game_state["pvp_countdown_inicio"] = None
                return "PVP_PLAYING"
        
        elif estado_jogo == "PVP_PLAYING":
            # --- 2. Update de Entidades PVP ---
            
            # Lista de todos os jogadores (para que bots ataquem todos)
            todos_jogadores = [nave_player] + list(grupo_bots)
            lista_alvos_para_bots = [j for j in todos_jogadores if j.vida_atual > 0]
            
            # Update dos bots (atacam TODOS os jogadores, incluindo player)
            for bot in grupo_bots:
                if bot.vida_atual > 0:
                    # No PVP, bots atacam todos (incluindo o player)
                    bot.update(nave_player, grupo_projeteis_bots, grupo_bots, 
                              pygame.sprite.Group(), grupo_obstaculos, 
                              game_groups["grupo_efeitos_visuais"], pos_ouvinte)
            
            # Update de projéteis
            grupo_projeteis_player.update()
            grupo_projeteis_bots.update()
            
            # --- 3. Colisões PVP ---
            
            # Colisões: Projéteis do player vs Bots
            colisoes = pygame.sprite.groupcollide(grupo_bots, grupo_projeteis_player, False, True)
            for bot, proj_list in colisoes.items():
                for proj in proj_list:
                    dano = nave_player.nivel_dano if hasattr(nave_player, 'nivel_dano') else 1
                    bot.foi_atingido(dano, estado_jogo, proj.posicao)
            
            # Colisões: Projéteis do player vs Obstáculos
            pygame.sprite.groupcollide(grupo_obstaculos, grupo_projeteis_player, False, True)
            
            # Colisões: Projéteis dos bots vs Player
            colisoes_player = pygame.sprite.spritecollide(nave_player, grupo_projeteis_bots, True)
            for proj in colisoes_player:
                if nave_player.vida_atual > 0:
                    nave_player.foi_atingido(1, estado_jogo, proj.posicao)
            
            # Colisões: Projéteis dos bots vs Outros bots
            for bot_atirador in grupo_bots:
                # Pega apenas os projéteis deste bot
                projeteis_deste_bot = [p for p in grupo_projeteis_bots if hasattr(p, 'dono') and p.dono == bot_atirador]
                
                for bot_alvo in grupo_bots:
                    if bot_alvo != bot_atirador and bot_alvo.vida_atual > 0:
                        for proj in projeteis_deste_bot:
                            if bot_alvo.rect.collidepoint(proj.posicao.x, proj.posicao.y):
                                dano = bot_atirador.nivel_dano if hasattr(bot_atirador, 'nivel_dano') else 1
                                bot_alvo.foi_atingido(dano, estado_jogo, proj.posicao)
                                proj.kill()
            
            # Colisões: Projéteis dos bots vs Obstáculos
            pygame.sprite.groupcollide(grupo_obstaculos, grupo_projeteis_bots, False, True)
            
            # Colisões de Ramming: Player vs Bots
            bots_colididos = pygame.sprite.spritecollide(nave_player, grupo_bots, False)
            for bot in bots_colididos:
                if nave_player.vida_atual > 0:
                    nave_player.foi_atingido(1, estado_jogo, bot.posicao)
                if bot.vida_atual > 0:
                    bot.foi_atingido(1, estado_jogo, nave_player.posicao)
            
            # Colisões de Ramming: Bots vs Bots
            for i, bot1 in enumerate(grupo_bots):
                for bot2 in list(grupo_bots)[i+1:]:
                    if bot1.rect.colliderect(bot2.rect):
                        if bot1.vida_atual > 0:
                            bot1.foi_atingido(1, estado_jogo, bot2.posicao)
                        if bot2.vida_atual > 0:
                            bot2.foi_atingido(1, estado_jogo, bot1.posicao)
            
            # --- 4. Verificação de Fim de Partida ---
            
            # Conta jogadores vivos
            jogadores_vivos = []
            if nave_player.vida_atual > 0:
                jogadores_vivos.append(nave_player)
            jogadores_vivos.extend([bot for bot in grupo_bots if bot.vida_atual > 0])
            
            # Fim por último sobrevivente
            if len(jogadores_vivos) == 1:
                game_state["pvp_vencedor_nome"] = jogadores_vivos[0].nome
                return "PVP_GAME_OVER"
            
            # Fim por tempo esgotado
            if agora >= game_state.get("pvp_partida_timer_fim", float('inf')):
                # Determina vencedor por maior vida
                if jogadores_vivos:
                    vencedor = max(jogadores_vivos, key=lambda j: j.vida_atual)
                    game_state["pvp_vencedor_nome"] = vencedor.nome
                else:
                    game_state["pvp_vencedor_nome"] = None  # Empate
                return "PVP_GAME_OVER"
            
            # Fim por todos mortos (empate)
            if len(jogadores_vivos) == 0:
                game_state["pvp_vencedor_nome"] = None
                return "PVP_GAME_OVER"
        
        return None