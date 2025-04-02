import hashlib
import socket
import threading
import json
from typing import Dict, List, Tuple, Optional, Any

from message_handler import process_message
from utils import hash_key, ID_BITS, ID_SPACE, ROUTING_TABLE_ROWS, ROUTING_TABLE_COLS, LEAF_SET_SIZE

class PastryNode:
    def __init__(self, ip: str, port: int, bootstrap_node: Optional[Tuple[str, int]] = None):
        self.ip = ip
        self.port = port
        self.node_id = self._generate_node_id(f"{ip}:{port}")
        
        # Data storage
        self.storage: Dict[int, Any] = {}
        
        # Routing tables
        self.routing_table = [[None for _ in range(ROUTING_TABLE_COLS)] for _ in range(ROUTING_TABLE_ROWS)]
        self.leaf_set_smaller: List[Tuple[int, str, int]] = []  # Nodes with smaller IDs
        self.leaf_set_larger: List[Tuple[int, str, int]] = []   # Nodes with larger IDs
        
        # Start the node server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((ip, port))
        self.server_socket.listen(5)
        
        print(f"Node {self.node_id} started at {ip}:{port}")
        
        # Start listening for connections in a separate thread
        self.running = True
        self.server_thread = threading.Thread(target=self._listen_for_connections)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Join the network if bootstrap node is provided
        if bootstrap_node:
            self.join_network(bootstrap_node)
    
    def _generate_node_id(self, seed: str) -> int:
        """Generate a unique node ID based on the IP:port."""
        hash_obj = hashlib.sha1(seed.encode())
        # Take first 16 bits (2 bytes) of the hash
        hash_bytes = hash_obj.digest()[:2]
        return int.from_bytes(hash_bytes, byteorder='big')
    
    def _listen_for_connections(self):
        """Listen for incoming connections from other nodes."""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                client_handler = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address)
                )
                client_handler.daemon = True
                client_handler.start()
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle incoming client connections."""
        try:
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Check if we have a complete message
                if b'\n' in data:
                    break
            
            if data:
                message = json.loads(data.decode('utf-8'))
                response = process_message(self, message)
                if response:
                    client_socket.sendall(json.dumps(response).encode('utf-8') + b'\n')
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
    
    def update_routing_tables(self, node_id: int, ip: str, port: int):
        """Update routing tables with a new node."""
        if node_id == self.node_id:
            return
        
        # Update leaf sets
        if node_id < self.node_id:
            # Add to smaller leaf set
            self.leaf_set_smaller.append((node_id, ip, port))
            self.leaf_set_smaller.sort(key=lambda x: x[0], reverse=True)  # Sort in descending order
            if len(self.leaf_set_smaller) > LEAF_SET_SIZE:
                self.leaf_set_smaller = self.leaf_set_smaller[:LEAF_SET_SIZE]
        else:
            # Add to larger leaf set
            self.leaf_set_larger.append((node_id, ip, port))
            self.leaf_set_larger.sort(key=lambda x: x[0])  # Sort in ascending order
            if len(self.leaf_set_larger) > LEAF_SET_SIZE:
                self.leaf_set_larger = self.leaf_set_larger[:LEAF_SET_SIZE]
        
        # Update routing table (simplified)
        # In a real implementation, this would use prefix matching
        node_id_bin = bin(node_id)[2:].zfill(ID_BITS)
        self_id_bin = bin(self.node_id)[2:].zfill(ID_BITS)
        
        # Find the row based on the first different bit
        for i in range(min(ROUTING_TABLE_ROWS, ID_BITS)):
            if node_id_bin[i] != self_id_bin[i]:
                # Calculate column based on the next 4 bits
                col_bits = node_id_bin[i:i+4]
                col = int(col_bits, 2) if len(col_bits) == 4 else int(col_bits + '0' * (4 - len(col_bits)), 2)
                
                if col < ROUTING_TABLE_COLS:
                    self.routing_table[i][col] = (node_id, ip, port)
                break
    
    def is_responsible_for_key(self, key_hash: int) -> bool:
        """Determine if this node is responsible for a key."""
        # Check if we have any nodes in our leaf sets
        if not self.leaf_set_smaller and not self.leaf_set_larger:
            return True
        
        # Check if the key is between this node and the closest smaller node
        if self.leaf_set_smaller and key_hash > self.leaf_set_smaller[0][0] and key_hash <= self.node_id:
            return True
        
        # Check if the key is between this node and the closest larger node
        if self.leaf_set_larger and key_hash > self.node_id and key_hash <= self.leaf_set_larger[0][0]:
            return True
        
        # Handle wrap-around in the ID space
        if self.leaf_set_smaller and self.leaf_set_larger:
            largest_node = max(self.leaf_set_larger, key=lambda x: x[0])[0]
            smallest_node = min(self.leaf_set_smaller, key=lambda x: x[0])[0]
            
            if self.node_id > largest_node and key_hash > self.node_id:
                return True
            if self.node_id < smallest_node and key_hash < self.node_id:
                return True
        
        return False
    
    def route_to_node(self, key_hash: int) -> Optional[Tuple[int, str, int]]:
        """Find the next node to route a message to for a given key."""
        # Check if the key is in the range of our leaf sets
        if self.leaf_set_smaller:
            for node in self.leaf_set_smaller:
                if key_hash <= node[0]:
                    return node
        
        if self.leaf_set_larger:
            for node in self.leaf_set_larger:
                if key_hash >= node[0]:
                    return node
        
        # Use the routing table (simplified)
        key_bin = bin(key_hash)[2:].zfill(ID_BITS)
        self_bin = bin(self.node_id)[2:].zfill(ID_BITS)
        
        for i in range(min(ROUTING_TABLE_ROWS, ID_BITS)):
            if key_bin[i] != self_bin[i]:
                # Calculate column based on the next 4 bits
                col_bits = key_bin[i:i+4]
                col = int(col_bits, 2) if len(col_bits) == 4 else int(col_bits + '0' * (4 - len(col_bits)), 2)
                
                if col < ROUTING_TABLE_COLS and self.routing_table[i][col]:
                    return self.routing_table[i][col]
                
                # If exact match not found, find the closest node
                for j in range(ROUTING_TABLE_COLS):
                    if self.routing_table[i][j]:
                        return self.routing_table[i][j]
        
        # If no suitable node found in routing table, return the closest node from leaf sets
        closest_node = None
        closest_distance = ID_SPACE
        
        for node in self.leaf_set_smaller + self.leaf_set_larger:
            distance = abs(node[0] - key_hash)
            if distance < closest_distance:
                closest_distance = distance
                closest_node = node
        
        return closest_node
    
    def send_message(self, ip: str, port: int, message: Dict) -> Dict:
        """Send a message to another node and get the response."""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((ip, port))
            
            # Send the message
            client_socket.sendall(json.dumps(message).encode('utf-8') + b'\n')
            
            # Receive the response
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Check if we have a complete message
                if b'\n' in data:
                    break
            
            client_socket.close()
            
            if data:
                return json.loads(data.decode('utf-8'))
            else:
                return {'status': 'error', 'message': 'No response received'}
        except Exception as e:
            print(f"Error sending message to {ip}:{port}: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def join_network(self, bootstrap_node: Tuple[str, int]):
        """Join the Pastry network through a bootstrap node."""
        try:
            # Send a JOIN message to the bootstrap node
            join_message = {
                'type': 'JOIN',
                'node_id': self.node_id,
                'ip': self.ip,
                'port': self.port
            }
            
            response = self.send_message(bootstrap_node[0], bootstrap_node[1], join_message)
            
            if response.get('status') == 'success':
                # Update our routing tables with the received information
                routing_info = response.get('routing_info', {})
                if routing_info:
                    # Process routing information
                    self.handle_routing_info({'routing_info': routing_info})
                    
                    print(f"Node {self.node_id} successfully joined the network")
                    return True
            
            print(f"Failed to join the network: {response.get('message', 'Unknown error')}")
            return False
        except Exception as e:
            print(f"Error joining network: {e}")
            return False
    
    def store(self, key: str, value: Any) -> Dict:
        """Store a key-value pair in the DHT."""
        key_hash = hash_key(key)
        
        # Check if this node is responsible for the key
        if self.is_responsible_for_key(key_hash):
            self.storage[key_hash] = value
            return {'status': 'success', 'message': 'Key stored successfully'}
        else:
            # Forward to the appropriate node
            store_message = {
                'type': 'STORE',
                'key': key,
                'value': value
            }
            
            next_node = self.route_to_node(key_hash)
            if next_node:
                return self.send_message(next_node[1], next_node[2], store_message)
            else:
                # If no suitable node found, store locally as a fallback
                self.storage[key_hash] = value
                return {'status': 'success', 'message': 'Key stored locally (fallback)'}
    
    def lookup(self, key: str) -> Dict:
        """Look up a value by key in the DHT."""
        key_hash = hash_key(key)
        
        # Check if this node has the key
        if key_hash in self.storage:
            return {'status': 'success', 'value': self.storage[key_hash]}
        
        # Check if this node is responsible for the key
        if self.is_responsible_for_key(key_hash):
            return {'status': 'error', 'message': 'Key not found'}
        
        # Forward to the appropriate node
        lookup_message = {
            'type': 'LOOKUP',
            'key': key
        }
        
        next_node = self.route_to_node(key_hash)
        if next_node:
            return self.send_message(next_node[1], next_node[2], lookup_message)
        else:
            return {'status': 'error', 'message': 'No route to key'}
    
    def handle_join(self, message: Dict) -> Dict:
        """Handle a join request from a new node."""
        new_node_id = message['node_id']
        new_node_ip = message['ip']
        new_node_port = message['port']
        
        # Update routing tables with the new node
        self.update_routing_tables(new_node_id, new_node_ip, new_node_port)
        
        # Return routing information to the new node
        return {
            'status': 'success',
            'routing_info': {
                'node_id': self.node_id,
                'leaf_set_smaller': self.leaf_set_smaller,
                'leaf_set_larger': self.leaf_set_larger,
                'routing_table': self.routing_table
            }
        }
    
    def handle_store(self, message: Dict) -> Dict:
        """Handle a request to store a key-value pair."""
        key = message['key']
        value = message['value']
        key_hash = hash_key(key)
        
        # Check if this node is responsible for the key
        if self.is_responsible_for_key(key_hash):
            self.storage[key_hash] = value
            return {'status': 'success', 'message': 'Key stored successfully'}
        else:
            # Forward to the appropriate node
            next_node = self.route_to_node(key_hash)
            if next_node:
                # Forward the store request
                forward_message = {
                    'type': 'STORE',
                    'key': key,
                    'value': value
                }
                response = self.send_message(next_node[1], next_node[2], forward_message)
                return response
            else:
                # If no suitable node found, store locally as a fallback
                self.storage[key_hash] = value
                return {'status': 'success', 'message': 'Key stored locally (fallback)'}
    
    def handle_lookup(self, message: Dict) -> Dict:
        """Handle a request to look up a value by key."""
        key = message['key']
        key_hash = hash_key(key)
        
        # Check if this node has the key
        if key_hash in self.storage:
            return {'status': 'success', 'value': self.storage[key_hash]}
        
        # Check if this node is responsible for the key
        if self.is_responsible_for_key(key_hash):
            return {'status': 'error', 'message': 'Key not found'}
        
        # Forward to the appropriate node
        next_node = self.route_to_node(key_hash)
        if next_node:
            # Forward the lookup request
            forward_message = {
                'type': 'LOOKUP',
                'key': key
            }
            response = self.send_message(next_node[1], next_node[2], forward_message)
            return response
        else:
            return {'status': 'error', 'message': 'No route to key'}
    
    def handle_routing_info(self, message: Dict) -> Dict:
        """Handle a request for routing information."""
        routing_info = message.get('routing_info', {})
        
        # Update our routing tables with the received information
        if routing_info:
            node_id = routing_info.get('node_id')
            leaf_set_smaller = routing_info.get('leaf_set_smaller', [])
            leaf_set_larger = routing_info.get('leaf_set_larger', [])
            routing_table = routing_info.get('routing_table', [])
            
            # Update our routing information with the received data
            for node in leaf_set_smaller + leaf_set_larger:
                if node and node[0] != self.node_id:
                    self.update_routing_tables(node[0], node[1], node[2])
            
            # Update with routing table entries
            for row in routing_table:
                for node in row:
                    if node and node[0] != self.node_id:
                        self.update_routing_tables(node[0], node[1], node[2])
        
        return {'status': 'success'}
    
    def shutdown(self):
        """Shutdown the node."""
        self.running = False
        self.server_socket.close()
        print(f"Node {self.node_id} shut down")