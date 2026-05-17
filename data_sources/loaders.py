class Document:
    def __init__(self,content,metadata=None):
        self.content=content
        self.metadata=metadata or {}
    
        
    def load_pubmed_text(file_path):
        with open(file_path,"r",encoding="utf-8")as f:
            text=f.read()
            docs=text.split("\n\n")
            documents=[]
            for i,doc in enumerate(docs):
                if len(doc.strip())>50:
                    documents.append(Document(content=doc.strip(),metadata={"id":i}))
            return documents 
    