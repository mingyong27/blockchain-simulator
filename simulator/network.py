# simulator/network.py

import random

class Network:
    """Simulates the network layer, including message delays."""
    def __init__(self, latency_min, latency_max):
        self.nodes = {}  
        self.message_queue = []
        self.latency_min = latency_min
        self.latency_max = latency_max
        self.is_partitioned = False
        self.partition_groups = []

    def partition(self, groups):
        """Splits the network into isolated groups of node IDs."""
        self.is_partitioned = True
        # Using sets for efficient 'in' checks
        self.partition_groups = [set(g) for g in groups]
        print(" NETWORK PARTITIONED")

    def heal(self):
        """Rejoins the network into a single group."""
        self.is_partitioned = False
        self.partition_groups = []
        print(" NETWORK HEALED")

    def add_node(self, node):
        self.nodes[node.id] = node

    def broadcast(self, sender_id, message):
        if not self.is_partitioned:
            for node_id, recipient_node in self.nodes.items():
                if node_id != sender_id:
                    delay = random.randint(self.latency_min, self.latency_max)
                    self.message_queue.append((delay, recipient_node, message))
        else:
            sender_group = None
            for group in self.partition_groups:
                if sender_id in group:
                    sender_group = group
                    break
            
            if sender_group:
                for node_id in sender_group:
                    if node_id != sender_id:
                        recipient_node = self.nodes[node_id]
                        delay = random.randint(self.latency_min, self.latency_max)
                        self.message_queue.append((delay, recipient_node, message))
        

    def tick(self, time_step):
        delivered_messages = []
        remaining_messages = []
        for (delay, recipient, message) in self.message_queue:
            if delay <= time_step:
                delivered_messages.append((recipient, message))
            else:
                remaining_messages.append((delay - time_step, recipient, message))
        
        self.message_queue = remaining_messages
        
        return delivered_messages