#!/usr/bin/env python3
"""MCP Server for TKA MongoDB – allows Claude Code to query the thekey-academy database."""

import json
import os
from datetime import datetime

from bson import ObjectId
from mcp.server.fastmcp import FastMCP
from pymongo import MongoClient

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://catja-ro:d1xBk6hepbJKQ9WH@thekey-academy-lms-prod.tyk6k.mongodb.net/thekey-academy"
    "?retryWrites=true&w=majority&appName=thekey-academy-lms-production&authSource=admin",
)
DB_NAME = os.environ.get("MONGO_DB", "thekey-academy")


def _json_serial(obj):
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.hex()
    raise TypeError(f"Type {type(obj)} not serializable")


def _serialize(doc):
    return json.loads(json.dumps(doc, default=_json_serial))


def _get_db():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    return client[DB_NAME]


mcp = FastMCP("tka-mongo", instructions="Query the TKA MongoDB (thekey-academy) database. Read-only access.")


@mcp.tool()
def list_collections() -> str:
    """List all collections in the thekey-academy database with document counts."""
    db = _get_db()
    result = []
    for name in sorted(db.list_collection_names()):
        count = db[name].estimated_document_count()
        result.append({"collection": name, "document_count": count})
    return json.dumps(result, indent=2)


@mcp.tool()
def collection_schema(collection: str, sample_size: int = 5) -> str:
    """Sample documents from a collection to understand its schema.

    Args:
        collection: Name of the MongoDB collection
        sample_size: Number of sample documents to return (default 5, max 20)
    """
    db = _get_db()
    sample_size = min(sample_size, 20)
    docs = list(db[collection].find().limit(sample_size))
    return json.dumps(_serialize(docs), indent=2, ensure_ascii=False)


@mcp.tool()
def find_documents(
    collection: str,
    filter: str = "{}",
    projection: str | None = None,
    sort: str | None = None,
    limit: int = 20,
    skip: int = 0,
) -> str:
    """Find documents in a collection with optional filtering, projection, and sorting.

    Args:
        collection: Name of the MongoDB collection
        filter: JSON string with MongoDB query filter (e.g. '{"status": "active"}')
        projection: JSON string with fields to include/exclude (e.g. '{"name": 1, "email": 1}')
        sort: JSON string with sort specification (e.g. '{"createdAt": -1}')
        limit: Maximum number of documents to return (default 20, max 100)
        skip: Number of documents to skip (for pagination)
    """
    db = _get_db()
    limit = min(limit, 100)
    query_filter = json.loads(filter)
    proj = json.loads(projection) if projection else None
    sort_spec = list(json.loads(sort).items()) if sort else None

    cursor = db[collection].find(query_filter, proj)
    if sort_spec:
        cursor = cursor.sort(sort_spec)
    cursor = cursor.skip(skip).limit(limit)

    docs = list(cursor)
    total = db[collection].count_documents(query_filter)
    return json.dumps(
        {"total": total, "returned": len(docs), "skip": skip, "documents": _serialize(docs)},
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def aggregate(collection: str, pipeline: str) -> str:
    """Run a MongoDB aggregation pipeline on a collection.

    Args:
        collection: Name of the MongoDB collection
        pipeline: JSON string with aggregation pipeline stages
    """
    db = _get_db()
    stages = json.loads(pipeline)
    results = list(db[collection].aggregate(stages))
    return json.dumps(
        {"count": len(results), "results": _serialize(results)},
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
def count_documents(collection: str, filter: str = "{}") -> str:
    """Count documents in a collection matching a filter.

    Args:
        collection: Name of the MongoDB collection
        filter: JSON string with MongoDB query filter
    """
    db = _get_db()
    query_filter = json.loads(filter)
    count = db[collection].count_documents(query_filter)
    return json.dumps({"collection": collection, "filter": query_filter, "count": count})


@mcp.tool()
def distinct_values(collection: str, field: str, filter: str = "{}") -> str:
    """Get distinct values for a field in a collection.

    Args:
        collection: Name of the MongoDB collection
        field: The field to get distinct values for
        filter: JSON string with MongoDB query filter
    """
    db = _get_db()
    query_filter = json.loads(filter)
    values = db[collection].distinct(field, query_filter)
    return json.dumps(
        {"collection": collection, "field": field, "count": len(values), "values": _serialize(values)},
        indent=2,
        ensure_ascii=False,
    )


if __name__ == "__main__":
    mcp.run()
