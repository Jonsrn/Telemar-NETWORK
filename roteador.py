import socket
import threading
import json
import networkx as nx

def carregar_topologia(nome_arquivo):
    """
    Lê o grafo da topologia de um arquivo JSON com arestas e pesos.
    Exemplo:
    [
        [9000, 9010, 1],
        [9010, 9020, 1],
        [9020, 9030, 2]
    ]
    """
    with open(nome_arquivo, "r") as f:
        arestas = json.load(f)
    
    print(f"[DEBUG] Topologia carregada do arquivo '{nome_arquivo}':")
    for a in arestas:
        print(" →", a)    

    grafo = nx.Graph()
    grafo.add_weighted_edges_from(arestas)
    return grafo

def calcular_proximo_salto(grafo, origem, destino_final):
    try:
        caminho = nx.shortest_path(grafo, source=origem, target=destino_final, weight="weight")
        if len(caminho) > 1:
            return caminho[1]  # O próximo nó após mim
        else:
            return None
    except nx.NetworkXNoPath:
        return None

def roteador(porta_escuta, subrede_inicio, subrede_fim, grafo):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", porta_escuta))

    print(f"\n[ROTEADOR {porta_escuta}] Ativo.")
    print(f" - Subrede local: portas {subrede_inicio} até {subrede_fim}")
    print(f" - Roteamento com Dijkstra ativado\n")

    subrede_local = range(subrede_inicio, subrede_fim + 1)

    while True:
        data, addr = sock.recvfrom(4096)
        try:
            pacote = json.loads(data.decode())
            destino_real = int(pacote["destino"])

            # 🔧🔧🔧 SOLUÇÃO TEMPORÁRIA 🔧🔧🔧
            # Usamos o destino 'ajustado' apenas para cálculo de rota,
            # mas preservamos o destino real dentro do pacote
            if destino_real % 10 != 0:
                destino_para_rotear = destino_real - (destino_real % 10)
                print(f"[ROTEADOR {porta_escuta}] [AJUSTE TEMPORÁRIO] Roteando via subrede base: {destino_para_rotear}")
            else:
                destino_para_rotear = destino_real
            # 🔧🔧🔧 FIM DA SOLUÇÃO TEMPORÁRIA 🔧🔧🔧

            if destino_real in subrede_local:
                print(f"[ROTEADOR {porta_escuta}] Entregando localmente → {destino_real}")
                sock.sendto(data, ("127.0.0.1", destino_real))
            else:
                proximo = calcular_proximo_salto(grafo, porta_escuta, destino_para_rotear)
                if proximo:
                    print(f"[ROTEADOR {porta_escuta}] Encaminhando via Dijkstra → {proximo}")
                    sock.sendto(data, ("127.0.0.1", proximo))
                else:
                    print(f"[ROTEADOR {porta_escuta}] Sem rota para {destino_para_rotear}. Pacote descartado.")
        except Exception as e:
            print(f"[ROTEADOR {porta_escuta}] Pacote inválido ou erro: {e}")

if __name__ == "__main__":
    print("Configuração do Roteador (com grafo de topologia via JSON)\n")

    try:
        porta_escuta = int(input("Porta do roteador (onde escutar): "))
        subrede_inicio = int(input("Início da faixa de hosts locais (porta): "))
        subrede_fim = int(input("Fim da faixa de hosts locais (porta): "))
        arquivo_topologia = input("Arquivo da topologia (ex: topologia.json): ")
    except ValueError:
        print("❌ Entrada inválida. Use números inteiros.")
        exit(1)

    grafo = carregar_topologia(arquivo_topologia)
    roteador(porta_escuta, subrede_inicio, subrede_fim, grafo)
