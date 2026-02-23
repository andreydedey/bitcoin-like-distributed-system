import unittest

from src.blockchain import Block, Blockchain, Transaction, Miner


class TestGenesis(unittest.TestCase):
    def test_hash_genesis(self):
        genesis = Block.create_genesis()
        self.assertEqual(
            genesis.hash,
            "0567c32b97c36a70d3f4cb865710d329a0be5d713c8cb1b8c769fbaf89f1afb7",
        )

    def test_genesis_campos(self):
        genesis = Block.create_genesis()
        self.assertEqual(genesis.index, 0)
        self.assertEqual(genesis.previous_hash, "0" * 64)
        self.assertEqual(genesis.transactions, [])
        self.assertEqual(genesis.nonce, 0)
        self.assertEqual(genesis.timestamp, 0)


class TestTransaction(unittest.TestCase):
    def test_criacao_valida(self):
        tx = Transaction(origem="alice", destino="bob", valor=10.0)
        self.assertEqual(tx.origem, "alice")
        self.assertEqual(tx.destino, "bob")
        self.assertEqual(tx.valor, 10.0)
        self.assertIsNotNone(tx.id)
        self.assertIsNotNone(tx.timestamp)

    def test_valor_negativo(self):
        with self.assertRaises(ValueError):
            Transaction(origem="alice", destino="bob", valor=-1.0)

    def test_valor_zero(self):
        with self.assertRaises(ValueError):
            Transaction(origem="alice", destino="bob", valor=0)

    def test_origem_igual_destino(self):
        with self.assertRaises(ValueError):
            Transaction(origem="alice", destino="alice", valor=10.0)

    def test_serialization(self):
        tx = Transaction(origem="alice", destino="bob", valor=10.0)
        d = tx.to_dict()
        tx2 = Transaction.from_dict(d)
        self.assertEqual(tx.id, tx2.id)
        self.assertEqual(tx.valor, tx2.valor)


class TestBlockchain(unittest.TestCase):
    def setUp(self):
        self.bc = Blockchain()

    def test_inicia_com_genesis(self):
        self.assertEqual(len(self.bc.chain), 1)
        self.assertEqual(self.bc.chain[0].index, 0)

    def test_saldo_inicial_zero(self):
        self.assertEqual(self.bc.get_balance("alice"), 0.0)

    def test_adiciona_transacao_coinbase(self):
        tx = Transaction(origem="coinbase", destino="alice", valor=50.0)
        resultado = self.bc.add_transaction(tx)
        self.assertTrue(resultado)
        self.assertIn(tx, self.bc.pending_transactions)

    def test_saldo_pendente_nao_conta(self):
        tx = Transaction(origem="coinbase", destino="alice", valor=50.0)
        self.bc.add_transaction(tx)
        self.assertEqual(self.bc.get_balance("alice"), 0.0)

    def test_saldo_disponivel_desconta_pendente(self):
        tx = Transaction(origem="coinbase", destino="alice", valor=50.0)
        self.bc.add_transaction(tx)
        self.assertEqual(self.bc.get_available_balance("alice"), 0.0)

    def test_rejeita_saldo_insuficiente(self):
        tx = Transaction(origem="alice", destino="bob", valor=10.0)
        resultado = self.bc.add_transaction(tx)
        self.assertFalse(resultado)

    def test_rejeita_duplicata(self):
        tx = Transaction(origem="coinbase", destino="alice", valor=50.0)
        self.bc.add_transaction(tx)
        resultado = self.bc.add_transaction(tx)
        self.assertFalse(resultado)

    def test_saldo_apos_mineracao(self):
        tx = Transaction(origem="coinbase", destino="alice", valor=50.0)
        self.bc.add_transaction(tx)
        miner = Miner(self.bc, "minerador")
        block = miner.mine_block()
        self.bc.add_block(block)
        self.assertEqual(self.bc.get_balance("alice"), 50.0)

    def test_nao_pode_gastar_saldo_pendente(self):
        tx1 = Transaction(origem="coinbase", destino="alice", valor=50.0)
        self.bc.add_transaction(tx1)
        tx2 = Transaction(origem="alice", destino="bob", valor=30.0)
        resultado = self.bc.add_transaction(tx2)
        self.assertFalse(resultado)

    def test_pode_gastar_saldo_confirmado(self):
        tx1 = Transaction(origem="coinbase", destino="alice", valor=50.0)
        self.bc.add_transaction(tx1)
        miner = Miner(self.bc, "minerador")
        block = miner.mine_block()
        self.bc.add_block(block)
        tx2 = Transaction(origem="alice", destino="bob", valor=30.0)
        resultado = self.bc.add_transaction(tx2)
        self.assertTrue(resultado)

    def test_gasto_duplo_pendente(self):
        tx1 = Transaction(origem="coinbase", destino="alice", valor=50.0)
        self.bc.add_transaction(tx1)
        miner = Miner(self.bc, "minerador")
        block = miner.mine_block()
        self.bc.add_block(block)
        tx2 = Transaction(origem="alice", destino="bob", valor=40.0)
        tx3 = Transaction(origem="alice", destino="carol", valor=40.0)
        self.bc.add_transaction(tx2)
        resultado = self.bc.add_transaction(tx3)
        self.assertFalse(resultado)

    def test_cadeia_valida(self):
        self.assertTrue(self.bc.is_valid_chain())

    def test_pendentes_removidos_apos_mineracao(self):
        tx = Transaction(origem="coinbase", destino="alice", valor=50.0)
        self.bc.add_transaction(tx)
        miner = Miner(self.bc, "minerador")
        block = miner.mine_block()
        self.bc.add_block(block)
        self.assertEqual(len(self.bc.pending_transactions), 0)


class TestProofOfWork(unittest.TestCase):
    def setUp(self):
        self.bc = Blockchain()

    def test_hash_bloco_minerado_comeca_com_000(self):
        miner = Miner(self.bc, "minerador")
        block = miner.mine_block()
        self.assertTrue(block.hash.startswith("000"))

    def test_bloco_invalido_rejeitado(self):
        tx = Transaction(origem="coinbase", destino="alice", valor=50.0)
        self.bc.add_transaction(tx)
        miner = Miner(self.bc, "minerador")
        block = miner.mine_block()
        block.hash = "hash_invalido"
        resultado = self.bc.add_block(block)
        self.assertFalse(resultado)

    def test_recompensa_vai_para_minerador(self):
        miner = Miner(self.bc, "andrey")
        block = miner.mine_block()
        self.bc.add_block(block)
        self.assertEqual(self.bc.get_balance("andrey"), 50.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
