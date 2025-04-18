import socket
import threading
import json
import sys

def escutar(minha_porta):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", minha_porta))
    print(f"[HOST {minha_porta}] Escutando...")

    while True:
        data, addr = sock.recvfrom(4096)
        try:
            pacote = json.loads(data.decode())
            print(f"[HOST {minha_porta}] De {pacote['origem']}: {pacote['mensagem']}")
        except:
            print("[HOST] Pacote inválido")

def enviar_loop(minha_porta, gateway_porta):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        destino = int(input(f"[HOST {minha_porta}] Destino final (porta): "))
        mensagem = input(f"[HOST {minha_porta}] Mensagem: ") 

        # 🔧🔧🔧 WORKAROUND TEMPORÁRIO 🔧🔧🔧
        # Como o grafo só conhece interfaces WAN (não LANs como 9000),
        # o campo "destino" será ajustado para uma interface roteável (WAN)
        # de entrada no roteador do destino final. Por ora, assumimos que
        # todos os hosts finais terminam em 1-9 e estão na subrede base múltipla de 10.
        # Assim, mandamos para o vizinho WAN mais próximo (ex: 9001 → 9011).
        # 🔧🔧🔧 FIM DO WORKAROUND 🔧🔧🔧

        subrede_base = destino - (destino % 10)
        porta_destino_roteavel = subrede_base + 11  # ex: 9000 → 9011, 9020 → 9031, etc.

        pacote = {
            "origem": minha_porta,
            "destino": porta_destino_roteavel,  # WAN do roteador de destino
            "entrega_final": destino,           # host real que deve receber
            "mensagem": mensagem
        }

        sock.sendto(json.dumps(pacote).encode(), ("127.0.0.1", gateway_porta))
        print(f"[HOST {minha_porta}] Enviado via roteador {gateway_porta}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python host.py <minha_porta> <gateway_porta>")
        sys.exit(1)

    minha_porta = int(sys.argv[1])
    gateway_porta = int(sys.argv[2])

    threading.Thread(target=escutar, args=(minha_porta,), daemon=True).start()
    enviar_loop(minha_porta, gateway_porta)
