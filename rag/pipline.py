from rag.indexing import build_index
from rag.retriever import retrieve


class RAGPipeline:
    def __init__(self, file_path):
        self.store, self.embedder = build_index(file_path)

    def run(self, query):
        contexts = retrieve(query, self.store, self.embedder)

        context_text = "\n\n".join(contexts)

        # placeholder LLM
        answer = f"""
        Answer based on context:

        {context_text[:1000]}
        """

        return answer