# simulator/consensus.py

from time import time
from .block import Block
import random

class PoW:
    """Encapsulates the rules for Proof of Work consensus."""
    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.difficulty_prefix = '0' * difficulty

    def mine_block(self, node, transactions):
        """
        Creates a new candidate block and performs the mining process.
        Returns a new valid block if successful, otherwise None.
        """
        head = node.get_chain_head()
        
        candidate_block = Block(
            height=head.height + 1,
            transactions=transactions,
            previous_hash=head.hash,
            creator=node.id
        )

        # The core mining loop
        while not candidate_block.hash.startswith(self.difficulty_prefix):
            candidate_block.nonce += 1
            # In a real system, the timestamp would update. Here, it's less critical.
            # candidate_block.timestamp = time()
            candidate_block.hash = candidate_block.calculate_hash()
        
        print(f"[{node.id}] ✨ Mined block {candidate_block.height}! Nonce: {candidate_block.nonce}")
        return candidate_block

    def validate_and_resolve_chain(self, my_chain, peer_chain):
        """
        Validates a peer's chain and resolves forks using the "longest chain" rule.
        Returns the winning chain.
        """
        # Rule 1: The longer chain wins
        if len(peer_chain) <= len(my_chain):
            return my_chain

        # Rule 2: The incoming chain must be valid
        if not self.is_chain_valid(peer_chain):
            print("Received chain is invalid.")
            return my_chain
            
        # If we get here, the peer's chain is longer and valid. It's the winner.
        return peer_chain

    def is_chain_valid(self, chain_to_validate):
        """A simple check to ensure a chain's integrity by checking hashes."""
        for i in range(1, len(chain_to_validate)):
            if chain_to_validate[i].previous_hash != chain_to_validate[i-1].hash:
                return False
        return True
    


class HybridStakePoW:
    """Encapsulates the rules for a Stake-guided Hybrid consensus."""
    def __init__(self, light_difficulty):
        self.light_difficulty = light_difficulty
        self.difficulty_prefix = '0' * light_difficulty

    def get_leader(self, previous_block_hash, nodes, attempt):
        """
        Deterministically selects a leader for a given block height and attempt number.
        This is the core of the stake-based selection.
        """
        # 1. Combine hash and attempt number to create a unique, deterministic seed.
        #    Every node will do this and get the same result.
        seed = f"{previous_block_hash}-{attempt}"
        
        # 2. Use a local PRNG instance seeded with our value.
        local_rng = random.Random(seed)
        
        # 3. Perform weighted random selection based on node balances (stake).
        total_stake = sum(node.balance for node in nodes)
        if total_stake == 0:
            # Fallback in case all nodes have zero balance
            return local_rng.choice(nodes)

        pick = local_rng.uniform(0, total_stake)
        
        current = 0
        for node in nodes:
            current += node.balance
            if current > pick:
                return node
        
        # This part should ideally not be reached, but as a fallback:
        return nodes[-1]

    def mine_light_block(self, node, transactions):
        """
        Performs the lightweight PoW for the designated leader.
        This is very similar to the PoW mining, but with a lower difficulty.
        """
        head = node.get_chain_head()
        
        candidate_block = Block(
            height=head.height + 1,
            transactions=transactions,
            previous_hash=head.hash,
            creator=node.id
        )
        
        # The light work: a low-difficulty mining loop.
        while not candidate_block.hash.startswith(self.difficulty_prefix):
            candidate_block.nonce += 1
            candidate_block.hash = candidate_block.calculate_hash()
            
        print(f"[{node.id}] 👑 Mined block {candidate_block.height} as leader. Nonce: {candidate_block.nonce}")
        return candidate_block

    def validate_and_resolve_chain(self, my_chain, peer_chain):
        """For this hybrid model, the 'longest chain' rule remains a safe choice for resolving forks."""
        # Note: More advanced PoS systems use different fork-choice rules (e.g., GHOST, LMD),
        # but longest chain is sufficient and correct for this project.
        if len(peer_chain) <= len(my_chain):
            return my_chain

        if not self._is_chain_valid(peer_chain): # Use a private helper
            print("Received invalid peer chain.")
            return my_chain
            
        return peer_chain

    def _is_chain_valid(self, chain):
        for i in range(1, len(chain)):
            if chain[i].previous_hash != chain[i-1].hash:
                return False
        return True