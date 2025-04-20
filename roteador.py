import socket
import threading
import json
import networkx as nx
import time 
import matplotlib.pyplot as plt
import argparse

# Para salvar graficamente o grafo
def salvar_grafo(grafo_dinamico, meu_ip):
    time.sleep(60)
    plt.figure(figsize=(6, 5))
    pos = nx.spring_layout(grafo_dinamico, seed=42)
    nx.draw(grafo_dinamico, pos, with_labels=True, node_color='skyblue', node_size=1200, font_size=10, font_weight='bold', edge_color='gray')
    plt.title(f"Topologia vista pelo roteador {meu_ip}")
    plt.savefig(f"grafo_{meu_ip.replace('.', '_')}.png")
    plt.close()
    print(f"[LOG] Grafo salvo como grafo_{meu_ip.replace('.', '_')}.png")

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

    todas_ifaces = list(interfaces_wan.keys())

    for iface_local, vizinhos_externos in interfaces_wan.items():
        vizinhos = set(vizinhos_externos)
        for outra in todas_ifaces:
            if outra != iface_local:
                vizinhos.add(outra)

        mensagem = {
            "tipo": "lsa",
            "origem": iface_local,
            "vizinhos": list(vizinhos),
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
                    pass

def iniciar_lsa_protocol(interfaces_wan, grafo_dinamico):
    def ciclo():
        while True:
            enviar_lsa(interfaces_wan, grafo_dinamico)
            time.sleep(10)
    threading.Thread(target=ciclo, daemon=True).start()

# === Processamento de LSA recebido ===
def processar_lsa(pacote, porta_origem, grafo_dinamico):
    origem = pacote["origem"]
    vizinhos = pacote["vizinhos"]
    seq = pacote["seq"]

    if (origem, seq) in lsas_vistos:
        return

    lsas_vistos.add((origem, seq))

    for vizinho in vizinhos:
        if not grafo_dinamico.has_edge(origem, vizinho):
            grafo_dinamico.add_edge(origem, vizinho, weight=1)
            print(f"[LSA] Roteador {origem} ↔ {vizinho} adicionado")

    for vizinhos_iface in interfaces_wan.values():
        for vizinho in vizinhos_iface:
            try:
                nova_mensagem = json.dumps(pacote).encode()
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(nova_mensagem, (vizinho, 5000))
                sock.close()
            except:
                continue

# === Dijkstra ===
def calcular_proximo_salto(grafo, origem, destino):
    try:
        print(f"[Dijkstra DEBUG] {origem} → {destino}")
        caminho = nx.shortest_path(grafo, source=origem, target=destino, weight="weight")
        print(f"[Dijkstra DEBUG] Caminho: {caminho}")
        if len(caminho) > 1:
            return caminho[1]
    except nx.NetworkXNoPath:
        print(f"[Dijkstra] Sem caminho de {origem} para {destino}")
        return None
    return None

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

                if tipo == "lsa":
                    processar_lsa(pacote, minha_iface, grafo_dinamico)
                    continue

                if tipo == "hello":
                    origem = pacote.get("origem")
                    if not grafo_dinamico.has_edge(minha_iface, origem):
                        grafo_dinamico.add_edge(minha_iface, origem, weight=1)
                        print(f"[HELLO] Vizinho descoberto: {minha_iface} ↔ {origem}")
                     # 🔧 ADICIONE ESTA LINHA AQUI:
                    vizinho_para_iface[origem] = minha_iface
                    continue
                   

                destino = pacote["destino"]
                entrega_final = pacote.get("entrega_final", destino)

                if "ttl" in pacote:
                    pacote["ttl"] -= 1
                    if pacote["ttl"] < 0:
                        continue
                    data = json.dumps(pacote).encode()

                if entrega_final in subrede_local:
                    print(f"[IF {minha_iface}] Entrega local → {entrega_final}")
                    sock.sendto(data, (entrega_final, 5000))
                    continue

                # Calcula roteador da subrede do destino
                partes = entrega_final.split(".")
                gateway_destino = f"{partes[0]}.{partes[1]}.{partes[2]}.1"
                proximo = calcular_proximo_salto(grafo_dinamico, minha_iface, gateway_destino)
                if not proximo:
                    print(f"[IF {minha_iface}] Sem rota para {destino}")
                    continue

                if proximo == minha_iface:
                    sock.sendto(data, (proximo, 5000))

                
                # Verifica se o próximo salto é outra interface local
                if proximo in interfaces_locais:
                    print(f"[IF {minha_iface}] Encaminhamento interno → {proximo}")
                    sockets[proximo].sendto(data, (proximo, 5000))
                    continue
                # 👇 Caso contrário, busca a interface correta para enviar externamente 
                elif proximo in vizinho_para_iface:
                    iface_saida = vizinho_para_iface[proximo]
                    sockets[iface_saida].sendto(data, (proximo, 5000))
                    print(f"[IF {minha_iface}] Encaminhando para {proximo} via {iface_saida}")
                else:
                    print(f"[IF {minha_iface}] Sem interface para {proximo}")

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
    
    '''
    # === Salva imagem do grafo após 60 segundos
    threading.Thread(
        target=salvar_grafo,
        args=(grafo_dinamico, meu_ip),
        daemon=True
    ).start()  

    '''

    print(f"\n[Roteador {meu_ip}] Interfaces ativas: {interfaces}")
    print(f"[LAN]: {subrede_local}")
    print(f"[WANs]: {interfaces_wan}\n")

    while True:
        pass
