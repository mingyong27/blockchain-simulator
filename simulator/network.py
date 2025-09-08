import random
from copy import deepcopy
import heapq

class Network:
    def __init__(self, *args, **kwargs):
        self.latency_min = kwargs.get("latency_min", kwargs.get("min_latency", 0))
        self.latency_max = kwargs.get("latency_max", kwargs.get("max_latency", 0))
        self.nodes = {}  # id -> Node
        self.current_time = 0  # in ms
        self.message_queue = []  
        self._counter = 0
        self.partition_groups = None  # None or list of sets

    def add_node(self, node):
        self.nodes[node.id] = node

    def _can_deliver(self, sender_id, recipient_id):
        if self.partition_groups is None:
            return True
        for grp in self.partition_groups:
            if sender_id in grp:
                return recipient_id in grp
        return True

    def broadcast(self, sender_id, message):
        for nid in list(self.nodes.keys()):
            if nid == sender_id:
                continue
            if not self._can_deliver(sender_id, nid):
                continue
            deliver_delay = random.randint(self.latency_min, self.latency_max)
            deliver_time = self.current_time + deliver_delay
            msg = {"type": message["type"], "time": message.get("time", self.current_time), "data": deepcopy(message["data"])}
            heapq.heappush(self.message_queue, (deliver_time, self._counter, nid, sender_id, msg))
            self._counter += 1

    def send_direct(self, sender_id, recipient_id, message):
        if recipient_id not in self.nodes:
            return
        if not self._can_deliver(sender_id, recipient_id):
            return
        deliver_delay = random.randint(self.latency_min, self.latency_max)
        deliver_time = self.current_time + deliver_delay
        msg = {"type": message["type"], "time": message.get("time", self.current_time), "data": deepcopy(message["data"])}
        heapq.heappush(self.message_queue, (deliver_time, self._counter, recipient_id, sender_id, msg))
        self._counter += 1

    def tick(self, elapsed_ms):
        self.current_time += elapsed_ms
        delivered = []
        while self.message_queue and self.message_queue[0][0] <= self.current_time:
            deliver_time, _, recipient_id, sender_id, msg = heapq.heappop(self.message_queue)
            node = self.nodes.get(recipient_id)
            if not node:
                continue
            delivered.append((node, msg))
        return delivered

    def partition(self, groups):
        self.partition_groups = [set(g) for g in groups]

    def heal(self):
        self.partition_groups = None