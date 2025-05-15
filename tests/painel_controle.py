import subprocess
import json

def ip_para_host_container(ip_roteador):
    """Converte IP do roteador em nome do container do host."""
    try:
        _, second_octet, _, last = ip_roteador.strip().split(".")
        router_idx = int(second_octet) - 100
        host_id = f"host{router_idx}_1"  # sempre escolhe o host .10 (_1)
        return host_id
    except Exception:
        print(f"[Erro] IP inválido: {ip_roteador}")
        return None

def enviar_comando_via_host(container_host, roteador_ip, comando, iface=None):
    """Executa o comando no host via docker exec."""
    cli_pkt = {
        "tipo": "cli_comando",
        "comando": comando
    }
    if iface:
        cli_pkt["destino"] = iface

    # Usa o IP do roteador como gateway, não mais 0.0.0.0
    cmd = [
        "docker", "exec", container_host,
        "python", "src/host.py",
        roteador_ip, roteador_ip,
        "--cli_envia_json", json.dumps(cli_pkt)
    ]

    try:
        resultado = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print(resultado.stdout.strip())
        if resultado.stderr.strip():
            print("[Erro] stderr:", resultado.stderr.strip())
    except Exception as e:
        print(f"[Erro] Falha ao executar comando via docker exec: {e}")

def main():
    roteador_ip = input("IP do roteador alvo (ex: 172.101.0.1): ").strip()
    container_host = ip_para_host_container(roteador_ip)

    if not container_host:
        print("[Erro] Não foi possível determinar o host.")
        return

    print(f"[Info] Usando container do host: {container_host}")

    while True:
        print("\n=== Painel CLI ===")
        print("1. Aumentar peso de TODAS as interfaces")
        print("2. Reduzir  peso de TODAS as interfaces")
        print("3. Gerar imagem do grafo do roteador")
        print("0. Sair")
        opcao = input("> ")

        if opcao == "0":
            break

        if opcao == "1":
            enviar_comando_via_host(container_host, roteador_ip, "++++")
            print("✔️  Pesos de todas as interfaces +1.")

        elif opcao == "2":
            enviar_comando_via_host(container_host, roteador_ip, "----")
            print("✔️  Pesos de todas as interfaces -1.")

        elif opcao == "3":
            enviar_comando_via_host(container_host, roteador_ip, "graph")
            print("📷  Comando enviado. O grafo será salvo como imagem no roteador.")

        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
