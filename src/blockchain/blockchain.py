from typing import Any

from .block import Block
from .transaction import Transaction


class Blockchain:
    DIFFICULTY = "000"

    def __init__(self):
        self.chain: list[Block] = [Block.create_genesis()]
        self.pending_transactions: list[Transaction] = []
        self._pending_ids: set[str] = set()

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def get_balance(self, address: str) -> float:
        confirmed_txs = [
            tx
            for block in self.chain
            for tx in block.transactions
        ]

        received = sum(tx.valor for tx in confirmed_txs if tx.destino == address)
        sent = sum(tx.valor for tx in confirmed_txs if tx.origem == address)

        return received - sent

    def get_available_balance(self, address: str) -> float:
        confirmed = self.get_balance(address)
        pending_sent = sum(
            tx.valor for tx in self.pending_transactions if tx.origem == address
        )
        return confirmed - pending_sent

    def add_transaction(self, transaction: Transaction) -> bool:
        if transaction.id in self._pending_ids:
            return False

        for block in self.chain:
            for tx in block.transactions:
                if tx.id == transaction.id:
                    return False

        if transaction.origem not in ("genesis", "coinbase"):
            if self.get_available_balance(transaction.origem) < transaction.valor:
                return False

        self.pending_transactions.append(transaction)
        self._pending_ids.add(transaction.id)
        return True

    def add_block(self, block: Block) -> bool:
        if not self.is_valid_block(block):
            return False

        confirmed_ids = {tx.id for tx in block.transactions}
        self.pending_transactions = [
            tx for tx in self.pending_transactions if tx.id not in confirmed_ids
        ]
        self._pending_ids -= confirmed_ids

        self.chain.append(block)
        return True

    def is_valid_block(self, block: Block) -> bool:
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
        if len(new_chain) <= len(self.chain):
            return False

        if not self.is_valid_chain(new_chain):
            return False

        self.chain = new_chain
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Blockchain":
        blockchain = cls()
        blockchain.chain = [Block.from_dict(b) for b in data["chain"]]
        blockchain.pending_transactions = [
            Transaction.from_dict(tx) for tx in data["pending_transactions"]
        ]
        blockchain._pending_ids = {tx.id for tx in blockchain.pending_transactions}
        return blockchain
