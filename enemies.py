# enemies.py
import pygame
import math
import random
import settings as s 
from settings import (VERMELHO_VIDA_FUNDO, VERDE_VIDA, MAP_WIDTH, MAP_HEIGHT,
                      VERMELHO_PERSEGUIDOR, ROXO_ATIRADOR_RAPIDO, AMARELO_BOMBA, CIANO_MINION, CIANO_MOTHERSHIP,
                      LARANJA_RAPIDO, AZUL_TIRO_RAPIDO, ROXO_ATORDOADOR, BRANCO, AZUL_MINION_CONGELANTE, HP_MINION_CONGELANTE, PONTOS_MINION_CONGELANTE,
                        VELOCIDADE_MINION_CONGELANTE, COOLDOWN_TIRO_MINION_CONGELANTE, AZUL_CONGELANTE, HP_BOSS_CONGELANTE, PONTOS_BOSS_CONGELANTE,
    COOLDOWN_TIRO_CONGELANTE, COOLDOWN_SPAWN_MINION_CONGELANTE,
    MAX_MINIONS_CONGELANTE, MINION_CONGELANTE_LEASH_RANGE, VOLUME_BASE_TIRO_INIMIGO, 
    VOLUME_BASE_TIRO_LASER_LONGO, VOLUME_BASE_TIRO_CONGELANTE,
    NPC_AGGRO_RANGE)
# Importa as classes de projéteis necessárias
from projectiles import ProjetilInimigo, ProjetilInimigoRapido, ProjetilTeleguiadoLento, ProjetilInimigoRapidoCurto, ProjetilCongelante 
# Importa a classe Explosao
from effects import Explosao

try:
    from ships import tocar_som_posicional 
except ImportError:
    print("[AVISO] Nao foi possivel importar 'tocar_som_posicional'. Sons de inimigos podem falhar.")
    tocar_som_posicional = None

# Referências globais que serão definidas no main.py
grupo_explosoes = None
grupo_inimigos_global_ref = None

# Função para definir as referências globais
def set_global_enemy_references(explosions_group, enemies_group):
    global grupo_explosoes, grupo_inimigos_global_ref
    grupo_explosoes = explosions_group
    grupo_inimigos_global_ref = enemies_group

# Classe Base para Inimigos
class InimigoBase(pygame.sprite.Sprite):
    # ... (código da classe InimigoBase inalterado) ...
    def __init__(self, x, y, tamanho, cor, vida):
        super().__init__()
        self.tamanho = tamanho
        # --- CORREÇÃO IMPORTANTE: Definir 'cor' ANTES de usar ---
        self.cor = cor # Define o atributo cor
        # --- FIM CORREÇÃO ---
        self.image = pygame.Surface((self.tamanho, self.tamanho))
        self.image.fill(self.cor) # Agora self.cor existe
        self.posicao = pygame.math.Vector2(x, y); self.rect = self.image.get_rect(center=self.posicao)
        self.max_vida = vida; self.vida_atual = self.max_vida; self.pontos_por_morte = 0
        self.tempo_barra_visivel = 1500; self.ultimo_hit_tempo = 0

    def foi_atingido(self, dano):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_hit_tempo < 100: return False
        self.vida_atual -= dano; self.ultimo_hit_tempo = agora
        if self.vida_atual <= 0:
            if grupo_explosoes is not None:
                explosao = Explosao(self.rect.center, self.tamanho // 2 + 5); grupo_explosoes.add(explosao)
            self.kill(); return True
        return False

    def update_base(self, pos_alvo_generico, dist_despawn):
         # Lógica de despawn simples
         # --- MODIFICAÇÃO: Lógica de despawn removida para persistência ---
         # try:
         #     if self.posicao.distance_to(pos_alvo_generico) > dist_despawn:
         #         self.kill()
         #         return False # Indica que foi despawnado
         # except ValueError:
         #     pass
         # --- FIM DA MODIFICAÇÃO ---
         return True # Continua ativo

    def desenhar_vida(self, surface, camera):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_hit_tempo < self.tempo_barra_visivel:
            LARGURA_BARRA = self.tamanho; ALTURA_BARRA = 4; OFFSET_Y = (self.tamanho / 2) + 10 # Barra abaixo
            pos_x_mundo = self.posicao.x - LARGURA_BARRA / 2; pos_y_mundo = self.posicao.y + OFFSET_Y # CORREÇÃO: Barra abaixo
            percentual = max(0, self.vida_atual / self.max_vida); largura_vida_atual = LARGURA_BARRA * percentual
            rect_fundo_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, LARGURA_BARRA, ALTURA_BARRA); rect_vida_mundo = pygame.Rect(pos_x_mundo, pos_y_mundo, largura_vida_atual, ALTURA_BARRA)
            # --- CORREÇÃO: Aplicar câmera ---
            pygame.draw.rect(surface, VERMELHO_VIDA_FUNDO, camera.apply(rect_fundo_mundo));
            pygame.draw.rect(surface, VERDE_VIDA, camera.apply(rect_vida_mundo))
            # --- FIM CORREÇÃO ---

    # Método update padrão (será sobrescrito pelas classes filhas)
    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn, pos_ouvinte=None): # <-- MODIFICADO
        pass


# --- Minion Congelante --- (Definido ANTES do Boss)
class MinionCongelante(InimigoBase):
    # ... (código da classe MinionCongelante init inalterado) ...
    def __init__(self, x, y, owner_boss, index, max_minions): # <-- MODIFICADO
        # Chama o init base com stats corretos do minion
        super().__init__(x, y, tamanho=18, cor=AZUL_MINION_CONGELANTE, vida=HP_MINION_CONGELANTE)
        self.owner = owner_boss # Referência ao boss que o criou
        self.velocidade = VELOCIDADE_MINION_CONGELANTE
        self.pontos_por_morte = PONTOS_MINION_CONGELANTE
        self.cooldown_tiro = COOLDOWN_TIRO_MINION_CONGELANTE
        self.distancia_parar = 150 # Para perto antes de atirar
        self.distancia_tiro = 400  # Começa a atirar mais de perto
        self.ultimo_tiro_tempo = 0
        
        # --- INÍCIO DA MODIFICAÇÃO (Slots de Órbita) ---
        # Raio em torno do DONO (levemente aleatório para parecer mais orgânico)
        self.raio_orbita_dono = self.owner.tamanho * 0.8 + random.randint(40, 60) 
        # Ângulo base baseado no índice (para espalhar)
        self.angulo_orbita_atual = (index / max(1, max_minions)) * 360 
        # Velocidade de rotação em torno do dono
        self.velocidade_orbita = random.uniform(0.3, 0.7) 
        # --- FIM DA MODIFICAÇÃO ---


    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn, pos_ouvinte=None): # <-- MODIFICADO
        # --- Verificações Iniciais ---
        if not self.owner or not self.owner.groups():
            self.kill(); return
        pos_dono = self.owner.posicao # Define pos_dono aqui para usar em despawn
        
        # --- MODIFICAÇÃO: Chamada update_base removida para persistência ---
        # if not self.update_base(pos_dono, dist_despawn): return
        # --- FIM DA MODIFICAÇÃO ---

        # --- Lógica de Alvo para Tiro ---
        alvo_tiro = None
        dist_min_tiro = float('inf')
        
        # --- MODIFICAÇÃO: Bloco de encontrar 'pos_ouvinte' REMOVIDO ---

        # Prioriza atacante do boss
        atacante_do_boss = None
        if hasattr(self.owner, 'ultimo_atacante') and self.owner.ultimo_atacante and self.owner.ultimo_atacante.groups():
            atacante_do_boss = self.owner.ultimo_atacante
            try:
                dist_minion_atacante = self.posicao.distance_to(atacante_do_boss.posicao)
                # --- INÍCIO DA MODIFICAÇÃO (Reintroduz "coleira") ---
                dist_dono_atacante = pos_dono.distance_to(atacante_do_boss.posicao) 
                
                if dist_minion_atacante < self.distancia_tiro * 1.5 and dist_dono_atacante < MINION_CONGELANTE_LEASH_RANGE:
                # --- FIM DA MODIFICAÇÃO ---
                    alvo_tiro = atacante_do_boss
                    dist_min_tiro = dist_minion_atacante
            except ValueError: pass

        # Se não, procura mais próximo
        if not alvo_tiro:
            for alvo in lista_alvos_naves:
                is_player = type(alvo).__name__ == 'Player'
                is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
                if not is_player and not is_active_bot: continue
                try:
                    dist_minion_alvo = self.posicao.distance_to(alvo.posicao)
                    # --- INÍCIO DA MODIFICAÇÃO (Reintroduz "coleira") ---
                    dist_dono_alvo = pos_dono.distance_to(alvo.posicao) 

                    if dist_minion_alvo < self.distancia_tiro and dist_dono_alvo < MINION_CONGELANTE_LEASH_RANGE:
                    # --- FIM DA MODIFICAÇÃO ---
                        if dist_minion_alvo < dist_min_tiro:
                             dist_min_tiro = dist_minion_alvo
                             alvo_tiro = alvo
                except ValueError: continue

        # --- Lógica de Movimento com Coleira ---
        is_orbitando_alvo = False
        if alvo_tiro:
            is_orbitando_alvo = True

        # --- Cálculo do Movimento ---
        try:
            # --- INÍCIO DA MODIFICAÇÃO (CÁLCULO DE SEPARAÇÃO) ---
            
            # 1. Calcula a Posição Alvo (para onde o minion quer ir)
            posicao_alvo_seguir = self.posicao # Padrão
            
            if is_orbitando_alvo:
                # Lógica de orbitar o ALVO
                vetor_para_objetivo = alvo_tiro.posicao - self.posicao
                distancia_objetivo = vetor_para_objetivo.length()
                raio_orbita_desejado_alvo = 180 # Raio em torno do ALVO
                
                if distancia_objetivo > 10:
                    vetor_tangencial = vetor_para_objetivo.rotate(90).normalize()
                    vetor_radial = pygame.math.Vector2(0, 0)
                    if distancia_objetivo > raio_orbita_desejado_alvo + 20:
                        vetor_radial = vetor_para_objetivo.normalize()
                    elif distancia_objetivo < raio_orbita_desejado_alvo - 20:
                        vetor_radial = -vetor_para_objetivo.normalize()
                    
                    direcao_movimento = (vetor_tangencial * 0.6 + vetor_radial * 0.4)
                    if direcao_movimento.length() > 0:
                        direcao_movimento.normalize_ip()
                        # O alvo do LERP é um ponto à frente nesta direção
                        posicao_alvo_seguir = self.posicao + direcao_movimento * self.velocidade
            else:
                # Lógica de orbitar o DONO (baseado no slot)
                self.angulo_orbita_atual = (self.angulo_orbita_atual + self.velocidade_orbita) % 360
                rad = math.radians(self.angulo_orbita_atual)
                posicao_orbita_ideal = pos_dono + pygame.math.Vector2(math.cos(rad), math.sin(rad)) * self.raio_orbita_dono
                posicao_alvo_seguir = posicao_orbita_ideal
            
            # 2. Calcula a nova posição baseada no LERP (movimento principal)
            # (Usando 0.15 como discutido para ser mais rápido)
            nova_posicao = self.posicao.lerp(posicao_alvo_seguir, 0.15) 

            # 3. Calcula o Vetor de Separação
            vetor_separacao = pygame.math.Vector2(0, 0)
            distancia_separacao_desejada = 40 # (tamanho * 2) - Raio de 40px
            fator_separacao = 0.5 # Força do "empurrão" (0.5 é sutil)

            # Itera sobre todos os minions do mesmo chefe
            for minion in self.owner.grupo_minions_congelantes:
                if minion != self: # Não se compara consigo mesmo
                    try:
                        dist = self.posicao.distance_to(minion.posicao)
                        if 0 < dist < distancia_separacao_desejada:
                            # Calcula vetor apontando para longe do outro minion
                            vetor_para_longe = self.posicao - minion.posicao
                            # A força é inversamente proporcional à distância
                            # (1 - (dist / dist_desejada)) -> 1.0 (grudado) a 0.0 (no limite)
                            forca = (1.0 - (dist / distancia_separacao_desejada))
                            vetor_para_longe.normalize_ip()
                            vetor_separacao += vetor_para_longe * forca * fator_separacao
                    except ValueError:
                        pass # Evita erro se posições forem idênticas
            
            # 4. Aplica o movimento principal (lerp) + o empurrão (separação)
            self.posicao = nova_posicao + vetor_separacao
            self.rect.center = self.posicao
            
            # --- FIM DA MODIFICAÇÃO (CÁLCULO DE SEPARAÇÃO) ---

        except ValueError:
             pass # Fica parado se alguma distância for zero

        # --- Lógica de Tiro ---
        if alvo_tiro:
            distancia_alvo_tiro = self.posicao.distance_to(alvo_tiro.posicao)
            if distancia_alvo_tiro < self.distancia_tiro:
                # --- MODIFICAÇÃO: Passa pos_ouvinte ---
                self.atirar(alvo_tiro.posicao, grupo_projeteis_inimigos, pos_ouvinte)

    # --- MODIFICAÇÃO: Remove o 'atirar' duplicado e corrige o restante ---
    # (O arquivo original tinha duas definições de 'atirar' aqui)
    def atirar(self, pos_alvo, grupo_projeteis_inimigos, pos_ouvinte=None):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora
            proj = ProjetilInimigo(self.posicao.x, self.posicao.y, pos_alvo) # Tiro normal
            grupo_projeteis_inimigos.add(proj)
            
            # --- MODIFICAÇÃO: Toca o som ---
            if tocar_som_posicional and pos_ouvinte and s.SOM_TIRO_INIMIGO_SIMPLES:
                tocar_som_posicional(s.SOM_TIRO_INIMIGO_SIMPLES, self.posicao, pos_ouvinte, VOLUME_BASE_TIRO_INIMIGO)

# --- FIM Minion Congelante ---


# --- Boss Congelante ---
class BossCongelante(InimigoBase):
    # ... (código do init inalterado) ...
    def __init__(self, x, y):
        # Chama super().__init__ PRIMEIRO para definir self.cor etc.
        super().__init__(x, y, tamanho=100, cor=AZUL_CONGELANTE, vida=HP_BOSS_CONGELANTE)

        # Desenho Circular
        self.image = pygame.Surface((self.tamanho, self.tamanho), pygame.SRCALPHA)
        centro = self.tamanho // 2
        pygame.draw.circle(self.image, self.cor, (centro, centro), centro) # self.cor já existe
        pygame.draw.circle(self.image, BRANCO, (centro, centro), centro, 2)
        self.rect = self.image.get_rect(center=self.posicao)
        self.distancia_deteccao = s.NPC_AGGRO_RANGE

        # Atributos específicos
        self.velocidade = 1
        self.pontos_por_morte = PONTOS_BOSS_CONGELANTE
        self.nome = f"Boss Congelante {random.randint(1, 9)}"
        self.cooldown_tiro = COOLDOWN_TIRO_CONGELANTE
        self.ultimo_tiro_tempo = 0
        self.alvo_ataque = None
        self.cooldown_spawn_minion = COOLDOWN_SPAWN_MINION_CONGELANTE
        self.ultimo_spawn_minion_tempo = 0
        self.max_minions = MAX_MINIONS_CONGELANTE
        self.grupo_minions_congelantes = pygame.sprite.Group()
        self.ultimo_atacante = None # Ainda não implementado como receber isso
        self.foi_atacado_recentemente = False
        
        # --- INÍCIO DA MODIFICAÇÃO (Wander) ---
        self.wander_target = None # Alvo para onde está vagando
        # --- FIM DA MODIFICAÇÃO ---

    # ... (código de foi_atingido inalterado) ...
    def foi_atingido(self, dano):
        vida_antes = self.vida_atual
        morreu = super().foi_atingido(dano)
        if not morreu and vida_antes > 0:
             self.foi_atacado_recentemente = True
        elif morreu: # Se morreu, limpa os minions que pertencem a ele
             print(f"[{self.nome}] Boss derrotado! Limpando minions...")
             self.grupo_minions_congelantes.empty() # Remove os minions dos grupos
        return morreu

    # ... (código do update inalterado) ...
    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn, pos_ouvinte=None): # <-- MODIFICADO
        # Lógica base de despawn
        pos_referencia = self.posicao
        alvo_mais_proximo_geral = None
        dist_min_geral = float('inf')
        
        # --- MODIFICAÇÃO: Bloco de encontrar 'pos_ouvinte' REMOVIDO ---
        
        for alvo in lista_alvos_naves:
             # --- MODIFICAÇÃO: Pega a posição do player (REMOVIDO) ---

            is_player = type(alvo).__name__ == 'Player'
            is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
            if is_player or is_active_bot:
                 try:
                     dist = self.posicao.distance_to(alvo.posicao)
                     if dist > self.distancia_deteccao:
                         continue # Ignora, muito longe
                     if dist < dist_min_geral:
                         dist_min_geral = dist
                         alvo_mais_proximo_geral = alvo
                         pos_referencia = alvo.posicao
                 except ValueError:
                     continue
        
        # --- MODIFICAÇÃO: Chamada update_base removida para persistência ---
        # if not self.update_base(pos_referencia, dist_despawn):
        #     self.grupo_minions_congelantes.empty()
        #     return
        # --- FIM DA MODIFICAÇÃO ---

        self.alvo_ataque = alvo_mais_proximo_geral
        # print(f"[{self.nome}] Alvo: {self.alvo_ataque.nome if self.alvo_ataque else 'Nenhum'}") # DEBUG

        agora = pygame.time.get_ticks()

        # Ataque
        if self.alvo_ataque:
            if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
                print(f"[{self.nome}] Atirando!") # DEBUG
                # --- MODIFICAÇÃO: Passa pos_ouvinte ---
                self.atirar(self.alvo_ataque, grupo_projeteis_inimigos, pos_ouvinte)
                self.ultimo_tiro_tempo = agora
            # else: print(f"[{self.nome}] Tiro em cooldown...") # DEBUG

        # Spawn
        if self.foi_atacado_recentemente and (agora - self.ultimo_spawn_minion_tempo > self.cooldown_spawn_minion):
             if len(self.grupo_minions_congelantes) < self.max_minions:
                 print(f"[{self.nome}] Gerando Minion!") # DEBUG
                 self.spawnar_minion()
                 self.ultimo_spawn_minion_tempo = agora
             self.foi_atacado_recentemente = False # Reseta flag
        # elif self.foi_atacado_recentemente: print(f"[{self.nome}] Foi atacado, spawn em cooldown...") # DEBUG

        # --- INÍCIO MODIFICAÇÃO: Lógica de Vaguear (Wander) ---
        # Movimento
        try:
            # 1. Se não tem alvo ou chegou perto do alvo, define um novo
            if self.wander_target is None or self.posicao.distance_to(self.wander_target) < 100:
                # Escolhe um ponto aleatório no mapa (com margem de borda)
                map_margin = 100
                target_x = random.randint(map_margin, MAP_WIDTH - map_margin)
                target_y = random.randint(map_margin, MAP_HEIGHT - map_margin)
                self.wander_target = pygame.math.Vector2(target_x, target_y)
                # print(f"[{self.nome}] Novo alvo de wander: {self.wander_target}") # DEBUG

            # 2. Move em direção ao alvo
            vetor_para_alvo = self.wander_target - self.posicao
            if vetor_para_alvo.length() > 5: # 5 é a distância mínima para parar
                # self.velocidade é 1 (definido no init), o que é bom para um boss
                self.posicao += vetor_para_alvo.normalize() * self.velocidade 
                self.rect.center = self.posicao
                
        except ValueError:
             self.wander_target = None # Reseta o alvo se houver um erro
             pass
        # --- FIM MODIFICAÇÃO ---

    # --- MODIFICAÇÃO: Usa SOM_TIRO_CONGELANTE e VOLUME_BASE_TIRO_CONGELANTE ---
    def atirar(self, alvo_sprite, grupo_projeteis_inimigos, pos_ouvinte=None): # Mudou de pos_alvo para alvo_sprite
        # Este método agora pertence ao BossCongelante
        # Verifica se o alvo_sprite ainda é válido antes de criar o projétil
        if alvo_sprite and alvo_sprite.groups():
            proj = ProjetilCongelante(self.posicao.x, self.posicao.y, alvo_sprite) # Passa o sprite
            grupo_projeteis_inimigos.add(proj)
            
            # Toca o som congelante
            if tocar_som_posicional and pos_ouvinte and s.SOM_TIRO_CONGELANTE:
                tocar_som_posicional(s.SOM_TIRO_CONGELANTE, self.posicao, pos_ouvinte, VOLUME_BASE_TIRO_CONGELANTE)
            
    # ... (código de spawnar_minion inalterado) ...
    def spawnar_minion(self):
        # Este método agora pertence ao BossCongelante
        angulo_rad = random.uniform(0, 2 * math.pi)
        raio_spawn = self.tamanho * 0.7
        spawn_x = self.posicao.x + math.cos(angulo_rad) * raio_spawn
        spawn_y = self.posicao.y + math.sin(angulo_rad) * raio_spawn

        # --- INÍCIO DA MODIFICAÇÃO ---
        # Passa o índice atual e o máximo de minions para o construtor
        indice_minion_atual = len(self.grupo_minions_congelantes)
        minion = MinionCongelante(spawn_x, spawn_y, self, indice_minion_atual, self.max_minions)
        # --- FIM DA MODIFICAÇÃO ---
        
        self.grupo_minions_congelantes.add(minion)

        if grupo_inimigos_global_ref is not None:
            grupo_inimigos_global_ref.add(minion)
        else:
             print("[ERRO] grupo_inimigos_global_ref não definido!")

# --- FIM Boss Congelante ---


# --- Outros Inimigos ---
# (Resto do arquivo inalterado, pois os outros inimigos já usam o som correto)

# Inimigo Perseguidor Padrão (Vermelho)
class InimigoPerseguidor(InimigoBase):
    def __init__(self, x, y):
        super().__init__(x, y, tamanho=30, cor=VERMELHO_PERSEGUIDOR, vida=3)
        self.velocidade = 2; self.distancia_parar = 200; self.cooldown_tiro = 2000
        self.ultimo_tiro_tempo = 0; self.distancia_tiro = 500; self.pontos_por_morte = 5
        self.distancia_deteccao = s.NPC_AGGRO_RANGE

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn, pos_ouvinte=None): # <-- MODIFICADO
        alvo_mais_proximo = None; dist_min = float('inf')
        
        # --- MODIFICAÇÃO: Bloco de encontrar 'pos_ouvinte' REMOVIDO ---

        for alvo in lista_alvos_naves:
             # --- MODIFICAÇÃO: Pega a posição do player (REMOVIDO) ---
        
            is_player = type(alvo).__name__ == 'Player'
            is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
            if not is_player and not is_active_bot: continue
            try: dist = self.posicao.distance_to(alvo.posicao)
            except ValueError: continue
            if dist > self.distancia_deteccao:
                continue # Ignora este alvo, está muito longe
            if dist < dist_min: dist_min = dist; alvo_mais_proximo = alvo

        if not alvo_mais_proximo:
             # --- MODIFICAÇÃO: Chamada update_base removida para persistência ---
             # if not self.update_base(self.posicao, dist_despawn): return
             # --- FIM DA MODIFICAÇÃO ---
             return

        pos_alvo = alvo_mais_proximo.posicao
        # --- MODIFICAÇÃO: Chamada update_base removida para persistência ---
        # if not self.update_base(pos_alvo, dist_despawn): return
        # --- FIM DA MODIFICAÇÃO ---
        distancia_alvo = dist_min

        if distancia_alvo > self.distancia_parar:
            try: direcao = (pos_alvo - self.posicao).normalize(); self.posicao += direcao * self.velocidade; self.rect.center = self.posicao
            except ValueError: pass
        if distancia_alvo < self.distancia_tiro: 
            # --- MODIFICAÇÃO: Passa pos_ouvinte ---
            self.atirar(pos_alvo, grupo_projeteis_inimigos, pos_ouvinte)

    # --- MODIFICAÇÃO: Aceita pos_ouvinte e toca som ---
    def atirar(self, pos_alvo, grupo_projeteis_inimigos, pos_ouvinte=None):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora
            proj = ProjetilInimigo(self.posicao.x, self.posicao.y, pos_alvo)
            grupo_projeteis_inimigos.add(proj)
            
            # Toca o som
            if tocar_som_posicional and pos_ouvinte and s.SOM_TIRO_INIMIGO_SIMPLES:
                tocar_som_posicional(s.SOM_TIRO_INIMIGO_SIMPLES, self.posicao, pos_ouvinte, VOLUME_BASE_TIRO_INIMIGO)

# Inimigo Atirador Rápido (Roxo - antigo, mantido por referência)
class InimigoAtiradorRapido(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.cor = ROXO_ATIRADOR_RAPIDO # Atualiza a cor
        self.image.fill(self.cor)
        self.max_vida = 1; self.vida_atual = 1
        self.cooldown_tiro = 500; self.distancia_parar = 300; self.pontos_por_morte = 10
    # O método 'atirar' é herdado (já modificado na classe InimigoPerseguidor)
    # O método 'update' é herdado (já modificado na classe InimigoPerseguidor)

# Inimigo Bomba (Amarelo)
class InimigoBomba(InimigoBase):
    def __init__(self, x, y):
        super().__init__(x, y, tamanho=25, cor=AMARELO_BOMBA, vida=1)
        self.velocidade = 3; self.DANO_EXPLOSAO = 3; self.pontos_por_morte = 3
        self.distancia_deteccao = s.NPC_AGGRO_RANGE

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn, pos_ouvinte=None): # <-- MODIFICADO
        alvo_mais_proximo = None; dist_min = float('inf')
        for alvo in lista_alvos_naves:
            is_player = type(alvo).__name__ == 'Player'
            is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
            if not is_player and not is_active_bot: continue
            try: dist = self.posicao.distance_to(alvo.posicao)
            except ValueError: continue
            if dist > self.distancia_deteccao:
                continue # Ignora este alvo, está muito longe
            if dist < dist_min: dist_min = dist; alvo_mais_proximo = alvo

        if not alvo_mais_proximo:
            # --- MODIFICAÇÃO: Chamada update_base removida para persistência ---
            # if not self.update_base(self.posicao, dist_despawn): return
            # --- FIM DA MODIFICAÇÃO ---
            return

        pos_alvo = alvo_mais_proximo.posicao
        # --- MODIFICAÇÃO: Chamada update_base removida para persistência ---
        # if not self.update_base(pos_alvo, dist_despawn): return
        # --- FIM DA MODIFICAÇÃO ---

        try: direcao = (pos_alvo - self.posicao).normalize(); self.posicao += direcao * self.velocidade; self.rect.center = self.posicao
        except ValueError: pass
        # Não atira, explode na colisão (tratado em main.py)
        
    def foi_atingido(self, dano):
            # Esta função agora substitui a de InimigoBase
        agora = pygame.time.get_ticks()
        
        # Ignora a lógica de cooldown de hit; a bomba morre no primeiro toque.
        self.vida_atual -= dano
        self.ultimo_hit_tempo = agora
        
        if self.vida_atual <= 0:
            if grupo_explosoes is not None:
                # Usa o tamanho maior que discutimos (Tamanho 25 + 15 = 40)
                tamanho_explosao_bomba = self.tamanho + 100 
                explosao = Explosao(self.rect.center, tamanho_explosao_bomba)
                grupo_explosoes.add(explosao)
            self.kill()
            return True
        return False

# Inimigo Rápido (Laranja)
class InimigoRapido(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.cor = LARANJA_RAPIDO
        self.image.fill(self.cor)
        self.max_vida = 5; self.vida_atual = 5
        self.velocidade = 4.0
        self.cooldown_tiro = 800
        self.pontos_por_morte = 9
    
    # O método 'update' é herdado (já modificado na classe InimigoPerseguidor)

    # --- MODIFICAÇÃO: Aceita pos_ouvinte e toca som ---
    def atirar(self, pos_alvo, grupo_projeteis_inimigos, pos_ouvinte=None):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora
            proj = ProjetilInimigoRapidoCurto(self.posicao.x, self.posicao.y, pos_alvo)
            grupo_projeteis_inimigos.add(proj)
            
            # Toca o som
            if tocar_som_posicional and pos_ouvinte and s.SOM_TIRO_INIMIGO_SIMPLES:
                tocar_som_posicional(s.SOM_TIRO_INIMIGO_SIMPLES, self.posicao, pos_ouvinte, VOLUME_BASE_TIRO_INIMIGO)

# Inimigo Tiro Rápido (Azul)
class InimigoTiroRapido(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.cor = AZUL_TIRO_RAPIDO
        self.image.fill(self.cor)
        self.max_vida = 10; self.vida_atual = 10
        self.velocidade = 1.5; self.cooldown_tiro = 1500; self.pontos_por_morte = 20
    
    # O método 'update' é herdado (já modificado na classe InimigoPerseguidor)

    # --- MODIFICAÇÃO: Aceita pos_ouvinte e toca som (SOM ESPECIAL) ---
    def atirar(self, pos_alvo, grupo_projeteis_inimigos, pos_ouvinte=None):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora
            proj = ProjetilInimigoRapido(self.posicao.x, self.posicao.y, pos_alvo)
            grupo_projeteis_inimigos.add(proj)
            
            # Toca o som especial de laser longo
            if tocar_som_posicional and pos_ouvinte and s.SOM_TIRO_LASER_LONGO:
                tocar_som_posicional(s.SOM_TIRO_LASER_LONGO, self.posicao, pos_ouvinte, VOLUME_BASE_TIRO_LASER_LONGO)

# Inimigo Atordoador (Roxo)
class InimigoAtordoador(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.cor = ROXO_ATORDOADOR
        self.image.fill(self.cor)
        self.max_vida = 5; self.vida_atual = 5
        self.velocidade = 1.0; self.cooldown_tiro = 5000; self.pontos_por_morte = 25

    # Update precisa passar o sprite do alvo para 'atirar'
    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn, pos_ouvinte=None): # <-- MODIFICADO
        alvo_mais_proximo = None; dist_min = float('inf')
        
        # --- MODIFICAÇÃO: Bloco de encontrar 'pos_ouvinte' REMOVIDO ---

        for alvo in lista_alvos_naves:
             # --- MODIFICAÇÃO: Pega a posição do player (REMOVIDO) ---
        
            is_player = type(alvo).__name__ == 'Player'
            is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
            if not is_player and not is_active_bot: continue
            try: dist = self.posicao.distance_to(alvo.posicao)
            except ValueError: continue
            if dist < dist_min: dist_min = dist; alvo_mais_proximo = alvo

        if not alvo_mais_proximo:
             # --- MODIFICAÇÃO: Chamada update_base removida para persistência ---
             # if not self.update_base(self.posicao, dist_despawn): return
             # --- FIM DA MODIFICAÇÃO ---
             return

        pos_alvo_para_mov = alvo_mais_proximo.posicao
        # --- MODIFICAÇÃO: Chamada update_base removida para persistência ---
        # if not self.update_base(pos_alvo_para_mov, dist_despawn): return
        # --- FIM DA MODIFICAÇÃO ---
        distancia_alvo = dist_min

        if distancia_alvo > self.distancia_parar:
            try: direcao = (pos_alvo_para_mov - self.posicao).normalize(); self.posicao += direcao * self.velocidade; self.rect.center = self.posicao
            except ValueError: pass
        if distancia_alvo < self.distancia_tiro:
            # --- MODIFICAÇÃO: Passa pos_ouvinte ---
            self.atirar(alvo_mais_proximo, grupo_projeteis_inimigos, pos_ouvinte) # Passa o sprite

    # --- MODIFICAÇÃO: Aceita pos_ouvinte e toca som ---
    def atirar(self, alvo_sprite, grupo_projeteis_inimigos, pos_ouvinte=None): # Recebe o sprite
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora
            proj = ProjetilTeleguiadoLento(self.posicao.x, self.posicao.y, alvo_sprite)
            grupo_projeteis_inimigos.add(proj)
            
            # Toca o som (som normal de inimigo, a menos que queira um som de "stun")
            if tocar_som_posicional and pos_ouvinte and s.SOM_TIRO_INIMIGO_SIMPLES:
                tocar_som_posicional(s.SOM_TIRO_INIMIGO_SIMPLES, self.posicao, pos_ouvinte, VOLUME_BASE_TIRO_INIMIGO)

# --- MINION E MOTHERSHIP ---

# Minion da Mothership
class InimigoMinion(InimigoBase):
    def __init__(self, x, y, owner, target, index, max_minions):
        super().__init__(x, y, tamanho=15, cor=CIANO_MINION, vida=2);
        self.owner = owner; self.target = target
        self.velocidade = 3; self.cooldown_tiro = 1000; self.distancia_tiro = 500; self.pontos_por_morte = 1
        self.ultimo_tiro_tempo = 0; self.distancia_despawn_minion = 1000 # Distância do *dono* para o alvo
        self.raio_orbita = self.owner.tamanho * 0.8 + random.randint(30, 60); self.angulo_orbita_atual = (index / max_minions) * 360
        self.velocidade_orbita = random.uniform(0.5, 1.0); self.angulo_mira = 0

        # Desenho (triângulo)
        self.imagem_original = pygame.Surface((self.tamanho + 5, self.tamanho + 5), pygame.SRCALPHA)
        centro = (self.tamanho + 5) / 2; ponto_topo = (centro, centro - self.tamanho / 2)
        ponto_base_esq = (centro - self.tamanho / 2, centro + self.tamanho / 2); ponto_base_dir = (centro + self.tamanho / 2, centro + self.tamanho / 2)
        pygame.draw.polygon(self.imagem_original, CIANO_MINION, [ponto_topo, ponto_base_esq, ponto_base_dir])
        self.image = self.imagem_original
        self.rect = self.image.get_rect(center=self.posicao) # Atualiza rect após criar imagem

    # --- MODIFICAÇÃO: Aceita pos_ouvinte e toca som ---
    def atirar(self, pos_alvo, grupo_projeteis_inimigos, pos_ouvinte=None):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro_tempo > self.cooldown_tiro:
            self.ultimo_tiro_tempo = agora
            proj = ProjetilInimigo(self.posicao.x, self.posicao.y, pos_alvo)
            grupo_projeteis_inimigos.add(proj)
            
            # Toca o som
            if tocar_som_posicional and pos_ouvinte and s.SOM_TIRO_INIMIGO_SIMPLES:
                tocar_som_posicional(s.SOM_TIRO_INIMIGO_SIMPLES, self.posicao, pos_ouvinte, VOLUME_BASE_TIRO_INIMIGO)

    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn, pos_ouvinte=None): # <-- MODIFICADO
        # Verifica se dono ou alvo ainda existem e se estão perto
        
        # --- INÍCIO DA MODIFICAÇÃO (MOTHERSHIP MINION TARGETING) ---
        if self.owner is None or not self.owner.groups(): 
            self.kill() # Dono morreu, minion morre
            return
            
        # O minion AGORA É BURRO: ele apenas copia o alvo do dono.
        # Verifica se o alvo do dono (Mothership) é válido
        if self.owner.alvo_retaliacao and self.owner.alvo_retaliacao.groups():
            # Verifica a "coleira" (leash) - O minion está perto o suficiente DO ALVO?
            try:
                dist_minion_alvo = self.posicao.distance_to(self.owner.alvo_retaliacao.posicao)
                if dist_minion_alvo < self.distancia_despawn_minion: # Usa a coleira do minion (1000)
                    self.target = self.owner.alvo_retaliacao
                else:
                    self.target = None # Alvo do dono está muito longe para este minion
            except ValueError:
                self.target = None
        else:
            self.target = None # Dono não tem alvo
        
        # --- FIM DA MODIFICAÇÃO (MOTHERSHIP MINION TARGETING) ---

        
        # --- MODIFICAÇÃO: Bloco de encontrar 'pos_ouvinte' REMOVIDO ---

        # Órbita
        self.angulo_orbita_atual = (self.angulo_orbita_atual + self.velocidade_orbita) % 360; rad = math.radians(self.angulo_orbita_atual)
        pos_alvo_orbita = self.owner.posicao + pygame.math.Vector2(math.cos(rad), math.sin(rad)) * self.raio_orbita
        self.posicao = self.posicao.lerp(pos_alvo_orbita, 0.05)

        # Mira e Tiro (no alvo guardado)
        # --- MODIFICAÇÃO: Adiciona verificação se 'self.target' existe ---
        if self.target:
            try:
                dist_para_alvo = self.posicao.distance_to(self.target.posicao); direcao_vetor = (self.target.posicao - self.posicao)
                if direcao_vetor.length() > 0:
                     # Calcula ângulo para mirar
                     self.angulo_mira = pygame.math.Vector2(0, -1).angle_to(direcao_vetor)
                     if dist_para_alvo < self.distancia_tiro:
                         # --- MODIFICAÇÃO: Passa pos_ouvinte ---
                         self.atirar(self.target.posicao, grupo_projeteis_inimigos, pos_ouvinte)
                else: # Se estiver exatamente sobre o alvo, mira para cima
                    self.angulo_mira = 0
            except ValueError:
                 self.angulo_mira = 0 # Erro ao calcular, mira para cima
        else:
            # Se não tem alvo, mira para "frente" (ângulo da órbita)
            # ou alinha com o dono (mais simples)
            try:
                vetor_para_dono = self.owner.posicao - self.posicao
                if vetor_para_dono.length() > 0:
                    self.angulo_mira = pygame.math.Vector2(0, -1).angle_to(vetor_para_dono) + 90 # Tangencial
                else:
                    self.angulo_mira = 0
            except ValueError:
                self.angulo_mira = 0
        # --- FIM DA MODIFICAÇÃO ---

        # Rotaciona imagem
        self.image = pygame.transform.rotate(self.imagem_original, self.angulo_mira);
        self.rect = self.image.get_rect(center = self.posicao)

# Mothership
class InimigoMothership(InimigoPerseguidor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.tamanho = 80; self.cor = CIANO_MOTHERSHIP
        self.image = pygame.Surface((self.tamanho, self.tamanho)); self.image.fill(self.cor) # Recria imagem com tamanho certo
        self.rect = self.image.get_rect(center=(x,y));
        self.max_vida = 200; self.vida_atual = 200; self.velocidade = 1; self.pontos_por_morte = 100
        self.nome = f"Mothership {random.randint(1, 99)}"; self.estado_ia = "VAGANDO"; self.alvo_retaliacao = None
        self.distancia_despawn_minion = 1000; self.max_minions = 8; self.grupo_minions = pygame.sprite.Group()
        self.distancia_deteccao = s.NPC_AGGRO_RANGE # <-- ADICIONE ESTA LINHA
        # Não atira diretamente (Mothership não tem método 'atirar', o que está correto)

    def encontrar_atacante_mais_proximo(self, lista_alvos_naves):
        dist_min = float('inf'); alvo_prox = None
        for alvo in lista_alvos_naves:
            is_player = type(alvo).__name__ == 'Player'
            is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
            if not is_player and not is_active_bot: continue
            try: dist = self.posicao.distance_to(alvo.posicao);
            except ValueError: continue
            if dist > self.distancia_deteccao:
                continue # Ignora, muito longe
            if dist < dist_min: dist_min = dist; alvo_prox = alvo
        return alvo_prox

    def spawnar_minions(self):
        # Spawna minions apenas se: tem alvo, grupo está vazio, e referência global existe
        if self.alvo_retaliacao and len(self.grupo_minions) == 0 and grupo_inimigos_global_ref is not None:
            is_player = type(self.alvo_retaliacao).__name__ == 'Player'
            is_active_bot = type(self.alvo_retaliacao).__name__ == 'NaveBot' and self.alvo_retaliacao.groups()
            if not is_player and not is_active_bot:
                self.alvo_retaliacao = None; self.estado_ia = "VAGANDO"; return

            print(f"[{self.nome}] Gerando {self.max_minions} minions!")
            for i in range(self.max_minions):
                angulo_rad = (i / self.max_minions) * 2 * math.pi; raio_spawn = self.tamanho * 0.8
                spawn_x = self.posicao.x + math.cos(angulo_rad) * raio_spawn; spawn_y = self.posicao.y + math.sin(angulo_rad) * raio_spawn
                # Passa a mothership (self) como dono e o alvo_retaliacao como target
                minion = InimigoMinion(spawn_x, spawn_y, self, self.alvo_retaliacao, i, self.max_minions)
                self.grupo_minions.add(minion); grupo_inimigos_global_ref.add(minion)

    def foi_atingido(self, dano):
        # Sobrescreve para limpar minions se morrer
        morreu = super().foi_atingido(dano)
        if morreu:
            print(f"[{self.nome}] Mothership derrotada! Limpando minions...")
            self.grupo_minions.empty()
        return morreu


    def update(self, lista_alvos_naves, grupo_projeteis_inimigos, dist_despawn, pos_ouvinte=None): # <-- MODIFICADO
        # Lógica base de despawn
        pos_referencia = self.posicao
        alvo_mais_proximo_ref = None
        dist_min_ref = float('inf')
        for alvo in lista_alvos_naves:
             is_player = type(alvo).__name__ == 'Player'
             is_active_bot = type(alvo).__name__ == 'NaveBot' and alvo.groups()
             if is_player or is_active_bot:
                 try:
                     dist = self.posicao.distance_to(alvo.posicao)
                     if dist < dist_min_ref:
                         dist_min_ref = dist
                         alvo_mais_proximo_ref = alvo
                         pos_referencia = alvo.posicao
                 except ValueError: continue

        # --- MODIFICAÇÃO: Chamada update_base removida para persistência ---
        # if not self.update_base(pos_referencia, dist_despawn):
        #      self.grupo_minions.empty() # Limpa minions ao despawnar
        #      return
        # --- FIM DA MODIFICAÇÃO ---

        agora = pygame.time.get_ticks()

        # Inicia retaliação se foi atingido recentemente e não tem alvo ainda
        if (agora - self.ultimo_hit_tempo < 1000) and self.alvo_retaliacao is None:
            self.alvo_retaliacao = self.encontrar_atacante_mais_proximo(lista_alvos_naves)
            if self.alvo_retaliacao:
                 print(f"[{self.nome}] Fui atacado! Retaliando contra {self.alvo_retaliacao.nome}")
                 self.estado_ia = "RETALIANDO"

        # Lógica de IA
        if self.estado_ia == "VAGANDO":
            # Move lentamente para o centro
            try:
                 vetor_para_centro = pygame.math.Vector2(MAP_WIDTH/2, MAP_HEIGHT/2) - self.posicao
                 if vetor_para_centro.length() > 50:
                     self.posicao += vetor_para_centro.normalize() * (self.velocidade * 0.5)
                     self.rect.center = self.posicao
            except ValueError: pass
        elif self.estado_ia == "RETALIANDO":
            perdeu_alvo = False
            if self.alvo_retaliacao is None or not self.alvo_retaliacao.groups(): perdeu_alvo = True
            else:
                is_player = type(self.alvo_retaliacao).__name__ == 'Player'
                is_active_bot = type(self.alvo_retaliacao).__name__ == 'NaveBot' and self.alvo_retaliacao.groups()
                if not is_player and not is_active_bot: perdeu_alvo = True
                else:
                    # --- MODIFICAÇÃO: Lógica da "coleira" (leash) REATIVADA ---
                    try: # Verifica distância para o alvo
                       # --- INÍCIO DA CORREÇÃO DO CRASH (Typo) ---
                       if self.posicao.distance_to(self.alvo_retaliacao.posicao) > self.distancia_despawn_minion: 
                       # --- FIM DA CORREÇÃO DO CRASH (Typo) ---
                           perdeu_alvo = True
                    except ValueError: 
                        perdeu_alvo = True
                    # --- FIM DA MODIFICAÇÃO ---


            if perdeu_alvo:
                print(f"[{self.nome}] Alvo perdido. Voltando a vagar.")
                self.alvo_retaliacao = None; self.estado_ia = "VAGANDO"
                # --- INÍCIO DA CORREÇÃO DO BUG (MOTHERSHIP) ---
                # self.grupo_minions.empty() # REMOVIDO: Esta linha matava os minions
                # --- FIM DA CORREÇÃO DO BUG (MOTHERSHIP) ---
            else:
                self.spawnar_minions() # Tenta spawnar (só funciona se o grupo estiver vazio)
                # Foge do alvo
                try:
                     direcao_fuga = (self.posicao - self.alvo_retaliacao.posicao).normalize()
                     self.posicao += direcao_fuga * self.velocidade
                     self.rect.center = self.posicao
                except ValueError: pass # Se estiver sobreposto, fica parado