import random
import socket
import threading
import logging
from typing import Callable

from .blockchain import Blockchain
from .block import Block
from .transaction import Transaction
from .miner import Miner
from .protocol import Protocol, Message, MessageType


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class Node:
    BUFFER_SIZE = 65536
    MAX_PEERS = 20
    MAX_FAILURES = 3

    def __init__(self, host: str = "localhost", port: int = 5000):
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"
        self.wallet = self.address

        self.blockchain = Blockchain()
        self.miner = Miner(self.blockchain, self.wallet)

        self.peers: set[str] = set()
        self._peer_failures: dict[str, int] = {}
        self.server_socket: socket.socket | None = None
        self.running = False

        self.logger = logging.getLogger(f"Node:{port}")

        self.on_new_block: Callable[[Block], None] | None = None
        self.on_new_transaction: Callable[[Transaction], None] | None = None

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.port))
        self.server_socket.listen(10)

        self.running = True
        self.logger.info(f"Nó iniciado em {self.address}")

        accept_thread = threading.Thread(target=self._accept_connections)
        accept_thread.daemon = True
        accept_thread.start()

    def stop(self):
        self.running = False
        self.miner.stop_mining()
        if self.server_socket:
            self.server_socket.close()
        self.logger.info("Nó encerrado")

    def _accept_connections(self):
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.running:
                    self.logger.error(f"Erro ao aceitar conexão: {e}")

    def _handle_client(self, client_socket: socket.socket, address: tuple):
        try:
            length_data = client_socket.recv(4)
            if not length_data:
                return

            length = int.from_bytes(length_data, 'big')

            data = b""
            while len(data) < length:
                chunk = client_socket.recv(min(self.BUFFER_SIZE, length - len(data)))
                if not chunk:
                    break
                data += chunk

            if data:
                message = Message.from_bytes(data)
                response = self._process_message(message)

                if response:
                    client_socket.sendall(response.to_bytes())

        except Exception as e:
            self.logger.error(f"Erro ao processar cliente {address}: {e}")
        finally:
            client_socket.close()

    def _process_message(self, message: Message) -> Message | None:
        self.logger.info(f"Mensagem recebida: {message.type.value} de {message.sender}")

        match message.type:
            case MessageType.NEW_TRANSACTION:
                tx_data = message.payload["transaction"]
                transaction = Transaction.from_dict(tx_data)
                if self.blockchain.add_transaction(transaction):
                    self.logger.info(f"Nova transação adicionada: {transaction.id[:8]}...")
                    self._broadcast(message, exclude=message.sender)
                    if self.on_new_transaction:
                        self.on_new_transaction(transaction)

            case MessageType.NEW_BLOCK:
                block_data = message.payload["block"]
                block = Block.from_dict(block_data)
                if self.blockchain.add_block(block):
                    self.logger.info(f"Novo bloco adicionado: #{block.index}")
                    self.miner.stop_mining()
                    self._broadcast(message, exclude=message.sender)
                    if self.on_new_block:
                        self.on_new_block(block)

            case MessageType.REQUEST_CHAIN:
                return Protocol.response_chain(self.blockchain.to_dict())

            case MessageType.RESPONSE_CHAIN:
                chain_data = message.payload["blockchain"]
                new_chain = [Block.from_dict(b) for b in chain_data["chain"]]
                if self.blockchain.replace_chain(new_chain):
                    self.logger.info(f"Blockchain atualizada: {len(new_chain)} blocos")

            case MessageType.PING:
                if message.sender and message.sender != self.address:
                    new_peer = message.sender
                    is_new = new_peer not in self.peers
                    self._register_peer(new_peer)
                    self.logger.info(f"Peer registrado via PING: {new_peer}")
                    if is_new:
                        self._broadcast(Protocol.peers_list([new_peer]), exclude=new_peer)
                        self.logger.info(f"Novo peer {new_peer} propagado para {len(self.peers) - 1} peers")
                return Protocol.pong()

            case MessageType.DISCOVER_PEERS:
                return Protocol.peers_list(list(self.peers))

            case MessageType.PEERS_LIST:
                new_peers = set(message.payload["peers"])
                for peer in new_peers - {self.address}:
                    self._register_peer(peer)

        return None

    def _register_peer(self, peer_address: str):
        if peer_address in self.peers:
            return
        if len(self.peers) >= self.MAX_PEERS:
            self.logger.debug(f"Limite de peers atingido, ignorando {peer_address}")
            return
        self.peers.add(peer_address)

    def connect_to_peer(self, peer_address: str) -> bool:
        if peer_address == self.address:
            return False

        if len(self.peers) >= self.MAX_PEERS:
            self.logger.warning(f"Limite de {self.MAX_PEERS} peers atingido")
            return False

        try:
            host, port = peer_address.split(":")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((host, int(port)))

                message = Protocol.ping()
                message.sender = self.address
                sock.sendall(message.to_bytes())

                length_data = sock.recv(4)
                if length_data:
                    self._register_peer(peer_address)
                    self._peer_failures[peer_address] = 0
                    self.logger.info(f"Conectado ao peer: {peer_address}")

                    try:
                        peers_msg = Protocol.discover_peers()
                        response = self._send_message(peer_address, peers_msg)
                        if response and response.type == MessageType.PEERS_LIST:
                            new_peers = set(response.payload["peers"])
                            for peer in new_peers - {self.address}:
                                self._register_peer(peer)
                            self.logger.info(f"Peers descobertos: {len(new_peers)}")
                    except Exception as e:
                        self.logger.warning(f"Falha ao descobrir peers de {peer_address}: {e}")

                    return True

        except Exception as e:
            self.logger.error(f"Erro ao conectar ao peer {peer_address}: {e}")

        return False

    def sync_blockchain(self):
        best_chain: list[Block] | None = None
        best_length = len(self.blockchain.chain)
        best_peer = ""

        for peer in list(self.peers):
            try:
                response = self._send_message(peer, Protocol.request_chain())
                if response and response.type == MessageType.RESPONSE_CHAIN:
                    chain_data = response.payload["blockchain"]
                    candidate = [Block.from_dict(b) for b in chain_data["chain"]]
                    if (
                        len(candidate) > best_length
                        and self.blockchain.is_valid_chain(candidate)
                    ):
                        best_chain = candidate
                        best_length = len(candidate)
                        best_peer = peer
                        self.logger.info(
                            f"Candidato melhor encontrado em {peer}: {len(candidate)} blocos"
                        )
            except Exception as e:
                self.logger.error(f"Erro ao sincronizar com {peer}: {e}")
                self._peer_failures[peer] = self._peer_failures.get(peer, 0) + 1

        if best_chain:
            self.blockchain.replace_chain(best_chain)
            self.logger.info(f"Blockchain sincronizada de {best_peer}: {best_length} blocos")

    def create_transaction(self, origem: str, destino: str, valor: float) -> Transaction | None:
        tx = Transaction(origem=origem, destino=destino, valor=valor)
        if self.broadcast_transaction(tx):
            return tx
        return None

    def broadcast_transaction(self, transaction: Transaction) -> bool:
        if self.blockchain.add_transaction(transaction):
            message = Protocol.new_transaction(transaction.to_dict())
            self._broadcast(message)
            return True
        return False

    def broadcast_block(self, block: Block):
        if self.blockchain.add_block(block):
            message = Protocol.new_block(block.to_dict())
            self._broadcast(message)
            self.logger.info(f"Bloco #{block.index} propagado para {len(self.peers)} peers")

    def mine(self) -> Block | None:
        if not self.blockchain.pending_transactions:
            self.logger.info("Nenhuma transação pendente para minerar.")
            return None
        self.logger.info("Iniciando mineração...")

        def on_progress(nonce: int):
            self.logger.debug(f"Mineração em progresso... nonce={nonce}")

        block = self.miner.mine_block(on_progress=on_progress)

        if block:
            self.logger.info(f"Bloco minerado! #{block.index} hash={block.hash[:16]}...")
            self.broadcast_block(block)

        return block

    def get_balance(self, address: str) -> float:
        return self.blockchain.get_balance(address)

    def get_available_balance(self, address: str) -> float:
        return self.blockchain.get_available_balance(address)

    def address_exists(self, address: str) -> bool:
        return self.blockchain.address_exists(address)

    @property
    def chain(self) -> list[Block]:
        return self.blockchain.chain

    @property
    def pending_transactions(self) -> list[Transaction]:
        return self.blockchain.pending_transactions

    @property
    def peer_count(self) -> int:
        return len(self.peers)

    def _send_message(self, peer_address: str, message: Message) -> Message | None:
        try:
            host, port = peer_address.split(":")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10)
                sock.connect((host, int(port)))

                message.sender = self.address
                sock.sendall(message.to_bytes())

                length_data = sock.recv(4)
                if length_data:
                    length = int.from_bytes(length_data, 'big')
                    data = b""
                    while len(data) < length:
                        chunk = sock.recv(min(self.BUFFER_SIZE, length - len(data)))
                        if not chunk:
                            break
                        data += chunk
                    if data:
                        self._peer_failures[peer_address] = 0
                        return Message.from_bytes(data)

        except Exception as e:
            self.logger.error(f"Erro ao enviar para {peer_address}: {e}")
            self._peer_failures[peer_address] = self._peer_failures.get(peer_address, 0) + 1

        return None

    def _broadcast(self, message: Message, exclude: str = ""):
        message.sender = self.address

        active_peers = [
            p for p in self.peers
            if p != exclude and self._peer_failures.get(p, 0) < self.MAX_FAILURES
        ]
        random.shuffle(active_peers)

        for peer in active_peers:
            threading.Thread(
                target=self._send_message,
                args=(peer, message)
            ).start()
