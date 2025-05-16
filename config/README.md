# 📂 Pasta `config` — Topologias Pré-Definidas

Esta pasta contém **modelos de topologias** em formato `.json`,  
usados pelo `launcher.py` para gerar automaticamente o `docker-compose.yml`.

Cada arquivo define:

- **Roteadores** com suas **interfaces WAN**.
- **Conexões** entre roteadores (enlaces).

## 📐 Exemplos de Topologias

### 🔄 Topologia Circular
![Topologia Circular](../grafos/grafo_topologia_circular.png)

### ➖ Topologia Linear
![Topologia Linear](../grafos/grafo_topologia_linear.png)

### 💎 Topologia Losango
![Topologia Losango](../grafos/grafo_topologia_losango.png)

### 🌐 Topologia Distribuída
![Topologia Distribuída](../grafos/grafo_topologia_distribuida.png)

### ⭐ Topologia Estrela
![grafo_172_106_0_1](https://github.com/user-attachments/assets/b0e42674-8381-4362-8047-d71bfd1c7038)


## ⚠️ Observação
- Sinta-se livre para **adicionar novas topologias**, seguindo o mesmo formato `.json`.
- Estes arquivos são **usados apenas no momento da geração** do `docker-compose.yml`.
