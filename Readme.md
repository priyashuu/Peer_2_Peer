# P2P-KeyNet  Implementation

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
   python main.py
```
