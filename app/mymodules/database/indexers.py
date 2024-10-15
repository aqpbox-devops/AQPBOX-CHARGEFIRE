import pygtrie
import pickle
import os
from typing import *

class CharTrieIndexer:
    def __init__(self, idx_path: str=None):
        super().__init__()

        self.tree = pygtrie.CharTrie()

        if idx_path is not None:
            self.idx_path = idx_path
            self.load_from_file()

    def info(self) -> str:
        return (f"[No. Trie keys: {len(self.tree)}]")

    def index(self, key: str, value: Any) -> None:
        to_store = str(value)

        words = key.replace(',', '').split()

        for word in words:
            for i in range(len(word)):
                if word[i:].lower() in self.tree:
                    self.tree[word[i:].lower()].add(to_store)
                else:
                    self.tree[word[i:].lower()] = {to_store}

    def save_to_file(self) -> None:
        if hasattr(self, 'idx_path'):
            with open(self.idx_path, 'wb') as f:
                pickle.dump(self.tree, f)

    def load_from_file(self) -> None:
        if hasattr(self, 'idx_path'):
            if os.path.exists(self.idx_path):
                with open(self.idx_path, 'rb') as f:
                    self.tree = pickle.load(f)

    def get_by(self, query: str) -> List[str]:
        query_words = query.split()
        
        found_values = None
        
        for word in query_words:
            if word.lower() in self.tree:
                if found_values is None:
                    found_values = self.tree[word.lower()].copy()
                else:
                    found_values &= self.tree[word.lower()]
            else:
                return []
            
        return list(found_values) if found_values else []