"""
Módulo de Transações
"""

import math
import uuid
import time
from dataclasses import dataclass, field
from typing import Any

# Endereços reservados pelo sistema (não precisam ter saldo para enviar)
_SYSTEM_ADDRESSES = frozenset({"genesis", "coinbase"})


@dataclass
class Transaction:
    """
    Representa uma transação na blockchain.

    Campos obrigatórios:
    - origem: endereço de origem (quem envia)
    - destino: endereço de destino (quem recebe)
    - valor: quantidade transferida (deve ser > 0 e finito)
    - id: identificador único UUID v4 (gerado automaticamente)
    - timestamp: momento da criação (Unix epoch)

    Invariantes verificadas no __post_init__:
    - valor deve ser positivo e finito (sem NaN ou Inf)
    - origem e destino são strings não-vazias
    - origem e destino não podem ser iguais (exceto endereços de sistema)
    """

    origem: str
    destino: str
    valor: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        """Valida a transação após criação."""
        if not isinstance(self.valor, (int, float)):
            raise TypeError(f"valor deve ser numérico, recebido: {type(self.valor)}")
        if self.valor <= 0:
            raise ValueError(f"valor deve ser positivo, recebido: {self.valor}")
        if not math.isfinite(self.valor):
            raise ValueError(f"valor deve ser finito, recebido: {self.valor}")
        if not self.origem or not isinstance(self.origem, str):
            raise ValueError("origem é obrigatória e deve ser uma string não-vazia")
        if not self.destino or not isinstance(self.destino, str):
            raise ValueError("destino é obrigatório e deve ser uma string não-vazia")
        if (
            self.origem == self.destino
            and self.origem not in _SYSTEM_ADDRESSES
        ):
            raise ValueError("origem e destino não podem ser o mesmo endereço")

    # ------------------------------------------------------------------
    # Protocolo: estes métodos NÃO podem ser alterados para manter
    # compatibilidade entre grupos (serialização e identidade da tx).
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Converte transação para dicionário (serialização JSON)."""
        return {
            "id": self.id,
            "origem": self.origem,
            "destino": self.destino,
            "valor": self.valor,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        """Cria transação a partir de dicionário."""
        return cls(
            id=data["id"],
            origem=data["origem"],
            destino=data["destino"],
            valor=data["valor"],
            timestamp=data["timestamp"],
        )

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Transaction):
            return self.id == other.id
        return False

    # ------------------------------------------------------------------
    # Utilidades internas (não afetam o protocolo)
    # ------------------------------------------------------------------

    def is_coinbase(self) -> bool:
        """Retorna True se esta é uma transação de recompensa de mineração."""
        return self.origem == "coinbase"

    def is_genesis(self) -> bool:
        """Retorna True se esta transação partiu do endereço genesis."""
        return self.origem == "genesis"

    def is_system(self) -> bool:
        """Retorna True se a origem é um endereço reservado do sistema."""
        return self.origem in _SYSTEM_ADDRESSES

    @property
    def age(self) -> float:
        """Retorna o tempo em segundos desde a criação da transação."""
        return time.time() - self.timestamp

    def __str__(self) -> str:
        return (
            f"Transaction({self.origem} → {self.destino} : {self.valor:.4f} "
            f"| id={self.id[:8]}...)"
        )

    def __repr__(self) -> str:
        return (
            f"Transaction(id={self.id!r}, origem={self.origem!r}, "
            f"destino={self.destino!r}, valor={self.valor})"
        )
