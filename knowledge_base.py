import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

class KnowledgeBase:
    def __init__(self, file_path):
        self.file_path = file_path
        self.vector_db = None
        self._initialize_kb()

    def _initialize_kb(self):
        print(f"Initializing Knowledge Base from {self.file_path}...")
        if not os.path.exists(self.file_path):
            print(f"Error: File {self.file_path} not found.")
            return

        loader = TextLoader(self.file_path, encoding='utf-8')
        documents = loader.load()
        
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(documents)
        
        # Use a lightweight local embedding model
        print("Loading embedding model...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_db = FAISS.from_documents(docs, embeddings)
        print("Knowledge Base initialized successfully.")

    def search(self, query, k=3):
        if not self.vector_db:
            return "Knowledge base not initialized."
        results = self.vector_db.similarity_search(query, k=k)
        return "\n\n".join([res.page_content for res in results])

if __name__ == "__main__":
    # Test
    kb = KnowledgeBase("tactiq-free-transcript-SsKkZTjUJEk.txt")
    print(kb.search("What is this transcript about?"))
