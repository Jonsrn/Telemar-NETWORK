# 🗺️ Pasta /grafos

## 📋 Descrição

Esta pasta é utilizada para armazenar as **visualizações gráficas** da **topologia da rede em tempo real**.

Sempre que um comando é enviado pelo **painel de controle** solicitando a geração de um grafo, o roteador cria uma imagem representando a sua visão atual da topologia e salva aqui. Essa geração também ocorre automaticamente a cada inicialização do programa, capturando imagens do grafo de cada roteador e sua visão relativa da topologia.

---

## 📸 Conteúdo

- **grafo_<ip>.png**  
  Representa a visão local do roteador identificado por `<ip>`, com todas as interfaces e enlaces conhecidos no momento da captura.

---

## 🛰️ Sobre as Imagens

- Cada **círculo azul** representa uma **interface de rede** (WAN ou LAN) de um roteador.
- Os **pontos cinza** conectando as interfaces representam as **ligações internas** de um roteador.
- As **interfaces orbitando um ponto central** ilustram que **todas pertencem ao mesmo roteador físico**, simulando o conceito de **barramento interno**.

---

## ⚠️ Observações

- As imagens se atualizam automaticamente a cada execução.  
- As imagens são sobrescritas a cada nova captura com o mesmo IP.
- Utilize estas imagens para documentar o **estado da rede** em diferentes momentos da simulação.
