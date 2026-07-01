"""
Phase 2, Tasks 2.2–2.3 — Build the ChromaDB vector index from products.parquet.

Run with:  python scripts/build_index.py

What it does:
  1. Reads data/processed/products.parquet
  2. Sends each product's text_for_embedding to OpenAI in batches
  3. Stores the embeddings + metadata in ChromaDB at data/index/
"""
import os
import sys
import pandas as pd
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
BATCH_SIZE = 100  # OpenAI allows up to 2048 inputs per call; 100 is safe
INDEX_PATH = "data/index"
COLLECTION_NAME = "products"


def embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def main():
    print("Loading products.parquet...")
    df = pd.read_parquet("data/processed/products.parquet")
    print(f"  {len(df)} products loaded.")

    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print(f"\nConnecting to ChromaDB at '{INDEX_PATH}'...")
    chroma_client = chromadb.PersistentClient(path=INDEX_PATH)

    # Delete existing collection so re-runs start fresh
    try:
        chroma_client.delete_collection(COLLECTION_NAME)
        print("  Existing collection deleted.")
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    print(f"\nEmbedding {len(df)} products in batches of {BATCH_SIZE}...")
    total_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(df), BATCH_SIZE):
        batch = df.iloc[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  Batch {batch_num}/{total_batches}...", end=" ", flush=True)

        texts = batch["text_for_embedding"].tolist()
        embeddings = embed_batch(openai_client, texts)

        # Metadata stored alongside each embedding for filtering
        metadatas = [
            {
                "title":        str(row["title"]),
                "brand":        str(row["brand"])    if pd.notna(row["brand"])    else "",
                "category":     str(row["category"]) if pd.notna(row["category"]) else "",
                "price":        float(row["price"]),
                "rating":       float(row["rating"]) if pd.notna(row["rating"])   else -1.0,
                "availability": str(row["availability"]) if pd.notna(row["availability"]) else "",
                "source":       str(row["source"])   if pd.notna(row["source"])   else "",
            }
            for _, row in batch.iterrows()
        ]

        collection.add(
            ids=batch["id"].tolist(),
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        print("done")

    print(f"\nIndex built. Total vectors stored: {collection.count()}")
    print(f"Saved to '{INDEX_PATH}/'")


if __name__ == "__main__":
    main()
