# main.py

import random
from simulator.node import Node
from simulator.network import Network
from simulator.block import Transaction 
from simulator.consensus import PoW, HybridStakePoW
from simulator.logger import setup_logger, log_event

import logging
import json
import os

LOG_FILE = "simulation_log.jsonl"
SEED = 42
random.seed(SEED)

NUM_NODES = 5
STARTING_BALANCE = 100
SIMULATION_DURATION_MS = 5000  
TICK_INTERVAL_MS = 10        

LATENCY_MIN_MS = 50
LATENCY_MAX_MS= 200

HYBRID_LIGHT_DIFFICULTY = 2
LEADER_TIMEOUT_MS = 1000

DIFFICULTY = 4 

def run_pow_simulation():
    """Sets up and runs the Proof of Work simulation with separated consensus."""
    print("--- Initializing PoW Simulation ---")
    
    # --- 1. Set up Consensus Algorithm ---
    # We create the PoW consensus object with the network's difficulty.
    pow_consensus = PoW(difficulty=DIFFICULTY)  # <--- KEY CHANGE
    print(f"Using consensus: PoW with Difficulty={DIFFICULTY}")
    
    # --- 2. Set up Network and Nodes ---
    network = Network(latency_min=LATENCY_MIN_MS, latency_max=LATENCY_MAX_MS)
    nodes = []
    for i in range(NUM_NODES):
        # We pass the consensus object to each node.
        node = Node(  # <--- KEY CHANGE
            node_id=f"N{i}",
            network=network,
            balance=STARTING_BALANCE,
            consensus_algo=pow_consensus
        )
        nodes.append(node)
        network.add_node(node)
        
    print(f"Created {len(nodes)} nodes.")
    print("\n--- Starting Simulation Loop ---")
    
    # The Main Simulation Loop
    for t in range(0, SIMULATION_DURATION_MS, TICK_INTERVAL_MS):
        # 1. Create random transactions to keep the network busy
        if t > 0 and t % 200 == 0:  # <--- DYNAMIC TRANSACTIONS
            sender = random.choice(nodes)
            recipient = random.choice([n for n in nodes if n is not sender])
            tx = Transaction(sender.id, recipient.id, random.randint(1, 5))
            sender.mempool.append(tx)
            sender.network.broadcast(sender.id, {"type": "new_tx", "data": tx})

        # 2. Process message delivery
        delivered = network.tick(TICK_INTERVAL_MS)
        for recipient, message in delivered:
            if message['type'] == 'new_tx':
                recipient.receive_transaction(message['data'])
            elif message['type'] == 'gossip_chain':  
                recipient.receive_chain(message['data'])

        # 3. Trigger node actions (mining)
        miner_node = random.choice(nodes)
        miner_node.tick()  

    print(f"\n--- Simulation Finished at {SIMULATION_DURATION_MS/1000.0}s ---")
    final_chain_heads = {}
    for node in nodes:
        head = node.get_chain_head()
        print(f"  - Node {node.id}: Chain Height={head.height}, Head Hash={head.hash[:15]}...")
        final_chain_heads[head.hash] = final_chain_heads.get(head.hash, 0) + 1

    print("\n--- Consensus Check ---")
    if len(final_chain_heads) == 1:
        print(f"Consensus Reached! All {NUM_NODES} nodes agree on the same chain head.")
    else:
        print(f"Consensus Failed! Nodes have different chain heads:")
        for h, count in final_chain_heads.items():
            print(f"  - Hash {h[:15]}... is the head for {count} node(s).")



def run_hybrid_simulation():
    """Sets up and runs the Stake-Guided Hybrid simulation."""
    print("--- Initializing Hybrid (Stake + Light PoW) Simulation ---")

    # 1. Set up Consensus Algorithm
    hybrid_consensus = HybridStakePoW(light_difficulty=HYBRID_LIGHT_DIFFICULTY)
    print(f"Using consensus: Hybrid with Light PoW Difficulty={HYBRID_LIGHT_DIFFICULTY}")
    
    # 2. Set up Network and Nodes
    network = Network(latency_min=LATENCY_MIN_MS, latency_max=LATENCY_MAX_MS)
    nodes = []
    for i in range(NUM_NODES):
        balance = 200 if i == 0 else 100
        node = Node(
            node_id=f"N{i}",
            network=network,
            balance=balance,
            consensus_algo=hybrid_consensus 
        )
        nodes.append(node)
        network.add_node(node)
        
    print(f"Created {len(nodes)} nodes with varying stakes.")

    # State variables for the leader-based simulation
    current_height = 0
    leader_attempt = 0
    time_of_last_block = 0
    
    print("\n--- Starting Simulation Loop ---")
    
    for t in range(0, SIMULATION_DURATION_MS, TICK_INTERVAL_MS):
        # --- 1. Leader Timeout Logic ---
        if t - time_of_last_block > LEADER_TIMEOUT_MS:
            print(f"[Time: {t:04d}ms] LEADER TIMEOUT! Leader for height {current_height+1} failed.")
            leader_attempt += 1 # Move to the next backup leader
            time_of_last_block = t # Reset the timer

        # --- 2. Create random transactions ---
        if t % 300 == 0 and t > 0: 
             sender = random.choice(nodes)
             recipient = random.choice([n for n in nodes if n is not sender])
             tx = Transaction(sender.id, recipient.id, random.randint(1, 5))
             sender.mempool.append(tx)
             sender.network.broadcast(sender.id, {"type": "new_tx", "data": tx})

        # --- 3. Process message delivery ---
        delivered = network.tick(TICK_INTERVAL_MS)
        for recipient, message in delivered:
            if message['type'] == 'new_tx':
                recipient.receive_transaction(message['data'])
            elif message['type'] == 'gossip_chain':
                previous_height = recipient.get_chain_head().height
                recipient.receive_chain(message['data'])
                # If a new block was successfully accepted, reset the leader logic
                if recipient.get_chain_head().height > previous_height:
                    current_height = recipient.get_chain_head().height
                    leader_attempt = 0
                    time_of_last_block = t
                    print(f"[Time: {t:04d}ms] Network advanced to height {current_height}.")


        canonical_head = network.nodes["N0"].get_chain_head()
        if canonical_head.height >= current_height:
             current_height = canonical_head.height

        leader = hybrid_consensus.get_leader(canonical_head.hash, nodes, leader_attempt)
        if leader.mempool:
            new_block = leader.consensus.mine_light_block(leader, leader.mempool[:2])
            if new_block:
                leader.chain.append(new_block)
                leader.mempool = [tx for tx in leader.mempool if tx not in new_block.transactions]
                leader.network.broadcast(leader.id, {"type": "gossip_chain", "data": leader.chain})
        
        if t == 5000:
            network.partition([['N0', 'N1'], ['N2', 'N3', 'N4']])
        if t == 15000:
            network.heal()
    
def setup_logger():
    """Sets up a logger to output structured JSON data to a file."""
    # Ensure the log file is empty before a new run
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    handler = logging.FileHandler(LOG_FILE)
    logger = logging.getLogger('simulator')
    logger.setLevel(logging.INFO)
    # Remove any existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(handler)
    return logger

def log_event(logger, event_data):
    """Logs a dictionary as a JSON string line."""
    logger.info(json.dumps(event_data))



# This makes the script runnable
if __name__ == "__main__":
    SIMULATION_MODE = "POW"  

    if SIMULATION_MODE == "POW":
        run_pow_simulation()
    elif SIMULATION_MODE == "HYBRID":
        run_hybrid_simulation()