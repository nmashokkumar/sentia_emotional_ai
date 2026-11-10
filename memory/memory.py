import os
import sqlite3
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer


# =============================
# CONFIG
# =============================
DB_PATH = "database/memory.db"
INDEX_PATH = "database/faiss.index"
ID_MAP_PATH = "database/id_map.pkl"
EMBEDDING_MODEL_PATH = "models/embedding_model"

RAM_MEMORY = []
MAX_RAM = 4


# =============================
# LOAD EMBEDDING MODEL (SAFE)
# =============================
def load_embedding_model():

    # If model exists locally → load
    if os.path.exists(EMBEDDING_MODEL_PATH):
        print("Loading embedding model from local...")
        return SentenceTransformer(EMBEDDING_MODEL_PATH)

    # If not → download once
    print("Downloading embedding model (one-time setup)...")

    try:
        model = SentenceTransformer("models/all-MiniLM-L6-v2")
        model.save(EMBEDDING_MODEL_PATH)

        print("Model downloaded and saved locally.")
        return model

    except Exception as e:
        print("❌ Failed to download embedding model.")
        print("Please connect to internet once.")
        exit()
model = load_embedding_model()


# =============================
# INIT DB
# =============================
def init_db():
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            response TEXT,
            emotion TEXT
        )
    """)

    conn.commit()
    conn.close()


# =============================
# INIT FAISS + ID MAP
# =============================
def init_faiss():
    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)
    else:
        index = faiss.IndexFlatL2(384)

    if os.path.exists(ID_MAP_PATH):
        with open(ID_MAP_PATH, "rb") as f:
            id_map = pickle.load(f)
    else:
        id_map = []

    return index, id_map


index, id_map = init_faiss()
init_db()


# =============================
# STORE MEMORY
# =============================
def store_memory(user_text, response, emotion):
    global RAM_MEMORY, id_map

    # ---- RAM MEMORY (Sliding Window) ----
    RAM_MEMORY.append({
        "user": user_text,
        "response": response
    })

    if len(RAM_MEMORY) > MAX_RAM:
        removed = RAM_MEMORY.pop(0)
        print("[RAM REMOVED]:", removed["user"])

    print("\n[RAM MEMORY STATE]")
    for i, m in enumerate(RAM_MEMORY, 1):
        print(f"{i}. {m['user']}")

    # ---- STORE IN SQLITE ----
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "INSERT INTO memory (user, response, emotion) VALUES (?, ?, ?)",
        (user_text, response, emotion)
    )

    row_id = c.lastrowid
    conn.commit()
    conn.close()

    # ---- FAISS EMBEDDING ----
    embedding = model.encode([user_text]).astype("float32")
    index.add(embedding)

    # ---- STORE ID MAP ----
    id_map.append(row_id)

    faiss.write_index(index, INDEX_PATH)

    with open(ID_MAP_PATH, "wb") as f:
        pickle.dump(id_map, f)


# =============================
# RETRIEVE MEMORY
# =============================
def retrieve_memory(user_text, k=3):

    results = []

    # ---- 1. RECENT RAM MEMORY ----
    if RAM_MEMORY:
        results.extend(RAM_MEMORY[-2:])

    # ---- 2. FAISS SEARCH ----
    if index.ntotal == 0:
        return results

    query = model.encode([user_text]).astype("float32")
    distances, indices = index.search(query, k)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for idx in indices[0]:
        if idx == -1 or idx >= len(id_map):
            continue

        db_id = id_map[idx]

        c.execute("SELECT user, response FROM memory WHERE id=?", (db_id,))
        row = c.fetchone()

        if row:
            results.append({
                "user": row[0],
                "response": row[1]
            })

    conn.close()

    return results