import ssl
import certifi
from Bio import Entrez
import time

ssl._create_default_https_context = ssl._create_unverified_context

class PubMedAPI:
    def __init__(self, email, api_key=None):
        Entrez.email = email 
        if api_key:
            Entrez.api_key = api_key
    
    def search(self, query, max_results=10):
        handle = Entrez.esearch(
            db="pubmed",
            term=query,
            retmax=max_results
        )

        record= Entrez.read(handle)
        return record["IdList"]

    
    def fetch_details(self, id_list):
        ids = ",".join(id_list)   
        handle = Entrez.efetch(
            db="pubmed",
            id=ids,
            rettype="abstract",
            retmode="text"
        )
        return handle.read()

    def fetch_papers(self, query, max_results = 10):
        ids = self.search(query, max_results)
        time.sleep(1)
        data = self.fetch_details(ids)
        return data