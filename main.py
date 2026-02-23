#!/usr/bin/env python3
import argparse
import time

from src.blockchain import Node, Transaction


def parse_args():
    parser = argparse.ArgumentParser(description="Nó da rede blockchain distribuída")
    parser.add_argument("--host", default="localhost", help="Host do nó (default: localhost)")
    parser.add_argument("--port", type=int, default=5000, help="Porta do nó (default: 5000)")
    parser.add_argument("--bootstrap", nargs="*", default=[], help="Endereços de nós bootstrap (ex: localhost:5001)")
    parser.add_argument("--wallet", default="", help="Nome da carteira para receber recompensas de mineração (ex: andrey)")
    return parser.parse_args()


def print_menu():
    print("\n" + "=" * 50)
    print("BITCOIN BLOCKCHAIN - Menu de Comandos")
    print("=" * 50)
    print("1. Criar transação")
    print("2. Ver transações pendentes")
    print("3. Minerar bloco")
    print("4. Ver blockchain")
    print("5. Ver saldo")
    print("6. Ver peers conectados")
    print("7. Conectar a peer")
    print("8. Sincronizar blockchain")
    print("0. Sair")
    print("=" * 50)


def create_transaction(node: Node):
    print("\n--- Nova Transação ---")
    origem = input("Origem: ").strip()
    destino = input("Destino: ").strip()
    try:
        valor = float(input("Valor: ").strip())
        tx = Transaction(origem=origem, destino=destino, valor=valor)

        saldo = node.blockchain.get_balance(origem)
        if origem not in ("genesis", "coinbase") and saldo < valor:
            print(f"✗ Saldo insuficiente! {origem} tem {saldo}, precisa de {valor}")
            return

        node.broadcast_transaction(tx)
        print(f"✓ Transação criada: {tx.id[:8]}...")
    except ValueError as e:
        print(f"✗ Erro: {e}")


def show_pending(node: Node):
    print("\n--- Transações Pendentes ---")
    if not node.blockchain.pending_transactions:
        print("Nenhuma transação pendente.")
        return

    for tx in node.blockchain.pending_transactions:
        print(f"  [{tx.id[:8]}...] {tx.origem} -> {tx.destino}: {tx.valor}")


def mine_block(node: Node):
    num_txs = len(node.blockchain.pending_transactions)
    print(f"\n⛏️  Minerando bloco com {num_txs} transação(ões)...")
    start = time.time()
    block = node.mine()
    elapsed = time.time() - start

    if block:
        print(f"✓ Bloco #{block.index} minerado em {elapsed:.2f}s")
        print(f"  Hash: {block.hash}")
        print(f"  Nonce: {block.nonce}")
    else:
        print("✗ Mineração interrompida")


def show_blockchain(node: Node):
    print("\n--- Blockchain ---")
    for block in node.blockchain.chain:
        print(f"\n[Bloco #{block.index}]")
        print(f"  Hash: {block.hash[:32]}...")
        print(f"  Previous: {block.previous_hash[:32]}...")
        print(f"  Nonce: {block.nonce}")
        print(f"  Transações: {len(block.transactions)}")
        for tx in block.transactions:
            print(f"    - {tx.origem} -> {tx.destino}: {tx.valor}")


def show_balance(node: Node):
    address = input("\nEndereço: ").strip()
    balance = node.blockchain.get_balance(address)
    print(f"Saldo de {address}: {balance}")


def show_peers(node: Node):
    print("\n--- Peers Conectados ---")
    if not node.peers:
        print("Nenhum peer conectado.")
        return

    for peer in node.peers:
        print(f"  - {peer}")


def connect_peer(node: Node):
    peer = input("\nEndereço do peer (host:port): ").strip()
    if node.connect_to_peer(peer):
        print(f"✓ Conectado a {peer}")
    else:
        print(f"✗ Falha ao conectar a {peer}")


def sync_chain(node: Node):
    print("\n🔄 Sincronizando blockchain...")
    node.sync_blockchain()
    print(f"✓ Blockchain com {len(node.blockchain.chain)} blocos")


def main():
    args = parse_args()

    node = Node(host=args.host, port=args.port, wallet=args.wallet)
    node.start()

    for bootstrap in args.bootstrap:
        if node.connect_to_peer(bootstrap):
            print(f"Conectado ao bootstrap: {bootstrap}")

    if node.peers:
        node.sync_blockchain()

    try:
        while True:
            print_menu()
            choice = input("Escolha: ").strip()

            match choice:
                case "1":
                    create_transaction(node)
                case "2":
                    show_pending(node)
                case "3":
                    mine_block(node)
                case "4":
                    show_blockchain(node)
                case "5":
                    show_balance(node)
                case "6":
                    show_peers(node)
                case "7":
                    connect_peer(node)
                case "8":
                    sync_chain(node)
                case "0":
                    print("Encerrando...")
                    break
                case _:
                    print("Opção inválida!")

    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário")

    finally:
        node.stop()


if __name__ == "__main__":
    main()
