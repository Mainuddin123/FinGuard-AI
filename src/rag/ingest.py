
import hashlib
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

load_dotenv()

# Resolve paths relative to the FinGuard-AI project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

POLICY_DIR = PROJECT_ROOT / "data" / "policies"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

COLLECTION_NAME = "finguard_policies"
EMBEDDING_MODEL = "models/gemini-embedding-001"


def get_embeddings():
    """Initialize Gemini embeddings for policy documents."""
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        task_type="RETRIEVAL_DOCUMENT",
    )


def generate_document_id(document: Document) -> str:
    """Generate a deterministic ID for each policy chunk."""
    identity = (
        f"{document.metadata['source']}:"
        f"{document.metadata['chunk']}:"
        f"{document.page_content}"
    )

    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def ingest_policies():
    """Load, split and index financial policy documents."""

    if not POLICY_DIR.exists():
        raise FileNotFoundError(
            f"Policy directory not found: {POLICY_DIR}"
        )

    files = sorted(POLICY_DIR.glob("*.txt"))

    if not files:
        raise FileNotFoundError(
            "No .txt policy documents found in data/policies."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
    )

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
        embedding_function=get_embeddings(),
    )

    total_chunks = 0

    for file_path in files:
        content = file_path.read_text(encoding="utf-8")

        if not content.strip():
            print(f"Skipping empty policy: {file_path.name}")
            continue

        chunks = splitter.split_text(content)

        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "source": file_path.name,
                    "chunk": index,
                    "document_type": "demonstration_policy",
                },
            )
            for index, chunk in enumerate(chunks)
        ]

        ids = [
            generate_document_id(document)
            for document in documents
        ]

        # Remove previous chunks from this source before re-indexing.
        # This prevents outdated chunks remaining after policy updates.
        vector_store.delete(
            where={"source": file_path.name}
        )

        vector_store.add_documents(
            documents=documents,
            ids=ids,
        )

        total_chunks += len(documents)

        print(
            f"Indexed {file_path.name}: {len(documents)} chunks"
        )

    print("\nPolicy ingestion completed successfully.")
    print(f"Policy files discovered: {len(files)}")
    print(f"Chunks indexed: {total_chunks}")
    print(f"ChromaDB location: {CHROMA_DIR}")


if __name__ == "__main__":
    ingest_policies()
