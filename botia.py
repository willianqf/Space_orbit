# botia.py
# ============================================================================
# INTELIGÊNCIA ARTIFICIAL DOS BOTS OFFLINE
# ============================================================================
# Este módulo controla o comportamento dos bots no modo offline do jogo.
# Implementa um sistema de IA com estados, priorização de alvos, desvio de
# projéteis, sistema de fuga inteligente e navegação suave.
# ============================================================================

import pygame
import random
import math
import settings as s


class BotAI:
    """
    Classe que representa o "cérebro" de um bot no jogo.
    Controla todas as decisões de movimento, combate e sobrevivência.
    """

    # ========================================================================
    # CONSTANTES DE CONFIGURAÇÃO DA IA - ESTADOS VÁLIDOS
    # ========================================================================
    ESTADOS_VALIDOS = [
        "VAGANDO",              # Sem alvo, explorando o mapa
        "CAÇANDO",              # Indo em direção a um alvo distante
        "ATACANDO",             # Em combate próximo, orbitando o alvo
        "FUGINDO",              # HP baixo, fugindo para área segura
        "REGENERANDO_NA_BORDA", # Parado na borda regenerando HP
        "EVITANDO_BORDA",       # Indo para o centro do mapa
        "COLETANDO",            # Coletando itens de vida (modo PVE)
        "DESVIANDO"             # Desviando de projéteis perigosos
    ]

    def __init__(self, bot_nave):
        """
        Inicializa o cérebro da IA.

        Parâmetros:
            bot_nave: Referência para a instância de NaveBot que este cérebro controla.
        """
        self.bot = bot_nave

        # ====================================================================
        # DIMENSÕES DO MAPA (atualizadas dinamicamente)
        # ====================================================================
        self.map_width = s.MAP_WIDTH
        self.map_height = s.MAP_HEIGHT

        # ====================================================================
        # VARIÁVEIS DE ESTADO DA IA
        # ====================================================================
        self.estado_ia = "VAGANDO"
        self.estado_anterior = "VAGANDO"  # Para transições suaves
        self.frames_no_estado_atual = 0   # Contador para o estado atual

        # ====================================================================
        # CONSTANTES DE COMPORTAMENTO - DISTÂNCIAS
        # ====================================================================
        self.distancia_scan_geral = 800       # Distância máxima para detectar qualquer entidade
        self.distancia_scan_inimigo = 600     # Distância para entrar em modo de combate
        self.distancia_orbita_max = 300       # Começa a avançar se mais longe que isso
        self.distancia_orbita_min = 200       # Começa a recuar se mais perto que isso
        self.distancia_tiro_ia = 500          # Distância ideal para atirar
        self.dist_borda_segura = 400          # Zona de perigo perto das bordas
        self.dist_zona_perigo_antecipada = 500  # Detecção antecipada de bordas

        # ====================================================================
        # CONSTANTES DE COMPORTAMENTO - HP
        # ====================================================================
        self.limite_hp_fugir = 0.20           # 20% do HP máximo para fugir
        self.limite_hp_regenerar = 0.80       # 80% do HP para parar de regenerar
        self.limite_hp_buscar_vida = 0.40     # 40% do HP para buscar itens de vida

        # ====================================================================
        # CONSTANTES DE COMPORTAMENTO - DESVIO DE PROJÉTEIS
        # ====================================================================
        self.distancia_deteccao_projetil = 250   # Raio de detecção de projéteis
        self.angulo_cone_perigo = 45             # Ângulo do cone de perigo (graus)
        self.tempo_minimo_desvio = 15            # Frames mínimos em modo de desvio

        # ====================================================================
        # SISTEMA DE DETECÇÃO DE "PRESO"
        # ====================================================================
        self.posicao_anterior = pygame.math.Vector2(0, 0)
        self.frames_sem_movimento = 0
        self.distancia_minima_movimento = 3   # Mínimo para considerar movimento
        self.frames_max_sem_movimento = 30    # Máximo de frames parado

        # ====================================================================
        # CACHES DE REFERÊNCIA (atualizados a cada frame)
        # ====================================================================
        self.player_ref_cache = None
        self.grupo_bots_ref_cache = None
        self.grupo_inimigos_ref_cache = None
        self.grupo_obstaculos_ref_cache = None
        self.grupo_vidas_ref = None
        self.grupo_projeteis_ref = None   # NOVO: Referência aos projéteis para desvio

        # ====================================================================
        # SISTEMA DE ÓRBITA ALEATÓRIA (movimentos imprevisíveis em combate)
        # ====================================================================
        self.direcao_orbita = random.choice([1, -1])  # 1 = horário, -1 = anti-horário
        self.timer_troca_orbita = 0
        self.duracao_orbita_atual = random.randint(60, 180)
        self.variacao_angulo_orbita = random.uniform(-15, 15)  # Variação no ângulo

        # ====================================================================
        # SISTEMA DE MICRO-MOVIMENTOS (nunca ficar completamente parado)
        # ====================================================================
        self.timer_micro_movimento = 0
        self.duracao_micro_movimento = random.randint(30, 90)
        self.offset_micro = pygame.math.Vector2(0, 0)

        # ====================================================================
        # SISTEMA DE FUGA INTELIGENTE
        # ====================================================================
        self.flee_destination = None
        self.zigue_zague_direcao = 1          # 1 ou -1
        self.timer_zigue_zague = 0
        self.duracao_zigue_zague = random.randint(10, 25)
        self.intensidade_zigue_zague = 100    # Pixels de desvio lateral

        # ====================================================================
        # SISTEMA DE MEMÓRIA DE DANO (evitar áreas perigosas)
        # ====================================================================
        self.locais_dano_recente = []         # Lista de (posição, tempo)
        self.tempo_memoria_dano = 5000        # 5 segundos de memória
        self.raio_memoria_dano = 200          # Raio de área a evitar

        # ====================================================================
        # SISTEMA DE WANDERING (exploração)
        # ====================================================================
        self.bot_wander_target = None
        self.timer_wander = 0
        self.duracao_wander_atual = random.randint(180, 360)

        # ====================================================================
        # SISTEMA DE DESVIO DE PROJÉTEIS
        # ====================================================================
        self.frames_desviando = 0
        self.direcao_desvio = None            # Direção do desvio atual

    # ========================================================================
    # MÉTODOS AUXILIARES - DETECÇÃO E ANÁLISE
    # ========================================================================

    def _calcular_score_alvo(self, alvo, distancia):
        """
        Calcula uma pontuação para um alvo baseada em vários fatores.
        Quanto MAIOR a pontuação, MELHOR o alvo.

        Fatores considerados:
        - HP do alvo (menos HP = mais prioridade)
        - Distância (mais perto = mais prioridade)
        - Se é um inimigo vs obstáculo

        Parâmetros:
            alvo: O sprite do alvo
            distancia: Distância até o alvo

        Retorna:
            float: Pontuação do alvo (maior = melhor)
        """
        score = 0.0

        # Fator distância: alvos mais próximos são melhores
        # Normaliza para 0-100 baseado na distância de scan
        fator_distancia = 100 * (1 - (distancia / self.distancia_scan_geral))
        score += fator_distancia * 1.0  # Peso 1.0

        # Fator HP: alvos com menos HP são mais fáceis de eliminar
        if hasattr(alvo, 'vida_atual') and hasattr(alvo, 'max_vida'):
            if alvo.max_vida > 0:
                percent_hp = alvo.vida_atual / alvo.max_vida
                fator_hp = 100 * (1 - percent_hp)  # 0% HP = 100 pontos
                score += fator_hp * 1.5  # Peso 1.5 (prioridade maior para HP baixo)

        # Fator tipo: inimigos têm prioridade sobre obstáculos
        if hasattr(alvo, 'vida_atual'):
            score += 20  # Bonus para entidades com vida

        return score

    def _detectar_projeteis_perigosos(self):
        """
        Detecta projéteis inimigos que estão vindo na direção do bot.

        Analisa a trajetória de cada projétil e verifica se vai colidir
        com o bot nos próximos frames.

        Retorna:
            list: Lista de projéteis perigosos ordenados por urgência
        """
        projeteis_perigosos = []

        # Verifica se temos referência ao grupo de projéteis
        if not self.grupo_projeteis_ref:
            return projeteis_perigosos

        pos_bot = self.bot.posicao

        for proj in self.grupo_projeteis_ref:
            # Ignora projéteis do próprio bot (se tiver owner)
            if hasattr(proj, 'owner') and proj.owner == self.bot:
                continue

            # Pega a posição do projétil
            if not hasattr(proj, 'posicao'):
                continue

            pos_proj = proj.posicao

            # Calcula distância
            try:
                dist = pos_bot.distance_to(pos_proj)
            except (ValueError, AttributeError):
                continue

            # Se está muito longe, ignora
            if dist > self.distancia_deteccao_projetil:
                continue

            # Pega a direção do projétil (vetor velocidade)
            if not hasattr(proj, 'velocidade_vetor'):
                continue

            vel_proj = proj.velocidade_vetor

            # Calcula vetor do projétil para o bot
            vetor_para_bot = pos_bot - pos_proj

            # Se o projétil está parado ou indo para longe, ignora
            if vel_proj.length() < 0.1:
                continue

            # Calcula o ângulo entre a direção do projétil e o vetor para o bot
            try:
                vel_normalizado = vel_proj.normalize()
                vetor_para_bot_norm = vetor_para_bot.normalize()

                # Produto escalar para verificar se está vindo em nossa direção
                dot = vel_normalizado.dot(vetor_para_bot_norm)

                # Se dot > 0, o projétil está vindo em nossa direção
                if dot > 0.5:  # Cone de ~60 graus
                    # Calcula urgência baseada na distância e velocidade
                    velocidade_proj = vel_proj.length()
                    tempo_impacto = dist / velocidade_proj if velocidade_proj > 0 else float('inf')

                    # Adiciona à lista com sua urgência (menor tempo = mais urgente)
                    projeteis_perigosos.append({
                        'projetil': proj,
                        'distancia': dist,
                        'tempo_impacto': tempo_impacto,
                        'direcao_proj': vel_normalizado,
                        'posicao_proj': pos_proj
                    })
            except (ValueError, ZeroDivisionError):
                continue

        # Ordena por urgência (tempo de impacto)
        projeteis_perigosos.sort(key=lambda x: x['tempo_impacto'])

        return projeteis_perigosos

    def _calcular_direcao_desvio(self, proj_info):
        """
        Calcula a melhor direção para desviar de um projétil.

        A direção de desvio é perpendicular à trajetória do projétil,
        escolhendo o lado que está mais longe das bordas.

        Parâmetros:
            proj_info: Dicionário com informações do projétil

        Retorna:
            pygame.math.Vector2: Direção normalizada para desviar
        """
        direcao_proj = proj_info['direcao_proj']

        # Calcula as duas direções perpendiculares
        perpendicular1 = pygame.math.Vector2(-direcao_proj.y, direcao_proj.x)
        perpendicular2 = pygame.math.Vector2(direcao_proj.y, -direcao_proj.x)

        # Calcula qual direção nos leva para mais longe das bordas
        pos_bot = self.bot.posicao
        centro_mapa = pygame.math.Vector2(self.map_width / 2, self.map_height / 2)

        # Posições potenciais após desviar
        pos1 = pos_bot + perpendicular1 * 100
        pos2 = pos_bot + perpendicular2 * 100

        # Escolhe a que está mais perto do centro (mais segura)
        dist1_centro = pos1.distance_to(centro_mapa)
        dist2_centro = pos2.distance_to(centro_mapa)

        # Verifica também se não ultrapassa as bordas
        margem = 50
        pos1_valida = (margem < pos1.x < self.map_width - margem and
                       margem < pos1.y < self.map_height - margem)
        pos2_valida = (margem < pos2.x < self.map_width - margem and
                       margem < pos2.y < self.map_height - margem)

        if pos1_valida and (not pos2_valida or dist1_centro < dist2_centro):
            return perpendicular1
        elif pos2_valida:
            return perpendicular2
        else:
            # Se ambas são inválidas, escolhe a mais próxima do centro
            if dist1_centro < dist2_centro:
                return perpendicular1
            return perpendicular2

    def _find_closest_edge_point(self):
        """
        VERSÃO ANTIGA - Mantida para compatibilidade.
        Calcula o ponto mais próximo na borda do mapa.

        Retorna:
            pygame.math.Vector2: Ponto na borda mais próxima
        """
        pos = self.bot.posicao
        margin = 50

        dist_to_top = pos.y
        dist_to_bottom = self.map_height - pos.y
        dist_to_left = pos.x
        dist_to_right = self.map_width - pos.x

        min_dist = min(dist_to_top, dist_to_bottom, dist_to_left, dist_to_right)

        if min_dist == dist_to_top:
            return pygame.math.Vector2(pos.x, margin)
        elif min_dist == dist_to_bottom:
            return pygame.math.Vector2(pos.x, self.map_height - margin)
        elif min_dist == dist_to_left:
            return pygame.math.Vector2(margin, pos.y)
        else:
            return pygame.math.Vector2(self.map_width - margin, pos.y)

    def _calcular_direcao_fuga_inteligente(self):
        """
        Calcula a melhor direção de fuga considerando:
        - Posição de todos os inimigos próximos
        - Posição das bordas (evita cantos)
        - Áreas com mais espaço de manobra

        Retorna:
            pygame.math.Vector2: Ponto de destino para fugir
        """
        pos_bot = self.bot.posicao

        # Encontra todas as ameaças próximas
        ameacas = []

        if self.grupo_inimigos_ref_cache:
            for inimigo in self.grupo_inimigos_ref_cache:
                if inimigo == self.bot:
                    continue
                if not hasattr(inimigo, 'posicao') or not inimigo.groups():
                    continue
                if hasattr(inimigo, 'vida_atual') and inimigo.vida_atual <= 0:
                    continue
                try:
                    dist = pos_bot.distance_to(inimigo.posicao)
                    if dist < self.distancia_scan_geral:
                        ameacas.append(inimigo.posicao)
                except (ValueError, AttributeError):
                    continue

        # Se não há ameaças, foge para longe do centro do mapa
        if not ameacas:
            return self._find_closest_edge_point()

        # Calcula o vetor médio de todas as ameaças
        vetor_ameaca_medio = pygame.math.Vector2(0, 0)
        for pos_ameaca in ameacas:
            vetor_para_ameaca = pos_ameaca - pos_bot
            if vetor_para_ameaca.length() > 0:
                vetor_ameaca_medio += vetor_para_ameaca.normalize()

        if vetor_ameaca_medio.length() > 0:
            vetor_ameaca_medio = vetor_ameaca_medio.normalize()
        else:
            # Fallback: foge para a borda mais próxima
            return self._find_closest_edge_point()

        # Direção de fuga é OPOSTA às ameaças
        direcao_fuga = -vetor_ameaca_medio

        # Calcula ponto de destino na direção de fuga
        distancia_fuga = 600  # Distância para fugir
        destino_inicial = pos_bot + direcao_fuga * distancia_fuga

        # Ajusta para não ir para fora do mapa ou para cantos
        margem = 100
        margem_canto = 200  # Evita cantos com margem maior

        # Limita às bordas do mapa
        destino_x = max(margem, min(destino_inicial.x, self.map_width - margem))
        destino_y = max(margem, min(destino_inicial.y, self.map_height - margem))

        # Verifica se está muito perto de um canto
        perto_canto = False
        if (destino_x < margem_canto or destino_x > self.map_width - margem_canto):
            if (destino_y < margem_canto or destino_y > self.map_height - margem_canto):
                perto_canto = True

        # Se está indo para um canto, ajusta para ir para o meio de uma borda
        if perto_canto:
            # Decide qual borda é mais segura (mais longe das ameaças)
            centro_topo = pygame.math.Vector2(self.map_width / 2, margem)
            centro_base = pygame.math.Vector2(self.map_width / 2, self.map_height - margem)
            centro_esq = pygame.math.Vector2(margem, self.map_height / 2)
            centro_dir = pygame.math.Vector2(self.map_width - margem, self.map_height / 2)

            # Calcula qual centro de borda está mais longe das ameaças
            centros = [centro_topo, centro_base, centro_esq, centro_dir]
            melhor_centro = centro_topo
            melhor_dist = 0

            for centro in centros:
                dist_total = 0
                for pos_ameaca in ameacas:
                    dist_total += centro.distance_to(pos_ameaca)
                if dist_total > melhor_dist:
                    melhor_dist = dist_total
                    melhor_centro = centro

            destino_x = melhor_centro.x
            destino_y = melhor_centro.y

        return pygame.math.Vector2(destino_x, destino_y)

    def _aplicar_zigue_zague(self, destino):
        """
        Aplica um movimento em zigue-zague ao destino de fuga.

        Parâmetros:
            destino: Ponto de destino original

        Retorna:
            pygame.math.Vector2: Ponto de destino com zigue-zague aplicado
        """
        if destino is None:
            return None

        # Atualiza o timer do zigue-zague
        self.timer_zigue_zague += 1
        if self.timer_zigue_zague >= self.duracao_zigue_zague:
            self.timer_zigue_zague = 0
            self.zigue_zague_direcao *= -1
            self.duracao_zigue_zague = random.randint(10, 25)

        # Calcula a direção até o destino
        direcao = destino - self.bot.posicao
        if direcao.length() < 1:
            return destino

        direcao = direcao.normalize()

        # Direção perpendicular
        perpendicular = pygame.math.Vector2(-direcao.y, direcao.x)

        # Aplica o offset do zigue-zague
        offset = perpendicular * self.intensidade_zigue_zague * self.zigue_zague_direcao

        # Novo destino com zigue-zague
        destino_zz = destino + offset

        # Garante que não sai do mapa
        margem = 50
        destino_zz.x = max(margem, min(destino_zz.x, self.map_width - margem))
        destino_zz.y = max(margem, min(destino_zz.y, self.map_height - margem))

        return destino_zz

    def _calcular_forca_borda(self):
        """
        Calcula um vetor de "campo de força" que empurra o bot para longe das bordas.
        A força aumenta conforme o bot se aproxima da borda.

        Retorna:
            pygame.math.Vector2: Vetor de força (pode ser zero se longe das bordas)
        """
        pos = self.bot.posicao
        forca = pygame.math.Vector2(0, 0)

        zona_perigo = self.dist_zona_perigo_antecipada

        # Força da borda esquerda
        if pos.x < zona_perigo:
            intensidade = 1 - (pos.x / zona_perigo)
            forca.x += intensidade * 50

        # Força da borda direita
        if pos.x > self.map_width - zona_perigo:
            dist_borda = self.map_width - pos.x
            intensidade = 1 - (dist_borda / zona_perigo)
            forca.x -= intensidade * 50

        # Força da borda superior
        if pos.y < zona_perigo:
            intensidade = 1 - (pos.y / zona_perigo)
            forca.y += intensidade * 50

        # Força da borda inferior
        if pos.y > self.map_height - zona_perigo:
            dist_borda = self.map_height - pos.y
            intensidade = 1 - (dist_borda / zona_perigo)
            forca.y -= intensidade * 50

        return forca

    def _find_closest_threat(self):
        """
        Encontra a ameaça (Inimigo ou Player/Bot) mais próxima.
        Usa o sistema de pontuação para escolher o melhor alvo.

        Retorna:
            sprite: O sprite da ameaça mais perigosa, ou None
        """
        melhor_alvo = None
        melhor_score = -float('inf')

        # 1. Procura Inimigos
        if self.grupo_inimigos_ref_cache:
            for inimigo in self.grupo_inimigos_ref_cache:
                # Não pode alvejar a si mesmo
                if inimigo == self.bot:
                    continue

                # Verifica se o alvo está vivo e em um grupo
                if not hasattr(inimigo, 'vida_atual') or inimigo.vida_atual <= 0:
                    continue
                if not inimigo.groups():
                    continue

                try:
                    dist = self.bot.posicao.distance_to(inimigo.posicao)
                    if dist < self.distancia_scan_geral:
                        score = self._calcular_score_alvo(inimigo, dist)
                        if score > melhor_score:
                            melhor_score = score
                            melhor_alvo = inimigo
                except (ValueError, AttributeError):
                    continue

        # 2. Se não achou inimigos, procura Player/Bots
        if melhor_alvo is None:
            lista_alvos = []
            if self.player_ref_cache and self.player_ref_cache.vida_atual > 0:
                lista_alvos.append(self.player_ref_cache)
            if self.grupo_bots_ref_cache:
                lista_alvos.extend(list(self.grupo_bots_ref_cache.sprites()))

            for alvo in lista_alvos:
                if alvo == self.bot:
                    continue
                if not alvo.groups() or alvo.vida_atual <= 0:
                    continue

                try:
                    dist = self.bot.posicao.distance_to(alvo.posicao)
                    if dist < self.distancia_scan_geral:
                        score = self._calcular_score_alvo(alvo, dist)
                        if score > melhor_score:
                            melhor_score = score
                            melhor_alvo = alvo
                except (ValueError, AttributeError):
                    continue

        return melhor_alvo

    def _registrar_dano(self, posicao):
        """
        Registra um local onde o bot levou dano recentemente.

        Parâmetros:
            posicao: Posição onde levou dano
        """
        agora = pygame.time.get_ticks()
        self.locais_dano_recente.append((posicao.copy(), agora))

        # Remove registros antigos
        self.locais_dano_recente = [
            (pos, tempo) for pos, tempo in self.locais_dano_recente
            if agora - tempo < self.tempo_memoria_dano
        ]

    def _esta_em_area_perigosa(self, posicao):
        """
        Verifica se uma posição está em uma área onde o bot levou dano recentemente.

        Parâmetros:
            posicao: Posição a verificar

        Retorna:
            bool: True se a posição é perigosa
        """
        agora = pygame.time.get_ticks()

        for pos_dano, tempo in self.locais_dano_recente:
            if agora - tempo < self.tempo_memoria_dano:
                try:
                    if posicao.distance_to(pos_dano) < self.raio_memoria_dano:
                        return True
                except (ValueError, AttributeError):
                    continue

        return False

    def _gerar_micro_movimento(self):
        """
        Gera pequenos movimentos aleatórios para parecer mais natural.

        Retorna:
            pygame.math.Vector2: Pequeno offset de movimento
        """
        self.timer_micro_movimento += 1

        if self.timer_micro_movimento >= self.duracao_micro_movimento:
            self.timer_micro_movimento = 0
            self.duracao_micro_movimento = random.randint(30, 90)

            # Gera novo offset aleatório
            angulo = random.uniform(0, 2 * math.pi)
            intensidade = random.uniform(10, 30)
            self.offset_micro = pygame.math.Vector2(
                math.cos(angulo) * intensidade,
                math.sin(angulo) * intensidade
            )

        return self.offset_micro

    # ========================================================================
    # MÉTODO PRINCIPAL - UPDATE_AI
    # ========================================================================

    def update_ai(self, player_ref, grupo_bots_ref, grupo_inimigos_ref,
                  grupo_obstaculos_ref, grupo_vidas_ref,
                  map_width=None, map_height=None, grupo_projeteis_ref=None):
        """
        O "tick" principal do cérebro da IA. Chamado a cada frame pelo NaveBot.

        Parâmetros:
            player_ref: Referência ao jogador
            grupo_bots_ref: Grupo de bots aliados
            grupo_inimigos_ref: Grupo de inimigos
            grupo_obstaculos_ref: Grupo de obstáculos
            grupo_vidas_ref: Grupo de itens de vida (ou efeitos visuais)
            map_width: Largura do mapa (opcional, usa settings se None)
            map_height: Altura do mapa (opcional, usa settings se None)
            grupo_projeteis_ref: Grupo de projéteis para detecção de desvio (opcional)
        """
        # Atualiza as dimensões do mapa se fornecidas
        if map_width is not None:
            self.map_width = map_width
        if map_height is not None:
            self.map_height = map_height

        # Atualiza os caches de referência
        self.grupo_vidas_ref = grupo_vidas_ref
        self.player_ref_cache = player_ref
        self.grupo_bots_ref_cache = grupo_bots_ref
        self.grupo_inimigos_ref_cache = grupo_inimigos_ref
        self.grupo_obstaculos_ref_cache = grupo_obstaculos_ref
        self.grupo_projeteis_ref = grupo_projeteis_ref  # NOVO: para detecção de projéteis

        # Incrementa contador de frames no estado atual
        self.frames_no_estado_atual += 1

        # ====================================================================
        # DETECÇÃO DE BOT PRESO
        # ====================================================================
        if self.bot.posicao.distance_to(self.posicao_anterior) < self.distancia_minima_movimento:
            self.frames_sem_movimento += 1
            if self.frames_sem_movimento > self.frames_max_sem_movimento:
                self._resolver_bot_preso()
        else:
            self.frames_sem_movimento = 0
        self.posicao_anterior = self.bot.posicao.copy()

        # ====================================================================
        # PRIORIDADE 0: VERIFICAR PROJÉTEIS PERIGOSOS
        # ====================================================================
        if self.estado_ia != "FUGINDO" and self.estado_ia != "REGENERANDO_NA_BORDA":
            projeteis_perigosos = self._detectar_projeteis_perigosos()
            if projeteis_perigosos:
                self._processar_desvio_projetil(projeteis_perigosos[0])
                return

        # Se estávamos desviando mas não há mais perigo, volta ao normal
        if self.estado_ia == "DESVIANDO":
            self.frames_desviando += 1
            if self.frames_desviando >= self.tempo_minimo_desvio:
                # Detecta novamente para ver se ainda há perigo
                projeteis_perigosos = self._detectar_projeteis_perigosos()
                if not projeteis_perigosos:
                    self._mudar_estado("VAGANDO")
                    self.frames_desviando = 0
                    self.direcao_desvio = None

        # ====================================================================
        # PRIORIDADE 1: PROCESSAR ESTADO ATUAL (FUGIR/REGENERAR)
        # ====================================================================
        self._processar_input_ia()

        # ====================================================================
        # PRIORIDADE 2: ENCONTRAR NOVO ALVO (se necessário)
        # ====================================================================
        alvo_esta_morto = False
        if self.bot.alvo_selecionado:
            if not hasattr(self.bot.alvo_selecionado, 'vida_atual'):
                alvo_esta_morto = True
            elif self.bot.alvo_selecionado.vida_atual <= 0:
                alvo_esta_morto = True

        estados_sem_busca = ["FUGINDO", "REGENERANDO_NA_BORDA", "EVITANDO_BORDA", "DESVIANDO"]
        if (self.bot.alvo_selecionado is None or not self.bot.alvo_selecionado.groups() or alvo_esta_morto):
            if self.estado_ia not in estados_sem_busca:
                lista_alvos_naves = []
                if player_ref and player_ref.vida_atual > 0:
                    lista_alvos_naves.append(player_ref)
                lista_alvos_naves.extend(list(grupo_bots_ref.sprites()))

                self._encontrar_alvo(grupo_inimigos_ref, grupo_obstaculos_ref,
                                    lista_alvos_naves, grupo_vidas_ref)

    def _mudar_estado(self, novo_estado):
        """
        Muda o estado da IA com transição suave.

        Parâmetros:
            novo_estado: O novo estado para mudar
        """
        if novo_estado != self.estado_ia:
            self.estado_anterior = self.estado_ia
            self.estado_ia = novo_estado
            self.frames_no_estado_atual = 0

    def _resolver_bot_preso(self):
        """
        Resolve situação quando o bot está preso (sem movimento por muito tempo).
        """
        zona_perigo = self.dist_borda_segura * 1.5

        em_zona_perigo = (
            self.bot.posicao.x < zona_perigo or
            self.bot.posicao.x > self.map_width - zona_perigo or
            self.bot.posicao.y < zona_perigo or
            self.bot.posicao.y > self.map_height - zona_perigo
        )

        if em_zona_perigo:
            # Vai para o centro do mapa
            centro = pygame.math.Vector2(self.map_width / 2, self.map_height / 2)
            direcao_centro = centro - self.bot.posicao
            if direcao_centro.length() > 0:
                self.bot.angulo = pygame.math.Vector2(0, -1).angle_to(direcao_centro)
        else:
            # Gira aleatoriamente
            self.bot.angulo += random.randint(90, 180)

        self.frames_sem_movimento = 0

    def _processar_desvio_projetil(self, proj_info):
        """
        Processa o desvio de um projétil perigoso.

        Parâmetros:
            proj_info: Dicionário com informações do projétil
        """
        self._mudar_estado("DESVIANDO")
        self.frames_desviando = 0

        # Calcula a direção de desvio
        self.direcao_desvio = self._calcular_direcao_desvio(proj_info)

        # Move na direção do desvio
        distancia_desvio = 150
        destino = self.bot.posicao + self.direcao_desvio * distancia_desvio

        # Limita às bordas do mapa
        margem = 50
        destino.x = max(margem, min(destino.x, self.map_width - margem))
        destino.y = max(margem, min(destino.y, self.map_height - margem))

        self.bot.posicao_alvo_mouse = destino

        # Continua atirando no alvo se tiver um
        if self.bot.alvo_selecionado and not self.bot.alvo_selecionado.groups():
            self.bot.alvo_selecionado = None

    # ========================================================================
    # MÉTODO DE BUSCA DE ALVOS
    # ========================================================================

    def _encontrar_alvo(self, grupo_inimigos, grupo_obstaculos, lista_alvos_naves, grupo_vidas):
        """
        Encontra o melhor alvo usando o sistema de pontuação.
        Considera HP, distância e tipo de alvo.

        Parâmetros:
            grupo_inimigos: Grupo de inimigos
            grupo_obstaculos: Grupo de obstáculos
            lista_alvos_naves: Lista de naves (player/bots) como alvos
            grupo_vidas: Grupo de itens de vida
        """
        self.bot.alvo_selecionado = None

        # ====================================================================
        # 1. PRIORIDADE MÁXIMA: BUSCAR VIDA (se HP baixo)
        # ====================================================================
        limite_hp = self.bot.max_vida * self.limite_hp_buscar_vida

        if self.bot.vida_atual <= limite_hp:
            vida_mais_perto = None
            dist_min = self.distancia_scan_geral

            if grupo_vidas:
                for vida in grupo_vidas:
                    if not vida.groups() or not hasattr(vida, 'posicao'):
                        continue
                    try:
                        dist = self.bot.posicao.distance_to(vida.posicao)
                        if dist < dist_min:
                            dist_min = dist
                            vida_mais_perto = vida
                    except (ValueError, AttributeError):
                        continue

            if vida_mais_perto:
                self._mudar_estado("COLETANDO")
                return

        # ====================================================================
        # 2. BUSCAR MELHOR ALVO (Inimigos, Obstáculos, Naves)
        # ====================================================================
        melhor_alvo = None
        melhor_score = -float('inf')

        # 2.1 Procura Inimigos (prioridade mais alta)
        for inimigo in grupo_inimigos:
            if inimigo == self.bot:
                continue
            if not hasattr(inimigo, 'vida_atual') or inimigo.vida_atual <= 0:
                continue
            if not inimigo.groups():
                continue

            try:
                dist = self.bot.posicao.distance_to(inimigo.posicao)
                if dist < self.distancia_scan_geral:
                    score = self._calcular_score_alvo(inimigo, dist)
                    # Bonus para inimigos (são alvos principais)
                    score += 50
                    if score > melhor_score:
                        melhor_score = score
                        melhor_alvo = inimigo
            except (ValueError, AttributeError):
                continue

        # 2.2 Procura Obstáculos (se não achou inimigos bons)
        for obstaculo in grupo_obstaculos:
            if not obstaculo.groups():
                continue
            try:
                dist = self.bot.posicao.distance_to(obstaculo.posicao)
                if dist < self.distancia_scan_geral:
                    score = self._calcular_score_alvo(obstaculo, dist)
                    if score > melhor_score:
                        melhor_score = score
                        melhor_alvo = obstaculo
            except (ValueError, AttributeError):
                continue

        # 2.3 Procura outras Naves (player/bots)
        for alvo in lista_alvos_naves:
            if alvo == self.bot:
                continue
            if not alvo.groups() or alvo.vida_atual <= 0:
                continue

            try:
                dist = self.bot.posicao.distance_to(alvo.posicao)
                if dist < self.distancia_scan_geral:
                    score = self._calcular_score_alvo(alvo, dist)
                    if score > melhor_score:
                        melhor_score = score
                        melhor_alvo = alvo
            except (ValueError, AttributeError):
                continue

        # ====================================================================
        # 3. DEFINE O ALVO E MUDA O ESTADO
        # ====================================================================
        if melhor_alvo:
            self.bot.alvo_selecionado = melhor_alvo
            try:
                dist = self.bot.posicao.distance_to(melhor_alvo.posicao)
                if dist < self.distancia_scan_inimigo:
                    self._mudar_estado("ATACANDO")
                else:
                    self._mudar_estado("CAÇANDO")
            except (ValueError, AttributeError):
                self._mudar_estado("VAGANDO")
        else:
            self.bot.alvo_selecionado = None
            self._mudar_estado("VAGANDO")

    # ========================================================================
    # PROCESSAMENTO DE ESTADOS
    # ========================================================================

    def _processar_input_ia(self):
        """
        Define as intenções de movimento baseado no estado atual.
        Gerencia transições entre estados e comportamentos específicos.
        """
        # Reseta intenções de movimento
        self.bot.quer_mover_frente = False
        self.bot.quer_mover_tras = False
        self.bot.posicao_alvo_mouse = None

        limite_hp_fugir = self.bot.max_vida * self.limite_hp_fugir
        limite_hp_regenerar = self.bot.max_vida * self.limite_hp_regenerar

        # ====================================================================
        # ESTADO: REGENERANDO NA BORDA
        # ====================================================================
        if self.estado_ia == "REGENERANDO_NA_BORDA":
            if self.bot.vida_atual < limite_hp_regenerar:
                # Continua parado regenerando
                self.bot.posicao_alvo_mouse = None
                self.flee_destination = None

                # Mas ainda pode atirar em inimigos (kiting defensivo)
                self.bot.alvo_selecionado = self._find_closest_threat()
                return
            else:
                # HP suficiente, volta a vagar
                print(f"[{self.bot.nome}] Regeneração concluída. Voltando a vagar.")
                self._mudar_estado("VAGANDO")
                self.flee_destination = None

        # ====================================================================
        # PRIORIDADE 1: FUGIR (HP muito baixo)
        # ====================================================================
        if self.bot.vida_atual <= limite_hp_fugir:
            zona_perigo = self.dist_borda_segura
            em_zona_perigo = (
                self.bot.posicao.x < zona_perigo or
                self.bot.posicao.x > self.map_width - zona_perigo or
                self.bot.posicao.y < zona_perigo or
                self.bot.posicao.y > self.map_height - zona_perigo
            )

            if em_zona_perigo:
                # Chegou na borda, para e regenera
                self._mudar_estado("REGENERANDO_NA_BORDA")
                self.bot.posicao_alvo_mouse = None
                self.flee_destination = None
            else:
                # Precisa fugir
                if self.estado_ia != "FUGINDO":
                    self._mudar_estado("FUGINDO")
                    # Calcula destino de fuga inteligente
                    self.flee_destination = self._calcular_direcao_fuga_inteligente()
                    print(f"[{self.bot.nome}] HP baixo! Fugindo para {self.flee_destination}")

                if self.flee_destination:
                    # Aplica zigue-zague para dificultar ser atingido
                    destino_com_zz = self._aplicar_zigue_zague(self.flee_destination)
                    self.bot.posicao_alvo_mouse = destino_com_zz

            # Kiting: atira enquanto foge
            self.bot.alvo_selecionado = self._find_closest_threat()
            return

        # ====================================================================
        # RESETAR ESTADO DE FUGA (se HP recuperou)
        # ====================================================================
        if self.estado_ia == "FUGINDO":
            self._mudar_estado("VAGANDO")
            self.flee_destination = None

        # ====================================================================
        # PRIORIDADE 2: EVITAR BORDAS (com curvas suaves)
        # ====================================================================
        if self.estado_ia != "EVITANDO_BORDA":
            zona_perigo = self.dist_borda_segura
            em_zona_perigo = (
                self.bot.posicao.x < zona_perigo or
                self.bot.posicao.x > self.map_width - zona_perigo or
                self.bot.posicao.y < zona_perigo or
                self.bot.posicao.y > self.map_height - zona_perigo
            )

            if em_zona_perigo:
                self._mudar_estado("EVITANDO_BORDA")
                self.bot.alvo_selecionado = None

        if self.estado_ia == "EVITANDO_BORDA":
            zona_segura = self.dist_borda_segura + 200
            em_zona_segura = (
                self.bot.posicao.x > zona_segura and
                self.bot.posicao.x < self.map_width - zona_segura and
                self.bot.posicao.y > zona_segura and
                self.bot.posicao.y < self.map_height - zona_segura
            )

            if em_zona_segura:
                self._mudar_estado("VAGANDO")
            else:
                # Move para o centro com curva suave
                centro_mapa = pygame.math.Vector2(self.map_width / 2, self.map_height / 2)
                forca_borda = self._calcular_forca_borda()

                # Combina direção do centro com a força da borda
                destino = centro_mapa + forca_borda
                self.bot.posicao_alvo_mouse = destino
            return

        # ====================================================================
        # ESTADO: COLETANDO VIDA
        # ====================================================================
        if self.estado_ia == "COLETANDO":
            vida_perto = None
            dist_min = self.distancia_scan_geral

            if self.grupo_vidas_ref:
                for vida in self.grupo_vidas_ref:
                    if not vida.groups() or not hasattr(vida, 'posicao'):
                        continue
                    try:
                        dist = self.bot.posicao.distance_to(vida.posicao)
                        if dist < dist_min:
                            dist_min = dist
                            vida_perto = vida
                    except (ValueError, AttributeError):
                        continue

            if vida_perto:
                self.bot.posicao_alvo_mouse = vida_perto.posicao
            else:
                self._mudar_estado("VAGANDO")
            return

        # ====================================================================
        # ESTADO: CAÇANDO (indo atrás de alvo distante)
        # ====================================================================
        if self.estado_ia == "CAÇANDO":
            alvo = self.bot.alvo_selecionado

            if not (alvo and alvo.groups() and hasattr(alvo, 'vida_atual') and alvo.vida_atual > 0):
                self._mudar_estado("VAGANDO")
                return

            try:
                distancia_alvo = self.bot.posicao.distance_to(alvo.posicao)
                if distancia_alvo < self.distancia_scan_inimigo:
                    self._mudar_estado("ATACANDO")
                    return

                self.bot.posicao_alvo_mouse = alvo.posicao
                return
            except (ValueError, AttributeError):
                self._mudar_estado("VAGANDO")

        # ====================================================================
        # ESTADO: ATACANDO (combate em órbita)
        # ====================================================================
        if self.estado_ia == "ATACANDO":
            alvo = self.bot.alvo_selecionado

            if not (alvo and alvo.groups() and hasattr(alvo, 'vida_atual') and alvo.vida_atual > 0):
                self._mudar_estado("VAGANDO")
                return

            try:
                direcao_alvo_vec = alvo.posicao - self.bot.posicao
                distancia_alvo = direcao_alvo_vec.length()

                # Se ficou muito longe, volta a caçar
                if distancia_alvo > self.distancia_scan_inimigo:
                    self._mudar_estado("CAÇANDO")
                    return

                ponto_movimento = self.bot.posicao

                # Lógica de órbita dinâmica
                if distancia_alvo > self.distancia_orbita_max:
                    # Muito longe, avança
                    ponto_movimento = alvo.posicao

                elif distancia_alvo < self.distancia_orbita_min:
                    # Muito perto, recua
                    if direcao_alvo_vec.length() > 0:
                        ponto_movimento = self.bot.posicao - direcao_alvo_vec.normalize() * 200

                else:
                    # Distância ideal, orbita
                    if direcao_alvo_vec.length() > 0:
                        # Atualiza timer de troca de órbita
                        self.timer_troca_orbita += 1
                        if self.timer_troca_orbita > self.duracao_orbita_atual:
                            self.timer_troca_orbita = 0
                            self.direcao_orbita = -self.direcao_orbita
                            self.duracao_orbita_atual = random.randint(60, 180)
                            # Adiciona variação no ângulo
                            self.variacao_angulo_orbita = random.uniform(-20, 20)

                        # Calcula ângulo de órbita com variação
                        angulo_orbita = 75 + self.variacao_angulo_orbita
                        vetor_orbita = direcao_alvo_vec.rotate(angulo_orbita * self.direcao_orbita)

                        if vetor_orbita.length() > 0:
                            vetor_orbita = vetor_orbita.normalize()

                        # Adiciona micro-movimento para parecer mais natural
                        micro = self._gerar_micro_movimento()
                        ponto_movimento = self.bot.posicao + vetor_orbita * 200 + micro

                # Aplica força de repulsão das bordas
                forca_borda = self._calcular_forca_borda()
                if forca_borda.length() > 0:
                    ponto_movimento = ponto_movimento + forca_borda

                # Limita às bordas do mapa
                margem = 50
                ponto_movimento.x = max(margem, min(ponto_movimento.x, self.map_width - margem))
                ponto_movimento.y = max(margem, min(ponto_movimento.y, self.map_height - margem))

                self.bot.posicao_alvo_mouse = ponto_movimento
                return

            except (ValueError, AttributeError):
                self._mudar_estado("VAGANDO")

        # ====================================================================
        # ESTADO: VAGANDO (exploração)
        # ====================================================================
        if self.estado_ia == "VAGANDO":
            # Se HP < 80%, para de andar para regenerar
            if self.bot.vida_atual < limite_hp_regenerar:
                self.bot.posicao_alvo_mouse = None
            else:
                # HP alto: anda aleatoriamente
                chegou_perto = False
                if self.bot_wander_target:
                    try:
                        if self.bot.posicao.distance_to(self.bot_wander_target) < 100:
                            chegou_perto = True
                    except (ValueError, AttributeError):
                        chegou_perto = True

                # Atualiza timer de wander
                self.timer_wander += 1
                if self.timer_wander > self.duracao_wander_atual:
                    chegou_perto = True

                if self.bot_wander_target is None or chegou_perto:
                    self.timer_wander = 0
                    self.duracao_wander_atual = random.randint(180, 360)

                    map_margin = 150
                    max_tentativas = 10

                    for _ in range(max_tentativas):
                        target_x = random.randint(map_margin, self.map_width - map_margin)
                        target_y = random.randint(map_margin, self.map_height - map_margin)
                        potencial_alvo = pygame.math.Vector2(target_x, target_y)

                        # Evita áreas onde levou dano recentemente
                        if not self._esta_em_area_perigosa(potencial_alvo):
                            self.bot_wander_target = potencial_alvo
                            break
                    else:
                        # Se não achou ponto seguro, vai para qualquer lugar
                        target_x = random.randint(map_margin, self.map_width - map_margin)
                        target_y = random.randint(map_margin, self.map_height - map_margin)
                        self.bot_wander_target = pygame.math.Vector2(target_x, target_y)

                # Adiciona micro-movimento
                micro = self._gerar_micro_movimento()
                destino = self.bot_wander_target + micro

                # Limita às bordas
                margem = 50
                destino.x = max(margem, min(destino.x, self.map_width - margem))
                destino.y = max(margem, min(destino.y, self.map_height - margem))

                self.bot.posicao_alvo_mouse = destino

    # ========================================================================
    # MÉTODO DE RESET
    # ========================================================================

    def resetar_ia(self):
        """
        Chamado quando o bot morre/respawna.
        Reseta todas as variáveis de estado para os valores iniciais.
        """
        # Reseta o alvo e movimento
        self.bot.alvo_selecionado = None
        self.bot.posicao_alvo_mouse = None

        # Reseta estado
        self.estado_ia = "VAGANDO"
        self.estado_anterior = "VAGANDO"
        self.frames_no_estado_atual = 0

        # Reseta detecção de preso
        self.frames_sem_movimento = 0
        self.posicao_anterior = pygame.math.Vector2(0, 0)

        # Reseta órbita
        self.direcao_orbita = random.choice([1, -1])
        self.timer_troca_orbita = 0
        self.duracao_orbita_atual = random.randint(60, 180)
        self.variacao_angulo_orbita = random.uniform(-15, 15)

        # Reseta micro-movimento
        self.timer_micro_movimento = 0
        self.duracao_micro_movimento = random.randint(30, 90)
        self.offset_micro = pygame.math.Vector2(0, 0)

        # Reseta fuga
        self.flee_destination = None
        self.zigue_zague_direcao = 1
        self.timer_zigue_zague = 0
        self.duracao_zigue_zague = random.randint(10, 25)

        # Reseta memória de dano
        self.locais_dano_recente = []

        # Reseta wandering
        self.bot_wander_target = None
        self.timer_wander = 0
        self.duracao_wander_atual = random.randint(180, 360)

        # Reseta desvio de projéteis
        self.frames_desviando = 0
        self.direcao_desvio = None


# ============================================================================
# FIM DO MÓDULO botia.py
# ============================================================================
