import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

from .transaction import Transaction


@dataclass
class Block:
    index: int
    previous_hash: str
    transactions: list[Transaction]
    nonce: int = 0
    timestamp: float = field(default_factory=time.time)
    hash: str = ""

    def __post_init__(self):
        if self.index < 0:
            raise ValueError(f"Índice do bloco deve ser >= 0, recebido: {self.index}")
        if len(self.previous_hash) != 64:
            raise ValueError(
                f"previous_hash deve ter 64 chars, recebido: {len(self.previous_hash)}"
            )
        if not self.hash:
            self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_data = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "timestamp": self.timestamp,
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Block":
        transactions = [Transaction.from_dict(tx) for tx in data["transactions"]]
        return cls(
            index=data["index"],
            previous_hash=data["previous_hash"],
            transactions=transactions,
            nonce=data["nonce"],
            timestamp=data["timestamp"],
            hash=data["hash"],
        )

    @classmethod
    def create_genesis(cls) -> "Block":
        genesis = cls(
            index=0,
            previous_hash="0" * 64,
            transactions=[],
            nonce=0,
            timestamp=0,
        )
        genesis.hash = genesis.calculate_hash()
        return genesis

    def is_valid_hash(self, difficulty: str = "000") -> bool:
        prefix_len = len(difficulty)
        return self.hash[:prefix_len] == difficulty

    @property
    def transaction_count(self) -> int:
        return len(self.transactions)

    @property
    def age(self) -> float:
        return time.time() - self.timestamp

    def is_genesis(self) -> bool:
        return self.index == 0 and self.previous_hash == "0" * 64

    def __str__(self) -> str:
        return (
            f"Block(#{self.index} | txs={self.transaction_count} "
            f"| nonce={self.nonce} | hash={self.hash[:12]}...)"
        )

    def __repr__(self) -> str:
        return (
            f"Block(index={self.index}, nonce={self.nonce}, "
            f"transactions={self.transaction_count}, hash={self.hash[:16]!r})"
        )
