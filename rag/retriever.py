def retrieve(query, store, embedder, k=3):
    query_embedding = embedder.embed([query])[0]
    results = store.search(query_embedding, k)
    return results