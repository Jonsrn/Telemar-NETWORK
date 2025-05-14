# Telemar Network - Linha do Tempo e Evolução

Este documento apresenta a linha do tempo da evolução da Telemar Network, um simulador de rede em Python com suporte a roteamento dinâmico, detecção de falhas, traceroute, ping e visualização gráfica.

### 🧠 Fase Conceitual e Protótipo Inicial

## ✨ Versão 1.0

Estrutura inicial com roteadores básicos e algoritmo de Dijkstra.

Cada roteador tinha apenas uma interface.

Comunicacão era feita por portas distintas.

Topologia pré-definida e estática.

### 🧪 Fase de Expansão Estrutural

## ✨ Versão 2.0

Roteadores com múltiplas interfaces LAN e WAN.

Suporte a multi-hop e rotação entre interfaces internas.

Estrutura de grafo adaptada para representar a nova topologia.

## ✨ Versão 2.5

Implementação do comando PING com TTL e estatísticas realistas.

Comunicação interna consolidada.

### 🗺️ Fase de Autodescoberta

## ✨ Versão 3.0

Introdução do protocolo HELLO e troca de LSAs.

Cada roteador constrói dinamicamente sua visão da rede.

O grafo é propagado em tempo real com atualizações de topologia.

### ⚙️ Fase Interativa

## ✨ Versão 4.0

Transição para endereçamento IP real (127.X.Y.Z).

Porta fixa 5000 para todos os sockets.

Simulação realista de subredes IP.

## ✨ Versões 4.1 ~ 4.3

Consolidação da comunicação baseada em IP.

Separadas interfaces LAN e WAN corretamente.

Roteamento entre subredes já funcional.

## ✨ Versões 4.4 ~ 4.6

Implementação do painel de controle CLI.

Comandos para alterar pesos dinâmicos nas interfaces WAN.

LSAs agora propagam atualizações de peso.

## ✨ Versão 4.7

Adicionada funcionalidade TRACEROUTE completa:

Respostas a cada salto

TTL decremental

## ✨ Versão 4.8

Gráfico redesenhado com visualização por hubs e interfaces orbitais.

Conjuntos de interfaces representadas como pólos de conexão.

Arestas internas com peso 0 agrupam roteadores visualmente.

## 🌏 Versão 4.9 Estável: Roteamento Realista

Roteamento entre IPs de subredes iguais (✓)

Hosts de diferentes LANs agora se comunicam corretamente.

TRACEROUTE agora alcança hosts finais.

Grafo atualizado reflete corretamente os roteadores e suas subredes.

### 🐳 Fase Dockerizada e Testes Automatizados

## ✨ Versão 5.0

Migração completa para Docker, com cada roteador e host executando em containers independentes.

Geração dinâmica do docker-compose.yml a partir da topologia em JSON.

Manutenção da estrutura de roteamento dinâmico com Dijkstra e LSDB.

Execução interativa por terminal via docker exec.

Suporte total a PING e TRACEROUTE em ambiente Dockerizado.

## ✨ Versão 5.1

Otimização do Dockerfile, reduzindo o tamanho dos containers de ~895 MB para ~295 MB.

Scripts de Teste Automatizados para:

Checklist de PING entre todos os hosts da topologia.

Geração de gráficos de latência e perda de pacotes.

Simulador de Ataques DDoS:

-Disparo massivo de pings simultâneos simulando ataque distribuído.

-Monitoramento em tempo real da capacidade da rede sob carga.

-Registro dos resultados em arquivos JSON e gráficos no diretório /tests/results.

## ✨ Versão 5.2

Conversão Completa para Programação Orientada a Objetos (POO):

Host e Roteador reescritos como classes Python com métodos encapsulados.

Lógica e comportamento preservados, garantindo compatibilidade total com as versões anteriores.

Modularização das funcionalidades:

Protocolo HELLO, LSA e Dijkstra encapsulados em métodos.

Processamento de pacotes separado por tipo (CLI, LSA, HELLO, ping, traceroute, etc).

Inicialização e controle centralizado no método start().

Preparação para futuras expansões, facilitando manutenção e evolução da arquitetura.

## ✨ Versão 5.3

Substituição do Algoritmo de Dijkstra por Implementação Própria:

-Implementação completa do algoritmo de Dijkstra sem dependência do NetworkX.

-Substituição de todas as chamadas de cálculo de rotas para utilizar a nova implementação.

-Manutenção de todas as funcionalidades existentes (roteamento dinâmico, PING, TRACEROUTE, atualização de pesos).

-Preparação para futuras otimizações e customizações no algoritmo de roteamento.

