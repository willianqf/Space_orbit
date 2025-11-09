# multi/pvp_manager.py
import pygame
import sys
import random
import math

# Importa as configurações do PVP
import multi.pvp_settings as pvp_s

# Importa as classes e módulos existentes do seu jogo
import settings as s # Importa as configurações principais também
from ships import Player, NaveBot, set_global_ship_references
from projectiles import Projetil, ProjetilTeleguiadoJogador
from effects import Explosao
from camera import Camera
from botia import BotAI # Os bots usarão a IA existente
from entities import Obstaculo # Podemos adicionar alguns obstáculos

# --- Funções de Inicialização ---

def inicializar_pygame():
    """Inicializa o Pygame e a tela."""
    pygame.init()
    # Usamos o tamanho da tela inicial das suas configurações principais
    tela = pygame.display.set_mode((s.LARGURA_TELA_INICIAL, s.ALTURA_TELA_INICIAL), pygame.RESIZABLE)
    pygame.display.set_caption("Modo PVP (Teste com Bots)")
    clock = pygame.time.Clock()
    return tela, clock

def distribuir_atributos(nave, pontos):
    """
    Distribui aleatoriamente os 10 pontos de atributos para os bots.
    (No futuro, o jogador humano fará isso na tela de lobby).
    """
    opcoes = ["motor", "dano", "max_health", "escudo"]
    for _ in range(pontos):
        upgrade_escolhido = random.choice(opcoes)
        
        # Tenta comprar, se falhar (ex: nível máximo), tenta outro
        if not nave.comprar_upgrade(upgrade_escolhido):
            # Tenta as outras opções em ordem
            for opt in opcoes:
                if nave.comprar_upgrade(opt):
                    break
    
    print(f"[{nave.nome}] Atributos distribuídos. HP: {nave.max_vida}, Motor: {nave.nivel_motor}, Dano: {nave.nivel_dano}, Escudo: {nave.nivel_escudo}")
    # Reseta a vida para o máximo após os upgrades
    nave.vida_atual = nave.max_vida

# --- Função Principal do Gerenciador PVP ---

def rodar_partida_pvp():
    
    tela, clock = inicializar_pygame()
    LARGURA_TELA, ALTURA_TELA = tela.get_size()
    
    # --- Grupos de Sprites ---
    grupo_pvp_jogadores = pygame.sprite.Group()
    grupo_projeteis = pygame.sprite.Group()
    grupo_efeitos = pygame.sprite.Group()
    grupo_obstaculos_pvp = pygame.sprite.Group() # Adicionamos alguns obstáculos
    
    # Define referências globais para explosões (necessário para ships.py)
    set_global_ship_references(grupo_efeitos)

    # --- Câmera ---
    # A câmera focará no jogador humano
    camera_pvp = Camera(LARGURA_TELA, ALTURA_TELA)
    
    # --- Estado do Jogo ---
    estado_jogo = "LOBBY" # LOBBY, COUNTDOWN, PLAYING, GAME_OVER
    tempo_inicio_partida = 0
    tempo_fim_partida = 0
    vencedor_nome = "Ninguém"
    
    # O jogador humano (controlado por você)
    player_humano = None

    rodando = True
    while rodando:
        
        # --- Redimensionamento da Tela ---
        for event in pygame.event.get(pygame.VIDEORESIZE):
            LARGURA_TELA, ALTURA_TELA = event.w, event.h
            tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.RESIZABLE)
            camera_pvp.resize(LARGURA_TELA, ALTURA_TELA)

        # --- Loop de Eventos ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                rodando = False
            
            if estado_jogo == "LOBBY":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # --- Inicia a Contagem ---
                        estado_jogo = "COUNTDOWN"
                        print("[PVP] Lobby pronto! Iniciando contagem...")
                        tempo_inicio_partida = pygame.time.get_ticks() + (pvp_s.LOBBY_COUNTDOWN_SEGUNDOS * 1000)
                        
                        # Limpa grupos
                        grupo_pvp_jogadores.empty()
                        grupo_projeteis.empty()
                        grupo_efeitos.empty()
                        grupo_obstaculos_pvp.empty()
                        
                        # Cria o Jogador Humano
                        pos_player = pvp_s.SPAWN_POSICOES[0]
                        player_humano = Player(pos_player.x, pos_player.y, nome="JogadorPVP")
                        distribuir_atributos(player_humano, pvp_s.PONTOS_ATRIBUTOS_INICIAIS)
                        grupo_pvp_jogadores.add(player_humano)
                        
                        # Cria os Bots
                        for i in range(1, pvp_s.MAX_JOGADORES_PVP):
                            pos_bot = pvp_s.SPAWN_POSICOES[i]
                            bot = NaveBot(pos_bot.x, pos_bot.y)
                            bot.nome = f"BotPVP_{i}"
                            distribuir_atributos(bot, pvp_s.PONTOS_ATRIBUTOS_INICIAIS)
                            grupo_pvp_jogadores.add(bot)
                            
                        # Adiciona alguns obstáculos
                        for _ in range(15):
                            x = random.randint(100, pvp_s.MAP_WIDTH - 100)
                            y = random.randint(100, pvp_s.MAP_HEIGHT - 100)
                            raio = random.randint(s.OBSTACULO_RAIO_MIN, s.OBSTACULO_RAIO_MAX)
                            grupo_obstaculos_pvp.add(Obstaculo(x, y, raio))
            
            if estado_jogo == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    # Permite sair da partida
                    if event.key == pygame.K_ESCAPE:
                        rodando = False # Volta ao menu (na integração)

            if estado_jogo == "GAME_OVER":
                 if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                        estado_jogo = "LOBBY" # Reinicia

        # --- Lógica de Jogo ---
        
        if estado_jogo == "COUNTDOWN":
            tempo_restante_ms = tempo_inicio_partida - pygame.time.get_ticks()
            if tempo_restante_ms <= 0:
                print("[PVP] Contagem terminada. Partida iniciada!")
                estado_jogo = "PLAYING"
                tempo_fim_partida = pygame.time.get_ticks() + (pvp_s.PARTIDA_DURACAO_SEGUNDOS * 1000)
        
        elif estado_jogo == "PLAYING":
            agora = pygame.time.get_ticks()
            
            # 1. Atualizar Jogador Humano
            if player_humano.vida_atual > 0:
                player_humano.update(grupo_projeteis, camera_pvp) # Usa o update offline
            
            # 2. Atualizar Bots
            # (A IA dos bots vai naturalmente atacar outros jogadores)
            alvos_vivos = [p for p in grupo_pvp_jogadores if p.vida_atual > 0]
            
            # Precisamos de uma "lista_alvos_naves" para a IA dos bots
            # A IA dos bots (botia.py) precisa de referências de grupos
            for bot in grupo_pvp_jogadores:
                if isinstance(bot, NaveBot) and bot.vida_atual > 0:
                    bot.update(
                        player_ref=player_humano, 
                        grupo_projeteis_bots=grupo_projeteis,
                        grupo_bots_ref=grupo_pvp_jogadores,
                        grupo_inimigos_ref=grupo_pvp_jogadores, # Bots veem outros jogadores como inimigos
                        grupo_obstaculos_ref=grupo_obstaculos_pvp,
                        grupo_efeitos_visuais_ref=grupo_efeitos,
                        pos_ouvinte=player_humano.posicao
                    )

            # 3. Atualizar Projéteis e Efeitos
            grupo_projeteis.update()
            grupo_efeitos.update()
            
            # 4. Lógica de Colisão (Simplificada)
            
            # Colisão: Projéteis vs Jogadores
            colisoes_proj = pygame.sprite.groupcollide(grupo_projeteis, grupo_pvp_jogadores, True, False)
            for proj, naves_atingidas in colisoes_proj.items():
                owner = proj.owner
                for nave in naves_atingidas:
                    if nave != owner: # Não atirar em si mesmo
                        nave.foi_atingido(proj.dano, "JOGANDO", proj.posicao, atacante=owner)
            
            # Colisão: Projéteis vs Obstáculos
            pygame.sprite.groupcollide(grupo_projeteis, grupo_obstaculos_pvp, True, True)

            # 5. Checar Condições de Fim de Jogo
            jogadores_vivos = [p for p in grupo_pvp_jogadores if p.vida_atual > 0]
            
            if len(jogadores_vivos) <= 1:
                estado_jogo = "GAME_OVER"
                if len(jogadores_vivos) == 1:
                    vencedor_nome = jogadores_vivos[0].nome
                else:
                    vencedor_nome = "Empate (Morte Súbita)"
                print(f"[PVP] Partida terminada. Vencedor: {vencedor_nome}")

            elif agora > tempo_fim_partida:
                estado_jogo = "GAME_OVER"
                # Lógica de desempate (mais vida)
                if not jogadores_vivos:
                    vencedor_nome = "Empate (Sem Sobreviventes)"
                else:
                    jogadores_vivos.sort(key=lambda p: p.vida_atual, reverse=True)
                    vencedor_nome = jogadores_vivos[0].nome
                print(f"[PVP] Partida terminada por tempo. Vencedor: {vencedor_nome}")

        
        # --- Desenho ---
        
        tela.fill(s.PRETO)
        
        # Foco da câmera
        if player_humano and player_humano.vida_atual > 0:
            camera_pvp.update(player_humano)
        elif 'jogadores_vivos' in locals() and jogadores_vivos:
            camera_pvp.update(jogadores_vivos[0]) # Foca no primeiro bot vivo
        elif player_humano:
            camera_pvp.update(player_humano) # Foca no corpo
            
        # Desenha Obstáculos
        for obst in grupo_obstaculos_pvp:
            tela.blit(obst.image, camera_pvp.apply(obst.rect))
            
        # Desenha Jogadores e Bots
        for nave in grupo_pvp_jogadores:
            if nave.vida_atual > 0:
                nave.desenhar(tela, camera_pvp)
                nave.desenhar_vida(tela, camera_pvp)
                nave.desenhar_nome(tela, camera_pvp)
                for aux in nave.grupo_auxiliares_ativos:
                    aux.desenhar(tela, camera_pvp)

        # Desenha Projéteis e Efeitos
        for proj in grupo_projeteis:
            tela.blit(proj.image, camera_pvp.apply(proj.rect))
        for efeito in grupo_efeitos:
            efeito.draw(tela, camera_pvp)
            
        # --- Desenho de UI (Sobreposição) ---
        
        if estado_jogo == "LOBBY":
            # (Tela de Lobby/Atributos iria aqui)
            texto_lobby = pvp_s.FONT_TITULO.render("Modo PVP (Arena)", True, pvp_s.BRANCO)
            tela.blit(texto_lobby, (LARGURA_TELA // 2 - texto_lobby.get_width() // 2, ALTURA_TELA // 3))
            texto_instr = pvp_s.FONT_TEXTO.render("Pressione [ESPAÇO] para iniciar (simulação de lobby)", True, pvp_s.BRANCO)
            tela.blit(texto_instr, (LARGURA_TELA // 2 - texto_instr.get_width() // 2, ALTURA_TELA // 2))

        elif estado_jogo == "COUNTDOWN":
            tempo_restante_s = (tempo_inicio_partida - pygame.time.get_ticks()) / 1000
            texto_timer = pvp_s.FONT_TITULO.render(f"Iniciando em {math.ceil(tempo_restante_s)}s", True, pvp_s.AMARELO)
            tela.blit(texto_timer, (LARGURA_TELA // 2 - texto_timer.get_width() // 2, ALTURA_TELA // 2 - texto_timer.get_height() // 2))
        
        elif estado_jogo == "PLAYING":
            # Timer da Partida
            tempo_restante_ms = tempo_fim_partida - pygame.time.get_ticks()
            minutos = int(tempo_restante_ms / 60000)
            segundos = int((tempo_restante_ms % 60000) / 1000)
            cor_timer = pvp_s.BRANCO if tempo_restante_ms > 10000 else pvp_s.VERMELHO
            texto_timer = pvp_s.FONT_TIMER.render(f"{minutos:02d}:{segundos:02d}", True, cor_timer)
            tela.blit(texto_timer, (LARGURA_TELA // 2 - texto_timer.get_width() // 2, 20))
            
            # Jogadores Vivos
            vivos_count = len([p for p in grupo_pvp_jogadores if p.vida_atual > 0])
            texto_vivos = pvp_s.FONT_TEXTO.render(f"Vivos: {vivos_count}/{pvp_s.MAX_JOGADORES_PVP}", True, pvp_s.BRANCO)
            tela.blit(texto_vivos, (LARGURA_TELA - texto_vivos.get_width() - 20, 20))

        elif estado_jogo == "GAME_OVER":
            texto_fim = pvp_s.FONT_TITULO.render("Fim de Jogo!", True, pvp_s.VERMELHO)
            tela.blit(texto_fim, (LARGURA_TELA // 2 - texto_fim.get_width() // 2, ALTURA_TELA // 3))
            texto_venc = pvp_s.FONT_TIMER.render(f"Vencedor: {vencedor_nome}", True, pvp_s.VERDE)
            tela.blit(texto_venc, (LARGURA_TELA // 2 - texto_venc.get_width() // 2, ALTURA_TELA // 2))
            texto_instr = pvp_s.FONT_TEXTO.render("Pressione [ESPAÇO] para voltar ao Lobby", True, pvp_s.BRANCO)
            tela.blit(texto_instr, (LARGURA_TELA // 2 - texto_instr.get_width() // 2, ALTURA_TELA * 0.7))


        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

# --- Ponto de Entrada ---
if __name__ == "__main__":
    # Este 'if' permite que você rode este arquivo diretamente para testar o modo PVP
    rodar_partida_pvp()