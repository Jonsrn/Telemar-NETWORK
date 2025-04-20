import socket
import threading
import json
import sys
import time

pings_ativos = {}

def escutar(meu_ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((meu_ip, 5000))
    print(f"[HOST {meu_ip}] Escutando...")

    while True:
        data, addr = sock.recvfrom(4096)
        try:
            pacote = json.loads(data.decode())
            tipo = pacote.get("tipo", "mensagem")

            if tipo == "mensagem":
                print(f"[HOST {meu_ip}] De {pacote['origem']}: {pacote['mensagem']}")

            elif tipo == "ping":
                resposta = {
                    "tipo": "pong",
                    "origem": meu_ip,
                    "destino": pacote["origem"],
                    "timestamp": pacote["timestamp"],
                    "ttl": pacote.get("ttl", "?")
                }
                sock.sendto(json.dumps(resposta).encode(), (pacote["origem"], 5000))

            elif tipo == "pong":
                ts = pacote.get("timestamp")
                if ts in pings_ativos:
                    tempo_ida_volta = int((time.time() - ts) * 1000)
                    print(f"Resposta de {pacote['origem']}: bytes=32 tempo={tempo_ida_volta}ms TTL={pacote.get('ttl', '?')}")
                    pings_ativos[ts]["latencia"] = tempo_ida_volta

            elif tipo == "ttl_exceeded":
                print(f"[HOST {meu_ip}] TTL excedido em {pacote['hop']}")

            elif tipo == "traceroute_complete":
                print(f"[HOST {meu_ip}] Traceroute finalizado: {pacote['hops']}")

            else:
                print(f"[HOST {meu_ip}] Pacote desconhecido: {pacote}")

        except Exception as e:
            print(f"[HOST {meu_ip}] Pacote inválido ou erro: {e}")

def realizar_ping(destino_ip, meu_ip, gateway_ip, sock):
    print(f"\nDisparando {destino_ip} com 32 bytes de dados:")

    tempos = []
    recebidos = 0
    total = 3

    for i in range(total):
        timestamp = time.time()
        pacote = {
            "tipo": "ping",
            "origem": meu_ip,
            "destino": gateway_ip,
            "entrega_final": destino_ip,
            "timestamp": timestamp,
            "ttl": 10
        }

        pings_ativos[timestamp] = {
            "destino": destino_ip,
            "enviado_em": timestamp
        }

        sock.sendto(json.dumps(pacote).encode(), (gateway_ip, 5000))

        def aguardar_resposta(ts):
            nonlocal recebidos
            inicio = time.time()
            while time.time() - inicio < 2:
                if ts in pings_ativos and pings_ativos[ts].get("latencia"):
                    return
                time.sleep(0.05)
            print(f"Tempo esgotado para o host {destino_ip}.")
            del pings_ativos[ts]

        threading.Thread(target=aguardar_resposta, args=(timestamp,), daemon=True).start()
        time.sleep(1)

    time.sleep(2.2)

    recebidos = 0
    tempos = []
    for ts in list(pings_ativos):
        info = pings_ativos[ts]
        if isinstance(info, dict) and info.get("latencia"):
            tempos.append(info["latencia"])
            recebidos += 1
        del pings_ativos[ts]

    perdidos = total - recebidos

    print(f"\nEstatísticas do Ping para {destino_ip}:")
    print(f"    Pacotes: Enviados = {total}, Recebidos = {recebidos}, Perdidos = {perdidos} ({int((perdidos/total)*100)}% de perda)")

    if tempos:
        print("Aproximar um número redondo de vezes em milissegundos:")
        print(f"    Mínimo = {min(tempos)}ms, Máximo = {max(tempos)}ms, Média = {sum(tempos)//len(tempos)}ms")

def enviar_loop(meu_ip, gateway_ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        print(f"\n[HOST {meu_ip}]")
        print("1. Enviar mensagem")
        print("2. Enviar ping")
        print("3. Enviar traceroute")
        escolha = input("Escolha uma opção: ")

        if escolha == "1":
            destino_ip = input("Destino final (IP): ")
            mensagem = input("Mensagem: ")

            pacote = {
                "tipo": "mensagem",
                "origem": meu_ip,
                "destino": gateway_ip,
                "entrega_final": destino_ip,
                "mensagem": mensagem,
                "ttl": 10
            }

            sock.sendto(json.dumps(pacote).encode(), (gateway_ip, 5000))
            print(f"[HOST {meu_ip}] Mensagem enviada via roteador {gateway_ip}")

        elif escolha == "2":
            destino_ip = input("Destino final (IP): ")
            realizar_ping(destino_ip, meu_ip, gateway_ip, sock)

        elif escolha == "3":
            print("🔧 TRACEROUTE ainda não implementado.")

        else:
            print("❌ Opção inválida.")

# === Execução principal ===
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python host.py <meu_ip> <gateway_ip>")
        sys.exit(1)

    meu_ip = sys.argv[1]
    gateway_ip = sys.argv[2]

    threading.Thread(target=escutar, args=(meu_ip,), daemon=True).start()
    enviar_loop(meu_ip, gateway_ip)
