# 📂 Pasta `src` — Código-Fonte Principal

Esta pasta contém os **scripts centrais da simulação**.

## 📜 Arquivos

| Arquivo      | Descrição                                                                 |
|--------------|--------------------------------------------------------------------------|
| `host.py`    | Código do **Host** da rede, que executa comandos como ping e traceroute.  |
| `roteador.py`| Código do **Roteador**, que implementa o protocolo de roteamento dinâmico.|

## 🛠️ Funções dos Componentes

- **`host.py`**  
  Simula o comportamento de um terminal de rede.
  - Envia mensagens.
  - Executa PING.
  - Executa TRACEROUTE.
  - Encaminha comandos para o painel de controle.

- **`roteador.py`**  
  Gerencia a comunicação entre redes:
  - Roteamento com estado de enlace.
  - Detecção de falhas via HELLO.
  - Propagação de LSAs.
  - Cálculo de rotas com Dijkstra.
  - Gerenciamento de pesos e geração de topologia.

## ⚠️ Observação

Estes scripts são **executados automaticamente** pelos containers criados via Docker Compose.  
Não é necessário executá-los manualmente fora do ambiente Docker.
