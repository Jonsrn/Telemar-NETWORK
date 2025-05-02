import socket
import threading
import json
import networkx as nx
import time 
import matplotlib.pyplot as plt
import argparse

import math

# Para salvar graficamente o grafo
def salvar_grafo(grafo_dinamico, meu_ip, interfaces_locais):

    time.sleep(1)

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

    clusters = agrupar_interfaces(grafo_dinamico)

    # Posiciona roteadores em um anel externo
    N = len(clusters)
    R_outer = 10
    pos = {}
    centers = {}
    Gdraw = grafo_dinamico.copy()

    for idx, cluster in enumerate(sorted(clusters, key=lambda x: meu_ip in x, reverse=True)):
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

    plt.title(f"Topologia – roteador {meu_ip}")
    plt.axis("off")
    plt.tight_layout()

    nome = f"grafo_{meu_ip.replace('.', '_')}.png"
    plt.savefig(nome, dpi=150)
    plt.close()
    print(f"[CLI] Topologia salva como {nome}")




# === Protocolo HELLO ===
def iniciar_hello_protocol(meu_ip, interfaces_wan, grafo_dinamico):
    def enviar_hellos():
        while True:
            for minha_iface, vizinhos in interfaces_wan.items():
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
                        pass
            time.sleep(3)

    threading.Thread(target=enviar_hellos, daemon=True).start()

# === Protocolo LSA ===
lsas_vistos = set()
seq_lsa = 0

def enviar_lsa(interfaces_wan, grafo_dinamico):
    global seq_lsa

    for iface_local in interfaces_wan.keys():
        vizinhos_com_peso = {}

        for vizinho in grafo_dinamico.neighbors(iface_local):
            peso = grafo_dinamico[iface_local][vizinho].get("weight", 1)
            vizinhos_com_peso[vizinho] = peso

        mensagem = {
            "tipo": "lsa",
            "origem": iface_local,
            "vizinhos": vizinhos_com_peso,
            "seq": seq_lsa
        }

        seq_lsa += 1
        lsas_vistos.add((iface_local, mensagem["seq"]))

        for lista in interfaces_wan.values():
            for viz in lista:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.sendto(json.dumps(mensagem).encode(), (viz, 5000))
                    s.close()
                except:
                    continue



def iniciar_lsa_protocol(interfaces_wan, grafo_dinamico):
    def ciclo():
        while True:
            enviar_lsa(interfaces_wan, grafo_dinamico)
            time.sleep(10)
    threading.Thread(target=ciclo, daemon=True).start()


# === Cache da topologia local
topologia_local = {}

# === Processamento de LSA recebido ===
def processar_lsa(pacote, porta_origem, grafo_dinamico):
    origem = pacote["origem"]
    vizinhos = pacote["vizinhos"]  # agora é um dicionário: {vizinho: peso}
    seq = pacote["seq"]

    if (origem, seq) in lsas_vistos:
        return

    lsas_vistos.add((origem, seq))

    # Se não houve mudança na topologia (estrutura e pesos), ignora
    vizinhos_recebidos = set(vizinhos.keys())
    vizinhos_atuais = topologia_local.get(origem, {})

    if vizinhos_atuais == vizinhos:
        return

    # Remove arestas antigas que não existem mais
    for vizinho_antigo in set(vizinhos_atuais.keys()):
        if vizinho_antigo not in vizinhos and grafo_dinamico.has_edge(origem, vizinho_antigo):
            grafo_dinamico.remove_edge(origem, vizinho_antigo)
            print(f"[LSA] Roteador {origem} ↔ {vizinho_antigo} REMOVIDO")

    # Adiciona ou atualiza as arestas recebidas
    for vizinho_novo, peso in vizinhos.items():
        if not grafo_dinamico.has_edge(origem, vizinho_novo):
            grafo_dinamico.add_edge(origem, vizinho_novo, weight=peso)
            print(f"[LSA] Roteador {origem} ↔ {vizinho_novo} ADICIONADO (peso {peso})")
        else:
            peso_atual = grafo_dinamico[origem][vizinho_novo].get("weight", 1)
            if peso != peso_atual:
                grafo_dinamico[origem][vizinho_novo]["weight"] = peso
                print(f"[LSA] Roteador {origem} ↔ {vizinho_novo} ATUALIZADO (peso {peso})")

    # Atualiza cache local
    topologia_local[origem] = vizinhos

    # Propaga o LSA para outros vizinhos
    for lista in interfaces_wan.values():
        for viz in lista:
            try:
                nova_mensagem = json.dumps(pacote).encode()
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(nova_mensagem, (viz, 5000))
                sock.close()
            except:
                continue



# === Dijkstra ===
def calcular_proximo_salto(grafo, origem, destino):
    try:
        caminho = nx.shortest_path(grafo, source=origem, target=destino, weight="weight")
        print(f"[Dijkstra DEBUG] Caminho: {caminho}")
        if len(caminho) > 1:
            return caminho[1]
    except nx.NetworkXNoPath:
        print(f"[Dijkstra] Sem caminho de {origem} para {destino}")
        return None
    return None

vizinhos_ativos = {}
estado_vizinhos = {}  # chave: vizinho, valor: 'ativo' ou 'inativo'

def monitorar_vizinhos(grafo_dinamico, interfaces_wan, interfaces_locais):
    snapshot_local = set()

    # Inicializar estado inicial dos vizinhos
    for iface_local, vizinhos_iface in interfaces_wan.items():
        for viz in vizinhos_iface:
            estado_vizinhos[viz] = 'inativo'

    while True:
        agora = time.time()

        # Monitorar cada interface WAN separadamente
        for iface_local, vizinhos_iface in interfaces_wan.items():
            for vizinho in vizinhos_iface:
                ultimo_hello = vizinhos_ativos.get(vizinho, 0)
                tempo_sem_hello = agora - ultimo_hello

                if tempo_sem_hello > 10:
                    # Vizinho caiu
                    if estado_vizinhos[vizinho] != 'inativo':
                        estado_vizinhos[vizinho] = 'inativo'
                        if grafo_dinamico.has_edge(iface_local, vizinho):
                            grafo_dinamico.remove_edge(iface_local, vizinho)
                            print(f"[TIMEOUT] {iface_local} perdeu conexão com {vizinho}")
                            enviar_lsa(interfaces_wan, grafo_dinamico)
                else:
                    # Vizinho ativo
                    if estado_vizinhos[vizinho] != 'ativo':
                        estado_vizinhos[vizinho] = 'ativo'
                        if not grafo_dinamico.has_edge(iface_local, vizinho):
                            grafo_dinamico.add_edge(iface_local, vizinho, weight=1)
                            print(f"[RECOVERY] {iface_local} recuperou conexão com {vizinho}")
                            enviar_lsa(interfaces_wan, grafo_dinamico)

        # Snapshot atualizado das arestas para todas as interfaces locais
        novo_snapshot = set()
        for iface_local in interfaces_locais:
            for vizinho in grafo_dinamico.neighbors(iface_local):
                novo_snapshot.add(tuple(sorted((iface_local, vizinho))))

        # Verifica se houve mudança global
        if novo_snapshot != snapshot_local:
            print(f"[LSA] Mudança detectada, snapshot atualizado: {novo_snapshot}")
            snapshot_local = novo_snapshot
            enviar_lsa(interfaces_wan, grafo_dinamico)

        time.sleep(3)



# === Escuta ===
def escutar_interface(minha_iface, sock, subrede_local, grafo_dinamico, interfaces_wan):
    print(f"[IF {minha_iface}] Escutando na 127.X.X.X:5000")
    if not grafo_dinamico.has_node(minha_iface):
        grafo_dinamico.add_node(minha_iface)

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            try:
                pacote = json.loads(data.decode())
                tipo = pacote.get("tipo", "mensagem")

                

                # ───── CLI remoto ────────────────────────────────────────────────────────────
                if tipo == "cli_comando":
                    comando       = pacote.get("comando", "").strip().lower()
                    destino_iface = pacote.get("destino")          # pode vir None em “graph”
                    ip_remetente  = addr[0]                        # quem pediu

                    # 1) RECUPERA GRAFO -------------------------------------------------------
                    if comando == "graph":
                        salvar_grafo(grafo_dinamico, meu_ip, interfaces_locais)
                        continue

                    # -------------------------------------------------------------------------

                    # 2) COMANDOS DE PESO ------------------------------------------------------
                    if destino_iface not in interfaces_wan:
                        print(f"[CLI] Interface {destino_iface} não pertence ao roteador.")
                        continue

                    if comando == "++++":                        # todas as ifaces +1
                        for iface, vizinhos in interfaces_wan.items():
                            for viz in vizinhos:
                                if grafo_dinamico.has_edge(iface, viz):
                                    w = grafo_dinamico[iface][viz].get("weight", 1)
                                    grafo_dinamico[iface][viz]["weight"] = min(w+1, 20)
                        enviar_lsa(interfaces_wan, grafo_dinamico)

                    elif comando.startswith(("++", "--")):       # uma iface específica
                        operacao = comando[:2]                   # '++' ou '--'
                        try:
                            idx = int(comando[2]) - 1            # 1‑base → 0‑base
                            iface_alvo = list(interfaces_wan)[idx]
                        except (ValueError, IndexError):
                            print("[CLI] Índice de interface inválido.")
                            continue

                        for viz in interfaces_wan[iface_alvo]:
                            if grafo_dinamico.has_edge(iface_alvo, viz):
                                w = grafo_dinamico[iface_alvo][viz].get("weight", 1)
                                grafo_dinamico[iface_alvo][viz]["weight"] = \
                                    min(w+1, 20) if operacao == "++" else max(w-1, 1)
                        enviar_lsa(interfaces_wan, grafo_dinamico)
                    # -------------------------------------------------------------------------
                    continue  # fim do cli_comando


                elif tipo == "traceroute":
                    destino_final = pacote["entrega_final"]
                    # ▶ Quando o roteador é o destino final
                    if destino_final == minha_iface:
                        resposta = {
                            "tipo": "traceroute_reply",
                            "origem": minha_iface,
                            "numero": pacote["numero"]
                        }
                        porta_dest = pacote.get("reply_port", 5000)   # idem
                        sock.sendto(json.dumps(resposta).encode(),
                                    (pacote["origem"], porta_dest))
                        continue

                    # ▶ Quando TTL chegar a 0  (resposta ttl_exceeded)
                    pacote["ttl"] -= 1
                    if pacote["ttl"] <= 0:
                        resposta = {
                            "tipo": "ttl_exceeded",
                            "hop" : minha_iface,
                            "numero": pacote["numero"]
                        }
                        porta_dest = pacote.get("reply_port", 5000)   # ➌ usa porta do host
                        sock.sendto(json.dumps(resposta).encode(),
                                    (pacote["origem"], porta_dest))
                        continue

                    # Segue encaminhando o traceroute normalmente
                    dados = json.dumps(pacote).encode()

                    partes = destino_final.split(".")
                    gateway_destino = f"{partes[0]}.{partes[1]}.{partes[2]}.1"
                    proximo = calcular_proximo_salto(grafo_dinamico, minha_iface, gateway_destino)
                    if proximo:
                        iface_saida = vizinho_para_iface.get(proximo, proximo)
                        sockets[iface_saida].sendto(dados, (proximo, 5000))



                if tipo == "lsa":
                    processar_lsa(pacote, minha_iface, grafo_dinamico)
                    continue

                if tipo == "hello":
                    origem = pacote.get("origem")

                    #print(f"[HELLO] Recebi HELLO de {origem} na interface {minha_iface}")

                    # Atualiza o timestamp imediatamente
                    vizinhos_ativos[origem] = time.time()

                    # Se estava inativo, reativa e dispara LSA imediatamente
                    if estado_vizinhos.get(origem) == 'inativo':
                        estado_vizinhos[origem] = 'ativo'
                        if not grafo_dinamico.has_edge(minha_iface, origem):
                            grafo_dinamico.add_edge(minha_iface, origem, weight=1)
                            print(f"[RECOVERY] Interface {minha_iface} reconectada com {origem}")
                            enviar_lsa(interfaces_wan, grafo_dinamico)

                    # Novo vizinho (primeira conexão)
                    elif not grafo_dinamico.has_edge(minha_iface, origem):
                        grafo_dinamico.add_edge(minha_iface, origem, weight=1)
                        print(f"[NOVO] Novo vizinho conectado: {minha_iface} ↔ {origem}")
                        enviar_lsa(interfaces_wan, grafo_dinamico)

                    # Atualiza a interface de saída sempre
                    vizinho_para_iface[origem] = minha_iface
                    continue


                   

                destino = pacote["destino"]
                entrega_final = pacote.get("entrega_final", destino)

                if "ttl" in pacote:
                    pacote["ttl"] -= 1
                    if pacote["ttl"] < 0:
                        # Aqui falta disparar resposta pro HOST origem
                        resposta = {
                            "tipo": "ttl_exceeded",
                            "origem": minha_iface,
                            "destino": pacote["origem"],
                            "hop": minha_iface  # quem respondeu o salto
                        }
                        sock.sendto(json.dumps(resposta).encode(), (pacote["origem"], 5000))
                        continue

                # Entrega local (para hosts ou para o próprio roteador)
                # Entrega local (HOST LAN local ou interfaces do roteador local)
                if entrega_final in subrede_local or entrega_final in interfaces_locais:
                    print(f"[IF {minha_iface}] Entrega local direta → {entrega_final}")

                    # Responde pings enviados ao próprio roteador
                    if tipo == "ping" and entrega_final == minha_iface:
                        resposta = {
                            "tipo": "pong",
                            "origem": minha_iface,
                            "destino": pacote["origem"],
                            "timestamp": pacote["timestamp"],
                            "ttl": pacote.get("ttl", "?")
                        }
                        sock.sendto(json.dumps(resposta).encode(), (pacote["origem"], 5000))
                        continue

                    # Caso seja pra host na LAN local
                    sock.sendto(data, (entrega_final, 5000))
                    continue

                # WAN direta (roteadores diretamente conectados na WAN)
                if entrega_final in vizinho_para_iface:
                    iface_saida = vizinho_para_iface[entrega_final]
                    print(f"[IF {minha_iface}] Encaminhando diretamente ao vizinho {entrega_final} via {iface_saida}")
                    sockets[iface_saida].sendto(data, (entrega_final, 5000))
                    continue

                # Se for um HOST remoto (não existe no grafo), calcula o gateway remoto (.1)
                partes = entrega_final.split(".")
                gateway_destino = f"{partes[0]}.{partes[1]}.{partes[2]}.1"

                # Usa Dijkstra para achar próximo salto até o gateway da subrede destino
                proximo = calcular_proximo_salto(grafo_dinamico, minha_iface, gateway_destino)

                if not proximo:
                    print(f"[IF {minha_iface}] Sem rota para o gateway {gateway_destino}")
                    continue

                # Se o próximo salto é interno (outra iface local)
                if proximo in interfaces_locais:
                    print(f"[IF {minha_iface}] Encaminhamento interno → {proximo}")
                    sockets[proximo].sendto(data, (proximo, 5000))

                # Caso contrário, busca a interface correta para enviar externamente 
                elif proximo in vizinho_para_iface:
                    iface_saida = vizinho_para_iface[proximo]
                    print(f"[IF {minha_iface}] Encaminhando para {proximo} via {iface_saida}")
                    sockets[iface_saida].sendto(data, (proximo, 5000))

                else:
                    print(f"[IF {minha_iface}] Sem interface conhecida para alcançar {proximo}")



            except Exception as e:
                print(f"[IF {minha_iface}] Erro: {e}")
                print(f"[Pacote bruto]: {data}")

        except ConnectionResetError:
            continue

# === Main ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--meu_ip", type=str, required=True)
    parser.add_argument("--lan", nargs='+', required=True)
    parser.add_argument("--wan", type=str, required=True)

    args = parser.parse_args()

    meu_ip = args.meu_ip
    subrede_local = args.lan
    interfaces_wan = json.loads(args.wan)

    # === Cria sockets (todos bindam em 127.X.X.X:5000)
    sockets = {}
    interfaces = list(set([meu_ip] + list(interfaces_wan.keys())))

    interfaces_locais = set([meu_ip] + list(interfaces_wan.keys()))

    for ip in interfaces:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((ip, 5000))
        sockets[ip] = sock

    # === Mapeia (vizinho → iface local)
    vizinho_para_iface = {}
    for iface, vizinhos in interfaces_wan.items():
        for viz in vizinhos:
            vizinho_para_iface[viz] = iface

    # === Grafo dinâmico
    grafo_dinamico = nx.Graph()
    grafo_dinamico.add_nodes_from(interfaces)
    for i, a in enumerate(interfaces):
        for b in interfaces[i+1:]:
            grafo_dinamico.add_edge(a, b, weight=0)

    # === Protocolos
    iniciar_hello_protocol(meu_ip, interfaces_wan, grafo_dinamico)
    iniciar_lsa_protocol(interfaces_wan, grafo_dinamico)

    # === Escuta
    for iface in interfaces:
        t = threading.Thread(
            target=escutar_interface,
            args=(iface, sockets[iface], subrede_local, grafo_dinamico, interfaces_wan),
            daemon=True
        )
        t.start()

    threading.Thread(
    target=monitorar_vizinhos,
    args=(grafo_dinamico, interfaces_wan, interfaces_locais),
    daemon=True
    ).start()
    
    
    '''
    # === Salva imagem do grafo após 60 segundos
   threading.Thread(
        target=salvar_grafo,
        args=(grafo_dinamico, meu_ip, interfaces_locais),
        daemon=True
    ).start()  

    '''

    print(f"\n[Roteador {meu_ip}] Interfaces ativas: {interfaces}")
    print(f"[LAN]: {subrede_local}")
    print(f"[WANs]: {interfaces_wan}\n")

    while True:
        pass
