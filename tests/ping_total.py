from utils import listar_topologias, carregar_hosts, salvar_resultados, container_para_ip, executar_ping_com_estatisticas, escolher_topologia


def main():
    topologia_escolhida = escolher_topologia()
    if not topologia_escolhida:
        return

    hosts = carregar_hosts(topologia_escolhida)
    print("\nHosts identificados na topologia:")
    print(hosts)

    print("\nIniciando checklist de ping entre os hosts...\n")

    for origem_idx, origem_ip in enumerate(hosts, 1):
        origem_container = container_para_ip(origem_ip)

        resultados_origem = []  # Acumula todos os resultados deste host origem

        for destino_ip in hosts:
            if origem_ip == destino_ip:
                continue  # não precisa pingar ele mesmo

            resultado = executar_ping_com_estatisticas(origem_container,
                                           origem_ip, destino_ip)


            if resultado:
                print(f"[{origem_ip}] -> [{destino_ip}] : ✅ OK")
                print(f"    Enviados: {resultado['enviados']}, Recebidos: {resultado['recebidos']}, Perdidos: {resultado['perdidos']}")
                print(f"    Latências: {resultado['latencias_ms']}")
                print(f"    Min: {resultado['min_ms']}ms, Max: {resultado['max_ms']}ms, Média: {resultado['media_ms']}ms\n")
                resultados_origem.append(resultado)
            else:
                print(f"[{origem_ip}] -> [{destino_ip}] : ❌ Falhou\n")
                resultados_origem.append({
                    "destino": destino_ip,
                    "enviados": 0,
                    "recebidos": 0,
                    "perdidos": 0,
                    "latencias_ms": [],
                    "min_ms": None,
                    "max_ms": None,
                    "media_ms": None
                })

        # Salva os resultados completos desse host origem
        salvar_resultados(origem_container, origem_ip, resultados_origem)


if __name__ == "__main__":
    main()
