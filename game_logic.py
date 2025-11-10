# game_logic.py
import pygame
import random
import settings as s
import multi.pvp_settings as pvp_s # <-- MODIFICAÇÃO: Importa configs PVP
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

    def update_offline_logic(self, game_state: dict, game_groups: dict, pos_ouvinte: pygame.math.Vector2): # <-- MODIFICADO
        """
        Processa toda a lógica de jogo PVE offline (spawns, updates, colisões).
        """
        # --- INÍCIO: TRAVA DE SEGURANÇA (NOVO) ---
        # Se por algum motivo esta função for chamada no mapa PVP, pare.
        if s.MAP_WIDTH < 5000: # O mapa PVE tem 8000, o PVP tem 1500
            #print("[ALERTA DE LÓGICA] update_offline_logic (PVE) chamada no mapa PVP. Abortando.")
            return game_state["estado_jogo"] # Retorna sem fazer nada
        # --- FIM: TRAVA DE SEGURANÇA ---
        # Extrai variáveis de estado
        estado_jogo = game_state["estado_jogo"]
        
        # --- INÍCIO: MODIFICAÇÃO (PVP) ---
        # Se estamos em qualquer estado PVP, NÃO rode a lógica PVE.
        if estado_jogo.startswith("PVP_"):
            return estado_jogo # A lógica PVP é tratada em 'update_pvp_logic'
        # --- FIM: MODIFICAÇÃO ---
        
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
        grupo_bots.update(nave_player, grupo_projeteis_bots, grupo_bots, grupo_inimigos, grupo_obstaculos, grupo_efeitos_visuais, pos_ouvinte, s.MAP_WIDTH, s.MAP_HEIGHT)
        grupo_inimigos.update(lista_alvos_naves, grupo_projeteis_inimigos, s.DESPAWN_DIST, pos_ouvinte)
        
        grupo_projeteis_player.update()
        grupo_projeteis_bots.update()
        grupo_projeteis_inimigos.update()

        # --- 2. Lógica de Spawn ---
        # (lógica de spawn PVE - sem mudança)
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
        self._handle_bot_projectile_collisions(nave_player, grupo_projeteis_bots, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo, pos_ouvinte)
        self._handle_enemy_projectile_collisions_vs_bots(grupo_bots, grupo_projeteis_inimigos, estado_jogo)
        self._handle_ramming_collisions_bots_vs_enemies(grupo_bots, grupo_inimigos, estado_jogo, nave_player, pos_ouvinte)
        
        # --- Bloco 3B: Colisões que SÓ AFETAM O JOGADOR ---
        if (estado_jogo == "JOGANDO" or estado_jogo == "LOJA" or estado_jogo == "TERMINAL"):
        
            self._handle_player_projectile_collisions(nave_player, grupo_projeteis_player, grupo_obstaculos, grupo_inimigos, grupo_bots, estado_jogo, pos_ouvinte)
            self._handle_enemy_projectile_collisions_vs_player(nave_player, grupo_projeteis_inimigos, estado_jogo)
            self._handle_ramming_collisions_player_vs_enemies(nave_player, grupo_inimigos, estado_jogo, pos_ouvinte)
            self._handle_ramming_collisions_player_vs_bots(nave_player, grupo_bots, estado_jogo)

            # --- 4. Checagem de Morte do Jogador (após todas as colisões) ---
            # --- INÍCIO: CORREÇÃO (Bug Congelamento PVE) ---
            if nave_player.vida_atual <= 0 and estado_jogo == "JOGANDO": # <-- Adicionado check
                print("[LOGIC] Morte do jogador detectada por colisões.")
                
                if hasattr(nave_player, 'ultimo_atacante') and nave_player.ultimo_atacante:
                    if hasattr(nave_player.ultimo_atacante, 'ganhar_pontos'):
                        pontos_ganhos = int(nave_player.pontos * 0.75)
                        nave_player.ultimo_atacante.ganhar_pontos(pontos_ganhos)
                        print(f"[{nave_player.ultimo_atacante.nome}] ganhou {pontos_ganhos} pontos por abater [{nave_player.nome}]")
                    nave_player.ultimo_atacante = None 
                
                # --- INÍCIO: CORREÇÃO (Não retorna, apenas muda o estado) ---
                estado_jogo = "ESPECTADOR"
                game_state["estado_jogo"] = "ESPECTADOR"
                
                # Configura o estado de espectador
                game_state["jogador_esta_vivo_espectador"] = False
                game_state["alvo_espectador"] = None
                game_state["alvo_espectador_nome"] = None
                game_state["spectator_overlay_hidden"] = False
                espectador_dummy_alvo = game_state.get("espectador_dummy_alvo")
                if espectador_dummy_alvo:
                    espectador_dummy_alvo.posicao = nave_player.posicao.copy()
                # --- FIM: CORREÇÃO ---
            # --- FIM: CORREÇÃO ---
            
        return estado_jogo # Retorna o estado atual (que pode ter sido mudado para ESPECTADOR)
    
    # --- INÍCIO: MODIFICAÇÃO (Nova Função PVP) ---
    def update_pvp_logic(self, game_state: dict, game_groups: dict, pos_ouvinte: pygame.math.Vector2):
        """
        Processa a lógica de jogo especificamente para o modo PVP.
        (Sem spawns PVE, apenas updates e colisões entre jogadores/bots)
        """
        
        # Extrai variáveis de estado
        estado_jogo = game_state["estado_jogo"]
        nave_player = game_state["nave_player"]
        agora = pygame.time.get_ticks()
        
        # --- INÍCIO: MODIFICAÇÃO (Ler tamanho do mapa) ---
        # Usa o s.MAP_WIDTH atual, que é definido pelo main.py
        map_width = s.MAP_WIDTH
        map_height = s.MAP_HEIGHT
        # --- FIM: MODIFICAÇÃO ---

        # Extrai grupos de sprites
        grupo_bots = game_groups["grupo_bots"] # Bots PVP
        grupo_player = game_groups["grupo_player"] # Jogador
        grupo_projeteis_player = game_groups["grupo_projeteis_player"]
        grupo_projeteis_bots = game_groups["grupo_projeteis_bots"]
        grupo_obstaculos = game_groups["grupo_obstaculos"]
        grupo_efeitos_visuais = game_groups["grupo_efeitos_visuais"]

        # Combina player e bots em um único grupo para lógica
        grupo_pvp_jogadores = pygame.sprite.Group(grupo_player, grupo_bots)
        
        # --- INÍCIO: CORREÇÃO (Bug 3: Fim de Jogo) ---
        # A checagem de fim de jogo deve rodar ANTES da lógica de update
        # e deve rodar em PLAYING ou ESPECTADOR (no mapa PVP).
        is_pvp_map_check = (s.MAP_WIDTH < 5000) 
        
        if estado_jogo == "PVP_PLAYING" or (estado_jogo == "ESPECTADOR" and is_pvp_map_check):
            
            # Checar Condições de Fim de Jogo
            jogadores_vivos = [p for p in grupo_pvp_jogadores if p.vida_atual > 0]
            
            if len(jogadores_vivos) <= 1:
                # Alguém venceu
                estado_jogo = "PVP_GAME_OVER"
                game_state["estado_jogo"] = "PVP_GAME_OVER" # <-- Garante a atualização
                if len(jogadores_vivos) == 1:
                    game_state["pvp_vencedor_nome"] = jogadores_vivos[0].nome
                else:
                    game_state["pvp_vencedor_nome"] = "Empate" 
                print(f"[LOGIC] Partida PVP terminada. Vencedor: {game_state['pvp_vencedor_nome']}")
            
            elif agora > game_state.get("pvp_partida_timer_fim", 0):
                # Tempo acabou
                estado_jogo = "PVP_GAME_OVER"
                game_state["estado_jogo"] = "PVP_GAME_OVER" # <-- Garante a atualização
                jogadores_vivos.sort(key=lambda p: p.vida_atual, reverse=True)
                if jogadores_vivos:
                    game_state["pvp_vencedor_nome"] = jogadores_vivos[0].nome
                else:
                    game_state["pvp_vencedor_nome"] = "Empate"
                print(f"[LOGIC] Partida PVP terminada por tempo. Vencedor: {game_state['pvp_vencedor_nome']}")
        # --- FIM: CORREÇÃO (Bug 3) ---

        # --- 1. Lógica de Jogo (Lobby e Contagem) ---
        if estado_jogo == "PVP_LOBBY":
            # Verifica se atingiu o número de jogadores (para testes, começamos imediatamente)
            if len(grupo_pvp_jogadores) >= pvp_s.MAX_JOGADORES_PVP:
                print("[LOGIC] Jogadores suficientes. Iniciando contagem.")
                estado_jogo = "PVP_COUNTDOWN"
                game_state["estado_jogo"] = "PVP_COUNTDOWN"
                game_state["pvp_lobby_timer_fim"] = agora + (pvp_s.PVP_LOBBY_COUNTDOWN_SEGUNDOS * 1000)
            # (No seu jogo final, esta verificação seria: if len(jogadores_conectados) == 4)

        elif estado_jogo == "PVP_COUNTDOWN":
            if agora > game_state["pvp_lobby_timer_fim"]:
                print("[LOGIC] Contagem terminada. Teleportando para os cantos (freeze 5s).")
                
                # --- INÍCIO: MODIFICAÇÃO (Novo Estado) ---
                estado_jogo = "PVP_PRE_MATCH"
                game_state["estado_jogo"] = "PVP_PRE_MATCH"
                # Define o timer de 5 segundos de congelamento
                game_state["pvp_pre_match_timer_fim"] = agora + (5 * 1000) 
                # --- FIM: MODIFICAÇÃO ---

                # --- Lógica de Teleporte para os Cantos ---
                # (O resto deste bloco, linhas 167-183, está CORRETO e não muda)
                # Pega todos os jogadores/bots vivos
                jogadores_para_spawnar = [p for p in grupo_pvp_jogadores if p.vida_atual > 0]
                
                for i, nave in enumerate(jogadores_para_spawnar):
                    if i < len(pvp_s.SPAWN_POSICOES):
                        pos_canto = pvp_s.SPAWN_POSICOES[i]
                        nave.posicao = pos_canto.copy()
                        nave.rect.center = nave.posicao
                        nave.vida_atual = nave.max_vida # Cura total
                        nave.parar_regeneracao()
                        nave.alvo_selecionado = None
                        nave.posicao_alvo_mouse = None
                        print(f"[{nave.nome}] teleportado para o canto {i+1}.")
                    else:
                        # Se houver mais de 4, remove (não deve acontecer)
                        nave.kill()
        
        elif estado_jogo == "PVP_PRE_MATCH":
            # Naves estão congeladas (jogador não atualiza em main.py, bots não atualizam acima)
            # Apenas espera o timer de 5 segundos acabar
            if agora > game_state["pvp_pre_match_timer_fim"]:
                print("[LOGIC] Congelamento 5s terminou. Partida PVP iniciada!")
                estado_jogo = "PVP_PLAYING"
                game_state["estado_jogo"] = "PVP_PLAYING"
                # AGORA sim, define o timer de 3 minutos da partida
                game_state["pvp_partida_timer_fim"] = agora + (pvp_s.PVP_PARTIDA_DURACAO_SEGUNDOS * 1000)
        # --- FIM: ADICIONAR NOVO ESTADO ---
        
        elif estado_jogo == "PVP_PLAYING":
            # (Este bloco agora está vazio, pois a lógica de Fim de Jogo foi movida para cima,
            # e a lógica de Batalha está no `if estado_jogo != "PVP_GAME_OVER"` abaixo)
            pass

        # --- 3. Atualização de Grupos (em todos os estados PVP, exceto Game Over) ---
        if estado_jogo != "PVP_GAME_OVER":
            # Cria a lista de alvos (todos os jogadores vivos)
            lista_alvos_naves_pvp = [p for p in grupo_pvp_jogadores if p.vida_atual > 0]
            
            # --- INÍCIO: CORREÇÃO (Rodar bots/colisão no modo espectador) ---
            if estado_jogo == "PVP_PLAYING" or (estado_jogo == "ESPECTADOR" and is_pvp_map_check):
            # --- FIM: CORREÇÃO ---
            
                # Atualiza Bots (eles se veem como inimigos)
                for bot in grupo_bots:
                    if bot.vida_atual > 0:
                        # --- INÍCIO: MODIFICAÇÃO (Passar map_width/height) ---
                        bot.update(
                            player_ref=nave_player, 
                            grupo_projeteis_bots=grupo_projeteis_bots,
                            grupo_bots_ref=grupo_pvp_jogadores,
                            grupo_inimigos_ref=grupo_pvp_jogadores, # <--- AQUI ELES MIRAM EM TODOS
                            grupo_obstaculos_ref=grupo_obstaculos,
                            grupo_efeitos_visuais_ref=grupo_efeitos_visuais,
                            pos_ouvinte=pos_ouvinte,
                            map_width=map_width,
                            map_height=map_height
                        )
                        # --- FIM: MODIFICAÇÃO ---
                        
                # --- 4. Lógica de Colisão PVP (SÓ RODA SE ESTIVER EM "PVP_PLAYING") ---
                
                # Colisão: Projéteis do Player vs Bots
                colisoes_player_vs_bot = pygame.sprite.groupcollide(grupo_projeteis_player, grupo_bots, True, False)
                for proj, bots_atingidos in colisoes_player_vs_bot.items():
                    for bot in bots_atingidos:
                        # --- INÍCIO: CORREÇÃO (Respawn Bot PVP) ---
                        bot.foi_atingido(proj.dano, estado_jogo, proj.posicao, atacante=nave_player)
                        # --- FIM: CORREÇÃO ---

                # Colisão: Projéteis do Player vs Obstáculos
                pygame.sprite.groupcollide(grupo_projeteis_player, grupo_obstaculos, True, True)

                # Colisão: Projéteis de Bots vs Player
                colisoes_bot_vs_player = pygame.sprite.spritecollide(nave_player, grupo_projeteis_bots, True)
                for proj in colisoes_bot_vs_player:
                    if nave_player.vida_atual > 0:
                        # --- INÍCIO: CORREÇÃO (Respawn Bot PVP) ---
                        nave_player.foi_atingido(proj.dano, estado_jogo, proj.posicao, atacante=proj.owner)
                        # --- FIM: CORREÇÃO ---
                
                # Colisão: Projéteis de Bots vs outros Bots
                colisoes_bot_vs_bot = pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_bots, True, False)
                for proj, bots_atingidos in colisoes_bot_vs_bot.items():
                    owner = proj.owner
                    for bot in bots_atingidos:
                        if bot != owner: # Não atirar em si mesmo
                            # --- INÍCIO: CORREÇÃO (Respawn Bot PVP) ---
                            bot.foi_atingido(proj.dano, estado_jogo, proj.posicao, atacante=owner)
                            # --- FIM: CORREÇÃO ---

                # Colisão: Projéteis de Bots vs Obstáculos
                pygame.sprite.groupcollide(grupo_projeteis_bots, grupo_obstaculos, True, True)

                # Colisão: Ramming (Corpo a Corpo) entre todos
                colisoes_ramming = pygame.sprite.groupcollide(grupo_pvp_jogadores, grupo_pvp_jogadores, False, False)
                for nave_a, naves_colididas in colisoes_ramming.items():
                    for nave_b in naves_colididas:
                        if nave_a != nave_b and nave_a.vida_atual > 0 and nave_b.vida_atual > 0: # Só colide com os outros
                            # Aplica um pequeno dano de ramming
                            # --- INÍCIO: CORREÇÃO (Respawn Bot PVP) ---
                            nave_a.foi_atingido(0.1, estado_jogo, nave_b.posicao, atacante=nave_b)
                            # --- FIM: CORREÇÃO ---
            
            # --- INÍCIO: CORREÇÃO (Auto-Espectador no PVP) ---
            # Se o jogador morreu durante a partida
            if nave_player.vida_atual <= 0 and game_state["estado_jogo"] == "PVP_PLAYING":
                print("[LOGIC] Jogador morreu no PVP. Forçando modo espectador.")
                estado_jogo = "ESPECTADOR"
                game_state["estado_jogo"] = "ESPECTADOR"
                
                # Configura o estado de espectador (copiado do main.py)
                game_state["jogador_esta_vivo_espectador"] = False
                game_state["alvo_espectador"] = None
                game_state["alvo_espectador_nome"] = None
                game_state["spectator_overlay_hidden"] = False
                # Pega o "dummy" (alvo falso) do game_state
                espectador_dummy_alvo = game_state.get("espectador_dummy_alvo")
                if espectador_dummy_alvo:
                    espectador_dummy_alvo.posicao = nave_player.posicao.copy()
            # --- FIM: CORREÇÃO ---

            grupo_projeteis_player.update()
            grupo_projeteis_bots.update()

        return estado_jogo
    # --- FIM DA NOVA FUNÇÃO PVP ---


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
            # --- INÍCIO: MODIFICAÇÃO (Recompensa por Abate) ---
            nave_player.foi_atingido(dano, estado_jogo, inimigo.posicao, atacante=inimigo) # Inimigo é o atacante
            # --- FIM DA MODIFICAÇÃO ---
                
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
                # --- INÍCIO: MODIFICAÇÃO (Atacante) ---
                atacante = getattr(proj, 'owner', None)
                # --- FIM: MODIFICAÇÃO ---

                if isinstance(proj, ProjetilCongelante):
                    bot.aplicar_congelamento(s.DURACAO_CONGELAMENTO)
                elif isinstance(proj, ProjetilTeleguiadoLento):
                    bot.aplicar_lentidao(6000)
                else: 
                    # --- MODIFICAÇÃO: Passa atacante ---
                    bot.foi_atingido(1, estado_jogo, proj.posicao, atacante=atacante)
                proj.kill()
                
    def _handle_ramming_collisions_bots_vs_enemies(self, grupo_bots, grupo_inimigos, estado_jogo, nave_player, pos_ouvinte): # <-- MODIFICADO
        """ Processa colisões de corpo a corpo (Bots vs Inimigos). """
        for bot in grupo_bots:
            inimigos_colididos = pygame.sprite.spritecollide(bot, grupo_inimigos, False)
            for inimigo in inimigos_colididos:
                dano = 1 if not isinstance(inimigo, InimigoBomba) else inimigo.DANO_EXPLOSAO
                # --- MODIFICAÇÃO: Passa atacante ---
                bot.foi_atingido(dano, estado_jogo, inimigo.posicao, atacante=inimigo)
                
                morreu = inimigo.foi_atingido(1)
                if morreu: 
                    bot.ganhar_pontos(inimigo.pontos_por_morte)
                    self._tocar_som_explosao(inimigo, pos_ouvinte) # <-- MODIFICADO