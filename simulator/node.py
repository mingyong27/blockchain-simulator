from .block import Block, Transaction
from .logger import log_event

class Node:
    def __init__(self, node_id, network, balance, consensus_algo, k_finality=4, logger=None):
        self.id = node_id
        self.network = network
        self.balance = balance
        self.consensus = consensus_algo
        self.chain = []
        self.mempool = []
        self.k_finality = k_finality
        self.finalized_height = -1
        self.finalized_blocks = {}
        self.finalized_txs = set()
        self.logger = logger
        self.create_genesis_block()
        if hasattr(self.network, "add_node"):
            self.network.add_node(self)

    def create_genesis_block(self):
        genesis = Block(height=0, transactions=[], previous_hash="0", creator="System")
        self.chain.append(genesis)

    def get_chain_head(self):
        return self.chain[-1]

    def create_and_broadcast_transaction(self, recipient_id, amount):
        tx = Transaction(self.id, recipient_id, amount)
        self.receive_transaction(tx)
        self.network.broadcast(self.id, {"type": "new_tx", "data": tx})

    def receive_transaction(self, tx):
        if tx.id in self.finalized_txs:
            return
        for block in self.chain:
            if any(btx.id == tx.id for btx in block.transactions):
                return
        if any(mtx.id == tx.id for mtx in self.mempool):
            return
        self.mempool.append(tx)

    def tick(self, t):
        if not self.mempool:
            return
        to_include = self.mempool[:2]
        new_block = self.consensus.mine_block(self, to_include, t, self.logger)
        if new_block:
            self.chain.append(new_block)
            included_ids = {tx.id for tx in new_block.transactions}
            self.mempool = [tx for tx in self.mempool if tx.id not in included_ids]
            self.network.broadcast(self.id, {"type": "gossip_chain", "time": t, "data": self.chain[:]})
            self.check_and_update_finality(t)

    def receive_chain(self, peer_chain, t):
        winning_chain = self.consensus.validate_and_resolve_chain(self, peer_chain)
        if winning_chain[-1].hash == self.get_chain_head().hash:
            return
        old_chain = self.chain
        fork = 0
        for i in range(min(len(old_chain), len(winning_chain))):
            if old_chain[i].hash != winning_chain[i].hash:
                break
            fork = i
        if fork < self.finalized_height:
            log_event(self.logger, {
                "time": t,
                "event": "REORG_REJECTED_FINALITY",
                "node": self.id,
                "finalized_height": self.finalized_height,
                "fork": fork,
                "peer_height": len(peer_chain) - 1
            })
            return
        log_event(self.logger, {
            "time": t,
            "event": "REORG_START",
            "node": self.id,
            "current_height": self.get_chain_head().height,
            "peer_height": len(peer_chain) - 1
        })
        orphaned = {tx for block in old_chain[fork + 1:] for tx in block.transactions}
        self.chain = winning_chain
        txs_in_new = {tx.id for block in self.chain for tx in block.transactions}
        reconsider = {tx.id: tx for tx in self.mempool}
        for tx in orphaned:
            if tx.id not in self.finalized_txs and tx.id not in txs_in_new:
                reconsider.setdefault(tx.id, tx)
        self.mempool = [tx for txid, tx in reconsider.items() if txid not in txs_in_new]
        print(f"[{self.id}] Reorg complete. New height: {self.get_chain_head().height}.")

    def check_and_update_finality(self, t):
        tip = self.get_chain_head().height
        new_final = tip - self.k_finality
        if new_final <= self.finalized_height or new_final < 0:
            return
        initial = self.finalized_height
        for h in range(self.finalized_height + 1, new_final + 1):
            if h >= len(self.chain):
                continue
            blk = self.chain[h]
            if h in self.finalized_blocks and self.finalized_blocks[h] != blk.hash:
                log_event(self.logger, {"time": t, "event": "FINALITY_ERROR", "node": self.id, "reason": "Finality conflict", "height": h})
                return
            self.finalized_blocks[h] = blk.hash
            for tx in blk.transactions:
                if tx.id in self.finalized_txs:
                    log_event(self.logger, {"time": t, "event": "FINALITY_ERROR", "node": self.id, "reason": "Double-spend detected", "height": h})
                    return
                self.finalized_txs.add(tx.id)
        if new_final > initial:
            log_event(self.logger, {"time": t, "event": "FINALITY_UPDATE", "node": self.id, "previous_final_height": initial, "new_final_height": new_final})
            print(f"[{self.id}] Finalized chain up to height {new_final}")
            self.finalized_height = new_final
