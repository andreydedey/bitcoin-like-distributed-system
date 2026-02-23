#!/usr/bin/env python3
import argparse
import threading

import customtkinter as ctk

from src.blockchain import Node, Transaction

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class BlockchainGUI:
    def __init__(self, host: str, port: int, bootstrap_peers: list[str], wallet: str = ""):
        self.node = Node(host=host, port=port, wallet=wallet)
        self.node.start()

        for peer in bootstrap_peers:
            self.node.connect_to_peer(peer)
        if bootstrap_peers:
            self.node.sync_blockchain()

        self.root = ctk.CTk()
        label = wallet if wallet else f"{host}:{port}"
        self.root.title(f"Bitcoin Blockchain — {label}")
        self.root.geometry("1050x680")
        self.root.minsize(860, 580)

        self._build_ui()
        self._schedule_refresh()

    def _build_ui(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self.root, width=230, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="⛓  Blockchain Node",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(22, 4))

        self.lbl_address = ctk.CTkLabel(
            sidebar,
            text=self.node.address,
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self.lbl_address.grid(row=1, column=0, padx=20, pady=(0, 4))

        self.lbl_wallet = ctk.CTkLabel(
            sidebar,
            text=f"carteira: {self.node.wallet}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#3b9fd6",
        )
        self.lbl_wallet.grid(row=2, column=0, padx=20, pady=(0, 12))

        status_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        status_frame.grid(row=3, column=0, padx=20, pady=4, sticky="ew")
        status_frame.grid_columnconfigure((0, 1), weight=1)

        self.lbl_peers = ctk.CTkLabel(
            status_frame,
            text="Peers\n0",
            font=ctk.CTkFont(size=12),
            fg_color=("#2b2b2b", "#2b2b2b"),
            corner_radius=8,
            width=80,
            height=48,
        )
        self.lbl_peers.grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        self.lbl_blocks = ctk.CTkLabel(
            status_frame,
            text="Blocos\n1",
            font=ctk.CTkFont(size=12),
            fg_color=("#2b2b2b", "#2b2b2b"),
            corner_radius=8,
            width=80,
            height=48,
        )
        self.lbl_blocks.grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        self.lbl_pending = ctk.CTkLabel(
            status_frame,
            text="Pendentes\n0",
            font=ctk.CTkFont(size=12),
            fg_color=("#2b2b2b", "#2b2b2b"),
            corner_radius=8,
            width=80,
            height=48,
        )
        self.lbl_pending.grid(row=1, column=0, columnspan=2, padx=4, pady=4, sticky="ew")

        _divider(sidebar, row=4)

        self.btn_mine = ctk.CTkButton(
            sidebar,
            text="⛏  Minerar Bloco",
            command=self._mine,
            fg_color="#e67e22",
            hover_color="#d35400",
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.btn_mine.grid(row=5, column=0, padx=20, pady=(6, 4), sticky="ew")

        ctk.CTkButton(
            sidebar,
            text="🔄  Sincronizar",
            command=self._sync,
            fg_color="transparent",
            border_width=1,
            height=36,
        ).grid(row=6, column=0, padx=20, pady=4, sticky="ew")

        self.lbl_mine_status = ctk.CTkLabel(
            sidebar,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#e67e22",
        )
        self.lbl_mine_status.grid(row=7, column=0, padx=20, pady=2)

        _divider(sidebar, row=8)

        ctk.CTkLabel(sidebar, text="Conectar a peer", font=ctk.CTkFont(size=12)).grid(
            row=9, column=0, padx=20, pady=(4, 2)
        )
        self.entry_peer = ctk.CTkEntry(sidebar, placeholder_text="host:port")
        self.entry_peer.grid(row=10, column=0, padx=20, pady=4, sticky="ew")

        ctk.CTkButton(
            sidebar,
            text="Conectar",
            command=self._connect_peer,
            height=34,
        ).grid(row=11, column=0, padx=20, pady=(4, 20), sticky="ew")

    def _build_main(self):
        main = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        self.tabs = ctk.CTkTabview(main)
        self.tabs.grid(row=0, column=0, sticky="nsew")

        self._tab_transaction()
        self._tab_balance()
        self._tab_blockchain()
        self._tab_pending()

    def _tab_transaction(self):
        tab = self.tabs.add("💸  Nova Transação")
        tab.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(tab)
        card.grid(row=0, column=0, padx=30, pady=30, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        fields = [
            ("Origem", "ex: coinbase", "entry_origem"),
            ("Destino", "ex: andrey", "entry_destino"),
            ("Valor", "ex: 10.0", "entry_valor"),
        ]
        for i, (label, placeholder, attr) in enumerate(fields):
            ctk.CTkLabel(card, text=label, anchor="w", width=70).grid(
                row=i, column=0, padx=16, pady=12, sticky="w"
            )
            entry = ctk.CTkEntry(card, placeholder_text=placeholder)
            entry.grid(row=i, column=1, padx=16, pady=12, sticky="ew")
            setattr(self, attr, entry)

        ctk.CTkButton(
            card,
            text="Enviar Transação",
            command=self._create_transaction,
            height=42,
        ).grid(row=3, column=0, columnspan=2, padx=16, pady=16, sticky="ew")

        self.lbl_tx_status = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=13))
        self.lbl_tx_status.grid(row=1, column=0, pady=4)

    def _tab_balance(self):
        tab = self.tabs.add("💰  Saldo")
        tab.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(tab)
        card.grid(row=0, column=0, padx=30, pady=30, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="Endereço", anchor="w", width=80).grid(
            row=0, column=0, padx=16, pady=16, sticky="w"
        )
        self.entry_bal_addr = ctk.CTkEntry(card, placeholder_text="ex: andrey")
        self.entry_bal_addr.grid(row=0, column=1, padx=16, pady=16, sticky="ew")

        ctk.CTkButton(
            card,
            text="Consultar",
            command=self._check_balance,
            height=42,
        ).grid(row=1, column=0, columnspan=2, padx=16, pady=12, sticky="ew")

        self.lbl_balance = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=32, weight="bold"))
        self.lbl_balance.grid(row=1, column=0, pady=24)

    def _tab_blockchain(self):
        tab = self.tabs.add("⛓  Blockchain")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        self.txt_chain = ctk.CTkTextbox(
            tab, font=ctk.CTkFont(family="Courier New", size=12), state="disabled"
        )
        self.txt_chain.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 4))

        ctk.CTkButton(tab, text="Atualizar", command=self._refresh_chain, height=32).grid(
            row=1, column=0, pady=(0, 6)
        )

    def _tab_pending(self):
        tab = self.tabs.add("⏳  Pendentes")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        self.txt_pending = ctk.CTkTextbox(
            tab, font=ctk.CTkFont(family="Courier New", size=12), state="disabled"
        )
        self.txt_pending.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 4))

        ctk.CTkButton(tab, text="Atualizar", command=self._refresh_pending, height=32).grid(
            row=1, column=0, pady=(0, 6)
        )

    def _create_transaction(self):
        origem = self.entry_origem.get().strip()
        destino = self.entry_destino.get().strip()
        valor_str = self.entry_valor.get().strip()

        if not origem or not destino or not valor_str:
            self._tx_status("Preencha todos os campos.", "red")
            return

        try:
            valor = float(valor_str)
        except ValueError:
            self._tx_status("Valor inválido.", "red")
            return

        tx = Transaction(origem=origem, destino=destino, valor=valor)
        if not self.node.broadcast_transaction(tx):
            saldo = self.node.blockchain.get_available_balance(origem)
            self._tx_status(f"Saldo insuficiente: {origem} tem {saldo:.2f} disponível", "red")
            return
        self._tx_status(f"✓ Transação enviada: {tx.id[:14]}...", "#2ecc71")
        for entry in (self.entry_origem, self.entry_destino, self.entry_valor):
            entry.delete(0, "end")

    def _tx_status(self, msg: str, color: str):
        self.lbl_tx_status.configure(text=msg, text_color=color)
        self.root.after(4000, lambda: self.lbl_tx_status.configure(text=""))

    def _check_balance(self):
        addr = self.entry_bal_addr.get().strip()
        if not addr:
            return
        balance = self.node.blockchain.get_balance(addr)
        color = "#2ecc71" if balance >= 0 else "#e74c3c"
        self.lbl_balance.configure(text=f"{addr}:  {balance:.2f}", text_color=color)

    def _mine(self):
        self.btn_mine.configure(state="disabled", text="Minerando...")
        self.lbl_mine_status.configure(text="⛏ em andamento...", text_color="#e67e22")

        def do_mine():
            block = self.node.mine()
            self.root.after(0, lambda: self._mine_done(block))

        threading.Thread(target=do_mine, daemon=True).start()

    def _mine_done(self, block):
        self.btn_mine.configure(state="normal", text="⛏  Minerar Bloco")
        if block:
            self.lbl_mine_status.configure(
                text=f"✓ Bloco #{block.index} minerado!", text_color="#2ecc71"
            )
        else:
            self.lbl_mine_status.configure(text="Mineração interrompida", text_color="gray")
        self.root.after(5000, lambda: self.lbl_mine_status.configure(text=""))

    def _sync(self):
        self.node.sync_blockchain()

    def _connect_peer(self):
        peer = self.entry_peer.get().strip()
        if peer:
            self.node.connect_to_peer(peer)
            self.entry_peer.delete(0, "end")

    def _refresh_chain(self):
        self.txt_chain.configure(state="normal")
        self.txt_chain.delete("1.0", "end")
        for block in self.node.blockchain.chain:
            self.txt_chain.insert(
                "end",
                f"Bloco #{block.index}\n"
                f"  Hash:     {block.hash[:40]}...\n"
                f"  Anterior: {block.previous_hash[:40]}...\n"
                f"  Nonce:    {block.nonce}\n"
                f"  Txs ({len(block.transactions)}):\n",
            )
            for tx in block.transactions:
                self.txt_chain.insert("end", f"    {tx.origem} → {tx.destino}: {tx.valor}\n")
            self.txt_chain.insert("end", "\n")
        self.txt_chain.configure(state="disabled")

    def _refresh_pending(self):
        self.txt_pending.configure(state="normal")
        self.txt_pending.delete("1.0", "end")
        txs = self.node.blockchain.pending_transactions
        if not txs:
            self.txt_pending.insert("end", "Nenhuma transação pendente.")
        else:
            for tx in txs:
                self.txt_pending.insert(
                    "end",
                    f"[{tx.id[:16]}...]\n"
                    f"  {tx.origem} → {tx.destino}: {tx.valor}\n\n",
                )
        self.txt_pending.configure(state="disabled")

    def _refresh_status(self):
        self.lbl_address.configure(text=self.node.address)
        self.lbl_peers.configure(text=f"Peers\n{len(self.node.peers)}")
        self.lbl_blocks.configure(text=f"Blocos\n{len(self.node.blockchain.chain)}")
        self.lbl_pending.configure(
            text=f"Pendentes\n{len(self.node.blockchain.pending_transactions)}"
        )

    def _schedule_refresh(self):
        self._refresh_status()
        self.root.after(2000, self._schedule_refresh)

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        self.node.stop()
        self.root.destroy()


def _divider(parent, row: int):
    ctk.CTkFrame(parent, height=1, fg_color=("gray70", "gray30")).grid(
        row=row, column=0, sticky="ew", padx=16, pady=6
    )


def main():
    parser = argparse.ArgumentParser(description="GUI do nó blockchain")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--bootstrap", nargs="*", default=[])
    parser.add_argument("--wallet", default="", help="Nome da carteira (ex: andrey)")
    args = parser.parse_args()

    app = BlockchainGUI(
        host=args.host,
        port=args.port,
        bootstrap_peers=args.bootstrap,
        wallet=args.wallet,
    )
    app.run()


if __name__ == "__main__":
    main()
