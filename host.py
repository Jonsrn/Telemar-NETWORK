import socket
import threading
import json
import sys
import time

# Armazena os pings pendentes aguardando resposta
pings_ativos = {}

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

            elif tipo == "ping":
                resposta = {
                    "tipo": "pong",
                    "origem": minha_porta,
                    "destino": pacote["origem"],
                    "timestamp": pacote["timestamp"],
                    "ttl": pacote.get("ttl", "?")  # TTL real que o pacote tinha ao chegar
                }
                sock.sendto(json.dumps(resposta).encode(), ("127.0.0.1", pacote["origem"]))

            elif tipo == "pong":
                ts = pacote.get("timestamp")
                if ts in pings_ativos:
                    tempo_ida_volta = int((time.time() - ts) * 1000)
                    print(f"Resposta de {pacote['origem']}: bytes=32 tempo={tempo_ida_volta}ms TTL={pacote.get('ttl', '?')}")
                    pings_ativos[ts]["latencia"] = tempo_ida_volta

            elif tipo == "ttl_exceeded":
                print(f"[HOST {minha_porta}] TTL excedido em {pacote['hop']}")

            elif tipo == "traceroute_complete":
                print(f"[HOST {minha_porta}] Traceroute finalizado: {pacote['hops']}")

            else:
                print(f"[HOST {minha_porta}] Pacote desconhecido: {pacote}")

        except Exception as e:
            print(f"[HOST] Pacote inválido ou erro: {e}")


def realizar_ping(destino, minha_porta, gateway_porta, sock):
    subrede_base = destino - (destino % 10)
    porta_destino_roteavel = subrede_base + 11

    print(f"\nDisparando {destino} com 32 bytes de dados:")

    tempos = []
    recebidos = 0
    total = 3

    for i in range(total):
        timestamp = time.time()
        pacote = {
            "tipo": "ping",
            "origem": minha_porta,
            "destino": porta_destino_roteavel,
            "entrega_final": destino,
            "timestamp": timestamp,
            "ttl": 10
        }

        pings_ativos[timestamp] = {
            "destino": destino,
            "enviado_em": timestamp
        }

        sock.sendto(json.dumps(pacote).encode(), ("127.0.0.1", gateway_porta))

        def aguardar_resposta(ts):
            nonlocal recebidos
            inicio = time.time()
            while time.time() - inicio < 2:
                if ts in pings_ativos and pings_ativos[ts].get("latencia"):
                    return  # Já respondeu!
                time.sleep(0.05)
            # Timeout
            print(f"Tempo esgotado para o host {destino}.")
            del pings_ativos[ts]

        threading.Thread(target=aguardar_resposta, args=(timestamp,), daemon=True).start()
        time.sleep(1)

    # Aguarda último pacote voltar ou expirar
    time.sleep(2.2)

    # Calcula estatísticas
    recebidos = 0
    tempos = []

    # 🧹 Coleta os tempos válidos e limpa os pings usados
    for ts in list(pings_ativos):
        info = pings_ativos[ts]
        if isinstance(info, dict) and info.get("latencia"):
            tempos.append(info["latencia"])
            recebidos += 1
        del pings_ativos[ts]

    perdidos = total - recebidos

    print(f"\nEstatísticas do Ping para {destino}:")
    print(f"    Pacotes: Enviados = {total}, Recebidos = {recebidos}, Perdidos = {perdidos} ({int((perdidos/total)*100)}% de perda)")

    if tempos:
        print("Aproximar um número redondo de vezes em milissegundos:")
        print(f"    Mínimo = {min(tempos)}ms, Máximo = {max(tempos)}ms, Média = {sum(tempos)//len(tempos)}ms")


# 💬 Menu de envio de pacotes
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
            destino = int(input("Destino final (porta): "))
            realizar_ping(destino, minha_porta, gateway_porta, sock)

        elif escolha == "3":
            print("🔧 TRACEROUTE ainda não implementado.")

        else:
            print("❌ Opção inválida.")

# === Execução principal ===
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python host.py <minha_porta> <gateway_porta>")
        sys.exit(1)

    minha_porta = int(sys.argv[1])
    gateway_porta = int(sys.argv[2])

    threading.Thread(target=escutar, args=(minha_porta,), daemon=True).start()
    enviar_loop(minha_porta, gateway_porta)
