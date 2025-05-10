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
- A confiabilidade é gerenciada na camada de aplicação.
- A velocidade de propagação das informações de estado de enlace é mais importante que a confirmação garantida de entrega.
- Reduz a sobrecarga de conexão e controle.

---

## 🌐 Como Funciona a Topologia

A rede é composta por **múltiplas subredes**, cada uma contendo:
- **2 Hosts**
- **1 Roteador**

Os roteadores se interconectam em **topologias configuráveis via arquivos JSON** na pasta `/config`.  
Exemplos:
- Topologia em **anel**, **linear**, **losango**, ou **personalizada**.

---

## 🚀 Como Executar o Projeto

### 1. Gere a Topologia Desejada
Escolha um arquivo `.json` da pasta `/config` ou crie o seu seguindo o padrão.

### 2. Gere o docker-compose.yml
```bash
python launcher.py
