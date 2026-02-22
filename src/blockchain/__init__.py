"""
Blockchain LSD - Criptomoeda Distribuída Simplificada
UFPA - Laboratório de Sistemas Distribuídos

Módulos:
- Block: estrutura de um bloco na cadeia
- Transaction: estrutura de uma transação
- Blockchain: gerenciamento da cadeia e mempool
- Miner: algoritmo de Proof of Work paralelo
- Node: nó P2P com gerenciamento de peers e sincronização
- Protocol / Message / MessageType: protocolo de comunicação entre nós
"""

from .block import Block
from .blockchain import Blockchain
from .transaction import Transaction
from .miner import Miner
from .node import Node
from .protocol import Protocol, Message, MessageType

__version__ = "0.1.0"
__all__ = [
    "Block",
    "Blockchain",
    "Transaction",
    "Miner",
    "Node",
    "Protocol",
    "Message",
    "MessageType",
]
