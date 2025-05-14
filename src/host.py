import socket
import threading
import json
import sys
import time


class Host:
    def __init__(self, meu_ip, gateway_ip):
        self.meu_ip = meu_ip
        self.gateway_ip = gateway_ip
        self.pings_ativos = {}

    def escutar(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.meu_ip, 5000))
        print(f"[HOST {self.meu_ip}] Escutando...")

        while True:
            try:
                data, addr = sock.recvfrom(4096)
                try:
                    pacote = json.loads(data.decode())
                    tipo = pacote.get("tipo", "mensagem")

                    if tipo == "mensagem":
                        print(f"[HOST {self.meu_ip}] De {pacote['origem']}: {pacote['mensagem']}")

                    elif tipo == "ping":
                        resposta = {
                            "tipo": "pong",
                            "origem": self.meu_ip,
                            "destino": self.gateway_ip,
                            "entrega_final": pacote["origem"],
                            "timestamp": pacote["timestamp"],
                            "ttl": 10
                        }
                        sock.sendto(json.dumps(resposta).encode(), (self.gateway_ip, 5000))

                    elif tipo == "pong":
                        ts = pacote.get("timestamp")
                        if ts in self.pings_ativos:
                            tempo_ida_volta = int((time.time() - ts) * 1000)
                            print(f"Resposta de {pacote['origem']}: bytes=32 tempo={tempo_ida_volta}ms TTL={pacote.get('ttl', '?')}")
                            self.pings_ativos[ts]["latencia"] = tempo_ida_volta

                    # Dentro do método escutar() em host.py
                    elif tipo == "traceroute":
                        print(f"[HOST {self.meu_ip}] DEBUG: Recebido pacote traceroute: {pacote}") # Log de recebimento
                        if pacote.get("entrega_final") == self.meu_ip:
                            print(f"[HOST {self.meu_ip}] DEBUG: Sou o destino final do traceroute.") # Log de processamento
                            resposta = {
                                "tipo": "traceroute_reply",
                                "origem": self.meu_ip,
                                "destino": self.gateway_ip,
                                "entrega_final": pacote["origem"],
                                "numero": pacote["numero"],
                                "ttl": 10,
                                "reply_port": pacote.get("reply_port", 5000)
                            }
                            print(f"[HOST {self.meu_ip}] DEBUG: Enviando traceroute_reply: {resposta} para {(self.gateway_ip, 5000)}") # Log de envio
                            sock.sendto(json.dumps(resposta).encode(), (self.gateway_ip, 5000))


                    elif tipo == "cli_ping":
                        destino_final = pacote["destino_final"]
                        reply_addr = addr

                        def _task():
                            stats = self.realizar_ping(destino_final, sock, retornar_resultado=True, quiet=True)
                            resposta = {
                                "tipo": "cli_ping_result",
                                "origem": self.meu_ip,
                                "resultado": stats
                            }
                            sock.sendto(json.dumps(resposta).encode(), reply_addr)

                        threading.Thread(target=_task, daemon=True).start()

                    else:
                        print(f"[HOST {self.meu_ip}] Pacote desconhecido: {pacote}")

                except Exception as e:
                    print(f"[HOST {self.meu_ip}] Pacote inválido ou erro: {e}")

            except ConnectionResetError:
                continue

    def realizar_ping(self, destino_ip, sock, retornar_resultado=False, quiet=False):
        if not retornar_resultado:
            print(f"\nDisparando {destino_ip} com 32 bytes de dados:")

        tempos = []
        recebidos = 0
        total = 3

        for _ in range(total):
            timestamp = time.time()
            pacote = {
                "tipo": "ping",
                "origem": self.meu_ip,
                "destino": self.gateway_ip,
                "entrega_final": destino_ip,
                "timestamp": timestamp,
                "ttl": 10
            }

            self.pings_ativos[timestamp] = {"destino": destino_ip, "enviado_em": timestamp}
            sock.sendto(json.dumps(pacote).encode(), (self.gateway_ip, 5000))

            def aguardar_resposta(ts):
                nonlocal recebidos
                inicio = time.time()
                while time.time() - inicio < 2:
                    if ts in self.pings_ativos and self.pings_ativos[ts].get("latencia"):
                        return
                    time.sleep(0.05)
                if not retornar_resultado:
                    print(f"Tempo esgotado para o host {destino_ip}.")
                del self.pings_ativos[ts]

            threading.Thread(target=aguardar_resposta, args=(timestamp,), daemon=True).start()
            time.sleep(1)

        time.sleep(2.2)

        recebidos = 0
        tempos = []
        for ts in list(self.pings_ativos):
            info = self.pings_ativos[ts]
            if isinstance(info, dict) and info.get("latencia"):
                tempos.append(info["latencia"])
                recebidos += 1
            del self.pings_ativos[ts]

        perdidos = total - recebidos

        if retornar_resultado:
            resultado = {
                "destino": destino_ip,
                "enviados": total,
                "recebidos": recebidos,
                "perdidos": perdidos,
                "latencias_ms": tempos,
                "min_ms": min(tempos) if tempos else None,
                "max_ms": max(tempos) if tempos else None,
                "media_ms": sum(tempos) // len(tempos) if tempos else None
            }
            if not quiet:
                print(json.dumps(resultado))
            return resultado
        else:
            print(f"\nEstatísticas do Ping para {destino_ip}:")
            print(f"    Pacotes: Enviados = {total}, Recebidos = {recebidos}, Perdidos = {perdidos} ({int((perdidos/total)*100)}% de perda)")

            if tempos:
                print("Aproximar um número redondo de vezes em milissegundos:")
                print(f"    Mínimo = {min(tempos)}ms, Máximo = {max(tempos)}ms, Média = {sum(tempos)//len(tempos)}ms")

    def realizar_traceroute(self, destino_ip, sock_lan):
        max_saltos = 15
        print(f"\nTRACEROUTE para {destino_ip} (máximo {max_saltos} saltos):")

        tr_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tr_sock.bind((self.meu_ip, 0))
        reply_port = tr_sock.getsockname()[1]

        for ttl_atual in range(1, max_saltos + 1):
            pacote = {
                "tipo": "traceroute",
                "origem": self.meu_ip,
                "reply_port": reply_port,
                "destino": self.gateway_ip,
                "entrega_final": destino_ip,
                "ttl": ttl_atual,
                "numero": ttl_atual
            }
            sock_lan.sendto(json.dumps(pacote).encode(), (self.gateway_ip, 5000))

            tr_sock.settimeout(5)
            try:
                while True:
                    data, _ = tr_sock.recvfrom(4096)
                    resp = json.loads(data.decode())

                    if resp.get("numero") != ttl_atual:
                        continue

                    if resp["tipo"] == "ttl_exceeded":
                        print(f"{ttl_atual}: salto → {resp['hop']}")
                        break
                    elif resp["tipo"] == "traceroute_reply":
                        print(f"{ttl_atual}: destino alcançado → {resp['origem']}")
                        tr_sock.close()
                        return
            except socket.timeout:
                print(f"{ttl_atual}: * (tempo esgotado)")

    def enviar_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            print(f"\n[HOST {self.meu_ip}]")
            print("1. Enviar mensagem")
            print("2. Enviar ping")
            print("3. Enviar traceroute")
            escolha = input("Escolha uma opção: ")

            if escolha == "1":
                destino_ip = input("Destino final (IP): ")
                mensagem = input("Mensagem: ")
                pacote = {
                    "tipo": "mensagem",
                    "origem": self.meu_ip,
                    "destino": self.gateway_ip,
                    "entrega_final": destino_ip,
                    "mensagem": mensagem,
                    "ttl": 10
                }
                sock.sendto(json.dumps(pacote).encode(), (self.gateway_ip, 5000))
                print(f"[HOST {self.meu_ip}] Mensagem enviada via roteador {self.gateway_ip}")

            elif escolha == "2":
                destino_ip = input("Destino final (IP): ")
                self.realizar_ping(destino_ip, sock)

            elif escolha == "3":
                destino_ip = input("Destino final (IP): ")
                self.realizar_traceroute(destino_ip, sock)

            else:
                print("❌ Opção inválida.")


# === Execução principal ===
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python host.py <meu_ip> <gateway_ip> [--cli_ping <destino_ip>]")
        sys.exit(1)

    meu_ip, gateway_ip = sys.argv[1], sys.argv[2]
    host = Host(meu_ip, gateway_ip)

    if len(sys.argv) == 5 and sys.argv[3] == "--cli_ping":
        destino_final = sys.argv[4]
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((meu_ip, 0))
        reply_port = sock.getsockname()[1]

        pedido = {
            "tipo": "cli_ping",
            "destino_final": destino_final,
            "reply_port": reply_port
        }
        sock.sendto(json.dumps(pedido).encode(), (meu_ip, 5000))
        sock.settimeout(10)
        data, _ = sock.recvfrom(4096)
        print(data.decode())
        sys.exit(0)

    threading.Thread(target=host.escutar, daemon=True).start()
    host.enviar_loop()
