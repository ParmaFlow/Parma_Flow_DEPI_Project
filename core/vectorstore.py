import faiss
import numpy as np
class VectorStore:
    def __init__(self, dim):
        self.index = faiss.IndexFlat(dim)
        self.texts = []
        
    def add(self, embeddings, texts):
        self.index.add(np.array(embeddings, dtype=np.float32))
        self.texts.extend(texts)
        
    def search(self, query_embedding, k=3):
        distance, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32), k
        )
        results = [] 
        for idx in indices[0]: 
            results.append(self.texts[idx])
        return results