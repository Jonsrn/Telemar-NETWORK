import socket
import threading
import json
import networkx as nx

# === Carrega a topologia global da rede ===
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
def escutar_interface(porta, sock, subrede_local, grafo, interfaces_wan, porta_lan):
    print(f"[INTERFACE {porta}] Escutando...")

    while True:
        data, addr = sock.recvfrom(4096)
        try:
            # 1) Parse básico
            pacote = json.loads(data.decode())
            tipo = pacote.get("tipo", "mensagem")  
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

            # 5) Pacote vindo de uma WAN → calcula Dijkstra
            proximo = calcular_proximo_salto(grafo, porta, destino_real)
            if not proximo:
                print(f"[INTERFACE {porta}] Sem rota para {destino_real}. Descartando.")
                continue

            # 6) Internal forwarding (entre minhas próprias interfaces)
            if proximo in sockets:
                print(f"[INTERFACE {porta}] Internal forwarding → {proximo}")
                sockets[proximo].sendto(data, ("127.0.0.1", proximo))
                continue

            # 7) External forwarding (busca interface certa)
            interface_envio = None
            for iface_local, vizinhos in interfaces_wan.items():
                if proximo in vizinhos:
                    interface_envio = iface_local
                    break

            if interface_envio:
                print(f"[INTERFACE {porta}] Encaminhando externamente para {destino_real} via iface {interface_envio} → {proximo}")
                sockets[interface_envio].sendto(data, ("127.0.0.1", proximo))
            else:
                print(f"[INTERFACE {porta}] Sem interface para alcançar {proximo}.")

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
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler config.json: {e}")
        exit(1)

    porta_lan = int(config["porta_lan"])
    subrede_local = range(config["subrede_inicio"], config["subrede_fim"] + 1)
    interfaces_wan = {int(k): v for k, v in config["interfaces_wan"].items()}

    # === Cria sockets para todas as interfaces ===
    sockets = {}
    interfaces = [porta_lan] + list(interfaces_wan.keys())

    for porta in interfaces:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("127.0.0.1", porta))
        sockets[porta] = sock

    # === Carrega o grafo global ===
    grafo = carregar_topologia("topologia.json")

    # === Inicia threads de escuta para cada interface ===
    for porta in interfaces:
        t = threading.Thread(
            target=escutar_interface,
            args=(porta, sockets[porta], subrede_local, grafo, interfaces_wan, porta_lan),
            daemon=True
        )

        t.start()

    print(f"\n[Roteador iniciado] Interfaces ativas: {interfaces}")
    print(f"[LAN]: {porta_lan} — Subrede local: {subrede_local}")
    print(f"[WANs]: {interfaces_wan}\n")

    while True:
        pass  # Mantém o processo vivo
