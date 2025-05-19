# 🛰️ Telemar Network – Simulador de Rede com Roteamento de Estado de Enlace

## 📋 Descrição do Projeto

Este projeto consiste em uma simulação completa de uma rede de computadores baseada em roteadores e hosts, com roteamento dinâmico implementado em **Python** e **Docker**.  
Cada roteador utiliza o **algoritmo de estado de enlace (Link State Routing Algorithm)**, com **troca de LSAs (Link State Advertisements)**, construção de **LSDBs (Link State Database)** e cálculo das rotas com **Dijkstra**.

A arquitetura é modular, permitindo simular **topologias personalizadas**, realizar **ping entre hosts**, executar **traceroute** e até simular **ataques DDoS**.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.12** – Lógica dos roteadores, hosts e simulações.
- **Docker** – Isolamento de cada roteador e host em containers independentes.
- **Docker Compose** – Geração dinâmica da infraestrutura da rede.
- **UDP (User Datagram Protocol)** – Utilizado para a comunicação entre os roteadores.

### 🎯 Justificativa da Escolha do Protocolo (UDP)

Optou-se pelo **UDP** devido à sua **baixa latência** e **simplicidade**, que o tornam ideal para protocolos de roteamento onde:
- **Baixa sobrecarga de controle**, ideal para ambientes simulados e cenários de roteamento dinâmico.
- **Comunicação sem conexão**, permitindo maior desempenho na troca de pacotes de controle (HELLO, LSA, etc.).
- **Maior escalabilidade e simplicidade**, reduzindo a complexidade da simulação em Docker.
- A **velocidade** de propagação das informações de estado de enlace é mais importante que a confirmação garantida de entrega.
- **Reduz a sobrecarga** de conexão e controle.


---

## 🌐 Como Funciona a Topologia

A rede é composta por **múltiplas subredes**, cada uma contendo:
- **2 Hosts**
- **1 Roteador**

As topologias de rede utilizadas neste simulador são **definidas por arquivos JSON** presentes na pasta `/config`.  
Esses arquivos descrevem:

- **As interfaces WAN de cada roteador** e seus **vizinhos diretamente conectados**.
- A **estrutura lógica da interconexão da rede**.

O launcher do projeto lê esses arquivos e gera automaticamente o `docker-compose.yml`, conectando cada roteador às suas respectivas WANs e LANs.  
Isso permite a simulação de diferentes cenários, como:

- **Topologias em linha**, **anel**, **estrela**, **distribuída** e **losango**.

## 📊 Resumo das Capacidades do Sistema

- ✅ **Limiar de Estresse:** Testado com topologias de **3, 6 e 9 roteadores**. O sistema se mostrou estável, inclusive sob estresse extremo com **17 hosts zumbis atacando simultaneamente** um único roteador central.
- ✅ **Vantagens:** Abordagem modular, comunicação realista via sockets, controle de pesos em tempo real e alta escalabilidade para diferentes topologias.
- ✅ **Desvantagens:** Consumo crescente de CPU e memória ao simular redes muito grandes em um hardware limitado.
- ✅ **Alcance do PING:** Comprovação de que **qualquer host pode alcançar qualquer outro**, mesmo em redes com múltiplos saltos, desde que a topologia esteja devidamente configurada.


## 🚀 Como Executar o Projeto

### 1. Gere a Topologia Desejada
Escolha um arquivo `.json` da pasta `/config` ou crie o seu seguindo o padrão.

### 2. Gere o docker-compose.yml
```bash
python launcher.py
```

### 3. Suba a infraestrutura com Docker Compose
```bash
docker compose up --build -d
```

### 4. Interaja com os containers manualmente (opcional)
```bash
docker exec -it host1_1 bash
```

Ou utilize os **scripts de teste** descritos abaixo para automação.

---

## 🧪 Scripts de Teste

### ✅ Checklist de Ping Total
Executa pings entre todos os hosts da topologia, gerando relatórios e gráficos de latência e perda.

```bash
python tests/ping_total.py
```

- Os resultados são salvos na pasta:
  - `/tests/results/`

### 🛡️ Simulador de Ataques DDoS
Executa um ataque distribuído ao alvo especificado, monitorando o comportamento da rede sob estresse.

```bash
python tests/ddos_simulator.py
```

- Permite escolher dinamicamente o alvo do ataque (host ou roteador).

---

## 📊 Relatórios e Gráficos

Ao final de cada teste, os seguintes arquivos são gerados em `/tests/results`:

- **Arquivo JSON** com os resultados detalhados de cada host.
- **Gráfico de latência** (`.png`).
- **Gráfico de perda de pacotes** (`.png`).

---

## 🛰️ Comunicação Entre Hosts

✅ Comunicação de **qualquer host para qualquer outro** da rede, mesmo em diferentes roteadores, via roteamento dinâmico.

✅ Suporte a **multihop** com atualizações automáticas de topologia.

---

## ⚙️ Recursos Implementados

- ✅ Roteamento dinâmico com algoritmo de estado de enlace (Dijkstra).
- ✅ Detecção de falhas com protocolo HELLO.
- ✅ Propagação de LSAs para toda a rede.
- ✅ Visualização gráfica da topologia em tempo real.
- ✅ Comando **PING** com métricas reais de latência e perda.
- ✅ Comando **TRACEROUTE** simulando saltos e TTL.
- ✅ **Simulador de DDoS** com monitoramento contínuo.
- ✅ **Docker Compose** para gerar e isolar topologias completas.

---

## ⚠️ Observações

- Requer Docker e Docker Compose instalados.
- Scripts de análise utilizam `matplotlib` e `networkx`.
- A visualização gráfica não abre janelas interativas, apenas gera arquivos `.png`.

---

## 📝 Histórico
Consulte o arquivo [`CHANGELOG.md`](CHANGELOG.md) para detalhes da evolução do projeto.

---

## 📂 Leia também

- [`/src`](./src) – Código-fonte principal do simulador (hosts e roteadores).
- [`/config`](./config) – Topologias de rede pré-definidas (formato JSON).
- [`/tests`](./tests) – Scripts de teste, simulação e análise de desempenho.
- [`/grafos`](./grafos) – Imagens geradas da topologia da rede em tempo real.
