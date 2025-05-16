# 🧪 **Testes Automatizados – diretório `/tests`**

Este diretório agrupa **todas as ferramentas de validação** da Telemar Network.  
Cada script tem um propósito específico (conectividade, resiliência, estresse ou gerenciamento) e **gera artefatos** em `/tests/results/` para documentação posterior.

---

## **Sumário Rápido**

| Script                 | Finalidade                                            | Saídas principais                                          |
| ---------------------- | ----------------------------------------------------- | ---------------------------------------------------------- |
| `ping_total.py`        | Checklist de _ping_ entre **todos** os hosts          | JSON consolidado + gráfico de barras                       |
| `ddos_simulator.py`    | Simula ataque **DDoS** via pings massivos             | Gráfico de oscilação de latência                           |
| `painel_controle.py`   | Ajusta **pesos de links** e gera grafo on-the-fly     | Log no terminal + `.png` no roteador                       |

---

## ✅ `ping_total.py` — Checklist completo de *ping*

### Objetivo
* Confirmar **conectividade plena** da topologia.  
* Medir **latência**, **perda** e gerar **gráficos** de resumo.

### Execução
```bash
```
python tests/ping_total.py


Escolha a topologia desejada quando solicitado.

Aguarde os pings — o script percorre origem × destino^1 (exceto para si mesmo).

^1 Complexidade O(n²). Em topologias grandes pode levar alguns minutos.

Saídas geradas
Tipo	Caminho	Conteúdo
JSON	checklist_ping_CONSOLIDADO_<timestamp>.json	Todos os pings individuais + metadados
PNG	checklist_ping_CONSOLIDADO_<timestamp>_grafico.png	Barras: enviados / recebidos / perdidos por origem

🛡️ ddos_simulator.py — Simulador de Ataque DDoS
Objetivo
Submeter um roteador ou host a tráfego extremo para analisar gargalos.

Registrar latência média durante o ataque.

Execução
bash
Copiar
Editar
python tests/ddos_simulator.py
Fluxo de uso:

Selecione a topologia.

Informe o IP alvo (ex.: 172.101.0.1 ou 172.101.0.10).

O script escalará todos os demais hosts como zumbis e iniciará o bombardeio de pings.

Saídas geradas
Tipo	Caminho	Conteúdo
PNG	ddos_oscilacao_latencia.png	Curva de latência média a cada 10 s (janela deslizante)

No terminal você verá relatórios periódicos do tipo:

yaml
Copiar
Editar
Rodada 3 : 1500 envios (150 pps), 1420 respostas, 80 falhas, latência média 18.4 ms
⚙️ painel_controle.py — Painel CLI de Gerência
Objetivo
Ajustar pesos das interfaces de um roteador enquanto a rede opera.

Solicitar ao roteador a geração do grafo (grafos/grafo_<ip>.png).

Execução
bash
Copiar
Editar
python tests/painel_controle.py
Digite o IP da interface LAN do roteador (ex.: 172.101.0.1).
O script mapeia automaticamente o host _1 daquela LAN para enviar comandos.

Navegue pelo menu:

swift
Copiar
Editar
=== Painel CLI ===
1 – Aumentar peso de TODAS as interfaces
2 – Reduzir  peso de TODAS as interfaces
3 – Gerar imagem do grafo do roteador
0 – Sair
> 
Cada ação envia um pacote CLI interno; o roteador confirma no log, e a imagem do grafo (opção 3) é salva dentro do contêiner roteador (montado em ./grafos).

📦 Requisitos
Topologia já levantada (docker compose up -d).

Bibliotecas Python extras (apenas no host, para geração de gráficos):

bash
Copiar
Editar
pip install matplotlib networkx
🗂️ Pastas de Resultados
Todos os artefatos são depositados em:

text
Copiar
Editar
/tests/results/
├── checklist_ping_CONSOLIDADO_*.json
├── checklist_ping_CONSOLIDADO_*_grafico.png
└── ddos_oscilacao_latencia.png
Mantenha esses arquivos para anexar no relatório final e na apresentação.

🛠️ Dicas Rápidas
Rode docker compose logs -f em paralelo para observar LSA updates enquanto mexe nos pesos.

Combine painel_controle.py + ddos_simulator.py para estudar como a rede se auto-adapta sob estresse e custo variável.

Limpeza completa:

bash
Copiar
Editar
docker compose down -v      # remove volumes e redes
rm -rf tests/results/*      # limpa artefatos
