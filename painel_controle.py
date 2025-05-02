import socket, json, sys, threading, time
import networkx as nx
import matplotlib.pyplot as plt

CLI_PORT = 5001          # onde o roteador enviará o grafo
TIMEOUT  = 3             # seg p/ aguardar respostas


def enviar_comando(ip_router, comando, iface=None):
    pkt = {"tipo":"cli_comando", "comando":comando}
    if iface: pkt["destino"] = iface
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(json.dumps(pkt).encode(), (ip_router, 5000))
    sock.close()

def main():
    router_ip = input("IP do roteador alvo: ").strip()

    # socket dedicado para ouvir grafo
    sock_listen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_listen.bind(("0.0.0.0", CLI_PORT))

    while True:
        print("\n=== Painel CLI ===")
        print("1. Aumentar peso (uma interface)")
        print("2. Reduzir  peso (uma interface)")
        print("3. Aumentar peso de TODAS as interfaces")
        print("4. Recuperar grafo do roteador")
        print("0. Sair")
        opcao = input("> ")

        if opcao == "0":
            break

        if opcao in ("1","2"):
            iface = input("Interface WAN de destino (ex: 127.1.1.1): ").strip()
            delta = int(input("Quanto? (1‑5): "))
            delta = max(1, min(delta, 5))
            cmd   = "++" if opcao=="1" else "--"
            # enviamos '++n' n vezes ou '--n' n vezes para simplificar
            for _ in range(delta):
                enviar_comando(router_ip, f"{cmd}1", iface)  # idx fictício=1
            print("✔️  Comando enviado.")

        elif opcao == "3":
            iface = input("Qual interface WAN será referência (ex: 127.1.1.1): ").strip()
            enviar_comando(router_ip, "++++", iface)
            print("✔️  Pesos de todas as interfaces +1.")

        elif opcao == "4":
            enviar_comando(router_ip, "graph")
            print("📷  Comando enviado. O grafo será salvo como imagem no roteador.")
                
        else:
            print("Opção inválida.")

    sock_listen.close()

if __name__ == "__main__":
    main()
