# ships.py
import pygame
import math
import random
import ui
import settings as s 
from settings import (AZUL_NAVE, PONTA_NAVE, VERDE_AUXILIAR, LARANJA_BOT, #MAP_WIDTH, MAP_HEIGHT, <-- REMOVIDO
                      MAX_TARGET_LOCK_DISTANCE, MAX_NIVEL_MOTOR, 
                      MAX_NIVEL_DANO, 
                      MAX_NIVEL_ESCUDO, 
                      REDUCAO_DANO_POR_NIVEL, DURACAO_FX_ESCUDO, COR_ESCUDO_FX,
                      RASTRO_MAX_PARTICULAS, RASTRO_DURACAO, RASTRO_TAMANHO_INICIAL, COR_RASTRO_MOTOR,
                      VERMELHO_VIDA_FUNDO, VERDE_VIDA, MAX_TOTAL_UPGRADES, MAX_DISTANCIA_SOM_AUDIVEL, PANNING_RANGE_SOM, VOLUME_BASE_TIRO_PLAYER,
                      PONTOS_LIMIARES_PARA_UPGRADE, PONTOS_SCORE_PARA_MUDAR_LIMIAR, CUSTOS_AUXILIARES, FONT_NOME_JOGADOR, BRANCO, VELOCIDADE_ROTACAO_NAVE,
                      REGEN_POR_TICK, REGEN_TICK_RATE, 
                      ROXO_TIRO_LENTO, AZUL_CONGELANTE,
                      # --- INÍCIO: MODIFICAÇÃO (Importar novas constantes) ---
                      DANO_POR_NIVEL, VIDA_POR_NIVEL
                      # --- FIM: MODIFICAÇÃO ---
                      ) 
# Importa classes necessárias
from projectiles import Projetil, ProjetilTeleguiadoJogador
from effects import Explosao
from entities import Obstaculo, NaveRegeneradora 

# --- INÍCIO DA REATORAÇÃO: Importa o cérebro do Bot ---
from botia import BotAI
# --- FIM DA REATORAÇÃO ---

def tocar_som_posicional(som, pos_fonte, pos_ouvinte, volume_base_config):
    if not som or not pos_ouvinte:
        return
    try:
        distancia = pos_fonte.distance_to(pos_ouvinte)
    except ValueError:
        distancia = 0 
    if distancia > MAX_DISTANCIA_SOM_AUDIVEL:
        return 
    fator_distancia = 1.0 - (distancia / MAX_DISTANCIA_SOM_AUDIVEL)
    volume_base = volume_base_config * fator_distancia
    vetor_para_som = pos_fonte - pos_ouvinte
    dist_x = vetor_para_som.x
    fator_pan = max(-1.0, min(1.0, dist_x / PANNING_RANGE_SOM))
    left_percent = (1.0 - fator_pan) / 2.0
    right_percent = (1.0 + fator_pan) / 2.0
    left_vol = volume_base * left_percent
    right_vol = volume_base * right_percent
    channel = pygame.mixer.find_channel() 
    if channel:
        channel.set_volume(left_vol, right_vol)
        channel.play(som)

# Referência global para o grupo de explosões
grupo_explosoes_ref = None
def set_global_ship_references(explosions_group):
    global grupo_explosoes_ref
    grupo_explosoes_ref = explosions_group

# Nave Auxiliar
class NaveAuxiliar(pygame.sprite.Sprite):
    def __init__(self, owner_nave, offset_pos):
        super().__init__(); self.owner = owner_nave; self.offset_pos = offset_pos; self.tamanho = 15
        self.imagem_original = pygame.Surface((self.tamanho + 5, self.tamanho + 5), pygame.SRCALPHA)
        centro = (self.tamanho + 5) / 2; ponto_topo = (centro, centro - self.tamanho / 2); ponto_base_esq = (centro - self.tamanho / 2, centro + self.tamanho / 2); ponto_base_dir = (centro + self.tamanho / 2, centro + self.tamanho / 2)
        pygame.draw.polygon(self.imagem_original, VERDE_AUXILIAR, [ponto_topo, ponto_base_esq, ponto_base_dir])
        self.posicao = self.owner.posicao + self.offset_pos.rotate(-self.owner.angulo); self.rect = self.imagem_original.get_rect(center=self.posicao)
        self.angulo = self.owner.angulo; self.alvo_atual = None; self.distancia_tiro = 600; self.cooldown_tiro = 1000; self.ultimo_tiro_tempo = 0

    # --- INÍCIO DA MODIFICAÇÃO (Assinatura e lógica Online) ---
    def update(self, lista_alvos, grupo_projeteis_destino, estado_jogo_atual, nave_player_ref, client_socket=None, online_players={}, online_npcs={}, pos_ouvinte=None): # <-- MODIFICADO
        """
        lista_alvos: (Offline) lista de sprites. (Online) Vazio.
        online_players/online_npcs: (Online) Dicionários de estado.
        pos_ouvinte: (Offline) Posição da câmera/jogador.
        """
        parar_ataque = (self.owner == nave_player_ref and estado_jogo_atual == "GAME_OVER")
        offset_rotacionado = self.offset_pos.rotate(-self.owner.angulo); posicao_alvo_seguir = self.owner.posicao + offset_rotacionado
        self.posicao = self.posicao.lerp(posicao_alvo_seguir, 0.1) 
        
        self.alvo_atual = None 

        if client_socket is None: # --- OFFLINE LOGIC ---
            if not parar_ataque:
                alvo_do_dono = self.owner.alvo_selecionado # This is a SPRITE
                
                if alvo_do_dono and alvo_do_dono.groups(): # Check if sprite is alive
                    try:
                        dist = self.posicao.distance_to(alvo_do_dono.posicao)
                        if dist < self.distancia_tiro: 
                            self.alvo_atual = alvo_do_dono
                    except ValueError:
                        self.alvo_atual = None
                
                if self.alvo_atual:
                    try: 
                        direcao = (self.alvo_atual.posicao - self.posicao).normalize()
                        self.angulo = direcao.angle_to(pygame.math.Vector2(0, -1))
                    except ValueError: 
                        self.angulo = self.owner.angulo 
                    
                    agora = pygame.time.get_ticks()
                    if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
                        self.ultimo_tiro_tempo = agora
                        radianos = math.radians(self.angulo)
                        
                        # --- INÍCIO: CORREÇÃO (Bug Tiro Auxiliar) ---
                        proj = ProjetilTeleguiadoJogador(self.posicao.x, self.posicao.y, radianos, 
                                                       self.owner.nivel_dano, # <--- CORRIGIDO
                                                       owner_nave=self.owner, 
                                                       alvo_sprite=self.alvo_atual)
                        # --- FIM: CORREÇÃO ---
                        
                        grupo_projeteis_destino.add(proj)
                        
                        # --- MODIFICADO: Usa pos_ouvinte ---
                        ouvinte_real = pos_ouvinte if pos_ouvinte is not None else nave_player_ref.posicao
                        tocar_som_posicional(s.SOM_TIRO_PLAYER, self.posicao, ouvinte_real, VOLUME_BASE_TIRO_PLAYER)
                else:
                    self.angulo = self.owner.angulo
            else: 
                self.angulo = self.owner.angulo
        
        else: # --- ONLINE LOGIC (VISUAL ONLY) ---
            alvo_do_dono_id = self.owner.alvo_selecionado # This is a STRING ID (e.g., 'npc_119')
            
            alvo_pos = None # Posição do alvo
            
            if alvo_do_dono_id:
                # Tentar encontrar a posição do alvo
                if alvo_do_dono_id in online_npcs:
                    alvo_state = online_npcs.get(alvo_do_dono_id)
                    # Verifica se o estado existe e se o alvo está vivo
                    if alvo_state and alvo_state.get('hp', 0) > 0:
                        alvo_pos = pygame.math.Vector2(alvo_state['x'], alvo_state['y'])
                
                elif alvo_do_dono_id in online_players:
                    alvo_state = online_players.get(alvo_do_dono_id)
                    # Verifica se o estado existe e se o alvo está vivo
                    if alvo_state and alvo_state.get('hp', 0) > 0:
                         alvo_pos = pygame.math.Vector2(alvo_state['x'], alvo_state['y'])
                
                # Se não encontrou (morreu ou desapareceu), limpa o alvo do dono (localmente)
                if alvo_pos is None:
                    self.owner.alvo_selecionado = None 
            
            # Agora, usa a 'alvo_pos' (que é um Vector2 ou None) para mirar
            if alvo_pos:
                try: 
                    direcao = (alvo_pos - self.posicao).normalize()
                    self.angulo = direcao.angle_to(pygame.math.Vector2(0, -1))
                except ValueError: 
                    self.angulo = self.owner.angulo
            else:
                # Se não tem alvo, apenas alinha com o dono
                self.angulo = self.owner.angulo
        # --- FIM DA MODIFICAÇÃO ---

        self.rect.center = self.posicao
        
    def desenhar(self, surface, camera):
        imagem_rotacionada = pygame.transform.rotate(self.imagem_original, self.angulo); rect_desenho = imagem_rotacionada.get_rect(center = self.posicao)
        surface.blit(imagem_rotacionada, camera.apply(rect_desenho))

# Classe Base para Naves
class Nave(pygame.sprite.Sprite):
    POSICOES_AUXILIARES = [pygame.math.Vector2(-40, 20), pygame.math.Vector2(40, 20), pygame.math.Vector2(-50, -10), pygame.math.Vector2(50, -10)]
    
    def __init__(self, x, y, cor=AZUL_NAVE, nome="Nave"):
        super().__init__()
        self.nome = nome; self.posicao = pygame.math.Vector2(x, y); self.largura_base = 30; self.altura = 30; self.cor = cor
        self.velocidade_rotacao = VELOCIDADE_ROTACAO_NAVE; self.angulo = 0.0; self.velocidade_movimento_base = 4
        
        # --- MUDANÇA: Adiciona tempo_fim_congelamento ---
        self.tempo_fim_congelamento = 0
        
        tamanho_surface = max(self.largura_base, self.altura) + 10; self.imagem_original = pygame.Surface((tamanho_surface, tamanho_surface), pygame.SRCALPHA)
        centro_x = tamanho_surface / 2; centro_y = tamanho_surface / 2; ponto_topo = (centro_x, centro_y - self.altura / 2); ponto_base_esq = (centro_x - self.largura_base / 2, centro_y + self.altura / 2); ponto_base_dir = (centro_x + self.largura_base / 2, centro_y + self.altura / 2)
        pygame.draw.polygon(self.imagem_original, self.cor, [ponto_topo, ponto_base_esq, ponto_base_dir])
        ponta_largura = 4; ponta_altura = 8; pygame.draw.rect(self.imagem_original, PONTA_NAVE, (ponto_topo[0] - ponta_largura / 2, ponto_topo[1] - ponta_altura, ponta_largura, ponta_altura))
        
        self.pontos_upgrade_disponiveis = 0
        self.total_upgrades_feitos = 0
        self._pontos_acumulados_para_upgrade = 0 
        self._limiares = PONTOS_LIMIARES_PARA_UPGRADE[:] 
        self._pontos_no_limiar = PONTOS_SCORE_PARA_MUDAR_LIMIAR[:] 
        self._limiar_pontos_atual = self._limiares[0] 
        self._indice_limiar = 0 
        
        self.image = self.imagem_original; self.rect = pygame.Rect(x, y, self.largura_base * 0.8, self.altura * 0.8); self.rect.center = self.posicao
        self.cooldown_tiro = 250; self.ultimo_tiro_tempo = 0; self.pontos = 0; self.nivel_motor = 1; self.nivel_dano = 1; self.nivel_max_vida = 1; self.nivel_escudo = 0
        
        self.nivel_aux = 0 
        
        # --- INÍCIO: MODIFICAÇÃO (Usa VIDA_POR_NIVEL) ---
        self.max_vida = VIDA_POR_NIVEL[self.nivel_max_vida] # 4 + self.nivel_max_vida
        # --- FIM: MODIFICAÇÃO ---
        self.vida_atual = self.max_vida
        self.velocidade_movimento_base = 4 + (self.nivel_motor * 0.5) 
        
        self.quer_virar_esquerda = False; self.quer_virar_direita = False; self.quer_mover_frente = False; self.quer_mover_tras = False; self.quer_atirar = False
        
        self.alvo_selecionado = None; self.posicao_alvo_mouse = None; self.tempo_barra_visivel = 2000; self.ultimo_hit_tempo = 0
        
        # --- INÍCIO DA MODIFICAÇÃO (Recompensa por Abate) ---
        self.ultimo_atacante = None # Armazena quem deu o último golpe
        # --- FIM DA MODIFICAÇÃO ---

        self.mostrar_escudo_fx = False; self.angulo_impacto_rad_pygame = 0; self.tempo_escudo_fx = 0; self.rastro_particulas = []
        self.tempo_fim_lentidao = 0; self.lista_todas_auxiliares = []; self.grupo_auxiliares_ativos = pygame.sprite.Group()
        for pos in self.POSICOES_AUXILIARES: self.lista_todas_auxiliares.append(NaveAuxiliar(self, pos))
        
        self.tempo_spawn_protecao_input = 0
        
        self.esta_regenerando = False
        self.nave_regeneradora_sprite = pygame.sprite.GroupSingle()
        self.ultimo_tick_regeneracao = 0
        
    def update(self, grupo_projeteis_destino, camera=None): pass
    
    def parar_regeneracao(self):
        """Para a regeneração e remove a nave lilás."""
        if self.esta_regenerando:
            self.esta_regenerando = False
            for sprite in self.nave_regeneradora_sprite:
                sprite.kill() 
            
    def iniciar_regeneracao(self, grupo_efeitos_visuais):
        """Inicia a regeneração se as condições forem válidas."""
        if self.vida_atual >= self.max_vida:
            return
        if self.esta_regenerando:
            return
            
        # --- INÍCIO DA MODIFICAÇÃO (Correção Bug 3) ---
        # NÃO inicia a regeneração (visual) se o bot/player tiver intenção de se mover.
        if self.quer_mover_frente or self.quer_mover_tras or self.posicao_alvo_mouse is not None:
            return
        # --- FIM DA MODIFICAÇÃO ---
            
        print(f"[{self.nome}] Iniciando regeneração...")
        self.esta_regenerando = True
        self.ultimo_tick_regeneracao = pygame.time.get_ticks()
        
        nova_nave_regen = NaveRegeneradora(self)
        self.nave_regeneradora_sprite.add(nova_nave_regen)
        if grupo_efeitos_visuais is not None:
            grupo_efeitos_visuais.add(nova_nave_regen)

    def toggle_regeneracao(self, grupo_efeitos_visuais):
        """Chamado pelo clique do botão ou tecla 'R'."""
        if self.esta_regenerando:
            self.parar_regeneracao()
        else:
            self.iniciar_regeneracao(grupo_efeitos_visuais)

    def update_regeneracao(self):
        """Controla a lógica de regeneração a cada frame."""
        if not self.esta_regenerando:
            return
        if self.quer_mover_frente or self.quer_mover_tras or self.posicao_alvo_mouse is not None:
            self.parar_regeneracao()
            return
        if self.vida_atual >= self.max_vida:
            self.vida_atual = self.max_vida 
            self.parar_regeneracao()
            return
            
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tick_regeneracao > REGEN_TICK_RATE:
            self.ultimo_tick_regeneracao = agora
            self.vida_atual = min(self.max_vida, self.vida_atual + REGEN_POR_TICK)
            self.ultimo_hit_tempo = agora 
            print(f"[{self.nome}] Regenerou! Vida: {self.vida_atual:.1f}/{self.max_vida}") # Log
            
    def rotacionar(self):
        angulo_alvo = None
        agora = pygame.time.get_ticks()
        # --- MUDANÇA: Verifica congelamento ---
        if agora < self.tempo_fim_congelamento:
            return 
        
        if self.alvo_selecionado:
            if not self.alvo_selecionado.groups(): self.alvo_selecionado = None
            elif self.posicao.distance_to(self.alvo_selecionado.posicao) > MAX_TARGET_LOCK_DISTANCE: self.alvo_selecionado = None
            else:
                try:
                    direcao_vetor = (self.alvo_selecionado.posicao - self.posicao)
                    if direcao_vetor.length() > 0: radianos = math.atan2(direcao_vetor.y, direcao_vetor.x); angulo_alvo = -math.degrees(radianos) - 90
                except ValueError: pass
        elif self.posicao_alvo_mouse:
            if self.posicao.distance_to(self.posicao_alvo_mouse) > 5.0:
                try:
                    direcao_vetor = (self.posicao_alvo_mouse - self.posicao)
                    if direcao_vetor.length() > 0: radianos = math.atan2(direcao_vetor.y, direcao_vetor.x); angulo_alvo = -math.degrees(radianos) - 90
                except ValueError: pass
                
        if angulo_alvo is not None: self.angulo = angulo_alvo
        elif self.quer_virar_esquerda: self.angulo += self.velocidade_rotacao
        elif self.quer_virar_direita: self.angulo -= self.velocidade_rotacao
        self.angulo %= 360
        
    def mover(self):
        agora = pygame.time.get_ticks()
        # --- MUDANÇA: Verifica congelamento ---
        if agora < self.tempo_fim_congelamento:
            self.posicao_alvo_mouse = None # Para o movimento
            return
        
        velocidade_atual = self.velocidade_movimento_base
        if agora < self.tempo_fim_lentidao: velocidade_atual *= 0.4
        
        nova_pos = pygame.math.Vector2(self.posicao.x, self.posicao.y); movendo_frente = False
        
        if self.quer_mover_frente or self.quer_mover_tras:
            radianos = math.radians(self.angulo)
            if self.quer_mover_frente: nova_pos.x += -math.sin(radianos) * velocidade_atual; nova_pos.y += -math.cos(radianos) * velocidade_atual; movendo_frente = True
            if self.quer_mover_tras: nova_pos.x -= -math.sin(radianos) * velocidade_atual; nova_pos.y -= -math.cos(radianos) * velocidade_atual
        elif self.posicao_alvo_mouse:
            distancia = self.posicao.distance_to(self.posicao_alvo_mouse)
            if distancia > 5.0:
                try:
                    direcao = (self.posicao_alvo_mouse - self.posicao).normalize(); nova_pos = self.posicao + direcao * velocidade_atual; movendo_frente = True
                    if self.posicao.distance_to(self.posicao_alvo_mouse) < velocidade_atual: nova_pos = self.posicao_alvo_mouse; self.posicao_alvo_mouse = None
                except ValueError: nova_pos = self.posicao
            else: nova_pos = self.posicao_alvo_mouse; self.posicao_alvo_mouse = None
            
        meia_largura = self.largura_base / 2; meia_altura = self.altura / 2
        # --- INÍCIO: CORREÇÃO (Bug Limite do Mapa) ---
        # Lê o valor ATUAL de s.MAP_WIDTH, que é modificado pelo main.py
        nova_pos.x = max(meia_largura, min(nova_pos.x, s.MAP_WIDTH - meia_largura)); 
        nova_pos.y = max(meia_altura, min(nova_pos.y, s.MAP_HEIGHT - meia_altura));
        # --- FIM: CORREÇÃO ---
        self.posicao = nova_pos; self.rect.center = self.posicao
        
        if self.nivel_motor == MAX_NIVEL_MOTOR and movendo_frente:
            agora = pygame.time.get_ticks(); radianos_oposto = math.radians(self.angulo + 180); offset_rastro = self.altura * 0.6
            pos_rastro_x = self.posicao.x + (-math.sin(radianos_oposto) * offset_rastro); pos_rastro_y = self.posicao.y + (-math.cos(radianos_oposto) * offset_rastro)
            self.rastro_particulas.append([pos_rastro_x, pos_rastro_y, agora])
            if len(self.rastro_particulas) > RASTRO_MAX_PARTICULAS: self.rastro_particulas.pop(0)
            
    def criar_projetil(self):
        radianos = math.radians(self.angulo); offset_ponta = self.altura / 2 + 10
        pos_x = self.posicao.x + (-math.sin(radianos) * offset_ponta); pos_y = self.posicao.y + (-math.cos(radianos) * offset_ponta)
        
        # --- INÍCIO: CORREÇÃO (Bug Tiro Principal) ---
        if self.alvo_selecionado and self.alvo_selecionado.groups():
            return ProjetilTeleguiadoJogador(pos_x, pos_y, radianos, 
                                           self.nivel_dano, # <--- CORRIGIDO
                                           owner_nave=self, 
                                           alvo_sprite=self.alvo_selecionado)
        else:
            return Projetil(pos_x, pos_y, radianos, self.nivel_dano, owner_nave=self) # <--- CORRIGIDO
        # --- FIM: CORREÇÃO ---
    
    def lidar_com_tiros(self, grupo_destino, pos_ouvinte=None): # <-- MODIFICADO
        agora = pygame.time.get_ticks() 
        # --- MUDANÇA: Verifica congelamento ---
        if agora < self.tempo_fim_congelamento:
            return 
        
        if self.quer_atirar or self.alvo_selecionado:
            if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
                self.ultimo_tiro_tempo = agora 
                grupo_destino.add(self.criar_projetil())
                
                # --- MODIFICADO: Usa pos_ouvinte ---
                ouvinte_real = pos_ouvinte if pos_ouvinte is not None else self.posicao
                tocar_som_posicional(s.SOM_TIRO_PLAYER, self.posicao, ouvinte_real, VOLUME_BASE_TIRO_PLAYER)
    
    def foi_atingido(self, dano, estado_jogo_atual, proj_pos=None, atacante=None): # <-- MODIFICADO
        if self.esta_regenerando:
            self.parar_regeneracao()
        
        if self.vida_atual <= 0 and estado_jogo_atual == "GAME_OVER": return False
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_hit_tempo < 150: return False
        
        # --- INÍCIO DA MODIFICAÇÃO (Recompensa por Abate) ---
        if atacante:
            self.ultimo_atacante = atacante # Registra o atacante
        # --- FIM DA MODIFICAÇÃO ---

        reducao_percent = min(self.nivel_escudo * REDUCAO_DANO_POR_NIVEL, 75)
        dano_reduzido = dano * (1 - reducao_percent / 100.0)
        
        vida_antes = self.vida_atual
        self.vida_atual -= dano_reduzido
        self.ultimo_hit_tempo = agora
        
        if vida_antes > 0:
            if self.nivel_escudo >= s.MAX_NIVEL_ESCUDO:
                self.mostrar_escudo_fx = True
                self.tempo_escudo_fx = agora
                if proj_pos:
                     vetor_para_origem = proj_pos - self.posicao
                     if vetor_para_origem.length() > 0: self.angulo_impacto_rad_pygame = math.atan2(vetor_para_origem.y, vetor_para_origem.x)
                     else: self.angulo_impacto_rad_pygame = math.radians(90 - self.angulo)
                else: self.angulo_impacto_rad_pygame = math.radians(90 - self.angulo)
                
        if self.vida_atual <= 0 and vida_antes > 0:
            print(f"[{self.nome}] MORREU!")
            if grupo_explosoes_ref is not None: explosao = Explosao(self.rect.center, self.altura // 2 + 10); grupo_explosoes_ref.add(explosao)
            return True
        return False

    def aplicar_lentidao(self, duracao_ms):
        agora = pygame.time.get_ticks(); self.tempo_fim_lentidao = max(self.tempo_fim_lentidao, agora + duracao_ms)
        print(f"[{self.nome}] LENTIDÃO aplicada/estendida por {duracao_ms}ms!")
        
    def aplicar_congelamento(self, duracao_ms):
        agora = pygame.time.get_ticks()
        self.tempo_fim_congelamento = max(self.tempo_fim_congelamento, agora + duracao_ms)
        print(f"[{self.nome}] CONGELADO por {duracao_ms}ms!")
    
    def ganhar_pontos(self, quantidade):
        if quantidade <= 0:
            return
        self.pontos += quantidade 
        self._pontos_acumulados_para_upgrade += quantidade
        while self._pontos_acumulados_para_upgrade >= self._limiar_pontos_atual:
            self.pontos_upgrade_disponiveis += 1
            self._pontos_acumulados_para_upgrade -= self._limiar_pontos_atual 
            print(f"[{self.nome}] Ganhou 1 Ponto de Upgrade! (Total: {self.pontos_upgrade_disponiveis})")
            pontos_totais_aproximados = self.pontos 
            if self._indice_limiar < len(self._pontos_no_limiar) and \
               pontos_totais_aproximados >= self._pontos_no_limiar[self._indice_limiar]:
                self._indice_limiar += 1
                if self._indice_limiar < len(self._limiares): # Proteção
                    self._limiar_pontos_atual = self._limiares[self._indice_limiar]
                    print(f"[{self.nome}] Próximo Ponto de Upgrade a cada {self._limiar_pontos_atual} pontos de score.")
        
    def comprar_auxiliar(self):
        num_ativos = len(self.grupo_auxiliares_ativos)
        if num_ativos < len(self.lista_todas_auxiliares):
            aux_para_adicionar = self.lista_todas_auxiliares[num_ativos]
            offset_rotacionado = aux_para_adicionar.offset_pos.rotate(-self.angulo)
            posicao_correta_atual = self.posicao + offset_rotacionado
            aux_para_adicionar.posicao = posicao_correta_atual
            aux_para_adicionar.rect.center = posicao_correta_atual 
            aux_para_adicionar.angulo = self.angulo 
            self.grupo_auxiliares_ativos.add(aux_para_adicionar)
            return True 
        else:
            return False
    
    def comprar_upgrade(self, tipo):
        if self.pontos_upgrade_disponiveis <= 0:
            print(f"[{self.nome}] Sem Pontos de Upgrade disponíveis!")
            return False
        if self.total_upgrades_feitos >= MAX_TOTAL_UPGRADES:
            print(f"[{self.nome}] Limite máximo de {MAX_TOTAL_UPGRADES} upgrades atingido!")
            return False

        comprou = False
        custo_upgrade_atual = 1
        
        if tipo == "motor":
            if self.nivel_motor < MAX_NIVEL_MOTOR:
                if self.pontos_upgrade_disponiveis >= custo_upgrade_atual:
                    self.pontos_upgrade_disponiveis -= custo_upgrade_atual
                    self.total_upgrades_feitos += 1
                    self.nivel_motor += 1
                    self.velocidade_movimento_base = 4 + (self.nivel_motor * 0.5) 
                    print(f"[{self.nome}] Motor comprado! Nível {self.nivel_motor}. ({self.pontos_upgrade_disponiveis} Pts Restantes)")
                    comprou = True
                else: print(f"[{self.nome}] Pontos insuficientes!") 
            else: print(f"[{self.nome}] Nível máximo de motor atingido!")
        
        elif tipo == "dano":
            if self.nivel_dano < MAX_NIVEL_DANO:
                if self.pontos_upgrade_disponiveis >= custo_upgrade_atual:
                    self.pontos_upgrade_disponiveis -= custo_upgrade_atual
                    self.total_upgrades_feitos += 1
                    self.nivel_dano += 1
                    print(f"[{self.nome}] Dano comprado! Nível {self.nivel_dano}. ({self.pontos_upgrade_disponiveis} Pts Restantes)")
                    comprou = True
                else: print(f"[{self.nome}] Pontos insuficientes!")
            else: print(f"[{self.nome}] Nível máximo de dano atingido!")
        
        elif tipo == "auxiliar":
            num_ativos = len(self.grupo_auxiliares_ativos)
            max_aux = len(self.lista_todas_auxiliares) 
            if num_ativos < max_aux:
                custo_atual_aux = CUSTOS_AUXILIARES[num_ativos] 
                if self.pontos_upgrade_disponiveis >= custo_atual_aux:
                    if self.comprar_auxiliar(): 
                        self.pontos_upgrade_disponiveis -= custo_atual_aux 
                        self.total_upgrades_feitos += 1 
                        self.nivel_aux += 1 # Sincroniza o contador
                        print(f"[{self.nome}] Auxiliar comprado por {custo_atual_aux} pts! ({self.pontos_upgrade_disponiveis} Pts Restantes)")
                        comprou = True
                else:
                    print(f"[{self.nome}] Pontos insuficientes para Auxiliar! Custo: {custo_atual_aux} Pts. Você tem: {self.pontos_upgrade_disponiveis}")
            else: 
                print(f"[{self.nome}] Nível máximo de auxiliares atingido!")
        
        elif tipo == "max_health":
            # --- INÍCIO: CORREÇÃO CRASH (Nível Máx. Vida) ---
            # Verifica se já estamos no nível 5 (índice 5 da lista)
            if self.nivel_max_vida >= len(VIDA_POR_NIVEL) - 1:
                print(f"[{self.nome}] Nível máximo de Vida Máx. atingido!")
                return False # Retorna Falso para o bot saber que falhou
            # --- FIM: CORREÇÃO ---
            
            if self.pontos_upgrade_disponiveis >= custo_upgrade_atual:
                self.pontos_upgrade_disponiveis -= custo_upgrade_atual
                self.total_upgrades_feitos += 1
                self.nivel_max_vida += 1
                # --- INÍCIO: MODIFICAÇÃO (Usa VIDA_POR_NIVEL) ---
                self.max_vida = VIDA_POR_NIVEL[self.nivel_max_vida] # 4 + self.nivel_max_vida
                # --- FIM: MODIFICAÇÃO ---
                self.vida_atual += 1 
                self.ultimo_hit_tempo = pygame.time.get_ticks() 
                print(f"[{self.nome}] Vida Máx. aumentada! Nível {self.nivel_max_vida}. ({self.pontos_upgrade_disponiveis} Pts Restantes)")
                comprou = True
            else: print(f"[{self.nome}] Pontos insuficientes!")
        
        elif tipo == "escudo":
            if self.nivel_escudo < MAX_NIVEL_ESCUDO:
                if self.pontos_upgrade_disponiveis >= custo_upgrade_atual:
                    self.pontos_upgrade_disponiveis -= custo_upgrade_atual
                    self.total_upgrades_feitos += 1
                    self.nivel_escudo += 1
                    print(f"[{self.nome}] Escudo comprado! Nível {self.nivel_escudo}. ({self.pontos_upgrade_disponiveis} Pts Restantes)")
                    comprou = True
                else: print(f"[{self.nome}] Pontos insuficientes!")
            else: print(f"[{self.nome}] Nível máximo de escudo atingido!")
            
        return comprou

    def coletar_vida(self, quantidade):
        return False
        
    # --- MUDANÇA: Adicionado client_socket=None ---
    def desenhar(self, surface, camera, client_socket=None):
        agora = pygame.time.get_ticks(); particulas_vivas = []
        for particula in self.rastro_particulas:
            pos_x, pos_y, tempo_criacao = particula; idade = agora - tempo_criacao
            if idade < RASTRO_DURACAO:
                particulas_vivas.append(particula); progresso = idade / RASTRO_DURACAO; tamanho_atual = max(1, int(RASTRO_TAMANHO_INICIAL * (1 - progresso)))
                alpha = int(200 * (1 - progresso)); cor_atual = (*COR_RASTRO_MOTOR, alpha)
                pos_tela_centro = camera.apply(pygame.Rect(pos_x, pos_y, 0, 0)).topleft; raio_desenho = tamanho_atual // 2
                temp_surf = pygame.Surface((tamanho_atual, tamanho_atual), pygame.SRCALPHA); pygame.draw.circle(temp_surf, cor_atual, (raio_desenho, raio_desenho), raio_desenho)
                surface.blit(temp_surf, (pos_tela_centro[0] - raio_desenho, pos_tela_centro[1] - raio_desenho))
        self.rastro_particulas = particulas_vivas
        
        self.image = pygame.transform.rotate(self.imagem_original, self.angulo); rect_desenho = self.image.get_rect(center = self.posicao)
        
        # --- MUDANÇA: Aplica efeitos de status (lento/congelado) ---
        if client_socket: # Só aplica efeitos visuais se estiver online
            # (Os tempos são atualizados pelo main.py a partir da rede)
            if agora < self.tempo_fim_congelamento:
                self.image.fill(AZUL_CONGELANTE, special_flags=pygame.BLEND_RGB_ADD)
            elif agora < self.tempo_fim_lentidao:
                self.image.fill(ROXO_TIRO_LENTO, special_flags=pygame.BLEND_RGB_MULT)
        else: # Lógica offline
             if agora < self.tempo_fim_congelamento:
                self.image.fill(AZUL_CONGELANTE, special_flags=pygame.BLEND_RGB_ADD)
             elif agora < self.tempo_fim_lentidao:
                self.image.fill(ROXO_TIRO_LENTO, special_flags=pygame.BLEND_RGB_MULT)
        # --- FIM MUDANÇA ---

        surface.blit(self.image, camera.apply(rect_desenho))
        
        if self.mostrar_escudo_fx:
            agora = pygame.time.get_ticks()
            if agora - self.tempo_escudo_fx < DURACAO_FX_ESCUDO:
                raio_escudo = self.altura * 0.8 + 10; largura_arco_rad = math.radians(90); cor_fx_com_alpha = COR_ESCUDO_FX
                
                angulo_central_invertido = -self.angulo_impacto_rad_pygame
                angulo_inicio_pygame_rad = angulo_central_invertido - (largura_arco_rad / 2)
                angulo_fim_pygame_rad = angulo_central_invertido + (largura_arco_rad / 2)
                
                rect_escudo_mundo = pygame.Rect(0, 0, raio_escudo * 2, raio_escudo * 2); rect_escudo_mundo.center = self.posicao; rect_escudo_tela = camera.apply(rect_escudo_mundo)
                temp_surface = pygame.Surface(rect_escudo_tela.size, pygame.SRCALPHA)
                try: pygame.draw.arc(temp_surface, cor_fx_com_alpha, (0, 0, rect_escudo_tela.width, rect_escudo_tela.height), angulo_inicio_pygame_rad, angulo_fim_pygame_rad, width=3); surface.blit(temp_surface, rect_escudo_tela.topleft)
                except ValueError: pass
            else: self.mostrar_escudo_fx = False
            
    def desenhar_vida(self, surface, camera):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_hit_tempo < self.tempo_barra_visivel:
            LARGURA_BARRA = 40; ALTURA_BARRA = 5; OFFSET_Y = 30
            pos_x_mundo = self.posicao.x - LARGURA_BARRA / 2; pos_y_mundo = self.posicao.y - OFFSET_Y
            percentual = max(0, self.vida_atual / self.max_vida); largura_vida_atual = LARGURA_BARRA * percentual
            rect_fundo_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, LARGURA_BARRA, ALTURA_BARRA); rect_vida_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, largura_vida_atual, ALTURA_BARRA)
            pygame.draw.rect(surface, VERMELHO_VIDA_FUNDO, camera.apply(rect_fundo_mundo)); pygame.draw.rect(surface, VERDE_VIDA, camera.apply(rect_vida_mundo))

    def desenhar_nome(self, surface, camera):
        """ Desenha o nome da nave acima da barra de vida. """
        try:
            OFFSET_Y_VIDA_TOPO = 30
            PADDING_ACIMA_VIDA = 3 
            pos_y_bottom_mundo = (self.posicao.y - OFFSET_Y_VIDA_TOPO) - PADDING_ACIMA_VIDA
            pos_x_center_mundo = self.posicao.x
            
            texto_surf = FONT_NOME_JOGADOR.render(self.nome, True, BRANCO)
            texto_rect_mundo = texto_surf.get_rect(midbottom=(pos_x_center_mundo, pos_y_bottom_mundo))
            surface.blit(texto_surf, camera.apply(texto_rect_mundo))
            
        except pygame.error as e:
            print(f"[ERRO] Falha ao renderizar nome '{self.nome}': {e}")
        except AttributeError:
            pass
            
# --- Classe do Jogador ---
class Player(Nave):
    def __init__(self, x, y, nome="Jogador"):
        super().__init__(x, y, cor=AZUL_NAVE, nome=nome)
        self.invencivel = False

    def foi_atingido(self, dano, estado_jogo_atual, proj_pos=None, atacante=None): # <-- MODIFICADO
        if self.invencivel:
            return False 
        # --- MODIFICADO: Passa o atacante para a classe base ---
        return super().foi_atingido(dano, estado_jogo_atual, proj_pos, atacante=atacante)

    # --- INÍCIO: MODIFICAÇÃO (Aceitar estado_jogo) ---
    def update(self, grupo_projeteis_jogador, camera, client_socket=None, pos_ouvinte=None, estado_jogo="JOGANDO"): # <-- MODIFICADO
    # --- FIM: MODIFICAÇÃO ---
        if client_socket is None:
            # --- INÍCIO DA CORREÇÃO ---
            # O 'camera' DEVE ser passado para processar_input_humano
            self.processar_input_humano(camera, estado_jogo) # <-- MODIFICADO
            # --- FIM DA CORREÇÃO ---
            self.update_regeneracao()
            self.rotacionar()
            self.mover()
            
            # --- INÍCIO: CORREÇÃO (Trava de Fogo Amigo no Lobby) ---
            # Só permite atirar se estiver no PVE (JOGANDO) ou na partida PVP (PVP_PLAYING)
            if estado_jogo == "JOGANDO" or estado_jogo == "PVP_PLAYING":
                self.lidar_com_tiros(grupo_projeteis_jogador, pos_ouvinte if pos_ouvinte is not None else self.posicao)
            # --- FIM: CORREÇÃO ---
        else:
            self.quer_virar_esquerda = False
            self.quer_virar_direita = False
            self.quer_mover_frente = False
            self.quer_mover_tras = False
            self.quer_atirar = False
            
            # --- MUDANÇA: A lógica de regeneração (visual) agora é chamada pelo main.py
            #            baseado no estado da rede, então não precisa ser chamada aqui.
            pass
        

    # --- INÍCIO: MODIFICAÇÃO (Aceitar estado_jogo) ---
    def processar_input_humano(self, camera, estado_jogo="JOGANDO"):
        """
        Lê teclado e mouse para controlar a nave.
        Bloqueia controles se estiver na Loja, Terminal ou Pré-Partida.
        """
        agora = pygame.time.get_ticks()

        # --- TRAVA DE SEGURANÇA (LOJA/TERMINAL/PRE_MATCH) ---
        # Se o jogador estiver nestes estados, ele não pode mover a nave nem atirar.
        # Isso permite que o jogo continue rodando ao fundo sem acidentes.
        if estado_jogo in ["PVP_PRE_MATCH", "LOJA", "TERMINAL"]:
            self.quer_virar_esquerda = False
            self.quer_virar_direita = False
            self.quer_mover_frente = False
            self.quer_mover_tras = False
            self.quer_atirar = False
            self.posicao_alvo_mouse = None
            return # Sai da função aqui, ignorando o resto dos inputs
        # -----------------------------------------------------

        teclas = pygame.key.get_pressed()
        self.quer_virar_esquerda = teclas[pygame.K_a] or teclas[pygame.K_LEFT]
        self.quer_virar_direita = teclas[pygame.K_d] or teclas[pygame.K_RIGHT]
        self.quer_mover_frente = teclas[pygame.K_w] or teclas[pygame.K_UP]
        self.quer_mover_tras = teclas[pygame.K_s] or teclas[pygame.K_DOWN]
        self.quer_atirar = teclas[pygame.K_SPACE]

        if agora > self.tempo_spawn_protecao_input:
            mouse_buttons = pygame.mouse.get_pressed()
            
            if mouse_buttons[0]:
                mouse_pos_tela = pygame.mouse.get_pos()
                # Evita mover se clicar nos botões do HUD
                if not ui.RECT_BOTAO_UPGRADE_HUD.collidepoint(mouse_pos_tela) and not ui.RECT_BOTAO_REGEN_HUD.collidepoint(mouse_pos_tela):
                    mouse_pos_mundo = camera.get_mouse_world_pos(mouse_pos_tela)
                    self.posicao_alvo_mouse = mouse_pos_mundo
                    self.quer_mover_frente = False 
                    self.quer_mover_tras = False
            
            # Se usar teclado, cancela o alvo do mouse
            if self.quer_mover_frente or self.quer_mover_tras:
                self.posicao_alvo_mouse = None
        
        else:
            # Proteção de spawn
            self.posicao_alvo_mouse = None
            pygame.mouse.get_pressed() # Limpa buffer

# --- Classe do Bot Aliado ---
class NaveBot(Nave):
    def __init__(self, x, y, dificuldade="Normal"):
        super().__init__(x, y, cor=LARANJA_BOT, nome=f"Bot {random.randint(1, 99)}")
        
        self.cerebro = BotAI(self) 
        
        if dificuldade == "Dificil":
            self.nivel_motor = random.randint(1, MAX_NIVEL_MOTOR)
            self.velocidade_movimento_base = 4 + (self.nivel_motor * 0.5) 
            self.nivel_dano = random.randint(1, MAX_NIVEL_DANO)
            self.nivel_escudo = random.randint(0, MAX_NIVEL_ESCUDO)
            max_spawn_vida_lvl = 3; self.nivel_max_vida = random.randint(1, max_spawn_vida_lvl); 
            # --- INÍCIO: MODIFICAÇÃO (Usa VIDA_POR_NIVEL) ---
            self.max_vida = VIDA_POR_NIVEL[self.nivel_max_vida] # 4 + self.nivel_max_vida
            # --- FIM: MODIFICAÇÃO ---
            self.vida_atual = self.max_vida
            max_aux = len(self.lista_todas_auxiliares); num_auxiliares = random.randint(0, max_aux)
            if num_auxiliares > 0:
                for _ in range(num_auxiliares): 
                    self.comprar_auxiliar() 
                    self.nivel_aux += 1 
    
    def foi_atingido(self, dano, estado_jogo_atual, proj_pos=None, atacante=None): # <-- MODIFICADO
        vida_antes = self.vida_atual
        
        # --- MODIFICADO: Passa o atacante para a classe base ---
        morreu = super().foi_atingido(dano, estado_jogo_atual, proj_pos, atacante=atacante)

        if morreu:
            # --- INÍCIO: CORREÇÃO (Bug 1: Respawn de Bot no PVP) ---
            # Verifica o tamanho do mapa ATUAL. s.MAP_WIDTH é dinâmico.
            # Se o mapa for < 5000, é PVP.
            is_pvp_map = (s.MAP_WIDTH < 5000) 
            
            if not is_pvp_map: # É PVE (Mapa grande)
                print(f"[{self.nome}] BOT MORREU! Resetando...")
                
                novo_x = random.randint(50, s.MAP_WIDTH - 50) 
                novo_y = random.randint(50, s.MAP_HEIGHT - 50) 
                self.posicao = pygame.math.Vector2(novo_x, novo_y); self.rect.center = self.posicao
                
                self.grupo_auxiliares_ativos.empty()
                self.lista_todas_auxiliares = [] 
                for pos in self.POSICOES_AUXILIARES: 
                    nova_aux = NaveAuxiliar(self, pos)
                    self.lista_todas_auxiliares.append(nova_aux)
                
                self.pontos = 0; self.nivel_motor = 1; self.nivel_dano = 1; self.nivel_max_vida = 1; self.nivel_escudo = 0; self.nivel_aux = 0
                
                self.velocidade_movimento_base = 4 + (self.nivel_motor * 0.5) 
                self.max_vida = VIDA_POR_NIVEL[self.nivel_max_vida] 
                self.vida_atual = self.max_vida
                self.alvo_selecionado = None; self.posicao_alvo_mouse = None; self.tempo_fim_lentidao = 0; self.rastro_particulas = []
                
                self.cerebro.resetar_ia()
                self.comprar_auxiliar()
                
                self.parar_regeneracao() 
            
            else: # É PVP (Mapa pequeno)
                print(f"[{self.nome}] BOT MORREU no PVP! Removendo sprite.")
                self.kill() # Apenas morre.
            # --- FIM: CORREÇÃO ---
            
        return morreu
        
    # --- INÍCIO: MODIFICAÇÃO (Aceitar map_width/height) ---
    def update(self, player_ref, grupo_projeteis_bots, grupo_bots_ref, grupo_inimigos_ref, grupo_obstaculos_ref, grupo_efeitos_visuais_ref, pos_ouvinte=None, map_width=s.MAP_WIDTH, map_height=s.MAP_HEIGHT):
    # --- FIM: MODIFICAÇÃO ---
    
        # --- MUDANÇA: Passa map_width/height para o cérebro ---
        self.cerebro.update_ai(player_ref, grupo_bots_ref, grupo_inimigos_ref, grupo_obstaculos_ref, grupo_efeitos_visuais_ref, map_width, map_height) # <-- MODIFICADO

        self.update_regeneracao()
        self.rotacionar() 
        self.mover()      
        
        # --- MODIFICADO: Passa pos_ouvinte ---
        self.lidar_com_tiros(grupo_projeteis_bots, pos_ouvinte if pos_ouvinte is not None else player_ref.posicao)
        self.processar_upgrades_ia()
        
        # --- INÍCIO DA MODIFICAÇÃO (Correção da lógica de regeneração) ---
        
        estado_cerebro = self.cerebro.estado_ia
        
        # Condições para INICIAR a regeneração:
        # A IA decidiu que deve regenerar (REGENERANDO_NA_BORDA)
        # OU a IA está VAGANDO e com HP baixo (o que a faz parar)
        
        esta_tentando_parar_para_regen = (estado_cerebro == "VAGANDO" and self.vida_atual < (self.max_vida * 0.8))
        esta_parado_na_borda = (estado_cerebro == "REGENERANDO_NA_BORDA")

        # Se o cérebro quer parar para regenerar, E não tem alvo, E não está regenerando
        if (esta_tentando_parar_para_regen or esta_parado_na_borda) and \
           self.alvo_selecionado is None and \
           not self.esta_regenerando:
            
            # Garante que o input de movimento esteja parado
            self.quer_mover_frente = False 
            self.posicao_alvo_mouse = None 
             
            self.iniciar_regeneracao(grupo_efeitos_visuais_ref) #
        
        # Condições para PARAR a regeneração
        # Se o cérebro NÃO está em estado de regeneração (ex: FUGINDO, ATACANDO, VAGANDO com HP cheio)
        # OU se adquiriu um alvo (o usuário quer que atire parado)
        elif (not esta_tentando_parar_para_regen and not esta_parado_na_borda) or \
             (self.alvo_selecionado is not None):
             
             self.parar_regeneracao()
        
        # --- FIM DA MODIFICAÇÃO ---

    def processar_upgrades_ia(self):
        if self.pontos_upgrade_disponiveis > 0 and self.total_upgrades_feitos < MAX_TOTAL_UPGRADES:
            if self.nivel_motor < MAX_NIVEL_MOTOR:
                 self.comprar_upgrade("motor")
            elif self.nivel_escudo < MAX_NIVEL_ESCUDO: 
                 self.comprar_upgrade("escudo")
            elif self.nivel_dano < MAX_NIVEL_DANO:
                 self.comprar_upgrade("dano")
            # --- INÍCIO: CORREÇÃO CRASH (Bot AI Offline) ---
            # Verifica se o nível atual é MENOR que o índice máximo (len-1)
            elif self.nivel_max_vida < len(VIDA_POR_NIVEL) - 1:
                 self.comprar_upgrade("max_health")
            # --- FIM: CORREÇÃO ---