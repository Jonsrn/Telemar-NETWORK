import socket
import threading
import json
import networkx as nx
import time
import matplotlib.pyplot as plt
import argparse
import os
import math
import heapq

class Roteador:
    @staticmethod
    def aguardar_ip_disponivel(ip, porta, tentativas=30):
        for i in range(tentativas):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.bind((ip, porta))
                s.close()
                return  # sucesso
            except OSError:
                print(f"[Roteador] Aguardando IP {ip}:{porta}... tentativa {i+1}")
                time.sleep(1)
        raise RuntimeError(f"[ERRO] IP {ip}:{porta} não ficou disponível a tempo.")

    def __init__(self, meu_ip, subrede_local, interfaces_wan_json):
        self.meu_ip = meu_ip
        self.subrede_local = subrede_local
        self.interfaces_wan = json.loads(interfaces_wan_json)

        self.sockets = {}
        self.interfaces_locais = set([self.meu_ip] + list(self.interfaces_wan.keys()))
        self.vizinho_para_iface = {}
        self.grafo_dinamico = nx.Graph()

        self.lsas_vistos = set()
        self.seq_lsa = 0
        self.topologia_local = {}
        self.vizinhos_ativos = {}
        self.estado_vizinhos = {}  # chave: vizinho, valor: 'ativo' ou 'inativo'
        
        # Criar diretório para grafos se não existir
        if not os.path.exists("grafos"):
            os.makedirs("grafos")

    # Para salvar graficamente o grafo
    def salvar_grafo(self):
        time.sleep(5) # Original sleep

        # Agrupa interfaces pelo roteador baseado em conexões internas (peso 0)
        def agrupar_interfaces(grafo):
            clusters = []
            visitado = set()

            for node in grafo.nodes():
                if node in visitado:
                    continue

                cluster = set()
                fila = [node]

                while fila:
                    atual = fila.pop()
                    if atual in visitado:
                        continue

                    visitado.add(atual)
                    cluster.add(atual)

                    for viz in grafo.neighbors(atual):
                        if grafo[atual][viz].get("weight", 1) == 0:
                            fila.append(viz)

                clusters.append(cluster)

            return clusters

        clusters = agrupar_interfaces(self.grafo_dinamico)

        # Posiciona roteadores em um anel externo
        N = len(clusters)
        R_outer = 10
        pos = {}
        centers = {}
        Gdraw = self.grafo_dinamico.copy()

        for idx, cluster in enumerate(sorted(clusters, key=lambda x: self.meu_ip in x, reverse=True)):
            ang_c = 2 * math.pi * idx / N
            cx, cy = R_outer * math.cos(ang_c), R_outer * math.sin(ang_c)
            centers[idx] = (cx, cy)

            hub_name = f"hub_{idx}"
            Gdraw.add_node(hub_name)
            pos[hub_name] = (cx, cy)

            interfaces = sorted(cluster)
            m = len(interfaces)
            R_inner = 1.3 + 0.35 * m

            for i, iface in enumerate(interfaces):
                if m == 1:
                    ang = ang_c + math.pi / 2
                else:
                    ang = ang_c + (2 * math.pi * i / m)

                px = cx + R_inner * math.cos(ang)
                py = cy + R_inner * math.sin(ang)
                pos[iface] = (px, py)

                # conecta visualmente interfaces ao hub
                Gdraw.add_edge(hub_name, iface)

            # fecha polígono visual
            if m >= 2:
                for i in range(m):
                    Gdraw.add_edge(interfaces[i], interfaces[(i + 1) % m])

        plt.figure(figsize=(11, 8))

        ports = [n for n in Gdraw.nodes() if not str(n).startswith("hub")]
        hubs = [n for n in Gdraw.nodes() if str(n).startswith("hub")]

        nx.draw_networkx_nodes(Gdraw, pos, nodelist=ports, node_color="skyblue", node_size=1100)
        nx.draw_networkx_nodes(Gdraw, pos, nodelist=hubs, node_color="#888888", node_size=80)
        nx.draw_networkx_edges(Gdraw, pos, edge_color="gray", width=1.4)

        nx.draw_networkx_labels(Gdraw, pos, labels={n: n for n in ports}, font_size=9, font_weight="bold")

        plt.title(f"Topologia – roteador {self.meu_ip}")
        plt.axis("off")
        plt.tight_layout()

        nome = os.path.join("grafos", f"grafo_{self.meu_ip.replace('.', '_')}.png")
        plt.savefig(nome, dpi=150)
        plt.close()
        print(f"[CLI] Topologia salva como {nome}")

    # === Protocolo HELLO ===
    def _enviar_hellos_target(self):
        while True:
            for minha_iface, vizinhos in self.interfaces_wan.items():
                for vizinho in vizinhos:
                    mensagem = {
                        "tipo": "hello",
                        "origem": minha_iface
                    }
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.sendto(json.dumps(mensagem).encode(), (vizinho, 5000))
                        sock.close()
                    except:
                        pass # Originalmente pass, mantendo assim
            time.sleep(3)

    def iniciar_hello_protocol(self):
        threading.Thread(target=self._enviar_hellos_target, daemon=True).start()

    # === Protocolo LSA ===
    def enviar_lsa(self):
        for iface_local in self.interfaces_wan.keys():
            vizinhos_com_peso = {}

            for vizinho in self.grafo_dinamico.neighbors(iface_local):
                peso = self.grafo_dinamico[iface_local][vizinho].get("weight", 1)
                vizinhos_com_peso[vizinho] = peso

            mensagem = {
                "tipo": "lsa",
                "origem": iface_local,
                "vizinhos": vizinhos_com_peso,
                "seq": self.seq_lsa
            }

            self.seq_lsa += 1
            self.lsas_vistos.add((iface_local, mensagem["seq"]))

            for lista_vizinhos_iface_wan in self.interfaces_wan.values(): # Renomeado para clareza
                for viz_wan in lista_vizinhos_iface_wan: # Renomeado para clareza
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.sendto(json.dumps(mensagem).encode(), (viz_wan, 5000))
                        s.close()
                    except:
                        continue

    def _lsa_ciclo_target(self):
        while True:
            self.enviar_lsa()
            time.sleep(10)

    def iniciar_lsa_protocol(self):
        threading.Thread(target=self._lsa_ciclo_target, daemon=True).start()

    # === Processamento de LSA recebido ===
    def processar_lsa(self, pacote, porta_origem_lsa): # porta_origem_lsa é a minha_iface que recebeu
        origem = pacote["origem"]
        vizinhos = pacote["vizinhos"]  # agora é um dicionário: {vizinho: peso}
        seq = pacote["seq"]

        if (origem, seq) in self.lsas_vistos:
            return

        self.lsas_vistos.add((origem, seq))

        # Se não houve mudança na topologia (estrutura e pesos), ignora
        vizinhos_recebidos_set = set(vizinhos.keys()) # Renomeado para clareza
        vizinhos_atuais_no_cache = self.topologia_local.get(origem, {}) # Renomeado para clareza

        if vizinhos_atuais_no_cache == vizinhos: # Compara dicts diretamente
            return

        # Remove arestas antigas que não existem mais
        for vizinho_antigo in set(vizinhos_atuais_no_cache.keys()):
            if vizinho_antigo not in vizinhos_recebidos_set and self.grafo_dinamico.has_edge(origem, vizinho_antigo):
                self.grafo_dinamico.remove_edge(origem, vizinho_antigo)
                print(f"[LSA] Roteador {origem} ↔ {vizinho_antigo} REMOVIDO")

        # Adiciona ou atualiza as arestas recebidas
        for vizinho_novo, peso in vizinhos.items():
            if not self.grafo_dinamico.has_edge(origem, vizinho_novo):
                self.grafo_dinamico.add_edge(origem, vizinho_novo, weight=peso)
                print(f"[LSA] Roteador {origem} ↔ {vizinho_novo} ADICIONADO (peso {peso})")
            else:
                peso_atual = self.grafo_dinamico[origem][vizinho_novo].get("weight", 1)
                if peso != peso_atual:
                    self.grafo_dinamico[origem][vizinho_novo]["weight"] = peso
                    print(f"[LSA] Roteador {origem} ↔ {vizinho_novo} ATUALIZADO (peso {peso})")

        # Atualiza cache local
        self.topologia_local[origem] = vizinhos

        # Propaga o LSA para outros vizinhos (exceto o que enviou originalmente para esta interface)
        for iface_local_prop, lista_vizinhos_wan in self.interfaces_wan.items():
            for viz_wan_prop in lista_vizinhos_wan:
                # Não propaga de volta para o vizinho de onde o LSA veio nesta interface específica
                # Esta lógica de não propagar de volta ao remetente imediato é complexa de implementar
                # perfeitamente sem saber o IP exato do remetente do LSA original.
                # O código original propaga para todos os vizinhos WAN.
                # Mantendo a lógica original de propagação para todos os vizinhos WAN.
                try:
                    nova_mensagem = json.dumps(pacote).encode()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.sendto(nova_mensagem, (viz_wan_prop, 5000))
                    sock.close()
                except:
                    continue

    # === Dijkstra ===
    def _dijkstra_customizado(self, origem, destino):
        # Grafo é self.grafo_dinamico
        # Nós são strings (IPs)
        # Pesos estão em self.grafo_dinamico[u][v]['weight']

        if not self.grafo_dinamico.has_node(origem):
            # print(f"[Dijkstra Custom DEBUG] Nó de origem {origem} não existe no grafo.")
            return None
        if not self.grafo_dinamico.has_node(destino):
            # print(f"[Dijkstra Custom DEBUG] Nó de destino {destino} não existe no grafo.")
            return None

        distancias = {node: float('inf') for node in self.grafo_dinamico.nodes()}
        predecessores = {node: None for node in self.grafo_dinamico.nodes()}
        distancias[origem] = 0

        # Fila de prioridade armazena (distancia, no)
        fila_prioridade = [(0, origem)]

        while fila_prioridade:
            dist_atual, no_atual = heapq.heappop(fila_prioridade)

            # Se já encontramos um caminho menor para no_atual, ignoramos
            if dist_atual > distancias[no_atual]:
                continue

            # Se alcançamos o destino, podemos parar e reconstruir o caminho
            # (Opcional: para Dijkstra padrão, continua até a fila esvaziar para encontrar todos os caminhos mais curtos)
            # Mas para encontrar UM caminho mais curto para um destino específico, podemos parar aqui.
            if no_atual == destino:
                break 

            try:
                vizinhos_do_no_atual = self.grafo_dinamico.neighbors(no_atual)
            except nx.NetworkXError: # Caso o nó não esteja no grafo (pouco provável se passou as verificações iniciais)
                # print(f"[Dijkstra Custom DEBUG] Erro ao obter vizinhos de {no_atual}.")
                continue
                
            for vizinho in vizinhos_do_no_atual:
                if self.grafo_dinamico.has_edge(no_atual, vizinho):
                    peso = self.grafo_dinamico[no_atual][vizinho].get("weight", 1) # Default weight 1 se não especificado
                    distancia_candidata = distancias[no_atual] + peso

                    if distancia_candidata < distancias[vizinho]:
                        distancias[vizinho] = distancia_candidata
                        predecessores[vizinho] = no_atual
                        heapq.heappush(fila_prioridade, (distancia_candidata, vizinho))
        
        # Reconstruir o caminho
        caminho = []
        passo_atual = destino
        if distancias[passo_atual] == float('inf'):
            return None # Destino inalcançável

        while passo_atual is not None:
            caminho.append(passo_atual)
            if passo_atual == origem:
                break
            passo_atual = predecessores[passo_atual]
            # Segurança contra loops se algo der muito errado com predecessores
            if passo_atual is not None and passo_atual in caminho:
                # print("[Dijkstra Custom DEBUG] Loop detectado na reconstrução do caminho!")
                return None # Caminho inválido
        
        if caminho[-1] == origem: # Verifica se o caminho realmente começa na origem
            return caminho[::-1]  # Retorna o caminho invertido (origem -> destino)
        else:
            return None # Caminho não encontrado ou inválido


    def calcular_proximo_salto(self, origem, destino):
        # Substitui a chamada a nx.shortest_path pela nossa implementação
        caminho = self._dijkstra_customizado(origem, destino)

        if caminho:
            print(f"[Dijkstra Custom DEBUG] Caminho: {caminho}") # Mantendo o print de debug original
            if len(caminho) > 1:
                return caminho[1] # Retorna o próximo salto
            elif len(caminho) == 1 and caminho[0] == origem and origem == destino:
                 # Caso especial: origem é o destino, não há "próximo" salto, mas o caminho é válido.
                 # A lógica original retornaria None aqui. Para manter consistência:
                return None 
        else:
            print(f"[Dijkstra Custom] Sem caminho de {origem} para {destino}") # Mantendo o print de debug original
            return None
        return None # Default return se nenhuma condição acima for atendida

    def _monitorar_vizinhos_target(self):
        snapshot_local = set()

        # Inicializar estado inicial dos vizinhos
        for iface_local, vizinhos_iface in self.interfaces_wan.items():
            for viz in vizinhos_iface:
                self.estado_vizinhos[viz] = 'inativo'

        while True:
            agora = time.time()

            mudanca_detectada_monitor = False # Flag para LSA no monitor

            # Monitorar cada interface WAN separadamente
            for iface_local, vizinhos_iface in self.interfaces_wan.items():
                for vizinho in vizinhos_iface:
                    ultimo_hello = self.vizinhos_ativos.get(vizinho, 0)
                    tempo_sem_hello = agora - ultimo_hello

                    if tempo_sem_hello > 10: # Timeout original de 10s
                        # Vizinho caiu
                        if self.estado_vizinhos.get(vizinho) != 'inativo': # Verifica se já não estava inativo
                            self.estado_vizinhos[vizinho] = 'inativo'
                            if self.grafo_dinamico.has_edge(iface_local, vizinho):
                                self.grafo_dinamico.remove_edge(iface_local, vizinho)
                                print(f"[TIMEOUT] {iface_local} perdeu conexão com {vizinho}")
                                mudanca_detectada_monitor = True
                    else:
                        # Vizinho ativo
                        if self.estado_vizinhos.get(vizinho) != 'ativo': # Verifica se já não estava ativo
                            self.estado_vizinhos[vizinho] = 'ativo'
                            if not self.grafo_dinamico.has_edge(iface_local, vizinho):
                                self.grafo_dinamico.add_edge(iface_local, vizinho, weight=1)
                                print(f"[RECOVERY] {iface_local} recuperou conexão com {vizinho}")
                                mudanca_detectada_monitor = True
            
            if mudanca_detectada_monitor:
                self.enviar_lsa()

            # Snapshot atualizado das arestas para todas as interfaces locais
            # Esta parte do snapshot no original parece redundante com a lógica acima, 
            # mas mantendo para fidelidade.
            novo_snapshot = set()
            for iface_local_snap in self.interfaces_locais: # Usar self.interfaces_locais
                for vizinho_snap in self.grafo_dinamico.neighbors(iface_local_snap):
                    novo_snapshot.add(tuple(sorted((iface_local_snap, vizinho_snap))))

            # Verifica se houve mudança global
            if novo_snapshot != snapshot_local:
                print(f"[LSA] Mudança detectada (snapshot), snapshot atualizado: {novo_snapshot}")
                snapshot_local = novo_snapshot
                self.enviar_lsa() # Envia LSA se o snapshot mudou

            time.sleep(3)

    # === Escuta ===
    def _escutar_interface_target(self, minha_iface, sock):
        print(f"[IF {minha_iface}] Escutando na 127.X.X.X:5000") # O IP real é o bind feito em start()
        if not self.grafo_dinamico.has_node(minha_iface):
            self.grafo_dinamico.add_node(minha_iface)

        while True:
            try:
                data, addr = sock.recvfrom(4096)
                try:
                    pacote = json.loads(data.decode())
                    tipo = pacote.get("tipo", "mensagem")

                    # ───── CLI remoto ────────────────────────────────────────────────────────────
                    if tipo == "cli_comando":
                        comando = pacote.get("comando", "").strip().lower()
                        destino_iface_cli = pacote.get("destino") # Renomeado para evitar conflito
                        # ip_remetente = addr[0] # quem pediu (não usado no original aqui)

                        # 1) RECUPERA GRAFO -------------------------------------------------------
                        if comando == "graph":
                            self.salvar_grafo() # Usa self.grafo_dinamico, self.meu_ip, self.interfaces_locais
                            continue
                        # -------------------------------------------------------------------------

                        # 2) COMANDOS DE PESO ------------------------------------------------------
                        if destino_iface_cli not in self.interfaces_wan:
                            print(f"[CLI] Interface {destino_iface_cli} não pertence ao roteador.")
                            continue

                        if comando == "++++":  # todas as ifaces +1
                            for iface_cmd, vizinhos_cmd in self.interfaces_wan.items():
                                for viz_cmd in vizinhos_cmd:
                                    if self.grafo_dinamico.has_edge(iface_cmd, viz_cmd):
                                        w = self.grafo_dinamico[iface_cmd][viz_cmd].get("weight", 1)
                                        self.grafo_dinamico[iface_cmd][viz_cmd]["weight"] = min(w + 1, 20)
                            self.enviar_lsa()

                        elif comando.startswith(("++", "--")):  # uma iface específica
                            operacao = comando[:2]  # '++' ou '--'
                            try:
                                idx = int(comando[2]) - 1  # 1‑base → 0‑base
                                iface_alvo = list(self.interfaces_wan.keys())[idx]
                            except (ValueError, IndexError):
                                print("[CLI] Índice de interface inválido.")
                                continue

                            for viz_cmd_target in self.interfaces_wan[iface_alvo]: # Renomeado
                                if self.grafo_dinamico.has_edge(iface_alvo, viz_cmd_target):
                                    w = self.grafo_dinamico[iface_alvo][viz_cmd_target].get("weight", 1)
                                    self.grafo_dinamico[iface_alvo][viz_cmd_target]["weight"] = \
                                        min(w + 1, 20) if operacao == "++" else max(w - 1, 1)
                            self.enviar_lsa()
                        # -------------------------------------------------------------------------
                        continue  # fim do cli_comando
                    
                    elif tipo == "traceroute":
                        destino_final = pacote["entrega_final"]
                        # ▶ Quando o roteador é o destino final
                        if destino_final == minha_iface:
                            host_origem = pacote["origem"]
                            reply_port = pacote.get("reply_port", 5000)
                            
                            # ── CASO 1 • host está NA MINHA LAN -------------------------------
                            if host_origem in self.subrede_local:
                                resposta = {
                                    "tipo": "traceroute_reply",
                                    "origem": minha_iface,
                                    "destino": host_origem,
                                    "entrega_final": host_origem,
                                    "numero": pacote["numero"],
                                    "ttl": 10
                                }
                                print(f"[IF {minha_iface}] Enviando traceroute_reply para host local {host_origem}:{reply_port}")
                                sock.sendto(json.dumps(resposta).encode(), (host_origem, reply_port))
                                continue
                                
                            # ── CASO 2 • host em outra sub-rede -------------------------------
                            p0, p1, p2, _ = host_origem.split(".")
                            gateway_dst = f"{p0}.{p1}.{p2}.1"
                            
                            proximo = self.calcular_proximo_salto(minha_iface, gateway_dst)
                            if not proximo:
                                print(f"[IF {minha_iface}] Sem rota p/ {host_origem}")
                                continue
                                
                            resposta = {
                                "tipo": "traceroute_reply",
                                "origem": minha_iface,
                                "destino": proximo,
                                "entrega_final": host_origem,
                                "numero": pacote["numero"],
                                "reply_port": reply_port,
                                "ttl": 10
                            }
                            print(f"[IF {minha_iface}] Enviando traceroute_reply via {proximo} para {host_origem}:{reply_port}")
                            iface_out = self.vizinho_para_iface.get(proximo, proximo)
                            self.sockets[iface_out].sendto(json.dumps(resposta).encode(), (proximo, 5000))
                            continue

                        # ▶ Quando TTL chegar a 0  ➜ devolve “ttl_exceeded” ao host de origem
                        pacote["ttl"] -= 1
                        if pacote["ttl"] <= 0:
                            host_origem = pacote["origem"]            # quem iniciou o traceroute
                            reply_port  = pacote.get("reply_port", 5000)

                            # ── CASO 1 • host está NA MINHA LAN -------------------------------
                            if host_origem in self.subrede_local:
                                resposta = {
                                    "tipo"       : "ttl_exceeded",
                                    "hop"        : minha_iface,
                                    "numero"     : pacote["numero"],
                                    "ttl"        : 10 # TTL da resposta
                                }
                                sock.sendto(json.dumps(resposta).encode(), (host_origem, reply_port))
                                continue
                            # ── CASO 2 • host em outra sub-rede -------------------------------
                            p0, p1, p2, _ = host_origem.split(".")
                            gateway_dst = f"{p0}.{p1}.{p2}.1"

                            proximo = self.calcular_proximo_salto(minha_iface, gateway_dst)
                            if not proximo:                          # sem rota → abandona
                                print(f"[IF {minha_iface}] Sem rota p/ {host_origem}")
                                continue

                            resposta = {
                                "tipo"         : "ttl_exceeded",
                                "hop"          : minha_iface,
                                "numero"       : pacote["numero"],
                                "destino"      : proximo,
                                "entrega_final": host_origem,
                                "reply_port"   : reply_port,
                                "ttl"          : 10 # TTL da resposta
                            }
                            iface_out = self.vizinho_para_iface.get(proximo, proximo)
                            self.sockets[iface_out].sendto(json.dumps(resposta).encode(), (proximo, 5000))
                            continue

                        # Segue encaminhando o traceroute normalmente
                        dados = json.dumps(pacote).encode()

                        partes = destino_final.split(".")
                        gateway_destino = f"{partes[0]}.{partes[1]}.{partes[2]}.1"
                        proximo = self.calcular_proximo_salto(minha_iface, gateway_destino)
                        if proximo:
                            iface_saida = self.vizinho_para_iface.get(proximo, proximo)
                            self.sockets[iface_saida].sendto(dados, (proximo, 5000))
                            continue # Adicionado para garantir que não prossiga para LSA/HELLO/etc.

                    if tipo == "lsa":
                        self.processar_lsa(pacote, minha_iface)
                        continue

                    if tipo == "hello":
                        origem_hello = pacote.get("origem") # Renomeado
                        #print(f"[HELLO] Recebi HELLO de {origem_hello} na interface {minha_iface}")

                        # Atualiza o timestamp imediatamente
                        self.vizinhos_ativos[origem_hello] = time.time()
                        mudanca_hello = False # Flag para LSA no hello

                        # Se estava inativo, reativa e dispara LSA imediatamente
                        if self.estado_vizinhos.get(origem_hello) == 'inativo':
                            self.estado_vizinhos[origem_hello] = 'ativo'
                            if not self.grafo_dinamico.has_edge(minha_iface, origem_hello):
                                self.grafo_dinamico.add_edge(minha_iface, origem_hello, weight=1)
                                print(f"[RECOVERY] Interface {minha_iface} reconectada com {origem_hello}")
                                mudanca_hello = True

                        # Novo vizinho (primeira conexão)
                        elif not self.grafo_dinamico.has_edge(minha_iface, origem_hello):
                            self.grafo_dinamico.add_edge(minha_iface, origem_hello, weight=1)
                            print(f"[NOVO] Novo vizinho conectado: {minha_iface} ↔ {origem_hello}")
                            mudanca_hello = True
                        
                        if mudanca_hello:
                            self.enviar_lsa()

                        # Atualiza a interface de saída sempre
                        self.vizinho_para_iface[origem_hello] = minha_iface
                        continue

                    # Demais tipos de pacotes (mensagem, ping, pong, traceroute_reply, ttl_exceeded)
                    destino = pacote["destino"]
                    entrega_final = pacote.get("entrega_final", destino)

                    if "ttl" in pacote:
                        pacote["ttl"] -= 1
                        if pacote["ttl"] < 0:
                            # Resposta para o HOST origem que o TTL expirou no roteador
                            # O host origem está em pacote["origem"]
                            host_origem_ttl_exp = pacote["origem"]
                            porta_resposta_ttl_exp = 5000 # Porta padrão para respostas diretas ao host
                            if pacote.get("tipo") == "traceroute": # Traceroute usa reply_port
                                porta_resposta_ttl_exp = pacote.get("reply_port", 5000)

                            resposta_ttl_exp = {
                                "tipo": "ttl_exceeded",
                                "hop": minha_iface, # Este roteador é o hop onde expirou
                                "numero": pacote.get("numero"), # Para traceroute
                                "ttl": 10 # TTL da resposta
                            }
                            
                            # Determinar como enviar a resposta TTL exceeded
                            # Se o host origem está na LAN deste roteador:
                            if host_origem_ttl_exp in self.subrede_local:
                                print(f"[IF {minha_iface}] TTL Expirado. Enviando ttl_exceeded para host local {host_origem_ttl_exp}:{porta_resposta_ttl_exp}")
                                sock.sendto(json.dumps(resposta_ttl_exp).encode(), (host_origem_ttl_exp, porta_resposta_ttl_exp))
                            else:
                                # Host origem em outra rede, rotear a resposta ttl_exceeded
                                p0_ttl, p1_ttl, p2_ttl, _ = host_origem_ttl_exp.split(".")
                                gateway_dst_ttl = f"{p0_ttl}.{p1_ttl}.{p2_ttl}.1"
                                proximo_ttl = self.calcular_proximo_salto(minha_iface, gateway_dst_ttl)

                                if proximo_ttl:
                                    resposta_ttl_exp["destino"] = proximo_ttl
                                    resposta_ttl_exp["entrega_final"] = host_origem_ttl_exp
                                    iface_out_ttl = self.vizinho_para_iface.get(proximo_ttl, proximo_ttl)
                                    print(f"[IF {minha_iface}] TTL Expirado. Roteando ttl_exceeded para {host_origem_ttl_exp} via {proximo_ttl}")
                                    self.sockets[iface_out_ttl].sendto(json.dumps(resposta_ttl_exp).encode(), (proximo_ttl, 5000))
                                else:
                                    print(f"[IF {minha_iface}] TTL Expirado. Sem rota para enviar ttl_exceeded para {host_origem_ttl_exp}")
                            continue

                    # ------------------------------------------------------------------
                    # Entrega local: HOST da LAN ou interface do próprio roteador
                    # ------------------------------------------------------------------
                    if entrega_final in self.subrede_local or entrega_final in self.interfaces_locais:
                        print(f"[IF {minha_iface}] Entrega local direta → {entrega_final}")

                        # ▸ 1. PING destinado à interface do roteador -------------------
                        if tipo == "ping" and entrega_final == minha_iface:
                            host_origem_ping = pacote["origem"]

                            # Caso 1: host está na mesma LAN → responde direto
                            if host_origem_ping in self.subrede_local:
                                resposta_ping = {
                                    "tipo"         : "pong",
                                    "origem"       : minha_iface,
                                    "destino"      : host_origem_ping,
                                    "entrega_final": host_origem_ping,
                                    "timestamp"    : pacote["timestamp"],
                                    "ttl"          : 10
                                }
                                sock.sendto(json.dumps(resposta_ping).encode(), (host_origem_ping, 5000))
                                continue

                            # Caso 2: host está em outra rede → calcula rota normalmente
                            p0_ping, p1_ping, p2_ping, _ = host_origem_ping.split(".")
                            gateway_dst_ping = f"{p0_ping}.{p1_ping}.{p2_ping}.1"

                            proximo_ping = self.calcular_proximo_salto(minha_iface, gateway_dst_ping)
                            if not proximo_ping:
                                print(f"[IF {minha_iface}] Sem rota p/ {host_origem_ping} (para pong)")
                                continue

                            resposta_ping = {
                                "tipo"         : "pong",
                                "origem"       : minha_iface,
                                "destino"      : proximo_ping,
                                "entrega_final": host_origem_ping,
                                "timestamp"    : pacote["timestamp"],
                                "ttl"          : 10
                            }
                            iface_out_ping = self.vizinho_para_iface.get(proximo_ping, proximo_ping)
                            self.sockets[iface_out_ping].sendto(json.dumps(resposta_ping).encode(), (proximo_ping, 5000))
                            continue
                        
                        # ▸ 2. TRACEROUTE destinado à interface do roteador (já tratado acima, mas para garantir)
                        # Esta lógica é coberta pela seção de traceroute onde destino_final == minha_iface.
                        # Se chegar aqui, é um pacote genérico para a LAN.

                        # ▸ 3. Qualquer outro tráfego local (hosts da própria LAN ou outras ifaces locais)
                        porta_alvo_local = 5000 # Porta padrão para entrega local
                        if tipo in ("traceroute_reply", "ttl_exceeded", "pong"):
                            porta_alvo_local = pacote.get("reply_port", 5000)
                            print(f"[IF {minha_iface}] Entregando RESPOSTA {tipo} localmente para {entrega_final}:{porta_alvo_local}")
                        else:
                            print(f"[IF {minha_iface}] Entregando REQUISIÇÃO {tipo} localmente para {entrega_final}:{porta_alvo_local}")
                        
                        # Se entrega_final é uma interface local, usa o socket dessa interface
                        if entrega_final in self.sockets:
                            self.sockets[entrega_final].sendto(data, (entrega_final, porta_alvo_local))
                        else: # É um host na LAN
                            sock.sendto(data, (entrega_final, porta_alvo_local))
                        continue

                    # Roteamento para WAN
                    # Se for um HOST remoto (não existe no grafo), calcula o gateway remoto (.1)
                    partes_remoto = entrega_final.split(".")
                    gateway_destino_remoto = f"{partes_remoto[0]}.{partes_remoto[1]}.{partes_remoto[2]}.1"

                    # Usa Dijkstra para achar próximo salto até o gateway da subrede destino
                    proximo_salto_wan = self.calcular_proximo_salto(minha_iface, gateway_destino_remoto)

                    if not proximo_salto_wan:
                        print(f"[IF {minha_iface}] Sem rota para o gateway {gateway_destino_remoto} (destino final {entrega_final})")
                        continue
                    
                    # Se o próximo salto é uma interface local (roteamento interno para outra sub-rede gerenciada)
                    # Esta lógica é complexa e o original não a trata explicitamente de forma robusta para múltiplas LANs.
                    # O original foca em WAN ou LAN local.
                    # Mantendo a lógica de encaminhar para o próximo salto na WAN.

                    iface_saida_wan = self.vizinho_para_iface.get(proximo_salto_wan, proximo_salto_wan)
                    if iface_saida_wan not in self.sockets:
                        print(f"[IF {minha_iface}] ERRO: Interface de saída {iface_saida_wan} para {proximo_salto_wan} não encontrada nos sockets.")
                        continue
                        
                    print(f"[IF {minha_iface}] Encaminhando para {proximo_salto_wan} (destino final {entrega_final}) via iface {iface_saida_wan}")
                    
                    # --- AJUSTE ROTEAMENTO DE RESPOSTA (mantido do original) ---
                    # Para respostas, o campo "destino" do pacote JSON deve ser o próximo salto físico.
                    # Para requisições, o campo "destino" já deve ser o gateway_ip do host que enviou, 
                    # e o roteador usa "entrega_final" para o roteamento real.
                    pacote_enviar = json.loads(data.decode()) # Decodifica para possível modificação
                    pacote_enviar["destino"] = proximo_salto_wan # Garante que o campo destino é o próximo salto físico
                    dados_enviar = json.dumps(pacote_enviar).encode()
                    self.sockets[iface_saida_wan].sendto(dados_enviar, (proximo_salto_wan, 5000))
                    # --- FIM AJUSTE ---

                except json.JSONDecodeError:
                    print(f"[IF {minha_iface}] Erro ao decodificar JSON: {data}")
                except Exception as e:
                    print(f"[IF {minha_iface}] Erro no processamento do pacote: {e}")
                    print(f"[Pacote bruto problemático]: {data}")
                    import traceback
                    traceback.print_exc()

            except ConnectionResetError: # Comum em UDP se o outro lado não está ouvindo
                # print(f"[IF {minha_iface}] ConnectionResetError com {addr}") # Debug opcional
                continue
            except Exception as e_outer:
                print(f"[IF {minha_iface}] Erro geral no loop de escuta: {e_outer}")
                import traceback
                traceback.print_exc()
                time.sleep(1) # Evita tight loop em caso de erro persistente

    def start(self):
        # === Cria sockets (todos bindam em 127.X.X.X:5000, mas o IP é o da interface)
        # interfaces_all = list(set([self.meu_ip] + list(self.interfaces_wan.keys())))
        # self.interfaces_locais já está definido em __init__

        for ip_iface in self.interfaces_locais:
            Roteador.aguardar_ip_disponivel(ip_iface, 5000)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((ip_iface, 5000))
            self.sockets[ip_iface] = sock

        # === Mapeia (vizinho → iface local) - Inicialização, será atualizado por HELLO
        for iface, vizinhos in self.interfaces_wan.items():
            for viz in vizinhos:
                self.vizinho_para_iface[viz] = iface # Supõe inicialmente que o vizinho é alcançável por esta iface

        # === Grafo dinâmico - Nós são as interfaces locais
        self.grafo_dinamico.add_nodes_from(self.interfaces_locais)
        # Conexões internas entre interfaces locais do mesmo roteador (peso 0)
        # O original conecta todas as interfaces locais entre si com peso 0.
        # Isso é para o agrupamento no salvamento do grafo.
        ifaces_list = list(self.interfaces_locais)
        for i, a in enumerate(ifaces_list):
            for b in ifaces_list[i+1:]:
                if not self.grafo_dinamico.has_edge(a,b):
                    self.grafo_dinamico.add_edge(a, b, weight=0)

        # === Protocolos
        self.iniciar_hello_protocol()
        self.iniciar_lsa_protocol()

        # === Escuta em cada interface local
        for iface_listen in self.interfaces_locais:
            t = threading.Thread(
                target=self._escutar_interface_target,
                args=(iface_listen, self.sockets[iface_listen]),
                daemon=True
            )
            t.start()

        # === Monitoramento de vizinhos WAN
        threading.Thread(
            target=self._monitorar_vizinhos_target,
            daemon=True
        ).start()
        
        # === Salva imagem do grafo após um tempo (original era 60s, mas salvar_grafo tem 5s sleep)
        # O original chama salvar_grafo com args=(grafo_dinamico, meu_ip, interfaces_locais)
        # O método salvar_grafo agora usa self.grafo_dinamico, self.meu_ip, self.interfaces_locais
        threading.Thread(
            target=self.salvar_grafo, # O método já tem acesso a self
            daemon=True
        ).start()  

        print(f"\n[Roteador {self.meu_ip}] Interfaces ativas: {self.interfaces_locais}")
        print(f"[LAN]: {self.subrede_local}")
        print(f"[WANs]: {self.interfaces_wan}\n")

# === Main ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--meu_ip", type=str, required=True, help="IP principal do roteador, usado para identificar o roteador e como uma de suas interfaces locais.")
    parser.add_argument("--lan", nargs='+', required=True, help="Lista de IPs na sub-rede local (LAN) diretamente conectada a este roteador.")
    parser.add_argument("--wan", type=str, required=True, help='JSON string descrevendo as interfaces WAN. Ex: \'{"127.0.0.2": ["127.0.0.3"], "127.0.0.4": ["127.0.0.5"]}\', onde chaves são IPs de interfaces WAN locais e valores são listas de IPs de vizinhos diretos nessas WANs.')

    args = parser.parse_args()

    roteador = Roteador(meu_ip=args.meu_ip, 
                        subrede_local=args.lan, 
                        interfaces_wan_json=args.wan)
    roteador.start()

    try:
        while True:
            time.sleep(1) # Mantém o programa rodando para as threads daemon
    except KeyboardInterrupt:
        print("\n[Roteador] Desligando...")

