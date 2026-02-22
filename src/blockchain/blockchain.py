"""
Módulo da Blockchain
"""

from typing import Any

from .block import Block
from .transaction import Transaction


class Blockchain:
    """
    Gerencia a cadeia de blocos e transações pendentes.

    Responsabilidades:
    - Manter a cadeia de blocos válida
    - Gerenciar pool de transações pendentes
    - Validar blocos e transações
    - Calcular saldos

    Otimizações internas:
    - _pending_ids: set de IDs para detecção de duplicatas em O(1)
    - get_balance usa expressões geradoras ao invés de loops imperativos
    - add_block remove pendentes com list comprehension (O(n)) em vez de remove() (O(n²))
    """

    DIFFICULTY = "000"  # Hash deve começar com 000

    def __init__(self):
        self.chain: list[Block] = [Block.create_genesis()]
        self.pending_transactions: list[Transaction] = []
        self._pending_ids: set[str] = set()  # Lookup rápido por ID

    @property
    def last_block(self) -> Block:
        """Retorna o último bloco da cadeia."""
        return self.chain[-1]

    def get_balance(self, address: str) -> float:
        """
        Calcula o saldo de um endereço.

        Agrega todas as transações da cadeia e do mempool em uma única lista
        e usa sum() com expressões geradoras para calcular entradas e saídas.
        """
        all_txs = [
            tx
            for block in self.chain
            for tx in block.transactions
        ] + self.pending_transactions

        received = sum(tx.valor for tx in all_txs if tx.destino == address)
        sent = sum(tx.valor for tx in all_txs if tx.origem == address)

        return received - sent

    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Adiciona uma transação ao pool de pendentes.

        Usa _pending_ids (set) para detecção de duplicata em O(1).
        Valida saldo antes de aceitar.
        """
        # Verificação de duplicata no mempool: O(1)
        if transaction.id in self._pending_ids:
            return False

        # Verificação de duplicata na cadeia
        for block in self.chain:
            for tx in block.transactions:
                if tx.id == transaction.id:
                    return False

        # Verifica saldo (exceto para origem "genesis" ou "coinbase")
        if transaction.origem not in ("genesis", "coinbase"):
            balance = self.get_balance(transaction.origem)
            if balance < transaction.valor:
                return False

        self.pending_transactions.append(transaction)
        self._pending_ids.add(transaction.id)
        return True

    def add_block(self, block: Block) -> bool:
        """
        Adiciona um bloco à cadeia após validação.

        Remove transações confirmadas do mempool via list comprehension
        (uma passagem O(n)) em vez de chamadas remove() repetidas (O(n²)).
        """
        if not self.is_valid_block(block):
            return False

        # Remove transações confirmadas do mempool em uma única passagem
        confirmed_ids = {tx.id for tx in block.transactions}
        self.pending_transactions = [
            tx for tx in self.pending_transactions if tx.id not in confirmed_ids
        ]
        self._pending_ids -= confirmed_ids

        self.chain.append(block)
        return True

    def is_valid_block(self, block: Block) -> bool:
        """Valida um bloco antes de adicionar à cadeia."""
        if block.index != len(self.chain):
            return False

        if block.previous_hash != self.last_block.hash:
            return False

        if not block.hash.startswith(self.DIFFICULTY):
            return False

        if block.hash != block.calculate_hash():
            return False

        return True

    def is_valid_chain(self, chain: list[Block] = None) -> bool:
        """
        Valida toda a cadeia de blocos.

        Verifica:
        - Bloco gênesis correto
        - Encadeamento de hashes
        - Proof of Work de cada bloco
        """
        if chain is None:
            chain = self.chain

        if not chain:
            return False

        genesis = Block.create_genesis()
        if chain[0].hash != genesis.hash:
            return False

        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i - 1]

            if current.previous_hash != previous.hash:
                return False

            if current.hash != current.calculate_hash():
                return False

            if not current.hash.startswith(self.DIFFICULTY):
                return False

        return True

    def replace_chain(self, new_chain: list[Block]) -> bool:
        """
        Substitui a cadeia atual por uma nova (mais longa e válida).

        Usado para resolução de conflitos (cadeia mais longa vence).
        """
        if len(new_chain) <= len(self.chain):
            return False

        if not self.is_valid_chain(new_chain):
            return False

        self.chain = new_chain
        return True

    def to_dict(self) -> dict[str, Any]:
        """Converte blockchain para dicionário (serialização JSON)."""
        return {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Blockchain":
        """Cria blockchain a partir de dicionário."""
        blockchain = cls()
        blockchain.chain = [Block.from_dict(b) for b in data["chain"]]
        blockchain.pending_transactions = [
            Transaction.from_dict(tx) for tx in data["pending_transactions"]
        ]
        # Reconstrói o índice de IDs a partir das transações desserializadas
        blockchain._pending_ids = {tx.id for tx in blockchain.pending_transactions}
        return blockchain
