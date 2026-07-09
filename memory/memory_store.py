# Retrieve database setting
from config.config import memory_db

# Import tinydb for memories management
from tinydb import TinyDB, Query

memories_db = TinyDB(memory_db)

def add_memory(memory_type, id, content):
    memories_db.insert({'type': memory_type, 'id': id, 'content': content})

def get_all_memories():
    return memories_db.all()

def search_memories(query):
    results = []
    for memory in memories_db.all():
        if query.lower() in memory['content'].lower() or query.lower() in memory['id'].lower():
            results.append(memory)

    return results

def get_memories_by_type(memory_type):
    Memory = Query()
    return memories_db.search(Memory.type == memory_type)