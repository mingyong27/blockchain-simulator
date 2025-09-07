# simulator/node.py

from .block import Block, Transaction
from .logger import log_event 

class Node:
    """A participant that holds state but delegates consensus rules."""

    def __init__(self, node_id, network, balance, consensus_algo,k_finality=4, logger=None):
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

        self.create_genesis_block()
        self.logger=logger

    def create_genesis_block(self):
        genesis_block = Block(height=0, transactions=[], previous_hash="0", creator="System")
        self.chain.append(genesis_block)

    def get_chain_head(self):
        return self.chain[-1]
    
    def tick(self):
        """
        On each tick, a node can attempt to mine.
        It delegates the actual mining process to its consensus object.
        """
        if not self.mempool:
            return # Don't mine if no transactions

        # Let the consensus algorithm try to mine a block
        transactions_to_include = self.mempool[:2]
        new_block = self.consensus.mine_block(self, transactions_to_include)

        if new_block:
            # We found a block! Add it and broadcast our new chain.
            self.chain.append(new_block)
            self.mempool = [tx for tx in self.mempool if tx not in new_block.transactions]
            self.network.broadcast(self.id, {"type": "gossip_chain", "data": self.chain})
            self.check_and_update_finality()
            
    def receive_transaction(self, tx):
        if tx not in self.mempool:
            self.mempool.append(tx)

    def receive_chain(self, peer_chain, t): 
        
        # 1. Let the consensus algorithm decide which chain is the "best".
        winning_chain = self.consensus.validate_and_resolve_chain(self.chain, peer_chain)

        # 2. Check if a reorg is necessary.
        if winning_chain is peer_chain:
            old_height = self.get_chain_head().height
            
            # This is a great place to log the start of the reorg.
            log_event(self.logger, {
                "time": t,
                "event": "REORG_START",
                "node": self.id,
                "reason": "Peer chain is longer and valid",
                "current_height": old_height,
                "peer_height": len(peer_chain) - 1,
            })
            
            # (The reorg logic itself is the same as before)
            fork_point_idx = 0
            for i in range(min(len(self.chain), len(peer_chain))):
                if self.chain[i].hash != peer_chain[i].hash:
                    break
                fork_point_idx = i
            
            orphaned_transactions = []
            for orphaned_block in self.chain[fork_point_idx + 1:]:
                orphaned_transactions.extend(orphaned_block.transactions)

            self.chain = peer_chain
            
            new_chain_transactions = {tx for block in self.chain[fork_point_idx + 1:] for tx in block.transactions}
            
            for tx in orphaned_transactions:
                if tx not in new_chain_transactions and tx not in self.mempool:
                    self.mempool.append(tx)
            
            print(f"[{self.id}] Reorg complete. New height: {self.get_chain_head().height}.")
        
        # 3. Check and update finality.
        # We must also pass the time 't' to this function.
        self.check_and_update_finality(t)


    def check_and_update_finality(self, t):
        """Checks if any new blocks can be marked as final based on the k-rule."""
        chain_tip_height = self.get_chain_head().height
        new_final_height = chain_tip_height - self.k_finality

        if new_final_height > self.finalized_height:
            assert new_final_height > self.finalized_height, \
                f"[{self.id}] INVARIANT FAIL: Finalized height decreased from {self.finalized_height} to {new_final_height}!"

            for h in range(self.finalized_height + 1, new_final_height + 1):
                block_to_finalize = self.chain[h]
                if h in self.finalized_blocks:
                    assert self.finalized_blocks[h] == block_to_finalize.hash, \
                        f"[{self.id}] INVARIANT FAIL: Finality conflict at height {h}!"
                
                self.finalized_blocks[h] = block_to_finalize.hash
                for tx in block_to_finalize.transactions:
                    tx_id = (tx.sender, tx.recipient, tx.amount) 
                    assert tx_id not in self.finalized_txs, \
                        f"[{self.id}] INVARIANT FAIL: Double-spend detected for tx {tx} in final block {h}!"
                    self.finalized_txs.add(tx_id)

            log_event(self.logger, {
            "time": t,
            "event": "FINALITY_UPDATE",
            "node": self.id,
            "previous_final_height": self.finalized_height,
            "new_final_height": new_final_height,
        })
            
            print(f"[{self.id}] ⛓️ Finalized chain up to height {new_final_height}")
            self.finalized_height = new_final_height

