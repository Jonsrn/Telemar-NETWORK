import subprocess
import json
import time
import ipaddress
import os

# ───── Topologia Base (com IPs 127.X.Y.Z) ─────────────────────────────
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
            "python", os.path.join("src", "roteador.py"),
            "--meu_ip", rot["meu_ip"],
            "--lan", *rot["lan"],
            "--wan", json.dumps(rot["wan"])
        ]
        subprocess.Popen(cmd)
        time.sleep(0.5)

# ───── Função para converter IPs e gerar docker-compose ──────────────
# ─── Função para converter IPs e gerar docker-compose (arquitetura “pod”) ────
def gerar_docker_compose() -> None:
    """Gera docker-compose.yml usando .1 para roteadores LAN e gateway Docker .254"""

    def ip_docker(ip127: str) -> str:
        # 127.b.c.d  ->  172.b.c.d   (mantém octetos)
        _, b, c, d = ip127.split(".")
        return f"172.{b}.{c}.{d}"

    compose = {"version": "3", "services": {}, "networks": {}, "volumes": {}}

    for idx, rot in enumerate(roteadores, 1):
        # ---------- LAN privada -------------------------------------------
        lan_name   = f"lan_{idx}"
        lan_pref   = 100 + idx               # 172.101 / 102 / 103…
        router_lan = f"172.{lan_pref}.0.1"   # << agora .1
        host_ips   = [f"172.{lan_pref}.0.10", f"172.{lan_pref}.0.11"]

        compose["networks"][lan_name] = {
            "ipam": {"config": [
                {"subnet": f"172.{lan_pref}.0.0/24",
                 "gateway": f"172.{lan_pref}.0.254"}   # gateway docker
            ]}
        }
        router_nets = {lan_name: {"ipv4_address": router_lan}}

        # ---------- WANs ---------------------------------------------------
        for iface_ip, viz in rot["wan"].items():
            b, c = iface_ip.split(".")[1:3]          # 127.b.c.x
            wan_name = f"wan_{b}_{c}"
            wan_sub  = f"172.{b}.{c}.0/24"

            compose["networks"].setdefault(
                wan_name,
                {"ipam": {"config": [
                    {"subnet": wan_sub, "gateway": f"172.{b}.{c}.254"}
                ]}}
            )
            router_nets[wan_name] = {"ipv4_address": ip_docker(iface_ip)}

        # ---------- --wan JSON --------------------------------------------
        wan_json = json.dumps({
            ip_docker(local): [ip_docker(v) for v in viz]
            for local, viz in rot["wan"].items()
        })

        # ---------- serviço do roteador -----------------------------------
        rname = f"router{idx}"
        compose["services"][rname] = {
            "build": {"context": ".", "dockerfile": "Dockerfile"},
            "container_name": rname,
            "volumes": [f"vol_{rname}:/dados", "./grafos:/app/grafos"],
            "networks": router_nets,
            "command": (
                f"python -u src/roteador.py "
                f"--meu_ip {router_lan} "
                f"--lan {' '.join(host_ips)} "
                f"--wan '{wan_json}'"
            )
        }
        compose["volumes"][f"vol_{rname}"] = {}

        # ---------- hosts --------------------------------------------------
        for i, hip in enumerate(host_ips, 1):
            hname = f"host{idx}_{i}"
            compose["services"][hname] = {
                "build": {"context": ".", "dockerfile": "Dockerfile"},
                "container_name": hname,
                "networks": {lan_name: {"ipv4_address": hip}},
                "stdin_open": True, "tty": True,
                "command": f"python src/host.py {hip} {router_lan}"
            }

    # grava
    with open("docker-compose.yml", "w") as f:
        json.dump(compose, f, indent=2)
    print("✔️  docker-compose.yml gerado com sucesso.")






# ───── Exportar topologia atual ─────
def exportar_topologia():
    nome_arquivo = input("Nome do arquivo para exportar (sem extensão): ").strip()
    caminho = os.path.join("config", nome_arquivo + ".json")
    with open(caminho, "w") as f:
        json.dump(roteadores, f, indent=4)
    print(f"✔️  Topologia exportada para {caminho}")

# ───── Importar topologia com listagem ─────
def importar_topologia():
    global roteadores
    arquivos = [f for f in os.listdir("config") if f.endswith(".json")]
    if not arquivos:
        print("⚠️  Nenhuma topologia encontrada na pasta config/")
        return

    print("\n📦 Topologias disponíveis:")
    for i, nome in enumerate(arquivos):
        print(f"{i+1}. {nome}")

    escolha = input("Escolha o número do arquivo: ").strip()
    try:
        idx = int(escolha) - 1
        caminho = os.path.join("config", arquivos[idx])
    except (ValueError, IndexError):
        print("❌ Escolha inválida.")
        return

    with open(caminho, "r") as f:
        roteadores = json.load(f)

    print(f"✔️  Topologia '{arquivos[idx]}' importada com sucesso!")

    print("Deseja:\n1. Executar localmente\n2. Gerar Docker Compose")
    sub = input("> ")
    if sub == "1":
        executar_local()
    elif sub == "2":
        gerar_docker_compose()

# ───── Menu principal ─────
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
