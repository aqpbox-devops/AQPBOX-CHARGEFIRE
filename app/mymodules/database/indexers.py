import pickle
import os
from typing import Any, Dict, List, Tuple
from collections import defaultdict

def default_dict_factory():
    return {"_end": False, "values": set()}

class Trie:
    """
    Implement a trie with insert, search, and startsWith methods.
    """
    def __init__(self) -> None:
        self.root = defaultdict(default_dict_factory)

    def __len__(self) -> int:
        """Returns the total number of nodes in the trie."""
        return self._count_nodes(self.root)

    def _count_nodes(self, node: Dict[str, Any]) -> int:
        """Recursively counts the number of nodes in the trie."""
        count = 1  # Count the current node
        for key, value in node.items():
            if isinstance(value, dict) and key not in ("_end", "values"):
                count += self._count_nodes(value)
        return count

    def insert(self, word: str, value: Any) -> None:
        """Inserts a word into the trie with an associated value."""
        current = self.root
        for letter in word:
            current = current.setdefault(letter, default_dict_factory())
        current["_end"] = True  # Mark the end of the word
        current["values"].add(value)  # Store the associated value

    def search(self, word: str) -> List[Any]:
        """Returns the values associated with the word if it exists in the trie."""
        current = self.root
        for letter in word:
            if letter not in current:
                return []  # Return an empty list if the word is not found
            current = current[letter]
        if current["_end"]:
            return list(current["values"])  # Return the associated values
        return []

    def startsWith(self, prefix: str) -> Tuple[List[Any], Any]:
        """
        Returns all values associated with words that start with the given prefix,
        and a boolean indicating if the complete prefix exists as a word in the trie.
        """
        current = self.root
        for letter in prefix:
            if letter not in current:
                return [], None  # Return an empty list and False if the prefix is not found
            current = current[letter]
        
        values = self.get_subtree_values(current)
        exact_match = current["values"].copy() if current["_end"] else None
        return values, exact_match

    def get_subtree_values(self, node: Dict[str, Any]) -> List[Any]:
        """Returns all values in the subtree rooted at the given node."""
        values = set()
        if node["_end"]:
            values.update(node["values"])
        for child in node.values():
            if isinstance(child, dict) and child != node:
                values.update(self.get_subtree_values(child))
        return list(values)


class CharTrieIndexer:
    def __init__(self, idx_path: str=None):
        super().__init__()

        self.tree = Trie()

        if idx_path is not None:
            self.idx_path = idx_path
            self.load_from_file()

    def info(self) -> str:
        return (f"[No. Trie keys: {len(self.tree)}]")

    def index(self, key: str, value: Any) -> None:
        words = key.replace(',', '').split()

        for word in words:
            lword = word.lower()
            self.tree.insert(lword, value)

    def save_to_file(self) -> None:
        if hasattr(self, 'idx_path'):
            with open(self.idx_path, 'wb') as f:
                pickle.dump(self.tree, f)

    def load_from_file(self) -> None:
        if hasattr(self, 'idx_path'):
            if os.path.exists(self.idx_path):
                with open(self.idx_path, 'rb') as f:
                    self.tree = pickle.load(f)

    def get_by(self, query: str) -> Tuple[List[Any], Any]:
        query_words = query.split()
        
        found_values = None

        exact_match = None
        
        for word in query_words:
            lword = word.lower()
            exist = None
            if found_values is None:
                chunk_values, exist = self.tree.startsWith(lword)
                found_values = set(chunk_values)
            else:
                chunk_values, exist = self.tree.startsWith(lword)
                found_values &= set(chunk_values)

            if exist is not None:
                exact_match = exist

        print('???', type(exact_match))
        
        if exact_match is not None and len(exact_match) == 1:
            exact_match = exact_match.pop()
            found_values.discard(exact_match)

        else:
            exact_match = None
            
        return list(found_values), exact_match