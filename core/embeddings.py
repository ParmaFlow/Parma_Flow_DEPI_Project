from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    def __init__(self):
        self.model =SentenceTransformer("all-miniLM-L6-v2")
        
    def embed(self,Texts):
        return self.model.encode(Texts)