# Pastry DHT Implementation

A minimal implementation of the Pastry Distributed Hash Table (DHT) algorithm for peer-to-peer networks.

## Features

- Node ID generation and management
- Routing table and leaf set maintenance
- Key-value storage and retrieval
- Node joining mechanism
- Socket-based communication between nodes

## Technologies Used

- **Python**: Core programming language
- **Socket Programming**: For communication between nodes
- **Threading**: To handle concurrent connections
- **Hashing (SHA-1)**: For generating node IDs and key hashes
- **JSON**: For message serialization and deserialization

## Project Structure

- `main.py`: Demo script to run the DHT network
- `pastry_node.py`: Core implementation of the Pastry node, including:
  - Node initialization
  - Routing table and leaf set management
  - Key-value storage and retrieval
  - Message routing and handling
- `message_handler.py`: Processes incoming messages and delegates them to appropriate handlers
- `utils.py`: Utility functions and constants, including:
  - Hashing functions
  - Configuration constants (e.g., ID space, routing table size)

## Usage

### Running the Demo

1. Clone the repository to your local machine.
2. Navigate to the project directory:
   ```bash
   cd d:\Peer_2_Peer
   ```
Run the demo script 
```bash
   pyhton main.py
```
Key Operations
Store a Key-Value Pair: Nodes can store key-value pairs in the DHT.
Lookup a Key: Nodes can retrieve values associated with a key from the DHT.
Join the Network: New nodes can join the network dynamically.
How It Works
Node Initialization:

Each node generates a unique ID based on its IP and port using SHA-1 hashing.
Nodes maintain routing tables and leaf sets for efficient message routing.
Key-Value Storage:

Keys are hashed to determine their position in the ID space.
The node responsible for the key stores the value.
Message Routing:

Messages are routed to the appropriate node using the Pastry algorithm.
Routing tables and leaf sets ensure efficient and fault-tolerant routing.
Node Joining:

New nodes join the network by contacting a bootstrap node.
The new node's routing tables and leaf sets are updated based on the network's state.
Future Enhancements
Add fault tolerance for node failures.
Implement replication for data redundancy.
Optimize routing table updates for large networks.
References
Pastry: Scalable, Decentralized Object Location and Routing for Large-Scale Peer-to-Peer Systems
