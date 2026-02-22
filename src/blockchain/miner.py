"""
Módulo de Mineração (Proof of Work)
"""

import time
import threading
from typing import Callable

from .block import Block
from .blockchain import Blockchain
from .transaction import Transaction


class Miner:
    """
    Implementa o algoritmo de Proof of Work com mineração paralela.

    Divide o espaço de nonces entre múltiplas threads trabalhadoras.
    Cada worker busca em sua própria faixa (interleaved): o worker i
    testa nonces i, i+WORKERS, i+2*WORKERS, ...

    A primeira thread a encontrar um hash válido sinaliza as demais para parar.
    """

    WORKERS = 4             # Número de threads de mineração paralelas
    PROGRESS_INTERVAL = 5000  # Reporta progresso a cada N tentativas por worker

    def __init__(self, blockchain: Blockchain, miner_address: str):
        self.blockchain = blockchain
        self.miner_address = miner_address
        self.mining = False
        self._found_block: Block | None = None
        self._lock = threading.Lock()

    def mine_block(
        self,
        transactions: list[Transaction] = None,
        on_progress: Callable[[int], None] = None,
    ) -> Block | None:
        """
        Minera um novo bloco com as transações pendentes.

        Seleciona transações priorizando maior valor (simula taxas de rede).
        Divide o trabalho de PoW entre WORKERS threads paralelas.

        Args:
            transactions: Lista de transações (usa pendentes ordenadas por valor se None)
            on_progress: Callback chamado periodicamente com o nonce atual

        Returns:
            Bloco minerado ou None se interrompido
        """
        if transactions is None:
            # Prioriza transações de maior valor (similar a fee priority)
            transactions = sorted(
                self.blockchain.pending_transactions,
                key=lambda tx: tx.valor,
                reverse=True,
            )

        # Adiciona transação de recompensa (Coinbase)
        reward_tx = Transaction(
            origem="coinbase",
            destino=self.miner_address,
            valor=50.0,
        )
        transactions = [reward_tx] + list(transactions)

        # Snapshot dos parâmetros do bloco antes de iniciar as threads
        block_index = len(self.blockchain.chain)
        prev_hash = self.blockchain.last_block.hash
        timestamp = time.time()
        difficulty = Blockchain.DIFFICULTY

        self.mining = True
        self._found_block = None
        stop_event = threading.Event()

        def worker(worker_id: int):
            """
            Busca nonces em faixa interleaved:
            worker 0 → 0, WORKERS, 2*WORKERS, ...
            worker 1 → 1, WORKERS+1, 2*WORKERS+1, ...
            """
            block = Block(
                index=block_index,
                previous_hash=prev_hash,
                transactions=transactions,
                nonce=worker_id,
                timestamp=timestamp,
            )
            attempts = 0

            while self.mining and not stop_event.is_set():
                block.hash = block.calculate_hash()

                if block.hash.startswith(difficulty):
                    with self._lock:
                        if self._found_block is None:
                            self._found_block = block
                    stop_event.set()
                    return

                block.nonce += self.WORKERS
                attempts += 1

                if on_progress and attempts % self.PROGRESS_INTERVAL == 0:
                    on_progress(block.nonce)

        threads = [
            threading.Thread(target=worker, args=(i,), daemon=True)
            for i in range(self.WORKERS)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.mining = False
        return self._found_block

    def stop_mining(self):
        """Interrompe todas as threads de mineração."""
        self.mining = False
