from .block import Block, Transaction
from .logger import log_event

class PoW:
    def __init__(self, difficulty=3):
        self.difficulty = difficulty

    def validate_block(self, block):
        return block.hash.startswith("0" * self.difficulty) and block.height >= 0

    def validate_chain(self, chain):
        if not chain or chain[0].height != 0:
            return False
        for i in range(1, len(chain)):
            if chain[i].previous_hash != chain[i-1].hash:
                return False
            if not self.validate_block(chain[i]):
                return False
        return True

    def validate_and_resolve_chain(self, node, peer_chain):
        local = node.chain
        peer_ok = self.validate_chain(peer_chain)
        local_ok = self.validate_chain(local)
        if not peer_ok and local_ok:
            return local
        if peer_ok and not local_ok:
            return peer_chain[:]
        if not peer_ok and not local_ok:
            return local
        if len(peer_chain) > len(local):
            return peer_chain[:]
        if len(peer_chain) < len(local):
            return local
        if peer_chain[-1].hash < local[-1].hash:
            return peer_chain[:]
        return local

    def mine_block(self, node, txs, t, logger=None):
        blk = Block(height=node.get_chain_head().height + 1,
                    transactions=txs,
                    previous_hash=node.get_chain_head().hash,
                    creator=node.id)
        nonce = 0
        while True:
            blk.set_nonce(nonce)
            if blk.hash.startswith("0" * self.difficulty):
                from .logger import log_event
                log_event(logger, {"time": t, "event": "BLOCK_MINED", "algorithm": "PoW", "node": node.id, "height": blk.height, "nonce": nonce})
                print(f"[{node.id}] Mined block {blk.height}! Nonce: {nonce}")
                return blk
            nonce += 1


class HybridStakePoW:
    def __init__(self, difficulty=2):
        self.difficulty = difficulty

    def validate_block(self, block):
        return block.hash.startswith("0" * self.difficulty) and block.height >= 0

    def validate_chain(self, chain):
        if not chain or chain[0].height != 0:
            return False
        for i in range(1, len(chain)):
            if chain[i].previous_hash != chain[i-1].hash:
                return False
            if not self.validate_block(chain[i]):
                return False
        return True

    def validate_and_resolve_chain(self, node, peer_chain):
        local = node.chain
        peer_ok = self.validate_chain(peer_chain)
        local_ok = self.validate_chain(local)
        if not peer_ok and local_ok:
            return local
        if peer_ok and not local_ok:
            return peer_chain[:]
        if not peer_ok and not local_ok:
            return local
        if len(peer_chain) > len(local):
            return peer_chain[:]
        if len(peer_chain) < len(local):
            return local
        if peer_chain[-1].hash < local[-1].hash:
            return peer_chain[:]
        return local

    def get_leader(self, seed, nodes, attempt):
        r = abs(hash((seed, attempt))) % sum(n.balance for n in nodes)
        s = 0
        for n in nodes:
            s += n.balance
            if r < s:
                return n
        return nodes[0]

    def mine_light_block(self, leader, txs, t, logger=None):
        blk = Block(height=leader.get_chain_head().height + 1,
                    transactions=txs,
                    previous_hash=leader.get_chain_head().hash,
                    creator=leader.id)
        nonce = 0
        while True:
            blk.set_nonce(nonce)
            if blk.hash.startswith("0" * self.difficulty):
                from .logger import log_event
                log_event(logger, {"time": t, "event": "BLOCK_MINED", "algorithm": "Hybrid", "node": leader.id, "height": blk.height, "nonce": nonce})
                print(f"[{leader.id}] (Hybrid) Mined block {blk.height}! Nonce: {nonce}")
                return blk
            nonce += 1
