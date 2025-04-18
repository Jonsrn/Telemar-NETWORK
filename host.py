import socket
import threading
import json
import sys
import time

# 🎧 Escuta pacotes recebidos pelo host
def escutar(minha_porta):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", minha_porta))
    print(f"[HOST {minha_porta}] Escutando...")

    while True:
        data, addr = sock.recvfrom(4096)
        try:
            pacote = json.loads(data.decode())
            tipo = pacote.get("tipo", "mensagem")

            if tipo == "mensagem":
                print(f"[HOST {minha_porta}] De {pacote['origem']}: {pacote['mensagem']}")

            elif tipo == "pong":
                print(f"[HOST {minha_porta}] Pong recebido de {pacote['origem']}!")

            elif tipo == "ttl_exceeded":
                print(f"[HOST {minha_porta}] TTL excedido em {pacote['hop']} (roteador intermediário)")

            elif tipo == "traceroute_complete":
                print(f"[HOST {minha_porta}] Traceroute finalizado. Caminho: {pacote['hops']}")

            else:
                print(f"[HOST {minha_porta}] Pacote desconhecido: {pacote}")

        except Exception as e:
            print(f"[HOST] Pacote inválido ou erro: {e}")

# 💬 Envia pacotes com base na escolha do usuário
def enviar_loop(minha_porta, gateway_porta):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        print(f"\n[HOST {minha_porta}]")
        print("1. Enviar mensagem")
        print("2. Enviar ping")
        print("3. Enviar traceroute")
        escolha = input("Escolha uma opção: ")

        if escolha == "1":
            destino = int(input("Destino final (porta): "))
            mensagem = input("Mensagem: ")

            # 🔧🔧🔧 WORKAROUND TEMPORÁRIO 🔧🔧🔧
            subrede_base = destino - (destino % 10)
            porta_destino_roteavel = subrede_base + 11
            # 🔧🔧🔧 FIM DO WORKAROUND 🔧🔧🔧

            pacote = {
                "tipo": "mensagem",
                "origem": minha_porta,
                "destino": porta_destino_roteavel,
                "entrega_final": destino,
                "mensagem": mensagem,
                "ttl": 10
            }

            sock.sendto(json.dumps(pacote).encode(), ("127.0.0.1", gateway_porta))
            print(f"[HOST {minha_porta}] Mensagem enviada via roteador {gateway_porta}")

        elif escolha == "2":
            print("🔧 PING ainda não implementado.")

        elif escolha == "3":
            print("🔧 TRACEROUTE ainda não implementado.")

        else:
            print("❌ Opção inválida.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python host.py <minha_porta> <gateway_porta>")
        sys.exit(1)

    minha_porta = int(sys.argv[1])
    gateway_porta = int(sys.argv[2])

    threading.Thread(target=escutar, args=(minha_porta,), daemon=True).start()
    enviar_loop(minha_porta, gateway_porta)
