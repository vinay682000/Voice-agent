"""
Knowledge Base Module
Automatically loads all documents from the 'knowledge/' folder.
Supports: .txt, .md files
"""
import os
import glob
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


# Default folder for knowledge documents
KNOWLEDGE_FOLDER = "knowledge"

# Supported file extensions
SUPPORTED_EXTENSIONS = [".txt", ".md"]


class KnowledgeBase:
    def __init__(self, folder_path=KNOWLEDGE_FOLDER):
        """
        Initialize Knowledge Base from a folder of documents.
        
        Args:
            folder_path: Path to folder containing knowledge documents.
                         Defaults to 'knowledge/' folder.
        """
        self.folder_path = folder_path
        self.vector_db = None
        self.loaded_files = []
        self._initialize_kb()

    def _get_all_documents(self):
        """Find all supported documents in the knowledge folder."""
        documents = []
        
        # Create folder if it doesn't exist
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)
            print(f"Created knowledge folder: {self.folder_path}/")
            print("Add your .txt or .md files to this folder.")
            return documents
        
        # Find all supported files
        for ext in SUPPORTED_EXTENSIONS:
            pattern = os.path.join(self.folder_path, f"*{ext}")
            files = glob.glob(pattern)
            for file_path in files:
                try:
                    loader = TextLoader(file_path, encoding='utf-8')
                    docs = loader.load()
                    documents.extend(docs)
                    self.loaded_files.append(os.path.basename(file_path))
                    print(f"  ✓ Loaded: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"  ✗ Error loading {file_path}: {e}")
        
        return documents

    def _initialize_kb(self):
        """Initialize the vector database from all documents."""
        print(f"Initializing Knowledge Base from '{self.folder_path}/' folder...")
        
        # Load all documents
        documents = self._get_all_documents()
        
        if not documents:
            print("⚠️  No documents found. Add .txt or .md files to the knowledge/ folder.")
            return
        
        # Split documents into chunks
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(documents)
        
        # Create embeddings and vector store
        print("Loading embedding model...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_db = FAISS.from_documents(docs, embeddings)
        
        print(f"✅ Knowledge Base ready! Loaded {len(self.loaded_files)} file(s), {len(docs)} chunks.")

    def search(self, query, k=3):
        """Search the knowledge base for relevant content."""
        if not self.vector_db:
            return "Knowledge base not initialized. Add documents to the 'knowledge/' folder."
        results = self.vector_db.similarity_search(query, k=k)
        return "\n\n".join([res.page_content for res in results])
    
    def list_files(self):
        """Return list of loaded files."""
        return self.loaded_files
    
    def reload(self):
        """Reload all documents (call after adding new files)."""
        self.loaded_files = []
        self.vector_db = None
        self._initialize_kb()


if __name__ == "__main__":
    # Test
    kb = KnowledgeBase()
    print(f"\nLoaded files: {kb.list_files()}")
    if kb.vector_db:
        print("\nTest search: 'What is this about?'")
        print(kb.search("What is this about?"))
