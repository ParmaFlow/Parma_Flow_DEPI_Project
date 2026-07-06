def chunk_text(text, chunk_size=300, overlap=50):
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def chunk_documents (documents):
    all_chunks = []
    
    for doc in documents:
        chunks = chunk_text(doc.content)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "content":chunk, 
                "metadata": doc.metadata 
                })
    return all_chunks
        
