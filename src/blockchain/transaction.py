import math
import uuid
import time
from dataclasses import dataclass, field
from typing import Any

_SYSTEM_ADDRESSES = frozenset({"genesis", "coinbase"})


@dataclass
class Transaction:
    origem: str
    destino: str
    valor: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
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
        if self.origem == self.destino and self.origem not in _SYSTEM_ADDRESSES:
            raise ValueError("origem e destino não podem ser o mesmo endereço")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "origem": self.origem,
            "destino": self.destino,
            "valor": self.valor,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
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

    def is_coinbase(self) -> bool:
        return self.origem == "coinbase"

    def is_genesis(self) -> bool:
        return self.origem == "genesis"

    def is_system(self) -> bool:
        return self.origem in _SYSTEM_ADDRESSES

    @property
    def age(self) -> float:
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
