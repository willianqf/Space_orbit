import pygame
import random
import math
from enum import Enum, auto
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import settings as s


class Personalidade(Enum):
    """Personalidades que afetam comportamento geral do bot."""
    AGRESSIVO = auto()
    DEFENSIVO = auto()
    EQUILIBRADO = auto()
    OPORTUNISTA = auto()
    VETERANO = auto()


class EstadoEmocional(Enum):
    """Estado emocional que afeta tomada de decisão."""
    CALMO = auto()
    ALERTA = auto()
    ESTRESSADO = auto()
    PANICO = auto()
    CONFIANTE = auto()


@dataclass
class MemoriaAmeaca:
    """Memória de uma ameaça encontrada."""
    entidade: Any
    posicao_ultima: pygame.math.Vector2
    dano_recebido: float = 0.0
    vezes_encontrada: int = 1
    timestamp: int = 0
    nivel_perigo: float = 0.5
    direcao_movimento: Optional[pygame.math. Vector2] = None
    velocidade_estimada: float = 0.0


@dataclass
class PercepcaoAmbiente:
    """Percepção atual do ambiente ao redor."""
    ameacas_proximas: List[Any] = field(default_factory=list)
    aliados_proximos: List[Any] = field(default_factory=list)
    itens_vida: List[Any] = field(default_factory=list)
    projeteis_perigosos: List[Any] = field(default_factory=list)
    zona_segura: bool = True
    direcao_perigo_principal: Optional[pygame. math.Vector2] = None
    nivel_perigo_geral: float = 0.0
    espaco_para_manobra: Dict[str, float] = field(default_factory=dict)


class SistemaPredicao:
    """Sistema para prever movimento de entidades."""
    
    def __init__(self):
        self.historico_posicoes: Dict[int, deque] = {}
        self.max_historico = 10
    
    def atualizar(self, entidade_id: int, posicao: pygame. math.Vector2):
        """Atualiza histórico de posições de uma entidade."""
        if entidade_id not in self. historico_posicoes:
            self.historico_posicoes[entidade_id] = deque(maxlen=self.max_historico)
        self.historico_posicoes[entidade_id].append(posicao. copy())
    
    def prever_posicao(self, entidade_id: int, frames_futuro: int = 30) -> Optional[pygame.math.Vector2]:
        """Prevê posição futura baseado no histórico."""
        if entidade_id not in self.historico_posicoes:
            return None
        
        historico = self.historico_posicoes[entidade_id]
        if len(historico) < 3:
            return None
        
        velocidades = []
        for i in range(1, len(historico)):
            vel = historico[i] - historico[i-1]
            velocidades.append(vel)
        
        if not velocidades:
            return None
        
        vel_media = pygame.math.Vector2(0, 0)
        peso_total = 0
        for i, vel in enumerate(velocidades):
            peso = i + 1
            vel_media += vel * peso
            peso_total += peso
        
        vel_media /= peso_total
        posicao_atual = historico[-1]
        return posicao_atual + (vel_media * frames_futuro)
    
    def obter_velocidade(self, entidade_id: int) -> Optional[pygame.math. Vector2]:
        """Obtém velocidade atual estimada."""
        if entidade_id not in self.historico_posicoes:
            return None
        
        historico = self.historico_posicoes[entidade_id]
        if len(historico) < 2:
            return None
        
        return historico[-1] - historico[-2]
    
    def limpar_entidade(self, entidade_id: int):
        """Remove entidade do histórico."""
        if entidade_id in self.historico_posicoes:
            del self. historico_posicoes[entidade_id]


class SistemaDecisao:
    """Sistema de tomada de decisão baseado em utilidade."""
    
    def __init__(self, personalidade: Personalidade):
        self. personalidade = personalidade
        self._configurar_pesos()
    
    def _configurar_pesos(self):
        """Configura pesos baseado na personalidade."""
        self.pesos = {
            'atacar': 1.0,
            'fugir': 1.0,
            'coletar_vida': 1.0,
            'patrulhar': 1.0,
            'emboscar': 1.0,
            'recuar_tatico': 1.0,
        }
        
        if self.personalidade == Personalidade. AGRESSIVO:
            self.pesos['atacar'] = 1.5
            self.pesos['fugir'] = 0.6
            self.pesos['emboscar'] = 0.8
            
        elif self.personalidade == Personalidade.DEFENSIVO:
            self.pesos['atacar'] = 0.7
            self.pesos['fugir'] = 1.4
            self.pesos['coletar_vida'] = 1.3
            self.pesos['recuar_tatico'] = 1.3
            
        elif self.personalidade == Personalidade. OPORTUNISTA:
            self.pesos['atacar'] = 1.2
            self.pesos['emboscar'] = 1.4
            self.pesos['coletar_vida'] = 1.2
            
        elif self.personalidade == Personalidade.VETERANO:
            self.pesos['atacar'] = 1.1
            self.pesos['recuar_tatico'] = 1.2
            self.pesos['emboscar'] = 1.2
    
    def calcular_utilidade(self, acao: str, contexto: dict) -> float:
        """Calcula utilidade de uma ação dado o contexto."""
        utilidade_base = 0.0
        
        hp_percent = contexto.get('hp_percent', 1.0)
        num_ameacas = contexto.get('num_ameacas', 0)
        distancia_alvo = contexto. get('distancia_alvo', float('inf'))
        hp_alvo_percent = contexto. get('hp_alvo_percent', 1.0)
        tem_vida_proxima = contexto. get('tem_vida_proxima', False)
        nivel_perigo = contexto.get('nivel_perigo', 0.0)
        estado_emocional = contexto.get('estado_emocional', EstadoEmocional.CALMO)
        
        if acao == 'atacar':
            if distancia_alvo < float('inf'):
                utilidade_base = 50 + (1 - hp_alvo_percent) * 30
                utilidade_base += max(0, (600 - distancia_alvo) / 10)
                
                if hp_percent < 0.3:
                    utilidade_base *= 0.5
                    
        elif acao == 'fugir':
            if hp_percent < 0.5:
                utilidade_base = (1 - hp_percent) * 100
            
            utilidade_base += num_ameacas * 15
            utilidade_base += nivel_perigo * 30
            
            if estado_emocional == EstadoEmocional.PANICO:
                utilidade_base *= 1.5
                
        elif acao == 'coletar_vida':
            if tem_vida_proxima and hp_percent < 0.8:
                utilidade_base = (1 - hp_percent) * 80
                
                if hp_percent < 0.3:
                    utilidade_base *= 1.5
                    
        elif acao == 'patrulhar':
            if num_ameacas == 0 and hp_percent > 0.5:
                utilidade_base = 30
                
        elif acao == 'emboscar':
            if hp_percent > 0.6 and distancia_alvo < 500:
                utilidade_base = 40 + (1 - hp_alvo_percent) * 20
                
        elif acao == 'recuar_tatico':
            if hp_percent < 0.5 and hp_percent > 0.2:
                utilidade_base = 50
                if num_ameacas > 1:
                    utilidade_base += 20
        
        utilidade_final = utilidade_base * self.pesos. get(acao, 1.0)
        
        variacao = random.gauss(0, 5)
        utilidade_final += variacao
        
        return max(0, utilidade_final)
    
    def escolher_acao(self, contexto: dict) -> str:
        """Escolhe a melhor ação baseado em utilidades."""
        acoes = ['atacar', 'fugir', 'coletar_vida', 'patrulhar', 'emboscar', 'recuar_tatico']
        
        utilidades = {acao: self.calcular_utilidade(acao, contexto) for acao in acoes}
        
        soma_utilidades = sum(utilidades.values())
        if soma_utilidades <= 0:
            return 'patrulhar'
        
        if random.random() < 0.8:
            return max(utilidades, key=utilidades. get)
        else:
            r = random.random() * soma_utilidades
            acumulado = 0
            for acao, util in utilidades.items():
                acumulado += util
                if acumulado >= r:
                    return acao
            return max(utilidades, key=utilidades.get)


class BotAI:
    """
    IA avançada que simula comportamento humano.
    Inclui memória, predição, personalidade e imperfeições.
    """

    def __init__(self, bot_nave):
        self.bot = bot_nave
        self.frame_atual = 0

        # Dimensões do mapa
        self. map_width = s.MAP_WIDTH
        self.map_height = s.MAP_HEIGHT

        # === PERSONALIDADE E EMOÇÃO ===
        self.personalidade = random.choice(list(Personalidade))
        self. estado_emocional = EstadoEmocional.CALMO
        self. nivel_estresse = 0.0
        self. confianca = 0.5
        
        # === CARACTERÍSTICAS HUMANAS ===
        self._gerar_caracteristicas_humanas()
        
        # === SISTEMAS ===
        self. sistema_predicao = SistemaPredicao()
        self.sistema_decisao = SistemaDecisao(self. personalidade)
        self.percepcao = PercepcaoAmbiente()
        
        # === MEMÓRIA ===
        self. memoria_ameacas: Dict[int, MemoriaAmeaca] = {}
        self.tempo_memoria = 300
        
        # === ESTADO ===
        self. estado_atual = "PATRULHANDO"
        self.estado_anterior = "PATRULHANDO"
        self.frames_no_estado = 0
        
        # === TIMERS E DELAYS ===
        self.delay_reacao_restante = 0
        self.delay_proximo_tiro = 0
        self.timer_reavaliacao = 0
        self.intervalo_reavaliacao = random.randint(15, 30)
        
        # === MOVIMENTO ===
        self.destino_atual: Optional[pygame.math.Vector2] = None
        self. direcao_strafe = random.choice([-1, 1])
        self. timer_strafe = 0
        self.duracao_strafe = random.randint(20, 60)
        
        # === COMBATE ===
        self.alvo_principal = None
        self. ultimo_dano_recebido_frame = 0
        self.dano_recebido_recente = 0.0
        self. tiros_disparados = 0
        self.tiros_acertados = 0
        
        # === DETECÇÃO ===
        self. raio_visao = 700
        self.raio_visao_sq = self.raio_visao ** 2
        self.raio_audicao = 400
        self.raio_audicao_sq = self. raio_audicao ** 2
        self.angulo_visao = 160
        
        # === DISTÂNCIAS DE COMBATE ===
        self.distancia_ideal_combate = random.randint(250, 350)
        self. distancia_minima = 150
        self.distancia_maxima_engajamento = 500
        
        # === CACHE DE REFERÊNCIAS ===
        self.player_ref = None
        self.grupo_bots_ref = None
        self.grupo_inimigos_ref = None
        self.grupo_obstaculos_ref = None
        self.grupo_vidas_ref = None
        self.lista_projeteis_ref = None
        
        # === ANTI-STUCK ===
        self.posicao_anterior = pygame.math.Vector2(0, 0)
        self.frames_parado = 0
        self.historico_posicoes: deque = deque(maxlen=60)

    def _gerar_caracteristicas_humanas(self):
        """Gera características únicas que simulam variação humana."""
        if self.personalidade == Personalidade. VETERANO:
            self. tempo_reacao_base = random.randint(8, 12)
            self. precisao_mira = random.uniform(0.85, 0.98)
        else:
            self. tempo_reacao_base = random.randint(12, 20)
            self. precisao_mira = random.uniform(0.7, 0.95)
        
        self.resistencia_pressao = random.uniform(0.5, 0.9)
        
        if self.personalidade == Personalidade. AGRESSIVO:
            self.agressividade = random.uniform(0.7, 1.0)
        elif self.personalidade == Personalidade. DEFENSIVO:
            self.agressividade = random. uniform(0.2, 0.5)
        else:
            self.agressividade = random.uniform(0.3, 0.8)
        
        self.paciencia = random.uniform(0.3, 0.8)
        self.vigilancia = random.uniform(0.5, 0.9)
        
        self.fadiga = 0.0
        self.taxa_fadiga = random.uniform(0.0001, 0.0005)
        self. taxa_recuperacao_fadiga = random. uniform(0.001, 0.003)

    # =========================================================================
    # LOOP PRINCIPAL
    # =========================================================================

    def update_ai(self, player_ref, grupo_bots_ref, grupo_inimigos_ref,
                  grupo_obstaculos_ref, grupo_vidas_ref,
                  map_width=None, map_height=None, lista_projeteis_hostis=None):
        """Método principal de atualização da IA."""
        
        if map_width:
            self.map_width = map_width
        if map_height:
            self.map_height = map_height
        
        self.player_ref = player_ref
        self.grupo_bots_ref = grupo_bots_ref
        self.grupo_inimigos_ref = grupo_inimigos_ref
        self.grupo_obstaculos_ref = grupo_obstaculos_ref
        self.grupo_vidas_ref = grupo_vidas_ref
        self.lista_projeteis_ref = lista_projeteis_hostis
        
        self.frame_atual += 1
        self.frames_no_estado += 1
        
        self._atualizar_percepcao()
        self._atualizar_estado_emocional()
        self._verificar_stuck()
        self._tomar_decisao()
        self._executar_estado_atual()
        self._atualizar_fadiga()
        self._limpar_memorias_antigas()
        self._diminuir_dano_recente()

    # =========================================================================
    # PERCEPÇÃO
    # =========================================================================

    def _atualizar_percepcao(self):
        """Atualiza a percepção do ambiente."""
        self.percepcao = PercepcaoAmbiente()
        pos = self.bot.posicao
        
        margem = 150
        self.percepcao. espaco_para_manobra = {
            'norte': pos.y - margem,
            'sul': self.map_height - pos.y - margem,
            'leste': self.map_width - pos.x - margem,
            'oeste': pos.x - margem
        }
        
        self._detectar_ameacas()
        self._detectar_itens()
        self._detectar_projeteis_perigosos()
        self._calcular_nivel_perigo()
        
        self.percepcao. zona_segura = self. percepcao.nivel_perigo_geral < 0.3

    def _detectar_ameacas(self):
        """Detecta e avalia ameaças ao redor."""
        ameacas = []
        
        def processar_entidade(entidade):
            if entidade == self.bot or not self._esta_vivo(entidade):
                return
            
            if hasattr(entidade, 'owner') and entidade. owner == self.bot:
                return
            
            try:
                dist_sq = self.bot.posicao. distance_squared_to(entidade.posicao)
                
                if dist_sq > self.raio_visao_sq:
                    return
                
                if not self._esta_no_campo_visao(entidade. posicao):
                    if dist_sq > self.raio_audicao_sq:
                        return
                
                entidade_id = id(entidade)
                self.sistema_predicao.atualizar(entidade_id, entidade. posicao)
                
                if entidade_id in self.memoria_ameacas:
                    mem = self.memoria_ameacas[entidade_id]
                    mem. posicao_ultima = entidade. posicao. copy()
                    mem.vezes_encontrada += 1
                    mem.timestamp = self.frame_atual
                    
                    vel = self.sistema_predicao.obter_velocidade(entidade_id)
                    if vel and vel.length() > 0.1:
                        mem.direcao_movimento = vel.normalize()
                        mem.velocidade_estimada = vel. length()
                else:
                    self.memoria_ameacas[entidade_id] = MemoriaAmeaca(
                        entidade=entidade,
                        posicao_ultima=entidade. posicao.copy(),
                        timestamp=self.frame_atual
                    )
                
                nivel_perigo = self._avaliar_perigo_entidade(entidade, dist_sq)
                self.memoria_ameacas[entidade_id].nivel_perigo = nivel_perigo
                
                ameacas.append((entidade, dist_sq, nivel_perigo))
                
            except (AttributeError, ValueError):
                pass
        
        if self.player_ref:
            processar_entidade(self.player_ref)
        
        if self.grupo_bots_ref:
            for bot in self.grupo_bots_ref:
                processar_entidade(bot)
        
        if self.grupo_inimigos_ref:
            for inimigo in self. grupo_inimigos_ref:
                processar_entidade(inimigo)
        
        ameacas.sort(key=lambda x: x[2], reverse=True)
        self.percepcao.ameacas_proximas = [a[0] for a in ameacas]
        
        if ameacas:
            perigo_principal = ameacas[0][0]
            try:
                dir_perigo = perigo_principal.posicao - self.bot.posicao
                if dir_perigo. length() > 0:
                    self.percepcao.direcao_perigo_principal = dir_perigo.normalize()
            except (ValueError, AttributeError):
                pass

    def _avaliar_perigo_entidade(self, entidade, dist_sq) -> float:
        """Avalia o nível de perigo de uma entidade."""
        perigo = 0.0
        
        dist = math.sqrt(dist_sq)
        perigo += max(0, (self.raio_visao - dist) / self. raio_visao) * 0.4
        
        max_vida = max(getattr(entidade, 'max_vida', 1), 1)
        hp_percent = getattr(entidade, 'vida_atual', 0) / max_vida
        perigo += hp_percent * 0.3
        
        entidade_id = id(entidade)
        if entidade_id in self.memoria_ameacas:
            mem = self.memoria_ameacas[entidade_id]
            if mem. dano_recebido > 0:
                perigo += min(mem.dano_recebido / 100, 0.3)
        
        if entidade == self.player_ref:
            perigo += 0.1
        
        return min(perigo, 1.0)

    def _esta_no_campo_visao(self, posicao_alvo: pygame.math.Vector2) -> bool:
        """Verifica se uma posição está no campo de visão do bot."""
        try:
            direcao_bot = pygame.math.Vector2(1, 0). rotate(-self.bot.angulo)
            dir_alvo = posicao_alvo - self.bot.posicao
            if dir_alvo. length() == 0:
                return True
            direcao_alvo = dir_alvo.normalize()
            
            dot = direcao_bot.dot(direcao_alvo)
            angulo = math.degrees(math.acos(max(-1, min(1, dot))))
            
            return angulo <= self.angulo_visao / 2
        except (ValueError, ZeroDivisionError):
            return True

    def _detectar_itens(self):
        """Detecta itens de vida próximos."""
        if not self.grupo_vidas_ref:
            return
        
        for vida in self.grupo_vidas_ref:
            if not vida. groups():
                continue
            try:
                dist_sq = self.bot.posicao. distance_squared_to(vida.posicao)
                if dist_sq < self.raio_visao_sq:
                    self.percepcao.itens_vida. append(vida)
            except AttributeError:
                continue

    def _detectar_projeteis_perigosos(self):
        """Detecta projéteis que representam perigo."""
        if not self.lista_projeteis_ref:
            return
        
        raio_deteccao_sq = 300 ** 2
        
        for proj in self.lista_projeteis_ref:
            if getattr(proj, 'owner', None) == self.bot:
                continue
            
            try:
                dist_sq = self. bot.posicao.distance_squared_to(proj.posicao)
                if dist_sq > raio_deteccao_sq:
                    continue
                
                vel = getattr(proj, 'velocidade_vetor', None)
                if vel and vel. length_squared() > 0.1:
                    dir_para_nos = self.bot.posicao - proj.posicao
                    if dir_para_nos.length_squared() > 0:
                        if vel.normalize().dot(dir_para_nos.normalize()) > 0.3:
                            self. percepcao.projeteis_perigosos.append(proj)
                            
            except (AttributeError, ValueError):
                continue

    def _calcular_nivel_perigo(self):
        """Calcula nível geral de perigo."""
        perigo = 0.0
        
        num_ameacas = len(self. percepcao. ameacas_proximas)
        perigo += min(num_ameacas * 0.15, 0.45)
        
        num_projeteis = len(self.percepcao.projeteis_perigosos)
        perigo += min(num_projeteis * 0.1, 0.3)
        
        hp_percent = self. bot.vida_atual / max(self.bot.max_vida, 1)
        if hp_percent < 0.5:
            perigo += (1 - hp_percent) * 0.3
        
        if self. dano_recebido_recente > 0:
            perigo += min(self. dano_recebido_recente / 100, 0.2)
        
        espaco_min = min(self.percepcao.espaco_para_manobra. values()) if self.percepcao.espaco_para_manobra else 0
        if espaco_min < 100:
            perigo += 0.1
        
        self.percepcao.nivel_perigo_geral = min(perigo, 1.0)

    # =========================================================================
    # ESTADO EMOCIONAL
    # =========================================================================

    def _atualizar_estado_emocional(self):
        """Atualiza estado emocional baseado na situação."""
        self.nivel_estresse += self.percepcao.nivel_perigo_geral * 0.02
        
        if self.frame_atual - self. ultimo_dano_recebido_frame < 60:
            self. nivel_estresse += 0.03
        
        if self.percepcao.zona_segura:
            self.nivel_estresse -= 0.01
        
        self.nivel_estresse = max(0, min(1, self.nivel_estresse))
        
        hp_percent = self. bot.vida_atual / max(self. bot.max_vida, 1)
        
        if self.nivel_estresse > 0.8 or hp_percent < 0.15:
            self. estado_emocional = EstadoEmocional.PANICO
        elif self. nivel_estresse > 0.5 or hp_percent < 0.3:
            self. estado_emocional = EstadoEmocional.ESTRESSADO
        elif self.nivel_estresse > 0.2 or len(self.percepcao. ameacas_proximas) > 0:
            self. estado_emocional = EstadoEmocional.ALERTA
        elif hp_percent > 0.8 and len(self.percepcao. ameacas_proximas) == 0:
            self. estado_emocional = EstadoEmocional.CONFIANTE
        else:
            self.estado_emocional = EstadoEmocional.CALMO

    def _obter_multiplicador_reacao(self) -> float:
        """Retorna multiplicador de tempo de reação baseado no estresse."""
        multiplicador = 1.0
        
        if self.estado_emocional == EstadoEmocional.ESTRESSADO:
            multiplicador = 1.3
        elif self. estado_emocional == EstadoEmocional.PANICO:
            multiplicador = 1.6
        
        multiplicador += self.fadiga * 0.5
        
        return multiplicador

    # =========================================================================
    # TOMADA DE DECISÃO
    # =========================================================================

    def _tomar_decisao(self):
        """Processo principal de tomada de decisão."""
        if self.delay_reacao_restante > 0:
            self.delay_reacao_restante -= 1
            return
        
        self.timer_reavaliacao += 1
        if self.timer_reavaliacao < self.intervalo_reavaliacao:
            return
        
        self.timer_reavaliacao = 0
        self.intervalo_reavaliacao = random.randint(10, 25)
        
        mult_reacao = self._obter_multiplicador_reacao()
        self.delay_reacao_restante = int(self.tempo_reacao_base * mult_reacao * random.uniform(0.8, 1.2))
        
        contexto = self._montar_contexto_decisao()
        acao_escolhida = self.sistema_decisao.escolher_acao(contexto)
        self._executar_transicao_estado(acao_escolhida)

    def _montar_contexto_decisao(self) -> dict:
        """Monta contexto para o sistema de decisão."""
        hp_percent = self. bot.vida_atual / max(self. bot.max_vida, 1)
        
        distancia_alvo = float('inf')
        hp_alvo_percent = 1.0
        
        if self.percepcao. ameacas_proximas:
            alvo = self.percepcao.ameacas_proximas[0]
            try:
                distancia_alvo = self.bot.posicao.distance_to(alvo.posicao)
                hp_alvo_percent = getattr(alvo, 'vida_atual', 1) / max(getattr(alvo, 'max_vida', 1), 1)
            except (AttributeError, ValueError):
                pass
        
        return {
            'hp_percent': hp_percent,
            'num_ameacas': len(self. percepcao. ameacas_proximas),
            'distancia_alvo': distancia_alvo,
            'hp_alvo_percent': hp_alvo_percent,
            'tem_vida_proxima': len(self.percepcao.itens_vida) > 0,
            'nivel_perigo': self.percepcao.nivel_perigo_geral,
            'estado_emocional': self. estado_emocional,
            'projeteis_proximos': len(self.percepcao. projeteis_perigosos),
        }

    def _executar_transicao_estado(self, acao: str):
        """Executa transição para novo estado."""
        mapa_estados = {
            'atacar': 'COMBATE',
            'fugir': 'FUGINDO',
            'coletar_vida': 'COLETANDO',
            'patrulhar': 'PATRULHANDO',
            'emboscar': 'EMBOSCANDO',
            'recuar_tatico': 'RECUANDO',
        }
        
        novo_estado = mapa_estados.get(acao, 'PATRULHANDO')
        
        if novo_estado != self.estado_atual:
            self. estado_anterior = self.estado_atual
            self. estado_atual = novo_estado
            self.frames_no_estado = 0
            
            if novo_estado == 'FUGINDO':
                self. destino_atual = None

    # =========================================================================
    # EXECUÇÃO DE ESTADOS
    # =========================================================================

    def _executar_estado_atual(self):
        """Executa lógica do estado atual."""
        self. bot. quer_mover_frente = False
        self.bot. quer_mover_tras = False
        self.bot.quer_atirar = False
        
        if self._desviar_projeteis_se_necessario():
            return
        
        if self.estado_atual == 'COMBATE':
            self._executar_combate()
        elif self.estado_atual == 'FUGINDO':
            self._executar_fuga()
        elif self.estado_atual == 'COLETANDO':
            self._executar_coleta()
        elif self.estado_atual == 'PATRULHANDO':
            self._executar_patrulha()
        elif self.estado_atual == 'EMBOSCANDO':
            self._executar_emboscada()
        elif self.estado_atual == 'RECUANDO':
            self._executar_recuo_tatico()
        else:
            self._executar_patrulha()

    def _desviar_projeteis_se_necessario(self) -> bool:
        """Desvia de projéteis se necessário."""
        if not self.percepcao. projeteis_perigosos:
            return False
        
        proj_mais_proximo = min(
            self.percepcao.projeteis_perigosos,
            key=lambda p: self. bot.posicao.distance_squared_to(p.posicao)
        )
        
        try:
            vel_proj = getattr(proj_mais_proximo, 'velocidade_vetor', pygame.math.Vector2(1, 0))
            if vel_proj. length_squared() > 0:
                perp1 = pygame.math.Vector2(-vel_proj.y, vel_proj. x).normalize()
                perp2 = pygame.math. Vector2(vel_proj.y, -vel_proj.x).normalize()
                
                pos1 = self.bot.posicao + perp1 * 100
                pos2 = self.bot. posicao + perp2 * 100
                
                if pos1.distance_squared_to(proj_mais_proximo.posicao) > pos2.distance_squared_to(proj_mais_proximo.posicao):
                    destino = pos1
                else:
                    destino = pos2
                
                self._clamp_destino(destino)
                self.bot.posicao_alvo_mouse = destino
                
                if self.alvo_principal and self._esta_vivo(self.alvo_principal):
                    self.bot.quer_atirar = True
                
                return True
                
        except (ValueError, AttributeError):
            pass
        
        return False

    def _executar_combate(self):
        """Executa comportamento de combate."""
        if not self.alvo_principal or not self._esta_vivo(self.alvo_principal):
            if self.percepcao. ameacas_proximas:
                self.alvo_principal = self.percepcao.ameacas_proximas[0]
            else:
                self.estado_atual = 'PATRULHANDO'
                return
        
        alvo = self.alvo_principal
        self.bot.alvo_selecionado = alvo
        
        try:
            dist_alvo = self.bot.posicao. distance_to(alvo.posicao)
        except AttributeError:
            self.alvo_principal = None
            return
        
        alvo_id = id(alvo)
        posicao_predita = self.sistema_predicao.prever_posicao(alvo_id, 15)
        
        if posicao_predita:
            erro = pygame.math.Vector2(
                random.gauss(0, 20 * (1 - self.precisao_mira)),
                random.gauss(0, 20 * (1 - self.precisao_mira))
            )
            ponto_mira = posicao_predita + erro
        else:
            ponto_mira = alvo.posicao
        
        self._executar_movimento_combate(alvo, dist_alvo)
        
        self.delay_proximo_tiro -= 1
        
        if self.delay_proximo_tiro <= 0:
            if self._esta_mirando_em(ponto_mira, tolerancia=30):
                self. bot.quer_atirar = True
                self.tiros_disparados += 1
                
                delay_base = 8
                if self. estado_emocional == EstadoEmocional. PANICO:
                    delay_base = 4
                elif self. estado_emocional == EstadoEmocional.CALMO:
                    delay_base = 12
                
                self.delay_proximo_tiro = delay_base + random. randint(-2, 4)

    def _executar_movimento_combate(self, alvo, dist_alvo: float):
        """Executa movimento durante combate (kiting/strafing)."""
        try:
            dir_para_alvo = (alvo.posicao - self.bot.posicao). normalize()
        except (ValueError, ZeroDivisionError):
            return
        
        dir_strafe = pygame.math.Vector2(-dir_para_alvo.y, dir_para_alvo.x) * self.direcao_strafe
        
        self.timer_strafe += 1
        if self.timer_strafe > self.duracao_strafe:
            self.timer_strafe = 0
            self.direcao_strafe *= -1
            self.duracao_strafe = random.randint(20, 60)
            
            if random.random() < 0.2:
                self. duracao_strafe = random.randint(10, 30)
        
        vetor_movimento = pygame.math.Vector2(0, 0)
        
        dist_ideal = self.distancia_ideal_combate
        if self.estado_emocional == EstadoEmocional. CONFIANTE:
            dist_ideal *= 0.8
        elif self.estado_emocional == EstadoEmocional. ESTRESSADO:
            dist_ideal *= 1.2
        
        if dist_alvo > dist_ideal + 50:
            vetor_movimento = dir_para_alvo * 0.6 + dir_strafe * 0.4
        elif dist_alvo < self.distancia_minima:
            vetor_movimento = -dir_para_alvo * 0.6 + dir_strafe * 0.4
        else:
            vetor_movimento = dir_strafe * 0.8
            diff = dist_alvo - dist_ideal
            vetor_movimento += dir_para_alvo * (diff / 500)
        
        if random.random() < 0.1:
            vetor_movimento += pygame.math.Vector2(
                random.uniform(-0.2, 0.2),
                random. uniform(-0.2, 0.2)
            )
        
        if vetor_movimento. length_squared() > 0:
            vetor_movimento = vetor_movimento.normalize()
            destino = self.bot.posicao + vetor_movimento * 150
            self._clamp_destino(destino)
            self.bot. posicao_alvo_mouse = destino

    def _executar_fuga(self):
        """Executa comportamento de fuga."""
        if not self.destino_atual or self.frames_no_estado % 60 == 0:
            self.destino_atual = self._encontrar_destino_fuga()
        
        if self. destino_atual:
            dir_fuga = self.destino_atual - self.bot.posicao
            if dir_fuga.length_squared() > 0:
                dir_fuga = dir_fuga.normalize()
                
                self.timer_strafe += 1
                if self.timer_strafe > 15:
                    self.direcao_strafe *= -1
                    self.timer_strafe = 0
                
                dir_lateral = pygame.math. Vector2(-dir_fuga.y, dir_fuga. x) * self.direcao_strafe * 0.3
                dir_final = (dir_fuga + dir_lateral). normalize()
                
                destino = self.bot.posicao + dir_final * 200
                self._clamp_destino(destino)
                self.bot.posicao_alvo_mouse = destino
        
        if self.percepcao.ameacas_proximas:
            ameaca = self.percepcao.ameacas_proximas[0]
            self. bot.alvo_selecionado = ameaca
            
            if random.random() < 0.3:
                self. bot.quer_atirar = True
        
        if self.percepcao.zona_segura and self.bot.vida_atual > self.bot.max_vida * 0.4:
            self. estado_atual = 'PATRULHANDO'

    def _encontrar_destino_fuga(self) -> pygame.math. Vector2:
        """Encontra melhor destino para fugir."""
        pos = self.bot.posicao
        melhor_destino = None
        melhor_score = float('-inf')
        
        for angulo in range(0, 360, 30):
            direcao = pygame. math.Vector2(1, 0).rotate(angulo)
            candidato = pos + direcao * 400
            
            candidato. x = max(100, min(candidato.x, self.map_width - 100))
            candidato.y = max(100, min(candidato. y, self.map_height - 100))
            
            score = 0
            for ameaca in self. percepcao. ameacas_proximas:
                try:
                    dist = candidato.distance_to(ameaca. posicao)
                    score += dist
                except (AttributeError, ValueError):
                    continue
            
            for vida in self.percepcao.itens_vida:
                try:
                    dist = candidato.distance_to(vida. posicao)
                    if dist < 200:
                        score += 100
                except (AttributeError, ValueError):
                    continue
            
            dist_borda = min(
                candidato.x, candidato.y,
                self.map_width - candidato. x,
                self.map_height - candidato.y
            )
            if dist_borda < 150:
                score -= 200
            
            if score > melhor_score:
                melhor_score = score
                melhor_destino = candidato
        
        return melhor_destino if melhor_destino else pygame.math.Vector2(
            self.map_width / 2, self. map_height / 2
        )

    def _executar_coleta(self):
        """Executa coleta de item de vida."""
        if not self.percepcao.itens_vida:
            self.estado_atual = 'PATRULHANDO'
            return
        
        vida_mais_proxima = min(
            self. percepcao.itens_vida,
            key=lambda v: self.bot.posicao.distance_squared_to(v. posicao)
        )
        
        try:
            self.bot.posicao_alvo_mouse = vida_mais_proxima. posicao
            
            if self.bot.posicao.distance_squared_to(vida_mais_proxima.posicao) < 900:
                self. estado_atual = 'PATRULHANDO'
                
        except AttributeError:
            self.estado_atual = 'PATRULHANDO'
        
        if self. percepcao.ameacas_proximas:
            ameaca = self.percepcao.ameacas_proximas[0]
            try:
                dist = self.bot. posicao.distance_to(ameaca.posicao)
                if dist < 300:
                    self.bot.alvo_selecionado = ameaca
                    self. bot.quer_atirar = True
            except (AttributeError, ValueError):
                pass

    def _executar_patrulha(self):
        """Executa patrulha/exploração."""
        precisa_novo_destino = False
        
        if not self.destino_atual:
            precisa_novo_destino = True
        elif self. bot.posicao. distance_squared_to(self.destino_atual) < 2500:
            precisa_novo_destino = True
        elif self.frames_no_estado > 300:
            precisa_novo_destino = True
        
        if precisa_novo_destino:
            self.destino_atual = self._gerar_destino_patrulha()
            self.frames_no_estado = 0
        
        self.bot.posicao_alvo_mouse = self. destino_atual
        
        if self.bot.vida_atual < self.bot.max_vida * 0.6:
            if self.percepcao.zona_segura:
                self.bot.posicao_alvo_mouse = None

    def _gerar_destino_patrulha(self) -> pygame.math.Vector2:
        """Gera um destino para patrulhar."""
        margem = 150
        
        if random.random() < 0.3:
            centro = pygame.math.Vector2(self.map_width / 2, self. map_height / 2)
            offset = pygame.math.Vector2(
                random. uniform(-200, 200),
                random.uniform(-200, 200)
            )
            return centro + offset
        
        return pygame.math.Vector2(
            random.randint(margem, self.map_width - margem),
            random. randint(margem, self.map_height - margem)
        )

    def _executar_emboscada(self):
        """Executa comportamento de emboscada."""
        if not self.destino_atual or self.frames_no_estado == 1:
            self. destino_atual = self._encontrar_posicao_emboscada()
        
        if self. destino_atual:
            dist = self.bot.posicao.distance_to(self.destino_atual)
            
            if dist > 30:
                self. bot.posicao_alvo_mouse = self. destino_atual
            else:
                self. bot.posicao_alvo_mouse = None
                
                if self.percepcao.ameacas_proximas:
                    alvo = self.percepcao.ameacas_proximas[0]
                    try:
                        dist_alvo = self. bot.posicao.distance_to(alvo.posicao)
                        if dist_alvo < 400:
                            self.alvo_principal = alvo
                            self.estado_atual = 'COMBATE'
                    except (AttributeError, ValueError):
                        pass

    def _encontrar_posicao_emboscada(self) -> pygame.math.Vector2:
        """Encontra boa posição para emboscar."""
        pos = self.bot. posicao
        centro = pygame.math. Vector2(self.map_width / 2, self. map_height / 2)
        return pos. lerp(centro, 0.3)

    def _executar_recuo_tatico(self):
        """Executa recuo mantendo pressão."""
        if not self.percepcao. ameacas_proximas:
            self.estado_atual = 'PATRULHANDO'
            return
        
        alvo = self.percepcao.ameacas_proximas[0]
        self.bot.alvo_selecionado = alvo
        
        try:
            dir_recuo = (self.bot.posicao - alvo. posicao).normalize()
        except (ValueError, ZeroDivisionError):
            dir_recuo = pygame.math.Vector2(1, 0)
        
        self.timer_strafe += 1
        if self.timer_strafe > 25:
            self. direcao_strafe *= -1
            self.timer_strafe = 0
        
        dir_lateral = pygame. math.Vector2(-dir_recuo. y, dir_recuo.x) * self.direcao_strafe
        dir_final = (dir_recuo * 0.7 + dir_lateral * 0.3). normalize()
        
        destino = self.bot.posicao + dir_final * 150
        self._clamp_destino(destino)
        self.bot.posicao_alvo_mouse = destino
        
        self.bot.quer_atirar = True
        
        hp_percent = self. bot.vida_atual / self.bot.max_vida
        if hp_percent > 0.6:
            self. estado_atual = 'COMBATE'

    # =========================================================================
    # UTILIDADES
    # =========================================================================

    def _esta_vivo(self, entidade) -> bool:
        """Verifica se entidade está viva."""
        if not entidade:
            return False
        if not entidade.groups():
            return False
        return getattr(entidade, 'vida_atual', 0) > 0

    def _esta_mirando_em(self, posicao: pygame. math.Vector2, tolerancia: float = 20) -> bool:
        """Verifica se está mirando aproximadamente em uma posição."""
        try:
            dir_atual = pygame.math.Vector2(1, 0).rotate(-self.bot.angulo)
            dir_alvo = posicao - self. bot.posicao
            if dir_alvo. length() == 0:
                return True
            dir_alvo = dir_alvo.normalize()
            
            dot = dir_atual. dot(dir_alvo)
            angulo = math.degrees(math.acos(max(-1, min(1, dot))))
            
            return angulo <= tolerancia
        except (ValueError, ZeroDivisionError):
            return True

    def _clamp_destino(self, destino: pygame.math.Vector2):
        """Limita destino às bordas do mapa."""
        margem = 80
        destino.x = max(margem, min(destino.x, self.map_width - margem))
        destino.y = max(margem, min(destino. y, self.map_height - margem))

    def _verificar_stuck(self):
        """Verifica se o bot está preso."""
        self.historico_posicoes.append(self.bot.posicao.copy())
        
        if len(self.historico_posicoes) >= 60:
            pos_antiga = self.historico_posicoes[0]
            dist_movida = self.bot. posicao.distance_squared_to(pos_antiga)
            
            if dist_movida < 100:
                self.frames_parado += 1
                
                if self.frames_parado > 30:
                    angulo = random.uniform(0, 360)
                    direcao = pygame. math.Vector2(1, 0). rotate(angulo)
                    self. destino_atual = self. bot.posicao + direcao * 200
                    self._clamp_destino(self.destino_atual)
                    self.frames_parado = 0
            else:
                self. frames_parado = 0

    def _atualizar_fadiga(self):
        """Atualiza nível de fadiga."""
        if self. estado_atual in ['COMBATE', 'FUGINDO', 'RECUANDO']:
            self.fadiga += self.taxa_fadiga
        else:
            self.fadiga -= self.taxa_recuperacao_fadiga
        
        self.fadiga = max(0, min(1, self.fadiga))

    def _limpar_memorias_antigas(self):
        """Remove memórias muito antigas."""
        tempo_limite = self.frame_atual - self. tempo_memoria
        
        ids_remover = [
            entidade_id for entidade_id, mem in self.memoria_ameacas.items()
            if mem. timestamp < tempo_limite
        ]
        
        for eid in ids_remover:
            del self.memoria_ameacas[eid]
            self.sistema_predicao.limpar_entidade(eid)

    def _diminuir_dano_recente(self):
        """Diminui gradualmente o registro de dano recente."""
        if self. dano_recebido_recente > 0:
            self. dano_recebido_recente *= 0.98

    def registrar_dano_recebido(self, quantidade: float, atacante=None):
        """Registra dano recebido para memória e reação."""
        self. dano_recebido_recente += quantidade
        self.ultimo_dano_recebido_frame = self.frame_atual
        self.nivel_estresse += 0.1
        
        if atacante:
            atacante_id = id(atacante)
            if atacante_id in self.memoria_ameacas:
                self. memoria_ameacas[atacante_id]. dano_recebido += quantidade
                self.memoria_ameacas[atacante_id].nivel_perigo = min(
                    1.0, self. memoria_ameacas[atacante_id].nivel_perigo + 0.1
                )

    def registrar_acerto(self):
        """Registra que um tiro acertou o alvo."""
        self.tiros_acertados += 1
        self.confianca = min(1.0, self.confianca + 0.02)

    def resetar_ia(self):
        """Reseta a IA para estado inicial."""
        self. bot.alvo_selecionado = None
        self.bot.posicao_alvo_mouse = None
        self.estado_atual = "PATRULHANDO"
        self.estado_anterior = "PATRULHANDO"
        self.frames_no_estado = 0
        self. frames_parado = 0
        self.alvo_principal = None
        self.destino_atual = None
        self.nivel_estresse = 0.0
        self. fadiga = 0.0
        self.dano_recebido_recente = 0.0
        self.memoria_ameacas. clear()
        self.sistema_predicao.historico_posicoes.clear()
        self.historico_posicoes.clear()
        self.estado_emocional = EstadoEmocional.CALMO