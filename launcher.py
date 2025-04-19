import subprocess
import json
import time

roteadores = [
    {
        "porta_lan": 9000,
        "subrede_inicio": 9001,
        "subrede_fim": 9009,
        "interfaces_wan": {
            9011: [9031]
        }
    },
    {
        "porta_lan": 9020,
        "subrede_inicio": 9021,
        "subrede_fim": 9029,
        "interfaces_wan": {
            9031: [9011],
            9030: [9051]
        }
    },
    {
        "porta_lan": 9040,
        "subrede_inicio": 9041,
        "subrede_fim": 9049,
        "interfaces_wan": {
            9051: [9030]
        }
    }
]

for rot in roteadores:
    comando = [
        "cmd", "/c", "start", "cmd", "/k",  # abre nova janela do CMD
        "python", "roteador.py",
        "--lan", str(rot["porta_lan"]),
        "--inicio", str(rot["subrede_inicio"]),
        "--fim", str(rot["subrede_fim"]),
        "--wan", json.dumps(rot["interfaces_wan"])
    ]

    subprocess.Popen(comando)
    time.sleep(0.5)  # pequeno delay pra evitar conflitos
