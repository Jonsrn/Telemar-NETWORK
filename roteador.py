import socket
import threading
import json
import networkx as nx
import time 
import matplotlib.pyplot as plt
import argparse


#Temporário, apenas pra imprimir o grafo da rede. 
def salvar_grafo(grafo_dinamico, porta_lan):
    time.sleep(60)  # espera a rede se estabilizar

    plt.figure(figsize=(6, 5))
    pos = nx.spring_layout(grafo_dinamico, seed=42)  # disposição dos nós
    nx.draw(grafo_dinamico, pos, with_labels=True, node_color='skyblue', node_size=1200, font_size=10, font_weight='bold', edge_color='gray')
    plt.title(f"Topologia vista pelo roteador {porta_lan}")
    plt.savefig(f"grafo_{porta_lan}.png")
    plt.close()
    print(f"[LOG] Grafo salvo como grafo_{porta_lan}.png")

def iniciar_lsa_protocol(interfaces_wan, grafo_dinamico):
    def ciclo_periodico():
        while True:
            enviar_lsa(interfaces_wan, grafo_dinamico)
            time.sleep(10)
    threading.Thread(target=ciclo_periodico, daemon=True).start()


def iniciar_hello_protocol(porta_lan, interfaces_wan, grafo_dinamico):
    """
    Inicia uma thread que periodicamente envia mensagens HELLO
    e escuta por respostas para construir dinamicamente o grafo da topologia.
    """
    def enviar_hellos():
        while True:
            for minha_porta, vizinhos in interfaces_wan.items():
                for vizinho in vizinhos:
                    mensagem = {
                        "tipo": "hello",
                        "origem": minha_porta
                    }
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.sendto(json.dumps(mensagem).encode(), ("127.0.0.1", vizinho))
                        sock.close()
                    except Exception as e:
                        pass  # Falha ao enviar hello (vizinho pode estar off)
            time.sleep(3)

    # Threads paralelas para envio e escuta
    threading.Thread(target=enviar_hellos, daemon=True).start()

lsas_vistos = set()
seq_lsa = 0  # incrementado a cada novo envio

def enviar_lsa(interfaces_wan, grafo_dinamico):
    """
    Para cada interface WAN (minha porta local) anuncia:
    - todos os vizinhos externos (cabos)
    - TODAS as minhas demais interfaces locais  ➜  garante aresta interna
    """
    global seq_lsa

    todas_as_portas_locais = list(interfaces_wan.keys())      # só WANs
    for iface_local, vizinhos_externos in interfaces_wan.items():

        # ─── acrescenta as demais portas do MESMO roteador ───────────
        vizinhos = set(vizinhos_externos)              # externos
        for outra in todas_as_portas_locais:
            if outra != iface_local:
                vizinhos.add(outra)                    # interno

        mensagem = {
            "tipo": "lsa",
            "origem": iface_local,
            "vizinhos": list(vizinhos),
            "seq": seq_lsa
        }
        seq_lsa += 1
        lsas_vistos.add((iface_local, mensagem["seq"]))

        # envia o LSA a todos os vizinhos WAN
        for lista in interfaces_wan.values():
            for viz in lista:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.sendto(json.dumps(mensagem).encode(), ("127.0.0.1", viz))
                    s.close()
                except:
                    pass



#Cuida de Processar os LSAs recebidos dos vizinhos
def processar_lsa(pacote, porta_origem, grafo_dinamico):
    origem = pacote["origem"]
    vizinhos = pacote["vizinhos"]
    seq = pacote["seq"]

    if (origem, seq) in lsas_vistos:
        return

    lsas_vistos.add((origem, seq))

    # atualiza o grafo com arestas reais recebidas
    for vizinho in vizinhos:
        if not grafo_dinamico.has_edge(origem, vizinho):
            grafo_dinamico.add_edge(origem, vizinho, weight=1)
            print(f"[LSA] Roteador {origem} ↔ {vizinho} adicionado")

    # repassa LSA para todos os meus vizinhos
    for vizinhos_iface in interfaces_wan.values():
        for vizinho in vizinhos_iface:
            try:
                nova_mensagem = json.dumps(pacote).encode()
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(nova_mensagem, ("127.0.0.1", vizinho))
                sock.close()
            except:
                continue

  


# === Carrega a topologia global da rede === Essa função vai sumir
def carregar_topologia(nome_arquivo):
    with open(nome_arquivo, "r") as f:
        arestas = json.load(f)

    print(f"\n[DEBUG] Topologia carregada do arquivo '{nome_arquivo}':")
    for a in arestas:
        print(" →", a)

    grafo = nx.Graph()
    grafo.add_weighted_edges_from(arestas)
    return grafo

# === Calcula o próximo salto via Dijkstra ===
def calcular_proximo_salto(grafo, origem, destino):
    try:
        print(f"[Dijkstra DEBUG] Buscando caminho de {origem} → {destino}")
        caminho = nx.shortest_path(grafo, source=origem, target=destino, weight="weight")
        print(f"[Dijkstra DEBUG] Caminho encontrado: {caminho}")

        if len(caminho) > 1:
            return caminho[1]
    except nx.NetworkXNoPath:
        print(f"[Dijkstra DEBUG] Sem caminho entre {origem} e {destino}")
        return None
    return None

# === Escuta em uma interface (porta específica) ===
def escutar_interface(porta, sock, subrede_local, grafo_dinamico, interfaces_wan, porta_lan):
    print(f"[INTERFACE {porta}] Escutando...")
    if not grafo_dinamico.has_node(porta):
        grafo_dinamico.add_node(porta)

    while True:
        data, addr = sock.recvfrom(4096)
        try:
            # 1) Parse básico
            pacote = json.loads(data.decode())
            tipo = pacote.get("tipo", "mensagem") 

            if tipo == "lsa":
                processar_lsa(pacote, porta, grafo_dinamico)
                continue

            # Trata mensagens HELLO diretamente no roteador (antes de acessar outros campos)
            if tipo == "hello":
                origem = int(pacote.get("origem"))
                if not grafo_dinamico.has_edge(porta, origem):
                    grafo_dinamico.add_edge(porta, origem, weight=1)
                    print(f"[HELLO] Vizinho descoberto: {porta} ↔ {origem}")
                continue

            destino_real = int(pacote.get("destino"))
            entrega_final = int(pacote.get("entrega_final", destino_real))

            # 2) TTL: decrementa e verifica expiração
            if "ttl" in pacote:
                pacote["ttl"] -= 1
                ttl_atual = pacote["ttl"]
                print(f"[INTERFACE {porta}] TTL atualizado: {ttl_atual}")
                # Re-serializa o pacote com o TTL novo
                data = json.dumps(pacote).encode()

                # Se expirou, descarta mensagens; (no futuro poderemos responder ping/traceroute)
                if ttl_atual < 0:
                    print(f"[INTERFACE {porta}] TTL expirado para pacote {tipo}; descartando.")
                    continue

            # 3) Entrega direta na LAN
            if entrega_final in subrede_local:
                print(f"[INTERFACE {porta}] Entregando localmente → {entrega_final}")
                sock.sendto(data, ("127.0.0.1", entrega_final))
                continue
           
            '''
            # 4) Pacote vindo da LAN → repassa pela primeira WAN
            if porta == porta_lan:
                if not interfaces_wan:
                    print(f"[INTERFACE {porta}] Nenhuma interface WAN disponível.")
                    continue
                iface_local, vizinhos = next(iter(interfaces_wan.items()))
                proximo = vizinhos[0]
                print(f"[INTERFACE {porta}] Repassando da LAN → iface {iface_local} → vizinho {proximo}")
                sockets[iface_local].sendto(data, ("127.0.0.1", proximo))
                continue
            '''    

            # 5) Pacote vindo de uma WAN → calcula Dijkstra
            proximo = calcular_proximo_salto(grafo_dinamico, porta, destino_real)
            if not proximo:
                print(f"[INTERFACE {porta}] Sem rota para {destino_real}. Descartando.")
                continue

            # 6) Internal forwarding (entre minhas próprias interfaces)
            if proximo in sockets:
                print(f"[INTERFACE {porta}] Internal forwarding → {proximo}")
                sockets[proximo].sendto(data, ("127.0.0.1", proximo))
                continue

            # 7) External forwarding (busca interface certa)
            interface_envio = vizinho_para_iface.get(proximo)

            if interface_envio:
                print(f"[INTERFACE {porta}] Encaminhando externamente para {destino_real} via iface {interface_envio} → {proximo}")
                sockets[interface_envio].sendto(data, ("127.0.0.1", proximo))
            else:
                print(f"[INTERFACE {porta}] Sem interface para alcançar o próximo-salto {proximo}.")

        except Exception as e:
            print(f"[INTERFACE {porta}] Erro ao processar pacote: {e}")
            print(f"[INTERFACE {porta}] Pacote bruto: {data}")
            try:
                pacote_debug = json.loads(data.decode())
                print(f"[INTERFACE {porta}] JSON decodificado: {pacote_debug}")
            except:
                print(f"[INTERFACE {porta}] Falha ao decodificar JSON")




# === Ponto de entrada principal ===
if __name__ == "__main__":
    print("Inicialização do Roteador com múltiplas interfaces\n")

    # === Carrega config.json ===
    parser = argparse.ArgumentParser()
    parser.add_argument("--lan", type=int, required=True)
    parser.add_argument("--inicio", type=int, required=True)
    parser.add_argument("--fim", type=int, required=True)
    parser.add_argument("--wan", type=str, required=True)  # JSON string

    args = parser.parse_args()

    porta_lan = args.lan
    subrede_local = range(args.inicio, args.fim + 1)
    interfaces_wan = json.loads(args.wan)
    interfaces_wan = {int(k): v for k, v in interfaces_wan.items()}

    # === Cria sockets para todas as interfaces ===
    sockets = {}
    interfaces = [porta_lan] + list(interfaces_wan.keys()) 

    # === Constrói mapa invertido "vizinho WAN → interface local" ===
    vizinho_para_iface = {}
    for iface_local, vizinhos in interfaces_wan.items():
        for vizinho in vizinhos:
            vizinho_para_iface[vizinho] = iface_local


    for porta in interfaces:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("127.0.0.1", porta))
        sockets[porta] = sock

    # === Grafo dinâmico compartilhado (vai sendo construído com HELLO)
    grafo_dinamico = nx.Graph()
    grafo_dinamico.add_nodes_from(interfaces)       # já adiciona todos os nós locais

    for i, a in enumerate(interfaces):
        for b in interfaces[i+1:]:
            grafo_dinamico.add_edge(a, b, weight=0)

    # === Inicia protocolo HELLO
    threading.Thread(
        target=iniciar_hello_protocol,
        args=(porta_lan, interfaces_wan, grafo_dinamico),
        daemon=True
    ).start()

    # ✅ Inicia envio periódico de LSAs (🚀 adicione isso AQUI)
    iniciar_lsa_protocol(interfaces_wan, grafo_dinamico)

    # === Inicia threads de escuta para cada interface
    for porta in interfaces:
        t = threading.Thread(
            target=escutar_interface,
            args=(porta, sockets[porta], subrede_local, grafo_dinamico, interfaces_wan, porta_lan),
            daemon=True
        )
        t.start()

    '''
    # === Salva imagem do grafo após 60 segundos
    threading.Thread(
        target=salvar_grafo,
        args=(grafo_dinamico, porta_lan),
        daemon=True
    ).start()  

    '''
  
    

    

    print(f"\n[Roteador iniciado] Interfaces ativas: {interfaces}")
    print(f"[LAN]: {porta_lan} — Subrede local: {subrede_local}")
    print(f"[WANs]: {interfaces_wan}\n")

    while True:
        pass  # Mantém o processo vivo
