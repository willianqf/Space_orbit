import pygame
import random
import math
from enum import Enum, auto
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import settings as s

# Tenta importar tipos de inimigos para prioridade
try:
    from enemies import InimigoAtordoador, BossCongelante, MinionCongelante
    TIPOS_PRIORITARIOS = (InimigoAtordoador, BossCongelante, MinionCongelante)
except ImportError:
    TIPOS_PRIORITARIOS = ()

class Personalidade(Enum):
    AGRESSIVO = auto()
    DEFENSIVO = auto()
    EQUILIBRADO = auto()
    OPORTUNISTA = auto()
    VETERANO = auto()

class EstadoEmocional(Enum):
    CALMO = auto()
    ALERTA = auto()
    ESTRESSADO = auto()
    PANICO = auto()
    CONFIANTE = auto()

@dataclass
class MemoriaAmeaca:
    entidade: Any
    posicao_ultima: pygame.math.Vector2
    dano_recebido: float = 0.0
    vezes_encontrada: int = 1
    timestamp: int = 0
    nivel_perigo: float = 0.5
    direcao_movimento: Optional[pygame.math.Vector2] = None
    velocidade_estimada: float = 0.0

@dataclass
class PercepcaoAmbiente:
    ameacas_proximas: List[Any] = field(default_factory=list)
    aliados_proximos: List[Any] = field(default_factory=list)
    itens_vida: List[Any] = field(default_factory=list)
    projeteis_perigosos: List[Any] = field(default_factory=list)
    zona_segura: bool = True
    distancia_ameaca_mais_proxima: float = float('inf') # Novo campo
    direcao_perigo_principal: Optional[pygame.math.Vector2] = None
    nivel_perigo_geral: float = 0.0
    espaco_para_manobra: Dict[str, float] = field(default_factory=dict)

class SistemaPredicao:
    def __init__(self):
        self.historico_posicoes: Dict[int, deque] = {}
        self.max_historico = 10
    
    def atualizar(self, entidade_id: int, posicao: pygame.math.Vector2):
        if entidade_id not in self.historico_posicoes:
            self.historico_posicoes[entidade_id] = deque(maxlen=self.max_historico)
        self.historico_posicoes[entidade_id].append(posicao.copy())
    
    def prever_posicao(self, entidade_id: int, frames_futuro: int = 30) -> Optional[pygame.math.Vector2]:
        if entidade_id not in self.historico_posicoes: return None
        historico = self.historico_posicoes[entidade_id]
        if len(historico) < 3: return None
        velocidades = []
        for i in range(1, len(historico)):
            vel = historico[i] - historico[i-1]
            velocidades.append(vel)
        if not velocidades: return None
        vel_media = pygame.math.Vector2(0, 0)
        peso_total = 0
        for i, vel in enumerate(velocidades):
            peso = i + 1
            vel_media += vel * peso
            peso_total += peso
        vel_media /= peso_total
        return historico[-1] + (vel_media * frames_futuro)
    
    def obter_velocidade(self, entidade_id: int) -> Optional[pygame.math.Vector2]:
        if entidade_id not in self.historico_posicoes: return None
        historico = self.historico_posicoes[entidade_id]
        if len(historico) < 2: return None
        return historico[-1] - historico[-2]
    
    def limpar_entidade(self, entidade_id: int):
        if entidade_id in self.historico_posicoes: del self.historico_posicoes[entidade_id]

class SistemaDecisao:
    def __init__(self, personalidade: Personalidade):
        self.personalidade = personalidade
        self._configurar_pesos()
    
    def _configurar_pesos(self):
        self.pesos = {'atacar': 1.0, 'fugir': 1.0, 'coletar_vida': 1.0, 'patrulhar': 1.0, 'emboscar': 1.0, 'recuar_tatico': 1.0}
        if self.personalidade == Personalidade.AGRESSIVO:
            self.pesos['atacar'] = 2.5; self.pesos['fugir'] = 0.1; self.pesos['emboscar'] = 0.8
        elif self.personalidade == Personalidade.DEFENSIVO:
            self.pesos['atacar'] = 0.9; self.pesos['fugir'] = 1.1; self.pesos['coletar_vida'] = 1.3; self.pesos['recuar_tatico'] = 1.3
        elif self.personalidade == Personalidade.OPORTUNISTA:
            self.pesos['atacar'] = 1.4; self.pesos['emboscar'] = 1.4; self.pesos['coletar_vida'] = 1.2
        elif self.personalidade == Personalidade.VETERANO:
            self.pesos['atacar'] = 1.3; self.pesos['recuar_tatico'] = 1.2; self.pesos['emboscar'] = 1.2
    
    def calcular_utilidade(self, acao: str, contexto: dict) -> float:
        utilidade_base = 0.0
        hp_percent = contexto.get('hp_percent', 1.0)
        num_ameacas = contexto.get('num_ameacas', 0)
        dist_ameaca = contexto.get('distancia_ameaca', 0)
        distancia_alvo = contexto.get('distancia_alvo', float('inf'))
        hp_alvo_percent = contexto.get('hp_alvo_percent', 1.0)
        tem_vida_proxima = contexto.get('tem_vida_proxima', False)
        nivel_perigo = contexto.get('nivel_perigo', 0.0)
        estado_emocional = contexto.get('estado_emocional', EstadoEmocional.CALMO)
        
        # Lógica de segurança para regeneração
        seguro_para_regen = (num_ameacas == 0) or (dist_ameaca > 700)

        if acao == 'atacar':
            if distancia_alvo < float('inf'):
                utilidade_base = 80 + (1 - hp_alvo_percent) * 40
                utilidade_base += max(0, (600 - distancia_alvo) / 10)
                if hp_percent > 0.35: utilidade_base += 30
                if hp_percent < 0.2: utilidade_base *= 0.4 # Reduz vontade de atacar se muito ferido
        
        elif acao == 'fugir':
            # Se a vida está crítica E tem inimigo perto, foge desesperado
            if hp_percent < 0.4 and not seguro_para_regen:
                utilidade_base = 300 # Prioridade absoluta
            # Se a vida está ok, não foge (exceto pânico)
            elif hp_percent > 0.5 and estado_emocional != EstadoEmocional.PANICO:
                utilidade_base = 0 
            else:
                # Fuga padrão
                utilidade_base = (1 - hp_percent) * 100
                utilidade_base += num_ameacas * 10
                
        elif acao == 'coletar_vida':
            if tem_vida_proxima and hp_percent < 0.9:
                utilidade_base = (1 - hp_percent) * 110
                if hp_percent < 0.4: utilidade_base *= 2.0
        
        elif acao == 'patrulhar': # VAGANDO (Estado de Regeneração)
            # Se estamos seguros e machucados -> Regenerar!
            if seguro_para_regen and hp_percent < 0.8:
                utilidade_base = 250 # Super prioridade para regenerar se estiver "safe"
            elif num_ameacas == 0:
                utilidade_base = 50
            else:
                utilidade_base = 0
                
        elif acao == 'emboscar':
            if hp_percent > 0.6 and distancia_alvo < 500: utilidade_base = 40 + (1 - hp_alvo_percent) * 20
        elif acao == 'recuar_tatico':
            if hp_percent < 0.5 and hp_percent > 0.2:
                utilidade_base = 60
                if num_ameacas > 1: utilidade_base += 20
        
        utilidade_final = utilidade_base * self.pesos.get(acao, 1.0)
        utilidade_final += random.gauss(0, 2)
        return max(0, utilidade_final)
    
    def escolher_acao(self, contexto: dict) -> str:
        acoes = ['atacar', 'fugir', 'coletar_vida', 'patrulhar', 'emboscar', 'recuar_tatico']
        utilidades = {acao: self.calcular_utilidade(acao, contexto) for acao in acoes}
        soma_utilidades = sum(utilidades.values())
        if soma_utilidades <= 0: return 'patrulhar'
        if random.random() < 0.95: return max(utilidades, key=utilidades.get)
        else:
            r = random.random() * soma_utilidades
            acumulado = 0
            for acao, util in utilidades.items():
                acumulado += util
                if acumulado >= r: return acao
            return max(utilidades, key=utilidades.get)

class BotAI:
    def __init__(self, bot_nave):
        self.bot = bot_nave
        self.frame_atual = 0
        self.map_width = s.MAP_WIDTH
        self.map_height = s.MAP_HEIGHT
        self.personalidade = random.choice(list(Personalidade))
        self.estado_emocional = EstadoEmocional.CALMO
        self.nivel_estresse = 0.0
        self.confianca = 0.5
        self.mira_atual = pygame.math.Vector2(0, 0)
        self.velocidade_mira = 0.3
        
        self.chance_esquiva = 0.5
        self.cooldown_esquiva = 0
        
        self._gerar_caracteristicas_humanas()
        self.sistema_predicao = SistemaPredicao()
        self.sistema_decisao = SistemaDecisao(self.personalidade)
        self.percepcao = PercepcaoAmbiente()
        self.memoria_ameacas: Dict[int, MemoriaAmeaca] = {}
        self.tempo_memoria = 300
        self.estado_ia = "VAGANDO"
        self.estado_anterior = "VAGANDO"
        self.frames_no_estado = 0
        self.delay_reacao_restante = 0
        self.delay_proximo_tiro = 0
        self.timer_reavaliacao = 0
        self.intervalo_reavaliacao = random.randint(10, 20)
        self.destino_atual: Optional[pygame.math.Vector2] = None
        self.direcao_strafe = random.choice([-1, 1])
        self.timer_strafe = 0
        self.duracao_strafe = random.randint(30, 90)
        self.alvo_principal = None
        self.tempo_fidelidade_alvo = 0
        self.ultimo_dano_recebido_frame = 0
        self.dano_recebido_recente = 0.0
        self.tiros_disparados = 0
        self.tiros_acertados = 0
        self.raio_visao = 1000
        self.raio_visao_sq = self.raio_visao ** 2
        self.raio_audicao = 800
        self.raio_audicao_sq = self.raio_audicao ** 2
        self.angulo_visao = 180 
        self.distancia_ideal_combate = random.randint(200, 300)
        self.distancia_minima = 100
        self.distancia_maxima_engajamento = 700
        self.player_ref = None
        self.grupo_bots_ref = None
        self.grupo_inimigos_ref = None
        self.grupo_obstaculos_ref = None
        self.grupo_vidas_ref = None
        self.lista_projeteis_ref = None
        self.posicao_anterior = pygame.math.Vector2(0, 0)
        self.frames_parado = 0
        self.historico_posicoes: deque = deque(maxlen=60)

    def _gerar_caracteristicas_humanas(self):
        if self.personalidade == Personalidade.VETERANO:
            self.tempo_reacao_base = random.randint(3, 6)
            self.precisao_mira = random.uniform(0.95, 0.99)
            self.velocidade_mira = 0.8
            self.chance_esquiva = 0.75
        else:
            self.tempo_reacao_base = random.randint(8, 12)
            self.precisao_mira = random.uniform(0.85, 0.95)
            self.velocidade_mira = 0.5 
            self.chance_esquiva = 0.50
        
        if self.personalidade == Personalidade.AGRESSIVO:
            self.agressividade = random.uniform(0.9, 1.0)
            self.velocidade_mira = 0.6
            self.chance_esquiva = 0.35
        elif self.personalidade == Personalidade.DEFENSIVO:
            self.agressividade = random.uniform(0.3, 0.6)
            self.chance_esquiva = 0.65
        else:
            self.agressividade = random.uniform(0.5, 0.9)
        
        self.resistencia_pressao = random.uniform(0.5, 0.9)
        self.paciencia = random.uniform(0.3, 0.8)
        self.vigilancia = random.uniform(0.5, 0.9)
        self.fadiga = 0.0
        self.taxa_fadiga = random.uniform(0.0001, 0.0005)
        self.taxa_recuperacao_fadiga = random.uniform(0.001, 0.003)

    def update_ai(self, player_ref, grupo_bots_ref, grupo_inimigos_ref,
                  grupo_obstaculos_ref, grupo_vidas_ref,
                  map_width=None, map_height=None, lista_projeteis_hostis=None):
        if map_width: self.map_width = map_width
        if map_height: self.map_height = map_height
        self.player_ref = player_ref
        self.grupo_bots_ref = grupo_bots_ref
        self.grupo_inimigos_ref = grupo_inimigos_ref
        self.grupo_obstaculos_ref = grupo_obstaculos_ref
        self.grupo_vidas_ref = grupo_vidas_ref
        self.lista_projeteis_ref = lista_projeteis_hostis
        
        if self.mira_atual == pygame.math.Vector2(0, 0): self.mira_atual = self.bot.posicao + pygame.math.Vector2(1, 0)
        
        self.frame_atual += 1
        self.frames_no_estado += 1
        
        if self.cooldown_esquiva > 0: self.cooldown_esquiva -= 1
        if self.tempo_fidelidade_alvo > 0: self.tempo_fidelidade_alvo -= 1
        
        self._atualizar_percepcao()
        self._atualizar_estado_emocional()
        self._verificar_stuck()
        self._tomar_decisao()
        self._executar_estado_atual()
        self._atualizar_fadiga()
        self._limpar_memorias_antigas()
        self._diminuir_dano_recente()

    def _atualizar_percepcao(self):
        self.percepcao = PercepcaoAmbiente()
        pos = self.bot.posicao
        margem = 150
        self.percepcao.espaco_para_manobra = {'norte': pos.y - margem, 'sul': self.map_height - pos.y - margem, 'leste': self.map_width - pos.x - margem, 'oeste': pos.x - margem}
        self._detectar_ameacas()
        self._detectar_itens()
        self._detectar_projeteis_perigosos()
        self._calcular_nivel_perigo()
        self.percepcao.zona_segura = self.percepcao.nivel_perigo_geral < 0.3

    def _detectar_ameacas(self):
        ameacas = []
        min_dist = float('inf')
        
        def processar_entidade(entidade):
            nonlocal min_dist
            if entidade == self.bot or not self._esta_vivo(entidade): return
            if hasattr(entidade, 'owner') and entidade.owner == self.bot: return
            try:
                dist_sq = self.bot.posicao.distance_squared_to(entidade.posicao)
                dist = math.sqrt(dist_sq)
                if dist < min_dist: min_dist = dist
                
                if dist_sq > self.raio_visao_sq: return
                entidade_id = id(entidade)
                self.sistema_predicao.atualizar(entidade_id, entidade.posicao)
                if entidade_id in self.memoria_ameacas:
                    mem = self.memoria_ameacas[entidade_id]
                    mem.posicao_ultima = entidade.posicao.copy()
                    mem.vezes_encontrada += 1
                    mem.timestamp = self.frame_atual
                    vel = self.sistema_predicao.obter_velocidade(entidade_id)
                    if vel and vel.length() > 0.1: mem.direcao_movimento = vel.normalize(); mem.velocidade_estimada = vel.length()
                else:
                    self.memoria_ameacas[entidade_id] = MemoriaAmeaca(entidade=entidade, posicao_ultima=entidade.posicao.copy(), timestamp=self.frame_atual)
                nivel_perigo = self._avaliar_perigo_entidade(entidade, dist_sq)
                self.memoria_ameacas[entidade_id].nivel_perigo = nivel_perigo
                ameacas.append((entidade, dist_sq, nivel_perigo))
            except (AttributeError, ValueError): pass
        
        if self.player_ref: processar_entidade(self.player_ref)
        if self.grupo_bots_ref: 
            for bot in self.grupo_bots_ref: processar_entidade(bot)
        if self.grupo_inimigos_ref:
            for inimigo in self.grupo_inimigos_ref: processar_entidade(inimigo)
        ameacas.sort(key=lambda x: x[2], reverse=True)
        self.percepcao.ameacas_proximas = [a[0] for a in ameacas]
        self.percepcao.distancia_ameaca_mais_proxima = min_dist
        
        if ameacas:
            perigo_principal = ameacas[0][0]
            try:
                dir_perigo = perigo_principal.posicao - self.bot.posicao
                if dir_perigo.length() > 0: self.percepcao.direcao_perigo_principal = dir_perigo.normalize()
            except (ValueError, AttributeError): pass

    def _avaliar_perigo_entidade(self, entidade, dist_sq) -> float:
        perigo = 0.0
        dist = math.sqrt(dist_sq)
        perigo += max(0, (self.raio_visao - dist) / self.raio_visao) * 0.4
        max_vida = max(getattr(entidade, 'max_vida', 1), 1)
        hp_percent = getattr(entidade, 'vida_atual', 0) / max_vida
        perigo += hp_percent * 0.3
        if isinstance(entidade, TIPOS_PRIORITARIOS): perigo += 0.3 
        entidade_id = id(entidade)
        if entidade_id in self.memoria_ameacas:
            mem = self.memoria_ameacas[entidade_id]
            if mem.dano_recebido > 0: perigo += min(mem.dano_recebido / 100, 0.4)
        if entidade == self.player_ref: perigo += 0.15
        return min(perigo, 1.0)

    def _esta_no_campo_visao(self, posicao_alvo: pygame.math.Vector2) -> bool: return True

    def _detectar_itens(self):
        if not self.grupo_vidas_ref: return
        for vida in self.grupo_vidas_ref:
            if not vida.groups(): continue
            try:
                dist_sq = self.bot.posicao.distance_squared_to(vida.posicao)
                if dist_sq < self.raio_visao_sq: self.percepcao.itens_vida.append(vida)
            except AttributeError: continue

    def _detectar_projeteis_perigosos(self):
        if not self.lista_projeteis_ref: return
        raio_deteccao_sq = 300 ** 2
        for proj in self.lista_projeteis_ref:
            if getattr(proj, 'owner', None) == self.bot: continue
            try:
                dist_sq = self.bot.posicao.distance_squared_to(proj.posicao)
                if dist_sq > raio_deteccao_sq: continue
                vel = getattr(proj, 'velocidade_vetor', None)
                if vel and vel.length_squared() > 0.1:
                    dir_para_nos = self.bot.posicao - proj.posicao
                    if dir_para_nos.length_squared() > 0:
                        if vel.normalize().dot(dir_para_nos.normalize()) > 0.3: self.percepcao.projeteis_perigosos.append(proj)
            except (AttributeError, ValueError): continue

    def _calcular_nivel_perigo(self):
        perigo = 0.0
        num_ameacas = len(self.percepcao.ameacas_proximas)
        perigo += min(num_ameacas * 0.15, 0.45)
        num_projeteis = len(self.percepcao.projeteis_perigosos)
        perigo += min(num_projeteis * 0.1, 0.3)
        hp_percent = self.bot.vida_atual / max(self.bot.max_vida, 1)
        # Reduzido impacto do HP no perigo geral para não causar pânico falso
        if hp_percent < 0.3: perigo += (1 - hp_percent) * 0.2 
        if self.dano_recebido_recente > 0: perigo += min(self.dano_recebido_recente / 100, 0.2)
        espaco_min = min(self.percepcao.espaco_para_manobra.values()) if self.percepcao.espaco_para_manobra else 0
        if espaco_min < 100: perigo += 0.1
        self.percepcao.nivel_perigo_geral = min(perigo, 1.0)

    def _atualizar_estado_emocional(self):
        self.nivel_estresse += self.percepcao.nivel_perigo_geral * 0.02
        if self.frame_atual - self.ultimo_dano_recebido_frame < 60: self.nivel_estresse += 0.03
        if self.percepcao.zona_segura: self.nivel_estresse -= 0.01
        self.nivel_estresse = max(0, min(1, self.nivel_estresse))
        hp_percent = self.bot.vida_atual / max(self.bot.max_vida, 1)
        if self.nivel_estresse > 0.8 or hp_percent < 0.15: self.estado_emocional = EstadoEmocional.PANICO
        elif self.nivel_estresse > 0.5 or hp_percent < 0.3: self.estado_emocional = EstadoEmocional.ESTRESSADO
        elif self.nivel_estresse > 0.2 or len(self.percepcao.ameacas_proximas) > 0: self.estado_emocional = EstadoEmocional.ALERTA
        elif hp_percent > 0.8 and len(self.percepcao.ameacas_proximas) == 0: self.estado_emocional = EstadoEmocional.CONFIANTE
        else: self.estado_emocional = EstadoEmocional.CALMO

    def _obter_multiplicador_reacao(self) -> float:
        multiplicador = 1.0
        if self.estado_emocional == EstadoEmocional.ESTRESSADO: multiplicador = 1.3
        elif self.estado_emocional == EstadoEmocional.PANICO: multiplicador = 1.6
        multiplicador += self.fadiga * 0.5
        return multiplicador

    def _tomar_decisao(self):
        if self.delay_reacao_restante > 0: self.delay_reacao_restante -= 1; return
        self.timer_reavaliacao += 1
        if self.timer_reavaliacao < self.intervalo_reavaliacao: return
        self.timer_reavaliacao = 0
        self.intervalo_reavaliacao = random.randint(10, 20)
        mult_reacao = self._obter_multiplicador_reacao()
        self.delay_reacao_restante = int(self.tempo_reacao_base * mult_reacao * random.uniform(0.8, 1.2))
        contexto = self._montar_contexto_decisao()
        acao_escolhida = self.sistema_decisao.escolher_acao(contexto)
        self._executar_transicao_estado(acao_escolhida)

    def _montar_contexto_decisao(self) -> dict:
        hp_percent = self.bot.vida_atual / max(self.bot.max_vida, 1)
        distancia_alvo = float('inf')
        hp_alvo_percent = 1.0
        if self.percepcao.ameacas_proximas:
            alvo = self.percepcao.ameacas_proximas[0]
            try:
                distancia_alvo = self.bot.posicao.distance_to(alvo.posicao)
                hp_alvo_percent = getattr(alvo, 'vida_atual', 1) / max(getattr(alvo, 'max_vida', 1), 1)
            except (AttributeError, ValueError): pass
        return {
            'hp_percent': hp_percent,
            'num_ameacas': len(self.percepcao.ameacas_proximas),
            'distancia_ameaca': self.percepcao.distancia_ameaca_mais_proxima, # Usado para decidir se foge ou regenera
            'distancia_alvo': distancia_alvo,
            'hp_alvo_percent': hp_alvo_percent,
            'tem_vida_proxima': len(self.percepcao.itens_vida) > 0,
            'nivel_perigo': self.percepcao.nivel_perigo_geral,
            'estado_emocional': self.estado_emocional,
            'projeteis_proximos': len(self.percepcao.projeteis_perigosos),
        }

    def _executar_transicao_estado(self, acao: str):
        mapa_estados = {'atacar': 'COMBATE', 'fugir': 'FUGINDO', 'coletar_vida': 'COLETANDO', 'patrulhar': 'VAGANDO', 'emboscar': 'EMBOSCANDO', 'recuar_tatico': 'RECUANDO'}
        novo_estado = mapa_estados.get(acao, 'VAGANDO')
        if novo_estado != self.estado_ia:
            self.estado_anterior = self.estado_ia
            self.estado_ia = novo_estado
            self.frames_no_estado = 0
            if novo_estado == 'FUGINDO': self.destino_atual = None

    def _executar_estado_atual(self):
        self.bot.quer_mover_frente = False
        self.bot.quer_mover_tras = False
        self.bot.quer_atirar = False
        
        desviando = self._desviar_projeteis_se_necessario()
        
        if desviando:
            if self.alvo_principal and self._esta_vivo(self.alvo_principal):
                self._tenta_atirar_defensivo()
            return 
        
        if self.estado_ia == 'COMBATE': self._executar_combate()
        elif self.estado_ia == 'FUGINDO': self._executar_fuga()
        elif self.estado_ia == 'COLETANDO': self._executar_coleta()
        elif self.estado_ia == 'VAGANDO': self._executar_patrulha()
        elif self.estado_ia == 'EMBOSCANDO': self._executar_emboscada()
        elif self.estado_ia == 'RECUANDO': self._executar_recuo_tatico()
        else: self._executar_patrulha()

    def _desviar_projeteis_se_necessario(self) -> bool:
        if self.cooldown_esquiva > 0: return False 
        if not self.percepcao.projeteis_perigosos: return False
        
        proj_mais_proximo = min(self.percepcao.projeteis_perigosos, key=lambda p: self.bot.posicao.distance_squared_to(p.posicao))
        
        try:
            dist_sq = self.bot.posicao.distance_squared_to(proj_mais_proximo.posicao)
            if dist_sq > 200**2: return False 

            if random.random() > self.chance_esquiva:
                self.cooldown_esquiva = 30 
                return False

            vel_proj = getattr(proj_mais_proximo, 'velocidade_vetor', pygame.math.Vector2(1, 0))
            if vel_proj.length_squared() > 0:
                perp1 = pygame.math.Vector2(-vel_proj.y, vel_proj.x).normalize()
                perp2 = pygame.math.Vector2(vel_proj.y, -vel_proj.x).normalize()
                pos1 = self.bot.posicao + perp1 * 100
                pos2 = self.bot.posicao + perp2 * 100
                
                if pos1.distance_squared_to(proj_mais_proximo.posicao) > pos2.distance_squared_to(proj_mais_proximo.posicao): destino = pos1
                else: destino = pos2
                
                self._clamp_destino(destino)
                self.bot.posicao_alvo_mouse = destino
                self.cooldown_esquiva = random.randint(40, 80)
                return True
        except (ValueError, AttributeError): pass
        return False

    def _calcular_vetor_desvio(self) -> pygame.math.Vector2:
        forca_repulsao = pygame.math.Vector2(0, 0)
        raio_deteccao = 150
        # --- CORREÇÃO ZIG-ZAG: Margem reduzida para 100px (Evita empurrar longe demais da parede) ---
        margem = 100 
        pos = self.bot.posicao
        if pos.x < margem: forca_repulsao.x += (margem - pos.x)
        if pos.x > self.map_width - margem: forca_repulsao.x -= (pos.x - (self.map_width - margem))
        if pos.y < margem: forca_repulsao.y += (margem - pos.y)
        if pos.y > self.map_height - margem: forca_repulsao.y -= (pos.y - (self.map_height - margem))
        if self.grupo_obstaculos_ref:
            for obstaculo in self.grupo_obstaculos_ref:
                dist_sq = self.bot.posicao.distance_squared_to(obstaculo.posicao)
                raio_seguro_sq = (raio_deteccao + getattr(obstaculo, 'raio', 30)) ** 2
                if dist_sq < raio_seguro_sq:
                    vetor_afastamento = self.bot.posicao - obstaculo.posicao
                    if vetor_afastamento.length_squared() > 0:
                        fator = 1.0 - (dist_sq / raio_seguro_sq)
                        forca_repulsao += vetor_afastamento.normalize() * (fator * 300)
        return forca_repulsao

    def _tenta_atirar_defensivo(self):
        if not self.alvo_principal: return
        alvo = self.alvo_principal
        self.bot.alvo_selecionado = alvo
        try: dist_alvo = self.bot.posicao.distance_to(alvo.posicao)
        except AttributeError: return
        alvo_id = id(alvo)
        tempo_voo = dist_alvo / 15
        posicao_predita = self.sistema_predicao.prever_posicao(alvo_id, int(tempo_voo)) or alvo.posicao
        vetor_correcao = posicao_predita - self.mira_atual
        if vetor_correcao.length_squared() > 0: self.mira_atual += vetor_correcao * 0.8
        self.delay_proximo_tiro -= 1
        if self.delay_proximo_tiro <= 0:
            if self._esta_mirando_em(posicao_predita, tolerancia=60):
                self.bot.quer_atirar = True; self.tiros_disparados += 1
                self.delay_proximo_tiro = random.randint(3, 8)

    def _atualizar_alvo_principal(self):
        alvo_atual_valido = self.alvo_principal and self._esta_vivo(self.alvo_principal)
        atacante_recente = None; maior_dano = 0
        for eid, mem in self.memoria_ameacas.items():
            if mem.dano_recebido > 5 and mem.dano_recebido > maior_dano and self._esta_vivo(mem.entidade):
                maior_dano = mem.dano_recebido; atacante_recente = mem.entidade
        if atacante_recente:
            self.alvo_principal = atacante_recente
            self.memoria_ameacas[id(atacante_recente)].dano_recebido = 0 
            self.tempo_fidelidade_alvo = 120 
            return
        if self.tempo_fidelidade_alvo > 0 and self.alvo_principal and self._esta_vivo(self.alvo_principal):
            if self.bot.posicao.distance_to(self.alvo_principal.posicao) < 1200: return
        if self.percepcao.ameacas_proximas:
            novo_alvo = max(self.percepcao.ameacas_proximas, key=self._calcular_score_alvo)
            if novo_alvo != self.alvo_principal: self.alvo_principal = novo_alvo; self.tempo_fidelidade_alvo = 180 
        else: self.alvo_principal = None

    def _calcular_score_alvo(self, alvo) -> float:
        if not self._esta_vivo(alvo): return -1000.0
        dist = self.bot.posicao.distance_to(alvo.posicao)
        max_vida = max(getattr(alvo, 'max_vida', 1), 1)
        vida_atual = getattr(alvo, 'vida_atual', 1)
        hp_percent = vida_atual / max_vida
        score = max(0, (1000 - dist) / 10)
        score += (1 - hp_percent) * 200
        if isinstance(alvo, TIPOS_PRIORITARIOS): score += 300
        return score

    def _executar_combate(self):
        self._atualizar_alvo_principal()
        if not self.alvo_principal: self.estado_ia = 'VAGANDO'; return
        alvo = self.alvo_principal
        self.bot.alvo_selecionado = alvo
        try: dist_alvo = self.bot.posicao.distance_to(alvo.posicao)
        except AttributeError: self.alvo_principal = None; return
        alvo_id = id(alvo)
        tempo_voo = dist_alvo / 15 
        posicao_predita = self.sistema_predicao.prever_posicao(alvo_id, int(tempo_voo)) or alvo.posicao
        fator_erro = (1 - self.precisao_mira) * 50
        if self.estado_emocional == EstadoEmocional.PANICO: fator_erro *= 2
        erro_humano = pygame.math.Vector2(random.gauss(0, fator_erro), random.gauss(0, fator_erro))
        ponto_desejado = posicao_predita + erro_humano
        vetor_correcao = ponto_desejado - self.mira_atual
        if vetor_correcao.length_squared() > 0: self.mira_atual += vetor_correcao * self.velocidade_mira
        self._executar_movimento_combate(alvo, dist_alvo)
        self.delay_proximo_tiro -= 1
        if self.delay_proximo_tiro <= 0:
            if self._esta_mirando_em(posicao_predita, tolerancia=40):
                self.bot.quer_atirar = True; self.tiros_disparados += 1
                delay_base = 8
                if self.estado_emocional == EstadoEmocional.PANICO: delay_base = 4
                elif self.estado_emocional == EstadoEmocional.CALMO: delay_base = 12
                self.delay_proximo_tiro = delay_base + random.randint(-2, 4)
                recuo = pygame.math.Vector2(random.uniform(-10, 10), random.uniform(-10, 10))
                self.mira_atual += recuo

    def _executar_movimento_combate(self, alvo, dist_alvo: float):
        try: dir_para_alvo = (alvo.posicao - self.bot.posicao).normalize()
        except (ValueError, ZeroDivisionError): return
        
        dir_strafe = pygame.math.Vector2(-dir_para_alvo.y, dir_para_alvo.x) * self.direcao_strafe
        self.timer_strafe += 1
        
        margem_borda = 250
        pos = self.bot.posicao
        perto_borda = (pos.x < margem_borda or pos.x > self.map_width - margem_borda or pos.y < margem_borda or pos.y > self.map_height - margem_borda)

        if self.timer_strafe > self.duracao_strafe or (perto_borda and self.frames_no_estado % 10 == 0):
            self.timer_strafe = 0
            self.direcao_strafe *= -1
            self.duracao_strafe = random.randint(30, 90)
            if random.random() < 0.2: self.duracao_strafe = random.randint(10, 30)
        
        segundos_combate = self.frames_no_estado / 60
        fator_aproximacao = max(0.0, 1.0 - (segundos_combate * 0.05)) 
        dist_ideal = self.distancia_ideal_combate * fator_aproximacao
        if segundos_combate > 10: dist_ideal = 50 
        if self.estado_emocional == EstadoEmocional.CONFIANTE: dist_ideal *= 0.8
        elif self.estado_emocional == EstadoEmocional.ESTRESSADO: dist_ideal *= 1.2
        
        vetor_final = pygame.math.Vector2(0, 0)
        
        if perto_borda:
             dir_centro = (pygame.math.Vector2(self.map_width/2, self.map_height/2) - pos).normalize()
             vetor_final += dir_centro * 1.5 
             if dist_alvo < self.distancia_minima:
                 vetor_final += dir_strafe * 1.5
        else:
             if dist_alvo > dist_ideal + 100: vetor_final += dir_para_alvo * 1.0 
             elif dist_alvo < self.distancia_minima: vetor_final -= dir_para_alvo * 1.2 
             else:
                 oscilacao = math.sin(self.frame_atual * 0.1) * 0.3
                 vetor_final += dir_strafe * 0.8
                 vetor_final += dir_para_alvo * (((dist_alvo - dist_ideal) / 500) + oscilacao)
        
        vetor_desvio = self._calcular_vetor_desvio()
        vetor_final += vetor_desvio * 1.5 
        if random.random() < 0.1: vetor_final += pygame.math.Vector2(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2))
        
        if vetor_final.length_squared() > 0:
            vetor_final = vetor_final.normalize()
            destino = self.bot.posicao + vetor_final * 200
            self._clamp_destino(destino)
            self.bot.posicao_alvo_mouse = destino

    def _executar_fuga(self):
        if not self.destino_atual or self.frames_no_estado % 60 == 0: self.destino_atual = self._encontrar_destino_fuga()
        if self.destino_atual:
            dir_fuga = (self.destino_atual - self.bot.posicao).normalize()
            vetor_desvio = self._calcular_vetor_desvio()
            dir_final = (dir_fuga + vetor_desvio).normalize()
            destino = self.bot.posicao + dir_final * 200
            self._clamp_destino(destino)
            self.bot.posicao_alvo_mouse = destino
        
        # --- CORREÇÃO: Fuga Inteligente ---
        # Se vida > 40% e seguro o suficiente (ameaças longe), muda para VAGANDO para regenerar
        # Se 1 ameaca longe (>800px), considera seguro para transição.
        ameaca_longe = self.percepcao.distancia_ameaca_mais_proxima > 800
        
        if self.bot.vida_atual > self.bot.max_vida * 0.4 and (self.percepcao.zona_segura or ameaca_longe):
             self.estado_ia = 'VAGANDO'
             return

        if self.percepcao.ameacas_proximas:
            ameaca = self.percepcao.ameacas_proximas[0]
            self.bot.alvo_selecionado = ameaca
            if random.random() < 0.3: self.bot.quer_atirar = True

    def _encontrar_destino_fuga(self) -> pygame.math.Vector2:
        pos = self.bot.posicao; melhor_destino = None; melhor_score = float('-inf')
        for angulo in range(0, 360, 30):
            direcao = pygame.math.Vector2(1, 0).rotate(angulo); candidato = pos + direcao * 400
            candidato.x = max(100, min(candidato.x, self.map_width - 100)); candidato.y = max(100, min(candidato.y, self.map_height - 100))
            score = 0
            for ameaca in self.percepcao.ameacas_proximas:
                try:
                    dist = candidato.distance_to(ameaca.posicao); score += dist
                except (AttributeError, ValueError): continue
            for vida in self.percepcao.itens_vida:
                try:
                    dist = candidato.distance_to(vida.posicao);
                    if dist < 200: score += 100
                except (AttributeError, ValueError): continue
            
            # --- CORREÇÃO: Destino nas bordas é BOM se a vida for baixa ---
            dist_borda = min(candidato.x, candidato.y, self.map_width - candidato.x, self.map_height - candidato.y)
            if self.bot.vida_atual < self.bot.max_vida * 0.4:
                # Se vida baixa, borda é boa (esconderijo)
                if dist_borda < 200: score += 150 
            else:
                # Se vida ok, evita canto
                if dist_borda < 150: score -= 100
            
            if score > melhor_score: melhor_score = score; melhor_destino = candidato
        return melhor_destino if melhor_destino else pygame.math.Vector2(self.map_width / 2, self.map_height / 2)

    def _executar_coleta(self):
        if not self.percepcao.itens_vida: self.estado_ia = 'VAGANDO'; return
        vida_mais_proxima = min(self.percepcao.itens_vida, key=lambda v: self.bot.posicao.distance_squared_to(v.posicao))
        try:
            self.bot.posicao_alvo_mouse = vida_mais_proxima.posicao
            if self.bot.posicao.distance_squared_to(vida_mais_proxima.posicao) < 900: self.estado_ia = 'VAGANDO'
        except AttributeError: self.estado_ia = 'VAGANDO'
        if self.percepcao.ameacas_proximas:
            ameaca = self.percepcao.ameacas_proximas[0]
            try:
                dist = self.bot.posicao.distance_to(ameaca.posicao)
                if dist < 300: self.bot.alvo_selecionado = ameaca; self.bot.quer_atirar = True
            except (AttributeError, ValueError): pass

    def _executar_patrulha(self):
        # Se vida baixa, tenta ficar parado para regenerar (se seguro)
        if self.bot.vida_atual < self.bot.max_vida * 0.8:
             # Se VAGANDO e vida < 80%, ships.py força o stop. 
             # Aqui garantimos que ele não tente setar um destino novo se já estiver parado regenerando.
             if self.percepcao.zona_segura or self.percepcao.distancia_ameaca_mais_proxima > 600:
                 self.bot.posicao_alvo_mouse = None
                 return

        precisa_novo_destino = False
        if not self.destino_atual: precisa_novo_destino = True
        elif self.bot.posicao.distance_squared_to(self.destino_atual) < 2500: precisa_novo_destino = True
        elif self.frames_no_estado > 300: precisa_novo_destino = True
        if precisa_novo_destino: self.destino_atual = self._gerar_destino_patrulha(); self.frames_no_estado = 0
        vetor_desvio = self._calcular_vetor_desvio()
        if vetor_desvio.length_squared() > 0: self.bot.posicao_alvo_mouse = self.bot.posicao + (self.destino_atual - self.bot.posicao).normalize() * 100 + vetor_desvio
        else: self.bot.posicao_alvo_mouse = self.destino_atual

    def _gerar_destino_patrulha(self) -> pygame.math.Vector2:
        margem = 150
        if random.random() < 0.3:
            centro = pygame.math.Vector2(self.map_width / 2, self.map_height / 2)
            offset = pygame.math.Vector2(random.uniform(-200, 200), random.uniform(-200, 200))
            return centro + offset
        return pygame.math.Vector2(random.randint(margem, self.map_width - margem), random.randint(margem, self.map_height - margem))

    def _executar_emboscada(self):
        if not self.destino_atual or self.frames_no_estado == 1: self.destino_atual = self._encontrar_posicao_emboscada()
        if self.destino_atual:
            dist = self.bot.posicao.distance_to(self.destino_atual)
            if dist > 30: self.bot.posicao_alvo_mouse = self.destino_atual
            else:
                self.bot.posicao_alvo_mouse = None
                if self.percepcao.ameacas_proximas:
                    alvo = self.percepcao.ameacas_proximas[0]
                    try:
                        dist_alvo = self.bot.posicao.distance_to(alvo.posicao)
                        if dist_alvo < 400: self.alvo_principal = alvo; self.estado_ia = 'COMBATE'
                    except (AttributeError, ValueError): pass

    def _encontrar_posicao_emboscada(self) -> pygame.math.Vector2:
        pos = self.bot.posicao; centro = pygame.math.Vector2(self.map_width / 2, self.map_height / 2); return pos.lerp(centro, 0.3)

    def _executar_recuo_tatico(self):
        if not self.percepcao.ameacas_proximas: self.estado_ia = 'VAGANDO'; return
        alvo = self.percepcao.ameacas_proximas[0]; self.bot.alvo_selecionado = alvo
        try: dir_recuo = (self.bot.posicao - alvo.posicao).normalize()
        except (ValueError, ZeroDivisionError): dir_recuo = pygame.math.Vector2(1, 0)
        self.timer_strafe += 1
        if self.timer_strafe > 25: self.direcao_strafe *= -1; self.timer_strafe = 0
        dir_lateral = pygame.math.Vector2(-dir_recuo.y, dir_recuo.x) * self.direcao_strafe
        dir_final = (dir_recuo * 0.7 + dir_lateral * 0.3).normalize()
        vetor_desvio = self._calcular_vetor_desvio()
        dir_final = (dir_final + vetor_desvio).normalize()
        destino = self.bot.posicao + dir_final * 150
        self._clamp_destino(destino)
        self.bot.posicao_alvo_mouse = destino
        self.bot.quer_atirar = True
        hp_percent = self.bot.vida_atual / self.bot.max_vida
        if hp_percent > 0.6: self.estado_ia = 'COMBATE'

    def _esta_vivo(self, entidade) -> bool:
        if not entidade: return False
        if not entidade.groups(): return False
        return getattr(entidade, 'vida_atual', 0) > 0

    def _esta_mirando_em(self, posicao: pygame.math.Vector2, tolerancia: float = 20) -> bool:
        try:
            dir_atual = (self.mira_atual - self.bot.posicao).normalize()
            dir_alvo = (posicao - self.bot.posicao)
            if dir_alvo.length() == 0: return True
            dir_alvo = dir_alvo.normalize()
            dot = dir_atual.dot(dir_alvo)
            angulo = math.degrees(math.acos(max(-1, min(1, dot))))
            return angulo <= tolerancia
        except (ValueError, ZeroDivisionError): return True

    def _clamp_destino(self, destino: pygame.math.Vector2):
        margem = 80
        destino.x = max(margem, min(destino.x, self.map_width - margem))
        destino.y = max(margem, min(destino.y, self.map_height - margem))

    def _verificar_stuck(self):
        self.historico_posicoes.append(self.bot.posicao.copy())
        if len(self.historico_posicoes) >= 60:
            pos_antiga = self.historico_posicoes[0]; dist_movida = self.bot.posicao.distance_squared_to(pos_antiga)
            if dist_movida < 100:
                self.frames_parado += 1
                if self.frames_parado > 30:
                    angulo = random.uniform(0, 360); direcao = pygame.math.Vector2(1, 0).rotate(angulo)
                    self.destino_atual = self.bot.posicao + direcao * 200
                    self._clamp_destino(self.destino_atual); self.frames_parado = 0
            else: self.frames_parado = 0

    def _atualizar_fadiga(self):
        if self.estado_ia in ['COMBATE', 'FUGINDO', 'RECUANDO']: self.fadiga += self.taxa_fadiga
        else: self.fadiga -= self.taxa_recuperacao_fadiga
        self.fadiga = max(0, min(1, self.fadiga))

    def _limpar_memorias_antigas(self):
        tempo_limite = self.frame_atual - self.tempo_memoria
        ids_remover = [entidade_id for entidade_id, mem in self.memoria_ameacas.items() if mem.timestamp < tempo_limite]
        for eid in ids_remover: del self.memoria_ameacas[eid]; self.sistema_predicao.limpar_entidade(eid)

    def _diminuir_dano_recente(self):
        if self.dano_recebido_recente > 0: self.dano_recebido_recente *= 0.98

    def registrar_dano_recebido(self, quantidade: float, atacante=None):
        self.dano_recebido_recente += quantidade
        self.ultimo_dano_recebido_frame = self.frame_atual
        self.nivel_estresse += 0.1
        if atacante:
            atacante_id = id(atacante)
            if atacante_id in self.memoria_ameacas:
                self.memoria_ameacas[atacante_id].dano_recebido += quantidade
                self.memoria_ameacas[atacante_id].nivel_perigo = min(1.0, self.memoria_ameacas[atacante_id].nivel_perigo + 0.1)

    def registrar_acerto(self):
        self.tiros_acertados += 1; self.confianca = min(1.0, self.confianca + 0.02)

    def resetar_ia(self):
        self.bot.alvo_selecionado = None; self.bot.posicao_alvo_mouse = None
        self.estado_ia = "VAGANDO"; self.estado_anterior = "VAGANDO"
        self.frames_no_estado = 0; self.frames_parado = 0
        self.alvo_principal = None; self.destino_atual = None
        self.nivel_estresse = 0.0; self.fadiga = 0.0
        self.dano_recebido_recente = 0.0
        self.memoria_ameacas.clear(); self.sistema_predicao.historico_posicoes.clear()
        self.historico_posicoes.clear(); self.estado_emocional = EstadoEmocional.CALMO
        self.mira_atual = pygame.math.Vector2(0, 0)