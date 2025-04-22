import subprocess
import json
import time

# Roteadores com IPs e subredes específicas (tudo em 127.X.Y.Z)
roteadores = [
    {
         #Router 1
        "meu_ip": "127.1.0.1",
        "lan": ["127.1.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.1.0.1": ["127.6.0.1"], #primeira interface WAN conectada na Primeira Interface do Router 6
            "127.1.1.1": ["127.5.1.1"], #Segunda Interface WAN é conectada na Segunda Interface do Router 5 
            "127.1.2.1": ["127.2.0.1"]  #Terceira interface WAN é conectada na Primeira Interface do Router 2
        }
    },
    {
         #Router 2
        "meu_ip": "127.2.0.1",
        "lan": ["127.2.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.2.0.1": ["127.1.2.1"], #Primeira Interface WAN é conectada na Terceira Interface do Router 1
            "127.2.1.1": ["127.5.2.1"], #Segunda Interface WAN é conectada na Terceira Interface Router 5
            "127.2.2.1": ["127.3.0.1"]  #Terceira Interface WAN é conectada na Primeira Interface do Router 3
        }
    },
    {
         #Router 3
        "meu_ip": "127.3.0.1",
        "lan": ["127.3.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.3.0.1": ["127.2.2.1"], #Primeira Interface WAN é conectada na Terceira Interface do Router 2
            "127.3.1.1": ["127.6.1.1"], #Segunda Interface WAN é conectada na Segunda Interface do Router 6
            "127.3.2.1": ["127.4.0.1"]  #Terceira Interface WAN é conectada na Primeira Interface do Router 4
        }
    }, 
    {
         #Router 4
        "meu_ip": "127.4.0.1",
        "lan": ["127.4.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.4.0.1": ["127.3.2.1"], #Primeira Interface WAN é conectada na Terceira Interface do Router 3
            "127.4.1.1": ["127.5.3.1"]  #Segunda Interface WAN é conectada na Quarta Interface do Router 5 
        }
    },
    {
         #Router 5
        "meu_ip": "127.5.0.1",
        "lan": ["127.5.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.5.0.1": ["127.6.2.1"], #Primeira Interface WAN é conectada na Terceira Interface do Router 6
            "127.5.1.1": ["127.1.1.1"], #Segunda Interface WAN é conectada na segunda Interface do Router 1
            "127.5.2.1": ["127.2.1.1"], #Terceira Interface WAN é conectada na Segunda Interface do Router 2
            "127.5.3.1": ["127.4.1.1"], #Quarta Interface WAN é conectada na Segunda Interface do Router 4 
            "127.5.4.1": ["127.7.0.1"]  #Quinta Interface WAN é conectada na Primeira Interface do Router 7

        }
    },
    {
         #Router 6
        "meu_ip": "127.6.0.1",
        "lan": ["127.6.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.6.0.1": ["127.1.0.1"], #Primeira Interface WAN é conectada na Primeira Interface do Router 1
            "127.6.1.1": ["127.3.1.1"], #Segunda Interface WAN é conectada a Segunda Interface do Router 3
            "127.6.2.1": ["127.5.0.1"]  #Terceira Interface WAN é conectada na Primeira Interface do Router 5
        }
    },
    {
        #Router 7
        "meu_ip": "127.7.0.1",
        "lan": ["127.7.0." + str(i) for i in range(10, 20)],
        "wan": {
            "127.7.0.1": ["127.5.4.1"] #Primeira Interface WAN é conectada na Quinta Interface WAN do Router 5
        }
    },

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
