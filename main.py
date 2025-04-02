

import time
from pastry_node import PastryNode

def run_demo():
    # Create the first node (bootstrap node)
    bootstrap = PastryNode('127.0.0.1', 5000)
    print(f"Bootstrap node created with ID: {bootstrap.node_id}")
    
    # Create additional nodes that join the network
    nodes = [bootstrap]
    for i in range(1, 5):
        node = PastryNode('127.0.0.1', 5000 + i, ('127.0.0.1', 5000))
        nodes.append(node)
        print(f"Node {i} created with ID: {node.node_id}")
        time.sleep(0.5)  # Give time for the join to complete
    
    # Store some key-value pairs
    print("\nStoring key-value pairs...")
    keys = ["apple", "banana", "cherry", "date", "elderberry"]
    values = ["red", "yellow", "red", "brown", "purple"]
    
    for i, (key, value) in enumerate(zip(keys, values)):
        node = nodes[i % len(nodes)]
        result = node.store(key, value)
        print(f"Node {node.node_id} storing {key}={value}: {result}")
    
    # Look up the values
    print("\nLooking up values...")
    for i, key in enumerate(keys):
        node = nodes[(i + 2) % len(nodes)]  # Use a different node than the one that stored the key
        result = node.lookup(key)
        print(f"Node {node.node_id} looking up {key}: {result}")
    
    # Shutdown all nodes
    print("\nShutting down nodes...")
    for node in nodes:
        node.shutdown()

if __name__ == "__main__":
    run_demo()