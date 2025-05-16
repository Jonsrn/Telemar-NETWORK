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

## 🛡️ `ddos_simulator.py` — Simulador de Ataque DDoS

**Objetivo**

- Submeter um **roteador ou host** a tráfego extremo para analisar gargalos.  
- Registrar **latência média** durante o ataque.

### Execução

```bash
python tests/ddos_simulator.py

```

## ⚙️ `painel_controle.py` — Painel CLI de Gerência

**Objetivo**

- Ajustar **pesos das interfaces** de um roteador em tempo real.  
- Solicitar ao roteador a geração do **grafo** (`grafos/grafo_<ip>.png`).

### Execução

```bash
python tests/painel_controle.py


