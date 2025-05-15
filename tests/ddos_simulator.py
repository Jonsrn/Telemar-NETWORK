import threading
import time
import os
import matplotlib.pyplot as plt
import queue

from utils import (
    escolher_topologia,
    carregar_hosts,
    container_para_ip,
    executar_ping_com_estatisticas
)


def ddos_worker(origem_container, origem_ip, destino_ip, resultados_queue):
    while True:
        resultado = executar_ping_com_estatisticas(origem_container, origem_ip, destino_ip)
        resultados_queue.put(resultado if resultado else {"falha": True})
        # Remove o sleep para atacar o máximo possível (DDoS realista)


def monitor_resultados(resultados_queue, intervalo=10, duracao_total=70):
    inicio = time.time()
    rodada = 1
    historico_medias = []
    tempos_rodada = []
    total_global = 0

    print(f"\n--- Monitoramento do Ataque DDoS por {duracao_total} segundos ---\n")

    while True:
        time.sleep(intervalo)
        resultados_janela = []
        try:
            while True:
                resultado = resultados_queue.get_nowait()
                resultados_janela.append(resultado)
        except queue.Empty:
            pass

        total = len(resultados_janela)
        total_global += total
        falhas = sum(1 for r in resultados_janela if "falha" in r)
        sucessos = total - falhas
        latencias = [l for r in resultados_janela if "latencias_ms" in r for l in r["latencias_ms"]]
        media = sum(latencias) / len(latencias) if latencias else 0
        taxa_pps = total / intervalo if intervalo > 0 else 0

        print(f"Rodada {rodada}: {total} envios ({taxa_pps:.2f} pps), {sucessos} respostas, {falhas} falhas, latência média {media:.2f}ms")
        
        historico_medias.append(media)
        tempos_rodada.append((rodada - 1) * intervalo)
        rodada += 1

        if time.time() - inicio >= duracao_total:
            print(f"\n⚠️  Limite atingido. Total acumulado: {total_global} envios. Encerrando o ataque e gerando gráfico...\n")
            break

    if historico_medias:
        os.makedirs("tests/results", exist_ok=True)
        plt.figure(figsize=(10, 5))
        plt.plot(tempos_rodada, historico_medias, marker="o", linestyle="-")
        plt.xlabel("Tempo (s)")
        plt.ylabel("Latência Média da Janela (ms)")
        plt.title("Oscilação de Latência Durante o Ataque DDoS")
        plt.grid(True)
        caminho_grafico = "tests/results/ddos_oscilacao_latencia.png"
        plt.savefig(caminho_grafico)
        plt.close()
        print(f"Gráfico salvo em {caminho_grafico}")


def main():
    topologia = escolher_topologia()
    if not topologia:
        return

    hosts = carregar_hosts(topologia)
    print("\nHosts disponíveis:")
    print(hosts)

    alvo_ip = input("\nInforme o IP do Roteador ou Host alvo para o DDoS: ").strip()

    hosts_zumbis = [h for h in hosts if h != alvo_ip]
    if not hosts_zumbis:
        print("\n[Erro] Não há zumbis disponíveis (alvo é o único host encontrado).")
        return

    print(f"\nIniciando ataque DDoS ao alvo {alvo_ip} usando {len(hosts_zumbis)} zumbis...\n")

    resultados_queue = queue.Queue()
    for origem_ip in hosts_zumbis:
        origem_container = container_para_ip(origem_ip)
        threading.Thread(target=ddos_worker, args=(origem_container, origem_ip, alvo_ip, resultados_queue), daemon=True).start()

    monitor_resultados(resultados_queue)


if __name__ == "__main__":
    main()
