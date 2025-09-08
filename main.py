import random
from collections import Counter
from simulator.network import Network
from simulator.consensus import PoW, HybridStakePoW
from simulator.node import Node

SEED = 42
random.seed(SEED)

def _deliver_all(network, tick_ms):
    delivered = network.tick(tick_ms)
    for recipient, message in delivered:
        if message["type"] == "new_tx":
            recipient.receive_transaction(message["data"])
        elif message["type"] == "gossip_chain":
            recipient.receive_chain(message["data"], message.get("time", 0))

def run_scenario(name, consensus_cls, num_nodes=5, steps=2000, tick_ms=10, delay_ms=100, partition_at_ms=None, heal_at_ms=None, settle_ms=2000):
    print(f"\n=== RUNNING SCENARIO: {name} | Consensus={consensus_cls.__name__} ===")
    network = Network(latency_min=delay_ms, latency_max=delay_ms + 50)
    consensus = consensus_cls(difficulty=2 if issubclass(consensus_cls, HybridStakePoW) else 3)
    nodes = []
    for i in range(num_nodes):
        balance = 200 if i == 0 and issubclass(consensus_cls, HybridStakePoW) else 100
        node = Node(node_id=f"N{i}", network=network, balance=balance, consensus_algo=consensus)
        nodes.append(node)
    print(f"Created {len(nodes)} nodes.")
    for t in range(0, steps, tick_ms):
        if partition_at_ms is not None and t == partition_at_ms:
            print(f"[SCENARIO @ t={t}ms] Partitioning network: [N0, N1] | [N2, N3, N4]")
            network.partition([["N0", "N1"], ["N2", "N3", "N4"]])
        if heal_at_ms is not None and t == heal_at_ms:
            print(f"[SCENARIO @ t={t}ms] Healing network partition")
            network.heal()
        if t > 0 and t % 300 == 0:
            sender = random.choice(nodes)
            recipient = random.choice([n for n in nodes if n is not sender])
            print(f"[SCENARIO @ t={t}ms] Creating transaction from {sender.id} to {recipient.id}")
            sender.create_and_broadcast_transaction(recipient.id, random.randint(1, 5))
        _deliver_all(network, tick_ms)
        if issubclass(consensus_cls, HybridStakePoW):
            head_counts = Counter(n.get_chain_head().hash for n in nodes)
            common_head = head_counts.most_common(1)[0][0]
            head_node = next(n for n in nodes if n.get_chain_head().hash == common_head)
            leader = consensus.get_leader(head_node.get_chain_head().hash, nodes, attempt=0)
            if leader.mempool:
                new_block = leader.consensus.mine_light_block(leader, leader.mempool[:2], t, leader.logger)
                if new_block:
                    leader.chain.append(new_block)
                    included_ids = {tx.id for tx in new_block.transactions}
                    leader.mempool = [tx for tx in leader.mempool if tx.id not in included_ids]
                    leader.network.broadcast(leader.id, {"type": "gossip_chain", "time": t, "data": leader.chain[:]})
                    leader.check_and_update_finality(t)
        else:
            miner = random.choice(nodes)
            miner.tick(t)
    settle_steps = max(0, settle_ms // tick_ms)
    for _ in range(settle_steps):
        _deliver_all(network, tick_ms)
    final_chain_heads = {}
    for node in nodes:
        head = node.get_chain_head()
        print(f"  - Node {node.id}: Chain Height={head.height}, Head Hash={head.hash[:10]}...")
        final_chain_heads[head.hash] = final_chain_heads.get(head.hash, 0) + 1
    print(f"[SCENARIO] Final consensus check:")
    if len(final_chain_heads) == 1:
        print(f"  Consensus Reached! All {num_nodes} nodes agree.")
    else:
        print(f"  Consensus Failed! Nodes have different chain heads: {final_chain_heads}")

run_scenario(
    name="PoW with Delay",
    consensus_cls=PoW,
    steps=5000,
    delay_ms=150
)

run_scenario(
    name="Hybrid with Delay",
    consensus_cls=HybridStakePoW,
    steps=5000,
    delay_ms=150
)

run_scenario(
    name="Hybrid with Partition",
    consensus_cls=HybridStakePoW,
    steps=10000,
    delay_ms=100,
    partition_at_ms=1000,
    heal_at_ms=5000
)
