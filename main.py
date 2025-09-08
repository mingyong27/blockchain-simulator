import random
import argparse
from simulator.network import Network
from simulator.consensus import PoW, HybridStakePoW
from simulator.node import Node

SEED = 42

def run_scenario(name, consensus_cls, num_nodes=5, steps=2000, tick_ms=10,
                 delay_ms=100, partition_at_ms=None, heal_at_ms=None):
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
        # partition / heal
        if partition_at_ms is not None and t == partition_at_ms:
            print(f"[SCENARIO @ t={t}ms] Partitioning network: [N0, N1] | [N2, N3, N4]")
            network.partition([['N0', 'N1'], ['N2', 'N3', 'N4']])
        if heal_at_ms is not None and t == heal_at_ms:
            print(f"[SCENARIO @ t={t}ms] Healing network partition")
            network.heal()

        # create random tx
        if t > 0 and t % 300 == 0:
            sender = random.choice(nodes)
            recipient = random.choice([n for n in nodes if n is not sender])
            print(f"[SCENARIO @ t={t}ms] Creating transaction from {sender.id} to {recipient.id}")
            sender.create_and_broadcast_transaction(recipient.id, random.randint(1, 5))

        # deliver messages
        delivered = network.tick(tick_ms)
        for recipient, message in delivered:
            if message['type'] == 'new_tx':
                recipient.receive_transaction(message['data'])
            elif message['type'] == 'gossip_chain':
                recipient.receive_chain(message['data'], message.get('time', t))

        # consensus step
        if issubclass(consensus_cls, HybridStakePoW):
            head = nodes[0].get_chain_head()
            leader = consensus.get_leader(head.hash, nodes, attempt=0)
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

    # summary
    final_heads = {}
    for node in nodes:
        head = node.get_chain_head()
        print(f"  - Node {node.id}: Chain Height={head.height}, Head Hash={head.hash[:10]}...")
        final_heads[head.hash] = final_heads.get(head.hash, 0) + 1

    print(f"[SCENARIO] Final consensus check:")
    if len(final_heads) == 1:
        print(f"  Consensus Reached! All {len(nodes)} nodes agree.")
    else:
        print(f"  Consensus Failed! Nodes have different chain heads: {final_heads}")

def main():
    parser = argparse.ArgumentParser(description="Blockchain Simulator Scenarios")
    parser.add_argument("--consensus", choices=["pow", "hybrid"], default="pow")
    parser.add_argument("--steps", type=int, default=5000)
    parser.add_argument("--delay", type=int, default=150)
    parser.add_argument("--partition_at", type=int, default=None)
    parser.add_argument("--heal_at", type=int, default=None)
    parser.add_argument("--nodes", type=int, default=5)
    args = parser.parse_args()

    random.seed(SEED)

    if args.consensus == "pow":
        run_scenario(
            name="PoW with Delay" if args.partition_at is None else "PoW with Partition",
            consensus_cls=PoW,
            num_nodes=args.nodes,
            steps=args.steps,
            delay_ms=args.delay,
            partition_at_ms=args.partition_at,
            heal_at_ms=args.heal_at,
        )
    else:
        run_scenario(
            name="Hybrid with Delay" if args.partition_at is None else "Hybrid with Partition",
            consensus_cls=HybridStakePoW,
            num_nodes=args.nodes,
            steps=args.steps,
            delay_ms=args.delay,
            partition_at_ms=args.partition_at,
            heal_at_ms=args.heal_at,
        )

if __name__ == "__main__":
    main()
