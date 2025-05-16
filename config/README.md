# 📂 Pasta `config` — Topologias Pré-Definidas

Esta pasta contém **modelos de topologias** em formato `.json`,  
usados pelo `launcher.py` para gerar automaticamente o `docker-compose.yml`.

Cada arquivo define:

- **Roteadores** com suas **interfaces WAN**.
- **Conexões** entre roteadores (enlaces).

## 📐 Exemplos de Topologias

### 🔄 Topologia Circular

![grafo_172_102_0_1](https://github.com/user-attachments/assets/6e9dc248-12db-4850-9aa0-06e11a9b9108)

### ➖ Topologia Linear

![grafo_172_102_0_1](https://github.com/user-attachments/assets/918b62b3-dcbc-424a-9152-bc867a445d91)


### 💎 Topologia Losango

![grafo_172_101_0_1](https://github.com/user-attachments/assets/8e66b974-3a4d-4a4f-ab12-80cdfa4ac38c)


### 🌐 Topologia Distribuída

![grafo_172_102_0_1](https://github.com/user-attachments/assets/1b2c39c7-007b-4afb-96a5-935bcac460dd)


### ⭐ Topologia Estrela
![grafo_172_106_0_1](https://github.com/user-attachments/assets/b0e42674-8381-4362-8047-d71bfd1c7038)


## ⚠️ Observação
- Sinta-se livre para **adicionar novas topologias**, seguindo o mesmo formato `.json`.
- Estes arquivos são **usados apenas no momento da geração** do `docker-compose.yml`.

- ## 🎓 Interpretação das Imagens Geradas

As imagens de topologia geradas pelo simulador representam cada **interface** dos roteadores como **pontos individuais (bolinhas)**.

Essas bolinhas orbitando um mesmo ponto central simulam as **interfaces físicas** de um roteador real, conectadas a diferentes redes.

Essa representação gráfica ilustra como um único roteador pode **administrar múltiplas interfaces** através de seus **barramentos internos**, **encaminhando pacotes entre elas** conforme as rotas calculadas dinamicamente.

> 📌 Exemplo:  
> Na imagem abaixo, as bolinhas que estão dentro do mesmo círculo representam os barramentos internos de um mesmo roteador, formando seu conjunto de interfaces:

![Captura de tela 2025-05-16 001710](https://github.com/user-attachments/assets/0973769b-53bf-4d44-8478-bcc2657d8868)


