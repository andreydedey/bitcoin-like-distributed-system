# Bitcoin Blockchain — Nó de Rede Distribuída

Implementação de um nó completo para uma rede blockchain distribuída, inspirada no Bitcoin. Cada instância do programa é um nó independente que se comunica com outros nós via sockets TCP.

## Equipe

- **Andrey Oliveira**
- **Andreya Paiva**

---

## Objetivo

Cada equipe implementa seu próprio nó da rede. Os nós de equipes diferentes devem ser capazes de se comunicar, sincronizar a blockchain e minerar blocos juntos, desde que sigam o protocolo padronizado pela turma.

---

## Estrutura do Projeto

```
bitcoin-like-distributed-system/
├── src/
│   └── blockchain/
│       ├── __init__.py
│       ├── block.py         # Estrutura do bloco e cálculo de hash
│       ├── blockchain.py    # Gerenciamento da cadeia e mempool
│       ├── transaction.py   # Modelo de transação
│       ├── node.py          # Nó P2P (servidor TCP, broadcast, sync)
│       ├── miner.py         # Proof of Work com mineração paralela
│       └── protocol.py      # Protocolo de mensagens (framing + tipos)
├── docs/
│   ├── DOCUMENTACAO.md
│   ├── PADRONIZACAO.md
│   └── PADRONIZACAO_INTEROPERABILIDADE.md
├── main.py                  # Ponto de entrada com menu interativo
├── Dockerfile
├── docker-compose.yml       # Sobe 3 nós locais para teste
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Instalação e Execução

### Sem Docker

```bash
# Instalar dependências
uv sync

# Iniciar um nó isolado
uv run python main.py --port 5000

# Iniciar conectando a outro nó (bootstrap)
uv run python main.py --host 0.0.0.0 --port 5001 --bootstrap localhost:5000
```

### Com Docker (3 nós locais)

```bash
# Sobe node1, node2 e node3 em uma rede interna
docker compose up --build

# Acessar o menu interativo de um nó
docker attach blockchain-node2
```

Os nós 2 e 3 já iniciam conectados ao nó 1 e sincronizam a blockchain automaticamente.

---

## Menu Interativo

Ao iniciar, o nó exibe um menu de linha de comando:

```
==================================================
BITCOIN BLOCKCHAIN - Menu de Comandos
==================================================
1. Criar transação
2. Ver transações pendentes
3. Minerar bloco
4. Ver blockchain
5. Ver saldo
6. Ver peers conectados
7. Conectar a peer
8. Sincronizar blockchain
0. Sair
==================================================
```

---

## Protocolo de Mensagens

Todas as mensagens usam framing TCP com 4 bytes big-endian de tamanho seguidos de JSON UTF-8.

| Tipo | Direção | Descrição |
|------|---------|-----------|
| `NEW_TRANSACTION` | Broadcast | Propaga nova transação para todos os peers |
| `NEW_BLOCK` | Broadcast | Propaga bloco minerado para todos os peers |
| `REQUEST_CHAIN` | Request | Solicita cópia completa da blockchain |
| `RESPONSE_CHAIN` | Response | Responde com a blockchain serializada |
| `PING` | Request | Verifica conectividade e registra o remetente como peer |
| `PONG` | Response | Resposta ao PING |
| `DISCOVER_PEERS` | Request | Solicita lista de peers conhecidos |
| `PEERS_LIST` | Response | Retorna lista de peers para descoberta da rede |

---

## Destaques de Implementação

### Mineração Paralela
O `Miner` divide o espaço de nonces entre 4 threads trabalhadoras usando busca interleaved (worker *i* testa nonces *i*, *i+4*, *i+8*, …). A primeira thread a encontrar um hash válido sinaliza as demais para parar.

### Priorização de Transações
Ao minerar, o nó ordena as transações pendentes por valor decrescente, simulando prioridade por taxa de rede. Uma transação de recompensa (`coinbase → minerador: 50.0`) é sempre incluída no início do bloco.

### Sincronização Robusta
`sync_blockchain` consulta **todos** os peers em vez de parar no primeiro. Coleta candidatos de todos e adota a cadeia válida mais longa dentre todas as respostas.

### Gestão de Peers
- Limite de 20 peers simultâneos (`MAX_PEERS`)
- Rastreamento de falhas por peer: peers com 3+ falhas consecutivas são ignorados no broadcast
- Ao conectar a um novo peer, o nó envia `DISCOVER_PEERS` para aprender outros nós da rede

### Broadcast Randomizado
A lista de peers é embaralhada antes de cada broadcast, evitando um padrão fixo de propagação pela rede.

### Detecção Rápida de Duplicatas
O mempool mantém um `set` de IDs (`_pending_ids`) para verificação de transação duplicada em O(1).

---

## Requisitos do Protocolo

| Parâmetro | Valor |
|-----------|-------|
| Hash | SHA-256, `sort_keys=True` no JSON |
| Dificuldade (PoW) | Hash deve iniciar com `000` |
| Transporte | TCP |
| Framing | 4 bytes big-endian com tamanho + JSON UTF-8 |
| Gênesis `previous_hash` | 64 zeros |
| Gênesis `timestamp` | `0` |
| Recompensa de mineração | 50.0 por bloco |
