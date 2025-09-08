import hashlib
import json
import time
import uuid

class Transaction:
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.id = str(uuid.uuid4())

    def to_dict(self):
        return {"id": self.id, "sender": self.sender, "recipient": self.recipient, "amount": self.amount}

    def __repr__(self):
        return f"Transaction(id={self.id[:8]}, from={self.sender}, to={self.recipient}, amount={self.amount})"

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class Block:
    def __init__(self, height, transactions, previous_hash, creator, timestamp=None, nonce=0):
        self.height = height
        self.transactions = list(transactions)  # list of Transaction objects
        self.previous_hash = previous_hash
        self.creator = creator
        self.timestamp = timestamp if timestamp is not None else int(time.time() * 1000)
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        tx_list = [tx.to_dict() for tx in self.transactions]
        block_data = {
            "height": self.height,
            "transactions": tx_list,
            "previous_hash": self.previous_hash,
            "creator": self.creator,
            "timestamp": self.timestamp,
            "nonce": self.nonce
        }
        block_bytes = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_bytes).hexdigest()
    
    def set_nonce(self, nonce):
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def is_valid(self):
        return self.hash == self.calculate_hash()

    def __repr__(self):
        return f"Block(H:{self.height}, creator={self.creator}, hash={self.hash[:10]}...)"