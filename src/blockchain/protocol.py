"""
Módulo de Protocolo de Comunicação

Define o formato das mensagens trocadas entre nós da rede P2P.
O protocolo é compatível com todas as implementações do grupo, desde que:
  - O framing seja: [4 bytes big-endian com o tamanho][JSON UTF-8]
  - Os campos da mensagem sejam: "type", "payload", "sender"
  - Os valores de MessageType correspondam às strings definidas abaixo
"""

import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Any

# Tipos de mensagem broadcast (propagadas para a rede)
_BROADCAST_TYPES = frozenset({"NEW_TRANSACTION", "NEW_BLOCK"})


class MessageType(Enum):
    """
    Tipos de mensagens do protocolo.

    Broadcast (propagadas para todos os peers):
    - NEW_TRANSACTION: envio de uma nova transação
    - NEW_BLOCK: envio de um bloco minerado

    Request/Response (comunicação direta entre dois nós):
    - REQUEST_CHAIN / RESPONSE_CHAIN: sincronização de blockchain
    - PING / PONG: verificação de conectividade
    - DISCOVER_PEERS / PEERS_LIST: descoberta de nós na rede
    """

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
    """
    Representa uma mensagem do protocolo P2P.

    Atributos:
    - type: tipo da mensagem (MessageType)
    - payload: dados específicos do tipo de mensagem
    - sender: endereço "host:port" do remetente
    """

    type: MessageType
    payload: dict[str, Any] = field(default_factory=dict)
    sender: str = ""

    # ------------------------------------------------------------------
    # Protocolo: estes métodos definem o formato wire. NÃO alterar
    # campos, encoding ou ordem de serialização.
    # ------------------------------------------------------------------

    def to_json(self) -> str:
        """Serializa a mensagem para JSON."""
        return json.dumps(
            {
                "type": self.type.value,
                "payload": self.payload,
                "sender": self.sender,
            }
        )

    @classmethod
    def from_json(cls, data: str) -> "Message":
        """Deserializa mensagem a partir de JSON, validando campos obrigatórios."""
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
        """
        Serializa a mensagem para bytes prontos para envio via socket.

        Formato: [4 bytes big-endian com o comprimento do JSON][JSON em UTF-8]
        """
        encoded = self.to_json().encode("utf-8")
        length_prefix = len(encoded).to_bytes(4, byteorder="big")
        return length_prefix + encoded

    @classmethod
    def from_bytes(cls, data: bytes) -> "Message":
        """Cria mensagem a partir de bytes (sem o prefixo de tamanho)."""
        return cls.from_json(data.decode("utf-8"))

    # ------------------------------------------------------------------
    # Utilidades internas (não afetam o protocolo)
    # ------------------------------------------------------------------

    @property
    def is_broadcast(self) -> bool:
        """Retorna True se a mensagem deve ser propagada para todos os peers."""
        return self.type.value in _BROADCAST_TYPES

    def validate(self) -> bool:
        """
        Valida se a mensagem está estruturalmente correta para o seu tipo.

        Verifica se os campos obrigatórios do payload estão presentes
        de acordo com o tipo da mensagem.
        """
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
    """
    Factory de mensagens do protocolo P2P.

    Cada método retorna uma Message com o tipo e payload corretos.
    O campo sender é preenchido pelo Node antes do envio.
    """

    @classmethod
    def ping(cls) -> Message:
        """Cria mensagem de verificação de conectividade."""
        return Message(type=MessageType.PING, payload={})

    @classmethod
    def pong(cls) -> Message:
        """Cria resposta de verificação de conectividade."""
        return Message(type=MessageType.PONG, payload={})

    @classmethod
    def discover_peers(cls) -> Message:
        """Cria mensagem de solicitação de peers conhecidos."""
        return Message(type=MessageType.DISCOVER_PEERS, payload={})

    @classmethod
    def peers_list(cls, peers: list[str]) -> Message:
        """Cria mensagem com lista de peers conhecidos."""
        return Message(
            type=MessageType.PEERS_LIST,
            payload={"peers": peers},
        )

    @classmethod
    def new_transaction(cls, transaction_dict: dict) -> Message:
        """Cria mensagem de broadcast de nova transação."""
        return Message(
            type=MessageType.NEW_TRANSACTION,
            payload={"transaction": transaction_dict},
        )

    @classmethod
    def new_block(cls, block_dict: dict) -> Message:
        """Cria mensagem de broadcast de bloco minerado."""
        return Message(
            type=MessageType.NEW_BLOCK,
            payload={"block": block_dict},
        )

    @classmethod
    def request_chain(cls) -> Message:
        """Cria mensagem de solicitação da blockchain completa."""
        return Message(type=MessageType.REQUEST_CHAIN, payload={})

    @classmethod
    def response_chain(cls, blockchain_dict: dict) -> Message:
        """Cria mensagem de resposta com a blockchain serializada."""
        return Message(
            type=MessageType.RESPONSE_CHAIN,
            payload={"blockchain": blockchain_dict},
        )
