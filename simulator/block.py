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

