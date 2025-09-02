# simulator/block.py

import hashlib
import json
from time import time

class Transaction:
    """A simple transaction to transfer coins."""
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount

    def to_dict(self):
        """Converts the transaction to a dictionary for serialization."""
        return self.__dict__

    def __repr__(self):
        """A user-friendly string representation of the transaction."""
        return f"Transaction(from: {self.sender}, to: {self.recipient}, amount: {self.amount})"


class Block:
    """The fundamental unit of the blockchain."""
    def __init__(self, height, transactions, previous_hash, creator):
        self.height = height
        self.transactions = transactions  # A list of Transaction objects
        self.previous_hash = previous_hash
        self.creator = creator
        self.timestamp = time()
        self.nonce = 0  # The nonce will be incremented during mining
        
        # The hash is calculated last, as it depends on all other attributes
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """
        Calculates the SHA-256 hash of the block.
        The block's data is first serialized to a JSON string.
        sort_keys=True is crucial for ensuring the hash is deterministic.
        """
        # We need to convert our list of transaction objects to a list of dictionaries
        transactions_as_dicts = [tx.to_dict() for tx in self.transactions]
        
        block_data = {
            "height": self.height,
            "transactions": transactions_as_dicts,
            "previous_hash": self.previous_hash,
            "creator": self.creator,
            "timestamp": self.timestamp,
            "nonce": self.nonce
        }
        
        # Convert the dictionary to a sorted JSON string, then encode it to bytes
        block_string = json.dumps(block_data, sort_keys=True).encode()
        
        # Return the hexadecimal representation of the hash
        return hashlib.sha256(block_string).hexdigest()

    def __repr__(self):
        """A user-friendly string representation of the block."""
        return f"Block(H: {self.height}, By: {self.creator}, Hash: {self.hash[:10]}...)"


# --- Self-Testing Block ---
# This code runs only when you execute this file directly (e.g., python3 simulator/block.py)
# It's a great way to test that your classes work as expected.
if __name__ == '__main__':
    # Create some sample transactions
    tx1 = Transaction(sender="N0", recipient="N1", amount=10)
    tx2 = Transaction(sender="N2", recipient="N3", amount=5)
    
    # Create the first block in the chain (the Genesis Block)
    genesis_block = Block(
        height=0, 
        transactions=[tx1], 
        previous_hash="0", 
        creator="System"
    )
    
    print("--- Genesis Block ---")
    print(genesis_block)
    print(f"Hash: {genesis_block.hash}")
    print(f"Nonce: {genesis_block.nonce}")
    print("-" * 20)

    # Create the next block in the chain
    block_1 = Block(
        height=1,
        transactions=[tx2],
        previous_hash=genesis_block.hash,
        creator="N0"
    )

    print("--- Block 1 ---")
    print(block_1)
    print(f"Hash: {block_1.hash}")
    print(f"Nonce: {block_1.nonce}")
    print(f"Previous Hash: {block_1.previous_hash}")
    print("-" * 20)
    
    # Verify that the previous_hash of Block 1 matches the hash of the Genesis Block
    assert block_1.previous_hash == genesis_block.hash
    print("Chain link verified: Block 1 correctly points to Genesis Block.")