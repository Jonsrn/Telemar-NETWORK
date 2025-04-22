import subprocess
import json
import time

# Roteadores com IPs e subredes específicas (tudo em 127.X.Y.Z)
roteadores = [
    {
        "meu_ip": "127.1.0.1",
        "lan": ["127.1.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.1.0.1": ["127.2.0.1"], #conecta com o router 2
            "127.1.1.1": ["127.4.0.1"] #conecta com o router 4
        }
    },
    {
        "meu_ip": "127.2.0.1",
        "lan": ["127.2.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.2.0.1": ["127.1.0.1"], 
            "127.2.1.1": ["127.3.0.1"]
        }
    },
    {
        "meu_ip": "127.3.0.1",
        "lan": ["127.3.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.3.0.1": ["127.2.0.1"], 
            "127.3.1.1": ["127.4.1.1"]
        }
    }, 
    {
        "meu_ip": "127.4.0.1",
        "lan": ["127.4.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.4.0.1": ["127.1.1.1"], 
            "127.4.1.1": ["127.3.1.1"]

        }
    }
    
]

for rot in roteadores:
    cmd = [
        "cmd", "/c", "start", "cmd", "/k",
        "python", "roteador.py",
        "--meu_ip", rot["meu_ip"],
        "--lan", *rot["lan"],
        "--wan", json.dumps(rot["wan"])
    ]
    subprocess.Popen(cmd)
    time.sleep(0.5)  # atraso pequeno pra evitar colisão de sockets
