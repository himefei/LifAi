from typing import Dict, List
import chromadb
import os

class AgentMemory:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("agent_memory")
        
    def store(self, text: str, metadata: Dict = None):
        # Store information in vector database
        pass
        
    def retrieve(self, query: str, n_results: int = 5) -> List[Dict]:
        # Retrieve relevant information
        pass 