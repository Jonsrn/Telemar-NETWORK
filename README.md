Telemar Network - Linha do Tempo e Evolução

Este documento apresenta a linha do tempo da evolução da Telemar Network, um simulador de rede em Python com suporte a roteamento dinâmico, detecção de falhas, traceroute, ping e visualização gráfica.

🧠 Fase Conceitual e Protótipo Inicial

✨ Versão 1.0

Estrutura inicial com roteadores básicos e algoritmo de Dijkstra.

Cada roteador tinha apenas uma interface.

Comunicacão era feita por portas distintas.

Topologia pré-definida e estática.

🧪 Fase de Expansão Estrutural

✨ Versão 2.0

Roteadores com múltiplas interfaces LAN e WAN.

Suporte a multi-hop e rotação entre interfaces internas.

Estrutura de grafo adaptada para representar a nova topologia.

✨ Versão 2.5

Implementação do comando PING com TTL e estatísticas realistas.

Comunicação interna consolidada.

🗺️ Fase de Autodescoberta

✨ Versão 3.0

Introdução do protocolo HELLO e troca de LSAs.

Cada roteador constrói dinamicamente sua visão da rede.

O grafo é propagado em tempo real com atualizações de topologia.

⚙️ Fase Interativa

✨ Versão 4.0

Transição para endereçamento IP real (127.X.Y.Z).

Porta fixa 5000 para todos os sockets.

Simulação realista de subredes IP.

✨ Versões 4.1 ~ 4.3

Consolidação da comunicação baseada em IP.

Separadas interfaces LAN e WAN corretamente.

Roteamento entre subredes já funcional.

✨ Versões 4.4 ~ 4.6

Implementação do painel de controle CLI.

Comandos para alterar pesos dinâmicos nas interfaces WAN.

LSAs agora propagam atualizações de peso.

✨ Versão 4.7

Adicionada funcionalidade TRACEROUTE completa:

Respostas a cada salto

TTL decremental

✨ Versão 4.8

Gráfico redesenhado com visualização por hubs e interfaces orbitais.

Conjuntos de interfaces representadas como pólos de conexão.

Arestas internas com peso 0 agrupam roteadores visualmente.

🌏 Versão 4.9 Estável: Roteamento Realista

Roteamento entre IPs de subredes iguais (✓)

Hosts de diferentes LANs agora se comunicam corretamente.

TRACEROUTE agora alcança hosts finais.

Grafo atualizado reflete corretamente os roteadores e suas subredes.

Sistema considerado robusto e pronto para migração ao Docker.
