import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Any

_BROADCAST_TYPES = frozenset({"NEW_TRANSACTION", "NEW_BLOCK"})


class MessageType(Enum):
    NEW_TRANSACTION = "NEW_TRANSACTION"
    NEW_BLOCK = "NEW_BLOCK"
    REQUEST_CHAIN = "REQUEST_CHAIN"
    RESPONSE_CHAIN = "RESPONSE_CHAIN"
    PING = "PING"
    PONG = "PONG"
    DISCOVER_PEERS = "DISCOVER_PEERS"
    PEERS_LIST = "PEERS_LIST"


@dataclass
class Message:
    type: MessageType
    payload: dict[str, Any] = field(default_factory=dict)
    sender: str = ""

    def to_json(self) -> str:
        return json.dumps(
            {
                "type": self.type.value,
                "payload": self.payload,
                "sender": self.sender,
            }
        )

    @classmethod
    def from_json(cls, data: str) -> "Message":
        parsed = json.loads(data)

        missing = {"type", "payload", "sender"} - parsed.keys()
        if missing:
            raise ValueError(f"Campos obrigatórios ausentes na mensagem: {missing}")

        return cls(
            type=MessageType(parsed["type"]),
            payload=parsed["payload"],
            sender=parsed.get("sender", ""),
        )

    def to_bytes(self) -> bytes:
        encoded = self.to_json().encode("utf-8")
        length_prefix = len(encoded).to_bytes(4, byteorder="big")
        return length_prefix + encoded

    @classmethod
    def from_bytes(cls, data: bytes) -> "Message":
        return cls.from_json(data.decode("utf-8"))

    @property
    def is_broadcast(self) -> bool:
        return self.type.value in _BROADCAST_TYPES

    def validate(self) -> bool:
        required_payload_keys: dict[MessageType, set[str]] = {
            MessageType.NEW_TRANSACTION: {"transaction"},
            MessageType.NEW_BLOCK: {"block"},
            MessageType.RESPONSE_CHAIN: {"blockchain"},
            MessageType.PEERS_LIST: {"peers"},
        }
        expected = required_payload_keys.get(self.type, set())
        return expected.issubset(self.payload.keys())

    def __repr__(self) -> str:
        return (
            f"Message(type={self.type.value!r}, sender={self.sender!r}, "
            f"payload_keys={list(self.payload.keys())})"
        )


class Protocol:
    @classmethod
    def ping(cls) -> Message:
        return Message(type=MessageType.PING, payload={})

    @classmethod
    def pong(cls) -> Message:
        return Message(type=MessageType.PONG, payload={})

    @classmethod
    def discover_peers(cls) -> Message:
        return Message(type=MessageType.DISCOVER_PEERS, payload={})

    @classmethod
    def peers_list(cls, peers: list[str]) -> Message:
        return Message(
            type=MessageType.PEERS_LIST,
            payload={"peers": peers},
        )

    @classmethod
    def new_transaction(cls, transaction_dict: dict) -> Message:
        return Message(
            type=MessageType.NEW_TRANSACTION,
            payload={"transaction": transaction_dict},
        )

    @classmethod
    def new_block(cls, block_dict: dict) -> Message:
        return Message(
            type=MessageType.NEW_BLOCK,
            payload={"block": block_dict},
        )

    @classmethod
    def request_chain(cls) -> Message:
        return Message(type=MessageType.REQUEST_CHAIN, payload={})

    @classmethod
    def response_chain(cls, blockchain_dict: dict) -> Message:
        return Message(
            type=MessageType.RESPONSE_CHAIN,
            payload={"blockchain": blockchain_dict},
        )
