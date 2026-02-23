import time
import threading
from typing import Callable

from .block import Block
from .blockchain import Blockchain
from .transaction import Transaction


class Miner:
    WORKERS = 4
    PROGRESS_INTERVAL = 5000

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
        if transactions is None:
            transactions = sorted(
                self.blockchain.pending_transactions,
                key=lambda tx: tx.valor,
                reverse=True,
            )

        reward_tx = Transaction(
            origem="coinbase",
            destino=self.miner_address,
            valor=50.0,
        )
        transactions = [reward_tx] + list(transactions)

        block_index = len(self.blockchain.chain)
        prev_hash = self.blockchain.last_block.hash
        timestamp = time.time()
        difficulty = Blockchain.DIFFICULTY

        self.mining = True
        self._found_block = None
        stop_event = threading.Event()

        def worker(worker_id: int):
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
        self.mining = False
