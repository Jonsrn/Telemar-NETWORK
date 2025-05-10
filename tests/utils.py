import os
import json
import matplotlib
matplotlib.use("Agg")   # não usa Qt/xcb, só grava em arquivo
import matplotlib.pyplot as plt
import subprocess
import json

# Caminhos base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
RESULTS_DIR = os.path.join(BASE_DIR, "tests", "results")

# Garante que a pasta results exista
os.makedirs(RESULTS_DIR, exist_ok=True)


def listar_topologias():
    """Lista os arquivos de configuração disponíveis em /config."""
    arquivos = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".json")]
    return arquivos


def carregar_topologia(nome_arquivo):
    """Carrega o JSON da topologia escolhida."""
    caminho = os.path.join(CONFIG_DIR, nome_arquivo)
    with open(caminho, "r") as f:
        return json.load(f)


def converter_ip(ip127):
    # 127.b.0.d  →  172.10<b>.0.d  (b = 1 → 101, b = 2 → 102 …)
    _, b, _, d = ip127.split(".")
    return f"172.{100 + int(b)}.0.{d}"

def container_para_ip(ip):
    # ip: 172.10<b>.0.<d>
    _, second_octet, _, last = ip.split(".")
    router_idx = int(second_octet) - 100      # 101 → 1, 102 → 2 …
    host_n = 1 if last == "10" else 2         # .10 = _1   |  .11 = _2
    return f"host{router_idx}_{host_n}"

def escolher_topologia():
    """Menu interativo para o usuário escolher uma topologia."""
    topologias = listar_topologias()
    if not topologias:
        print("Nenhuma topologia encontrada em /config.")
        return None
    print("\nTopologias disponíveis:")
    for idx, nome in enumerate(topologias, 1):
        print(f"[{idx}] {nome}")
    escolha = int(input("\nEscolha o número da topologia: ")) - 1
    return topologias[escolha]


def executar_ping_com_estatisticas(origem_container, origem_ip, destino_ip):
    cmd = [
        "docker", "exec", origem_container,
        "python", "src/host.py",
        origem_ip, "0.0.0.0",
        "--cli_ping", destino_ip
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    if proc.returncode != 0:
        return None

    for linha in proc.stdout.splitlines():
        linha = linha.strip()
        if not linha.startswith("{"):
            continue
        try:
            obj = json.loads(linha)
            return obj.get("resultado", obj)   # envelope ou direto
        except json.JSONDecodeError:
            continue
    return None




def carregar_hosts(nome_arquivo):
    topo = carregar_topologia(nome_arquivo)
    hosts = []
    for rot in topo:
        for ip in rot["lan"]:
            if ip.endswith(".10") or ip.endswith(".11"):
                hosts.append(converter_ip(ip))
    return hosts




def salvar_resultados(nome_origem, ip_origem, lista_de_resultados):
    """
    Salva o JSON completo e gera dois gráficos:
    - Latência média por destino.
    - Perda percentual por destino.
    """
    # Nome base para os arquivos
    base_nome = f"{nome_origem.replace('.', '_')}_{ip_origem.replace('.', '_')}"
    json_path = os.path.join(RESULTS_DIR, f"{base_nome}_result.json")
    latency_png_path = os.path.join(RESULTS_DIR, f"{base_nome}_latency.png")
    loss_png_path = os.path.join(RESULTS_DIR, f"{base_nome}_loss.png")

    # Salva o JSON
    with open(json_path, "w") as f:
        json.dump({"origem": ip_origem, "destinos": lista_de_resultados}, f, indent=4)

    # Prepara dados para os gráficos
    destinos = [r['destino'] for r in lista_de_resultados]
    medias = [r['media_ms'] if r['media_ms'] is not None else 0 for r in lista_de_resultados]
    perdas = [int((r['perdidos'] / r['enviados']) * 100) if r['enviados'] > 0 else 100 for r in lista_de_resultados]

    # Gráfico de Latência Média
    plt.figure()
    plt.bar(destinos, medias)
    plt.ylabel('Latência Média (ms)')
    plt.title(f'Latência Média - {nome_origem}')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(latency_png_path)
    plt.close()

    # Gráfico de Perda Percentual
    plt.figure()
    plt.bar(destinos, perdas, color='red')
    plt.ylabel('Perda (%)')
    plt.title(f'Perda de Pacotes - {nome_origem}')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(loss_png_path)
    plt.close()

    print(f"Resultados salvos em:\n- {json_path}\n- {latency_png_path}\n- {loss_png_path}")
