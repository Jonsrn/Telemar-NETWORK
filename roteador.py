import socket
import threading
import json

def roteador(porta_escuta, subrede_inicio, subrede_fim, porta_proximo):
    # Prepara o socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", porta_escuta))

    print(f"\n[ROTEADOR {porta_escuta}] Ativo.")
    print(f" - Subrede local: portas {subrede_inicio} até {subrede_fim}")
    print(f" - Próximo roteador (rota padrão): {porta_proximo}\n")

    subrede_local = range(subrede_inicio, subrede_fim + 1)

    while True:
        data, addr = sock.recvfrom(4096)
        try:
            pacote = json.loads(data.decode())
            destino = pacote["destino"]

            if destino in subrede_local:
                print(f"[ROTEADOR {porta_escuta}] Entregando localmente → {destino}")
                sock.sendto(data, ("127.0.0.1", destino))
            else:
                print(f"[ROTEADOR {porta_escuta}] Encaminhando para próximo roteador → {porta_proximo}")
                sock.sendto(data, ("127.0.0.1", porta_proximo))
        except:
            print(f"[ROTEADOR {porta_escuta}] Pacote inválido.")

if __name__ == "__main__":
    print("Configuração do Roteador\n")

    try:
        porta_escuta = int(input("Porta do roteador (onde escutar): "))
        subrede_inicio = int(input("Início da faixa de hosts locais (porta): "))
        subrede_fim = int(input("Fim da faixa de hosts locais (porta): "))
        porta_proximo = int(input("Porta do próximo roteador (default route): "))
    except ValueError:
        print("❌ Entrada inválida. Use números inteiros.")
        exit(1)

    roteador(porta_escuta, subrede_inicio, subrede_fim, porta_proximo)
