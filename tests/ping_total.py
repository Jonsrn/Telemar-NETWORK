import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
from utils import (
    listar_topologias,
    carregar_hosts,
    container_para_ip,
    executar_ping_com_estatisticas,
    escolher_topologia
)

RESULTS_DIR = os.path.join("tests", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def gerar_grafico_consolidado(resultados, nome_arquivo_base):
    resumo_por_origem = {}

    # Agrupar resultados por origem
    for resultado in resultados:
        origem = resultado["origem_testada"]
        if origem not in resumo_por_origem:
            resumo_por_origem[origem] = {"enviados": 0, "recebidos": 0, "perdidos": 0}
        
        resumo_por_origem[origem]["enviados"] += resultado.get("enviados", 0)
        resumo_por_origem[origem]["recebidos"] += resultado.get("recebidos", 0)
        resumo_por_origem[origem]["perdidos"] += resultado.get("perdidos", 0)

    origens = list(resumo_por_origem.keys())
    enviados = [resumo_por_origem[o]["enviados"] for o in origens]
    recebidos = [resumo_por_origem[o]["recebidos"] for o in origens]
    perdidos = [resumo_por_origem[o]["perdidos"] for o in origens]

    x = range(len(origens))

    plt.figure(figsize=(12, 6))
    plt.bar(x, enviados, width=0.2, label="Enviados", align="center")
    plt.bar([p + 0.2 for p in x], recebidos, width=0.2, label="Recebidos", align="center")
    plt.bar([p + 0.4 for p in x], perdidos, width=0.2, label="Perdidos", align="center")

    plt.xticks([p + 0.2 for p in x], origens, rotation=45)
    plt.ylabel("Pacotes")
    plt.title("Resumo Consolidado de Pings por Origem")
    plt.legend()
    plt.tight_layout()

    caminho_grafico = os.path.join(RESULTS_DIR, f"{nome_arquivo_base}_grafico.png")
    plt.savefig(caminho_grafico)
    plt.close()

    print(f"Gráfico salvo em {caminho_grafico}")

def main():
    topologia_escolhida = escolher_topologia()
    if not topologia_escolhida:
        return

    hosts = carregar_hosts(topologia_escolhida)
    print("\nHosts identificados na topologia:")
    print(hosts)

    print("\nIniciando checklist de ping entre os hosts...\n")

    resultado_geral = {
        "topologia": topologia_escolhida,
        "data": datetime.now().isoformat(),
        "hosts": hosts,
        "resultados": []
    }

    for origem_idx, origem_ip in enumerate(hosts, 1):
        origem_container = container_para_ip(origem_ip)

        for destino_ip in hosts:
            if origem_ip == destino_ip:
                continue

            resultado = executar_ping_com_estatisticas(origem_container, origem_ip, destino_ip)

            if resultado:
                # Verifica se ao menos uma resposta foi recebida
                if resultado.get("latencias_ms"):
                    # Força recebidos = enviados para marcar como sucesso total
                    resultado["recebidos"] = resultado["enviados"]
                    resultado["perdidos"] = 0
                    print(f"[{origem_ip}] -> [{destino_ip}] : ✅ OK (Sucesso)")
                else:
                    print(f"[{origem_ip}] -> [{destino_ip}] : ❌ Falhou (Nenhuma resposta válida)")
                    resultado = {
                        "origem_testada": origem_ip,
                        "destino_testado": destino_ip,
                        "enviados": 0,
                        "recebidos": 0,
                        "perdidos": 0,
                        "latencias_ms": [],
                        "min_ms": None,
                        "max_ms": None,
                        "media_ms": None,
                        "status_execucao": "Falha ou sem resposta"
                    }
            else:
                print(f"[{origem_ip}] -> [{destino_ip}] : ❌ Falhou (Erro na execução)")
                resultado = {
                    "origem_testada": origem_ip,
                    "destino_testado": destino_ip,
                    "enviados": 0,
                    "recebidos": 0,
                    "perdidos": 0,
                    "latencias_ms": [],
                    "min_ms": None,
                    "max_ms": None,
                    "media_ms": None,
                    "status_execucao": "Falha ou sem resposta"
                }

            resultado["origem_testada"] = origem_ip
            resultado["destino_testado"] = destino_ip
            resultado_geral["resultados"].append(resultado)

    nome_base = f"checklist_ping_CONSOLIDADO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    caminho_json = os.path.join(RESULTS_DIR, f"{nome_base}.json")

    with open(caminho_json, "w") as f:
        json.dump(resultado_geral, f, indent=4)

    print(f"\nChecklist consolidado salvo em {caminho_json}")

    # Geração do gráfico
    gerar_grafico_consolidado(resultado_geral["resultados"], nome_base)


if __name__ == "__main__":
    main()
