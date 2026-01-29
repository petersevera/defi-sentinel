# RAG Index

## What it does
Builds a Chroma vector index from event data (RSS + on-chain) using sentence-transformer
embeddings. Each event is converted into a text document (title + summary + source URL)
and chunked for retrieval.

## Run
- `pip install -r requirements.txt`
- `python scripts/build_rag_index.py`

## Query
- `python scripts/query_rag.py "what changed in aave governance"`

## Config
See `.env.example` or `docs/CONFIG.md` for:
- `CHROMA_PERSIST_DIR`
- `CHROMA_COLLECTION`
- `EMBEDDING_MODEL`
- `RAG_MAX_CHARS`
- `RAG_BATCH_SIZE`

## Notes
- The first run will download the embedding model.
- The index is stored locally in `data/chroma` (ignored by git).

