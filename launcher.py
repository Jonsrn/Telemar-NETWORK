import subprocess
import json
import time
import ipaddress
import os

# ───── Topologia Base (com IPs 127.X.Y.Z) ─────────────────────────────────────
roteadores = [
    {
        "meu_ip": "127.1.0.1",
        "lan": ["127.1.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.1.1.1": ["127.1.1.2"]
        }
    },
    {
        "meu_ip": "127.2.0.1",
        "lan": ["127.2.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.1.1.2": ["127.1.1.1"],
            "127.2.1.1": ["127.2.1.2"]
        }
    },
    {
        "meu_ip": "127.3.0.1",
        "lan": ["127.3.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.2.1.2": ["127.2.1.1"]
        }
    }
]

# ───── Função para executar localmente no 127 ─────────────────────────

def executar_local():
    for rot in roteadores:
        cmd = [
            "cmd", "/c", "start", "cmd", "/k",
            "python", "roteador.py",
            "--meu_ip", rot["meu_ip"],
            "--lan", *rot["lan"],
            "--wan", json.dumps(rot["wan"])
        ]
        subprocess.Popen(cmd)
        time.sleep(0.5)

# ───── Função para converter IPs e gerar docker-compose ──────────────

def gerar_docker_compose():
    def ip_docker(ip):
        parts = ip.split(".")
        return f"172.{parts[1]}.{parts[2]}.{parts[3]}"

    compose = {
        "version": "3",
        "services": {},
        "networks": {},
        "volumes": {}
    }

    for idx, rot in enumerate(roteadores):
        nome = f"router{idx+1}"
        lan_redes = set()
        networks = []
        cmd = ["python", "roteador.py", "--meu_ip", ip_docker(rot["meu_ip"]), "--lan"] + [ip_docker(ip) for ip in rot["lan"]] + ["--wan", json.dumps({ip_docker(k): [ip_docker(v) for v in vs] for k, vs in rot["wan"].items()})]

        for ip in rot["lan"]:
            net_name = f"net_{'.'.join(ip.split('.')[:3])}"
            compose["networks"].setdefault(net_name, {"ipam": {"config": [{"subnet": f"{'.'.join(ip_docker(ip).split('.')[:3])}.0/24"}]}})
            networks.append(net_name)
            lan_redes.add(net_name)

        for iface in rot["wan"]:
            net_name = f"net_{'.'.join(iface.split('.')[:3])}"
            compose["networks"].setdefault(net_name, {"ipam": {"config": [{"subnet": f"{'.'.join(ip_docker(iface).split('.')[:3])}.0/24"}]}})
            networks.append(net_name)

        compose["services"][nome] = {
            "build": ".",
            "container_name": nome,
            "volumes": [f"vol_{nome}:/dados"],
            "networks": {n: {"ipv4_address": ip_docker(rot["meu_ip"])} for n in lan_redes.union(set([f"net_{'.'.join(ip.split('.')[:3])}" for ip in rot["wan"]]))},
            "command": " ".join(cmd)
        }
        compose["volumes"][f"vol_{nome}"] = {}

        # Hosts (2 por roteador)
        for i in range(2):
            host_name = f"host{idx+1}_{i+1}"
            host_ip = ip_docker(rot["lan"][i])
            compose["services"][host_name] = {
                "build": ".",
                "container_name": host_name,
                "networks": {
                    f"net_{'.'.join(rot["lan"][i].split('.')[:3])}": {"ipv4_address": host_ip}
                },
                "command": f"python host.py {host_ip} {ip_docker(rot['meu_ip'])}"
            }

    with open("docker-compose.yml", "w") as f:
        json.dump(compose, f, indent=2)
    print("✔️  docker-compose.yml gerado com sucesso.")

# ───── Função para exportar topologia atual para JSON ─────

def exportar_topologia():
    nome_arquivo = input("Nome do arquivo para exportar (ex: topologia.json): ").strip()
    with open(nome_arquivo, "w") as f:
        json.dump(roteadores, f, indent=4)
    print(f"✔️  Topologia exportada para {nome_arquivo}")

# ───── Função para importar topologia de JSON e executar ─────

def importar_topologia():
    global roteadores
    nome_arquivo = input("Nome do arquivo para importar (ex: topologia.json): ").strip()
    if not os.path.exists(nome_arquivo):
        print("❌ Arquivo não encontrado.")
        return

    with open(nome_arquivo, "r") as f:
        roteadores = json.load(f)
    print("✔️  Topologia importada com sucesso!")

    print("Deseja:\n1. Executar localmente\n2. Gerar Docker Compose")
    sub = input("> ")
    if sub == "1":
        executar_local()
    elif sub == "2":
        gerar_docker_compose()

# ───── Menu principal ────────────────────────────

if __name__ == "__main__":
    print("=== Telemar Launcher ===")
    print("1. Executar topologia local (127.X.X.X)")
    print("2. Gerar docker-compose.yml")
    print("3. Exportar topologia atual para JSON")
    print("4. Importar topologia de JSON")

    op = input("Escolha uma opção: ").strip()

    if op == "1":
        executar_local()
    elif op == "2":
        gerar_docker_compose()
    elif op == "3":
        exportar_topologia()
    elif op == "4":
        importar_topologia()
    else:
        print("❌ Opção inválida.")
