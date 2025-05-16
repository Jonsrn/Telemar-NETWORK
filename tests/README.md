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


