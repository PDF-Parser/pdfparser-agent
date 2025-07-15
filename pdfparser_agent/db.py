import os
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://root:example@localhost:27017/")
MONGO_DB = os.environ.get("MONGO_DB", "pdfagent")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

def insert_document_metadata(document_path, processing_type, user_id):
    doc = {
        "document_path": document_path,
        "processing_type": processing_type,
        "user_id": user_id,
        "created_at": datetime.utcnow()
    }
    result = db.documents.insert_one(doc)
    return result.inserted_id

def insert_document_lines(document_id, lines):
    # lines: list of dicts with page_number, line_num_on_page, global_line_number, text
    for line in lines:
        line["document_id"] = document_id
    if lines:
        db.document_lines.insert_many(lines)

def get_lines(document_id, filter_query=None):
    query = {"document_id": ObjectId(document_id)}
    if filter_query:
        query.update(filter_query)
    return list(db.document_lines.find(query))

def get_document(document_id):
    return db.documents.find_one({"_id": ObjectId(document_id)})
