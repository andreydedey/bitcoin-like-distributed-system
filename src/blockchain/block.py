"""
Módulo de Blocos
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

from .transaction import Transaction


@dataclass
class Block:
    """
    Representa um bloco na blockchain.

    Campos obrigatórios:
    - index: índice do bloco na cadeia (>= 0)
    - previous_hash: hash SHA-256 do bloco anterior (64 hex chars)
    - transactions: lista de transações incluídas no bloco
    - nonce: valor encontrado no Proof of Work
    - timestamp: momento da criação (Unix epoch)
    - hash: hash SHA-256 deste bloco (calculado após criação)

    Invariantes verificadas no __post_init__:
    - index deve ser >= 0
    - previous_hash deve ter exatamente 64 caracteres hexadecimais
    """

    index: int
    previous_hash: str
    transactions: list[Transaction]
    nonce: int = 0
    timestamp: float = field(default_factory=time.time)
    hash: str = ""

    def __post_init__(self):
        """Valida campos obrigatórios e calcula hash se não fornecido."""
        if self.index < 0:
            raise ValueError(f"Índice do bloco deve ser >= 0, recebido: {self.index}")
        if len(self.previous_hash) != 64:
            raise ValueError(
                f"previous_hash deve ter 64 chars, recebido: {len(self.previous_hash)}"
            )
        if not self.hash:
            self.hash = self.calculate_hash()

    # ------------------------------------------------------------------
    # Protocolo: estes métodos NÃO podem ser alterados para manter
    # compatibilidade entre grupos (hash, serialização, genesis).
    # ------------------------------------------------------------------

    def calculate_hash(self) -> str:
        """
        Calcula o hash SHA-256 do bloco.

        Usa sort_keys=True para garantir resultado idêntico em qualquer
        implementação, independentemente da ordem dos campos no dicionário.
        """
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
        """Converte bloco para dicionário (serialização JSON)."""
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
        """Cria bloco a partir de dicionário."""
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
        """
        Cria o bloco gênesis (primeiro bloco da cadeia).

        Timestamp fixo em 0 e previous_hash de 64 zeros garantem que o
        hash do gênesis seja idêntico em todas as implementações.
        """
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
        """
        Verifica se o hash satisfaz o requisito de dificuldade (Proof of Work).

        Compara os primeiros len(difficulty) caracteres do hash com a
        dificuldade exigida, em vez de usar startswith para ser explícito
        sobre o número de caracteres verificados.
        """
        prefix_len = len(difficulty)
        return self.hash[:prefix_len] == difficulty

    # ------------------------------------------------------------------
    # Utilidades internas (não afetam o protocolo)
    # ------------------------------------------------------------------

    @property
    def transaction_count(self) -> int:
        """Retorna o número de transações no bloco."""
        return len(self.transactions)

    @property
    def age(self) -> float:
        """Retorna o tempo em segundos desde a criação do bloco."""
        return time.time() - self.timestamp

    def is_genesis(self) -> bool:
        """Retorna True se este bloco é o bloco gênesis."""
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
