
import pygame
import random
import math
import settings as s

class BotAI:
    """
    Classe que representa o "cérebro" de um bot no jogo.
    Controla todas as decisões de movimento, combate e sobrevivência.
    """

    def __init__(self, bot_nave):
        self.bot = bot_nave

        # Dimensões do mapa
        self.map_width = s.MAP_WIDTH
        self.map_height = s.MAP_HEIGHT

        # Variáveis de Estado
        self.estado_ia = "VAGANDO"
        self.estado_anterior = "VAGANDO"
        self.frames_no_estado_atual = 0

        # --- CONSTANTES E QUADRADOS (Otimização) ---
        self.distancia_scan_geral = 800
        self.dist_scan_geral_sq = self.distancia_scan_geral ** 2
        
        self.distancia_scan_inimigo = 600
        self.dist_scan_inimigo_sq = self.distancia_scan_inimigo ** 2
        
        # Distâncias de Kiting (Combate Próximo/Médio)
        self.distancia_orbita_max = 350
        self.dist_orbita_max_sq = self.distancia_orbita_max ** 2
        
        self.distancia_orbita_min = 180
        self.dist_orbita_min_sq = self.distancia_orbita_min ** 2
        
        self.dist_borda_segura = 400
        self.dist_zona_perigo_antecipada = 500

        # Limites de HP
        self.limite_hp_fugir = 0.20       # 20%
        self.limite_hp_regenerar = 0.80   # 80%
        self.limite_hp_buscar_vida = 0.40 # 40%

        # Desvio de Projéteis
        self.distancia_deteccao_projetil = 250
        self.dist_deteccao_proj_sq = self.distancia_deteccao_projetil ** 2
        self.tempo_minimo_desvio = 15

        # Detecção de "Preso"
        self.posicao_anterior = pygame.math.Vector2(0, 0)
        self.frames_sem_movimento = 0
        self.distancia_minima_movimento_sq = 3 ** 2
        self.frames_max_sem_movimento = 30

        # Caches de Referência
        self.player_ref_cache = None
        self.grupo_bots_ref_cache = None
        self.grupo_inimigos_ref_cache = None
        self.grupo_obstaculos_ref_cache = None
        self.grupo_vidas_ref = None
        self.lista_projeteis_hostis_ref = None

        # Combate / Movimento
        self.direcao_orbita = random.choice([1, -1]) # 1 ou -1
        self.timer_troca_orbita = 0
        self.duracao_orbita_atual = random.randint(120, 300)
        
        # Fuga
        self.flee_destination = None
        self.timer_zigue_zague = 0
        self.zigue_zague_direcao = 1
        self.duracao_zigue_zague = random.randint(10, 25)
        self.intensidade_zigue_zague = 100

        # Memória de Dano
        self.locais_dano_recente = []
        self.tempo_memoria_dano = 5000
        self.raio_memoria_dano_sq = 200 ** 2

        # Wandering
        self.bot_wander_target = None
        self.timer_wander = 0
        self.duracao_wander_atual = random.randint(180, 360)

        # Desvio
        self.frames_desviando = 0
        self.direcao_desvio = None # Não usado diretamente no novo método de força, mas mantido
        self.vetor_desvio_atual = None 

        # Micro-movimentos
        self.timer_micro = 0
        self.offset_micro = pygame.math.Vector2(0,0)

    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================

    def _calcular_score_alvo(self, alvo, dist_sq):
        score = 0.0
        if dist_sq > 0:
            fator_dist = 100000 / dist_sq 
            score += min(fator_dist, 100) 

        vida_atual = getattr(alvo, 'vida_atual', 0)
        max_vida = getattr(alvo, 'max_vida', 1)
        if max_vida > 0:
            percent_hp = vida_atual / max_vida
            score += (1 - percent_hp) * 50 

        if hasattr(alvo, 'vida_atual'):
            score += 100 
        
        return score

    def _esta_vivo(self, entidade):
        if not entidade: return False
        if not entidade.groups(): return False
        return getattr(entidade, 'vida_atual', 0) > 0

    def _calcular_forca_desvio(self):
        """
        Calcula um vetor de 'Campo de Força' baseado em TODOS os projéteis próximos.
        """
        forca_total = pygame.math.Vector2(0, 0)
        if not self.lista_projeteis_hostis_ref: return forca_total

        pos_bot = self.bot.posicao

        for proj in self.lista_projeteis_hostis_ref:
            # Ignora projéteis do próprio bot
            if getattr(proj, 'owner', None) == self.bot: continue
            
            try:
                # Verifica distância
                dist_sq = pos_bot.distance_squared_to(proj.posicao)
                if dist_sq > self.dist_deteccao_proj_sq: continue

                # Vetor do bot para o projétil
                vetor_para_proj = proj.posicao - pos_bot
                dist = math.sqrt(dist_sq)
                
                # Verifica se o projétil está vindo na direção do bot
                vel_proj = getattr(proj, 'velocidade_vetor', None)
                if vel_proj and vel_proj.length_squared() > 0.1:
                    # Se o projétil está se afastando, ignora (produto escalar < 0)
                    if vel_proj.normalize().dot(-vetor_para_proj.normalize()) < 0:
                        continue

                # Força de repulsão inversamente proporcional à distância
                if dist > 0:
                    forca_repulsao = -vetor_para_proj.normalize() * (self.distancia_deteccao_projetil / dist)
                    forca_total += forca_repulsao

            except (ValueError, AttributeError):
                continue
        
        return forca_total
    
    def _calcular_direcao_desvio(self, proj):
        """Calcula vetor perpendicular seguro (Fallback)."""
        try:
            vel = proj.velocidade_vetor.normalize()
            perp1 = pygame.math.Vector2(-vel.y, vel.x)
            perp2 = pygame.math.Vector2(vel.y, -vel.x)
            
            centro = pygame.math.Vector2(self.map_width/2, self.map_height/2)
            pos1 = self.bot.posicao + perp1 * 100
            pos2 = self.bot.posicao + perp2 * 100
            
            if pos1.distance_squared_to(centro) < pos2.distance_squared_to(centro):
                return perp1
            return perp2
        except:
            return pygame.math.Vector2(1, 0)

    # ========================================================================
    # LOOP PRINCIPAL (UPDATE)
    # ========================================================================

    def update_ai(self, player_ref, grupo_bots_ref, grupo_inimigos_ref, 
                  grupo_obstaculos_ref, grupo_vidas_ref, 
                  map_width=None, map_height=None, lista_projeteis_hostis=None):
        
        if map_width: self.map_width = map_width
        if map_height: self.map_height = map_height
        
        self.player_ref_cache = player_ref
        self.grupo_bots_ref_cache = grupo_bots_ref
        self.grupo_inimigos_ref_cache = grupo_inimigos_ref
        self.grupo_obstaculos_ref_cache = grupo_obstaculos_ref
        self.grupo_vidas_ref = grupo_vidas_ref
        self.lista_projeteis_hostis_ref = lista_projeteis_hostis

        self.frames_no_estado_atual += 1

        # 1. Verifica se está preso
        if self.bot.posicao.distance_squared_to(self.posicao_anterior) < self.distancia_minima_movimento_sq:
            self.frames_sem_movimento += 1
            if self.frames_sem_movimento > self.frames_max_sem_movimento:
                self.bot.angulo += random.randint(90, 180)
                self.frames_sem_movimento = 0
        else:
            self.frames_sem_movimento = 0
        self.posicao_anterior = self.bot.posicao.copy()

        # 2. Desvio de Projéteis (Prioridade Alta com Força de Repulsão)
        # --- CORREÇÃO: Permitir desvio mesmo se estiver regenerando na borda ---
        if self.estado_ia not in ["FUGINDO"]: 
            vetor_forca = self._calcular_forca_desvio()
            
            # Se a força for significativa, entra em modo de desvio
            if vetor_forca.length_squared() > 0.5:
                self._mudar_estado("DESVIANDO")
                self.vetor_desvio_atual = vetor_forca.normalize()
                self.frames_desviando = 0
        
        if self.estado_ia == "DESVIANDO":
            self.frames_desviando += 1
            if self.frames_desviando > self.tempo_minimo_desvio:
                # Tenta recalcular força para ver se ainda precisa desviar
                nova_forca = self._calcular_forca_desvio()
                if nova_forca.length_squared() < 0.5:
                    self._mudar_estado("VAGANDO")
                else:
                    self.vetor_desvio_atual = self.vetor_desvio_atual.lerp(nova_forca.normalize(), 0.2)

        # 3. Processa Lógica de Estado (Movimento)
        self._processar_estado_atual()

        # 4. Busca de Alvo
        if not self._esta_vivo(self.bot.alvo_selecionado):
            if self.estado_ia not in ["FUGINDO", "REGENERANDO_NA_BORDA", "EVITANDO_BORDA", "DESVIANDO"]:
                self._encontrar_novo_alvo()

    def _mudar_estado(self, novo):
        if self.estado_ia != novo:
            self.estado_anterior = self.estado_ia
            self.estado_ia = novo
            self.frames_no_estado_atual = 0

    # ========================================================================
    # SISTEMA DE BUSCA DE ALVOS
    # ========================================================================

    def _encontrar_novo_alvo(self):
        self.bot.alvo_selecionado = None
        
        # A. Coletar Vida
        limite_busca = self.bot.max_vida * self.limite_hp_buscar_vida
        if self.bot.vida_atual < limite_busca and self.grupo_vidas_ref:
            melhor_vida = None
            menor_dist_sq = self.dist_scan_geral_sq
            for vida in self.grupo_vidas_ref:
                if not vida.groups(): continue
                try:
                    d_sq = self.bot.posicao.distance_squared_to(vida.posicao)
                    if d_sq < menor_dist_sq:
                        menor_dist_sq = d_sq
                        melhor_vida = vida
                except: continue
            if melhor_vida:
                self._mudar_estado("COLETANDO")
                self.bot.posicao_alvo_mouse = melhor_vida.posicao
                return

        # B. Buscar Inimigos
        melhor_alvo = None
        melhor_score = -float('inf')

        candidatos = list(self.grupo_inimigos_ref_cache) if self.grupo_inimigos_ref_cache else []
        if self.player_ref_cache and self._esta_vivo(self.player_ref_cache):
            candidatos.append(self.player_ref_cache)
        if self.grupo_bots_ref_cache:
            for b in self.grupo_bots_ref_cache:
                if b != self.bot: candidatos.append(b)
        if self.grupo_obstaculos_ref_cache:
            candidatos.extend(list(self.grupo_obstaculos_ref_cache))

        for entidade in candidatos:
            if entidade == self.bot or not self._esta_vivo(entidade): continue
            # Ignora auxiliares (não ataca filhos)
            if isinstance(entidade, pygame.sprite.Sprite) and hasattr(entidade, 'owner') and entidade.owner:
                 continue

            try:
                dist_sq = self.bot.posicao.distance_squared_to(entidade.posicao)
                if dist_sq < self.dist_scan_geral_sq:
                    s = self._calcular_score_alvo(entidade, dist_sq)
                    if s > melhor_score:
                        melhor_score = s
                        melhor_alvo = entidade
            except: pass

        if melhor_alvo:
            self.bot.alvo_selecionado = melhor_alvo
            dist_sq_final = self.bot.posicao.distance_squared_to(melhor_alvo.posicao)
            if dist_sq_final < self.dist_scan_inimigo_sq:
                self._mudar_estado("ATACANDO")
            else:
                self._mudar_estado("CAÇANDO")
        else:
            self._mudar_estado("VAGANDO")

    # ========================================================================
    # LÓGICA DE COMPORTAMENTO (FSM)
    # ========================================================================

    def _processar_estado_atual(self):
        self.bot.quer_mover_frente = False
        self.bot.quer_mover_tras = False
        self.bot.quer_atirar = False 
        self.bot.posicao_alvo_mouse = None

        hp_lim_fugir = self.bot.max_vida * self.limite_hp_fugir
        hp_lim_regen = self.bot.max_vida * self.limite_hp_regenerar

        # --- Regenerando ---
        if self.estado_ia == "REGENERANDO_NA_BORDA":
            if self.bot.vida_atual < hp_lim_regen:
                # Fica parado, mas mira em quem chegar perto (defesa)
                alvo = self._find_threat_closest()
                self.bot.alvo_selecionado = alvo
                if alvo: self.bot.quer_atirar = True
                return
            else:
                self._mudar_estado("VAGANDO")
                return

        # --- Fugindo ---
        if self.bot.vida_atual <= hp_lim_fugir and self.estado_ia != "REGENERANDO_NA_BORDA":
            self._mudar_estado("FUGINDO")
            px, py = self.bot.posicao.x, self.bot.posicao.y
            margem = self.dist_borda_segura
            if px < margem or px > self.map_width - margem or py < margem or py > self.map_height - margem:
                self._mudar_estado("REGENERANDO_NA_BORDA")
            else:
                if not self.flee_destination: self.flee_destination = self._calcular_ponto_fuga_borda()
                self.timer_zigue_zague += 1
                if self.timer_zigue_zague > self.duracao_zigue_zague:
                    self.zigue_zague_direcao *= -1; self.timer_zigue_zague = 0
                if self.flee_destination:
                    vetor_fuga = (self.flee_destination - self.bot.posicao).normalize()
                    vetor_perp = pygame.math.Vector2(-vetor_fuga.y, vetor_fuga.x) * self.zigue_zague_direcao
                    self.bot.posicao_alvo_mouse = self.flee_destination + (vetor_perp * 100)
            
            alvo_kiting = self._find_threat_closest()
            if alvo_kiting:
                self.bot.alvo_selecionado = alvo_kiting; self.bot.quer_atirar = True
            return

        # --- Desviando (NOVA LÓGICA DE MOVIMENTO) ---
        if self.estado_ia == "DESVIANDO" and self.vetor_desvio_atual:
            # Move 200px na direção da força de repulsão acumulada
            destino = self.bot.posicao + (self.vetor_desvio_atual * 200)
            self._clamp_position(destino)
            self.bot.posicao_alvo_mouse = destino
            
            # Ainda tenta atirar se tiver alvo
            if self.bot.alvo_selecionado and self._esta_vivo(self.bot.alvo_selecionado):
                self.bot.quer_atirar = True
            return

        # --- Evitando Borda ---
        if self.estado_ia != "FUGINDO":
            px, py = self.bot.posicao.x, self.bot.posicao.y
            margem = self.dist_borda_segura
            if px < margem or px > self.map_width - margem or py < margem or py > self.map_height - margem:
                self._mudar_estado("EVITANDO_BORDA")
            
            if self.estado_ia == "EVITANDO_BORDA":
                centro = pygame.math.Vector2(self.map_width/2, self.map_height/2)
                if self.bot.posicao.distance_squared_to(centro) < (self.map_width/3)**2: self._mudar_estado("VAGANDO")
                else: self.bot.posicao_alvo_mouse = centro
                return

        # --- Coletando ---
        if self.estado_ia == "COLETANDO":
            if self.bot.posicao_alvo_mouse: pass 
            else: self._mudar_estado("VAGANDO")
            return

        # --- Caçando ---
        if self.estado_ia == "CAÇANDO":
            alvo = self.bot.alvo_selecionado
            if self._esta_vivo(alvo):
                dist_sq = self.bot.posicao.distance_squared_to(alvo.posicao)
                if dist_sq < self.dist_scan_inimigo_sq: self._mudar_estado("ATACANDO")
                else: self.bot.posicao_alvo_mouse = alvo.posicao
            else: self._mudar_estado("VAGANDO")
            return

        # --- Atacando (KITING MELHORADO) ---
        if self.estado_ia == "ATACANDO":
            alvo = self.bot.alvo_selecionado
            if self._esta_vivo(alvo):
                vec_to_target = alvo.posicao - self.bot.posicao
                dist_sq = vec_to_target.length_squared()
                
                if dist_sq > self.dist_scan_inimigo_sq * 1.5: 
                    self._mudar_estado("CAÇANDO"); return

                try:
                    vec_norm = vec_to_target.normalize()
                    vec_tangente = pygame.math.Vector2(-vec_norm.y, vec_norm.x) * self.direcao_orbita
                    
                    self.timer_troca_orbita += 1
                    if self.timer_troca_orbita > self.duracao_orbita_atual:
                        self.direcao_orbita *= -1; self.timer_troca_orbita = 0
                        self.duracao_orbita_atual = random.randint(60, 180)

                    vec_final = vec_tangente
                    
                    # Kiting mais agressivo no strafe, menos avanço
                    if dist_sq > self.dist_orbita_max_sq:
                        # Avança + Strafe (Aproxima mais)
                        vec_final = (vec_tangente * 0.4) + (vec_norm * 0.6)
                    elif dist_sq < self.dist_orbita_min_sq:
                        # Recua + Strafe
                        vec_final = (vec_tangente * 0.6) - (vec_norm * 0.4)
                    
                    destino = self.bot.posicao + (vec_final.normalize() * 150)
                    
                    self.timer_micro += 1
                    if self.timer_micro > 30:
                        self.offset_micro = pygame.math.Vector2(random.randint(-20,20), random.randint(-20,20))
                        self.timer_micro = 0
                    
                    destino += self.offset_micro
                    self._clamp_position(destino)
                    self.bot.posicao_alvo_mouse = destino
                    
                    self.bot.quer_atirar = True

                except ValueError: pass
            else: self._mudar_estado("VAGANDO")
            return

        # --- Vagando ---
        if self.estado_ia == "VAGANDO":
            if self.bot.vida_atual < hp_lim_regen: self.bot.posicao_alvo_mouse = None 
            else:
                chegou = False
                if self.bot_wander_target:
                    if self.bot.posicao.distance_squared_to(self.bot_wander_target) < 10000: chegou = True
                
                if not self.bot_wander_target or chegou:
                    margem = 100
                    rx = random.randint(margem, self.map_width - margem)
                    ry = random.randint(margem, self.map_height - margem)
                    self.bot_wander_target = pygame.math.Vector2(rx, ry)
                self.bot.posicao_alvo_mouse = self.bot_wander_target

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _clamp_position(self, vector):
        margem = 50
        vector.x = max(margem, min(vector.x, self.map_width - margem))
        vector.y = max(margem, min(vector.y, self.map_height - margem))

    def _calcular_ponto_fuga_borda(self):
        pos = self.bot.posicao; margem = 60
        d_top = pos.y; d_bottom = self.map_height - pos.y; d_left = pos.x; d_right = self.map_width - pos.x
        m = min(d_top, d_bottom, d_left, d_right)
        if m == d_top: return pygame.math.Vector2(pos.x, margem)
        if m == d_bottom: return pygame.math.Vector2(pos.x, self.map_height - margem)
        if m == d_left: return pygame.math.Vector2(margem, pos.y)
        return pygame.math.Vector2(self.map_width - margem, pos.y)

    def _find_threat_closest(self):
        if not self.grupo_inimigos_ref_cache: return None
        closest = None; closest_d = self.dist_scan_inimigo_sq
        for inimigo in self.grupo_inimigos_ref_cache:
            if not self._esta_vivo(inimigo) or inimigo == self.bot: continue
            d = self.bot.posicao.distance_squared_to(inimigo.posicao)
            if d < closest_d: closest_d = d; closest = inimigo
        return closest

    def resetar_ia(self):
        self.bot.alvo_selecionado = None; self.bot.posicao_alvo_mouse = None
        self.estado_ia = "VAGANDO"; self.estado_anterior = "VAGANDO"
        self.frames_no_estado_atual = 0; self.frames_sem_movimento = 0
        self.posicao_anterior = pygame.math.Vector2(0, 0); self.flee_destination = None