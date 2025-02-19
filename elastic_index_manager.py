from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv
import typer
import functools
import json

# Load the .env file
load_dotenv()

# Access environment variables
ES_URL = os.getenv('ES_URL')
ES_API_KEY = os.getenv('ES_API_KEY')

SUGGEST_INDEX_NAME = "suggest_index"
SEARCH_INDEX_NAME = "search_index"
RERANKER_ID = "my-elastic-reranker"

app = typer.Typer()

def catch_exceptions(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"{func.__name__}: {e}")
    return wrapper

def create_suggest_index():
    es = Elasticsearch(ES_URL,api_key=ES_API_KEY)

    index_mapping = {
        "mappings": {
            "properties": {
                "title": {
                    "type": "text"
                },
                "suggest": {
                    "type": "completion"
                }
            }
        }
    }

    if es.indices.exists(index=SUGGEST_INDEX_NAME):
        print(f"Index already exists: {SUGGEST_INDEX_NAME}")
    else: 
        response = es.indices.create(index=SUGGEST_INDEX_NAME, body=index_mapping)
        if response['acknowledged'] == True:
            print(f"Index created: {SUGGEST_INDEX_NAME}")

def populate_suggest_index():
    es = Elasticsearch(ES_URL,api_key=ES_API_KEY)
    with open('suggest_index.jsonl', 'r') as file:
        for line in file:
            doc = json.loads(line)
            es.index(index=SUGGEST_INDEX_NAME, body=doc)
    print(f"Index populated with data: {SUGGEST_INDEX_NAME}")

def create_reranker():
    es = Elasticsearch(ES_URL,api_key=ES_API_KEY, request_timeout=300)
    inference_config = {
        "service": "elasticsearch",
        "task_type": "rerank",
        "service_settings": {
            "model_id": ".rerank-v1", 
            "num_threads": 1,
            "num_allocations": 1
        }
    }
  
    response = es.inference.put(inference_id=RERANKER_ID, body=inference_config)
    if response['inference_id'] == RERANKER_ID:
        print(f"Reranker created: {RERANKER_ID}")
    else: 
        print(f"Failed to create reranker: {response}")

def create_search_index():
    es = Elasticsearch(ES_URL,api_key=ES_API_KEY)

    index_mapping = {
        "mappings": {
            "properties": {
                "profile": {
                    "type": "text",
                    "copy_to": "profile_semantic",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "profile_semantic": {
                    "type": "semantic_text",
                    "inference_id": ".multilingual-e5-small-elasticsearch"
                }
            }
        }
    }

    if es.indices.exists(index=SEARCH_INDEX_NAME):
        print(f"Index already exists: {SEARCH_INDEX_NAME}")
    else: 
        response = es.indices.create(index=SEARCH_INDEX_NAME, body=index_mapping)
        if response['acknowledged'] == True:
            print(f"Index created: {SEARCH_INDEX_NAME}")

def populate_search_index():
    es = Elasticsearch(ES_URL,api_key=ES_API_KEY, request_timeout=60)
    with open('search_index.jsonl', 'r') as file:
        for line in file:
            doc = json.loads(line)
            es.index(index=SEARCH_INDEX_NAME, body=doc)
    print(f"Index populated with data: {SEARCH_INDEX_NAME}")

@app.command(help="Setup Elasticsearch indices and populate them with data.")
@catch_exceptions
def setup():
    create_reranker()
    create_suggest_index()
    populate_suggest_index()
    create_search_index()
    populate_search_index()
    
@app.command(help="Teardown and Setup.")
@catch_exceptions
def reload():
    teardown()
    setup()

@app.command(help="Teardown Elasticsearch indices. This will delete all demo data.")
def teardown():
    es = Elasticsearch(ES_URL,api_key=ES_API_KEY)
    if es.indices.exists(index=SUGGEST_INDEX_NAME):
        response = es.indices.delete(index=SUGGEST_INDEX_NAME)
        if response['acknowledged'] == True:
            print(f"Index deleted: {SUGGEST_INDEX_NAME}")
    if es.indices.exists(index=SEARCH_INDEX_NAME):
        response = es.indices.delete(index=SEARCH_INDEX_NAME)
        if response['acknowledged'] == True:
            print(f"Index deleted: {SEARCH_INDEX_NAME}")
    try:
        es.inference.get(inference_id=RERANKER_ID)
        response = es.inference.delete(inference_id=RERANKER_ID)
        if response['acknowledged'] == True:
            print(f"Reranker deleted: {RERANKER_ID}")
    except Exception as e:
        if "resource_not_found_exception" in str(e):
            print(f"Reranker does not exist. Delete Skipped: {RERANKER_ID}")
if __name__ == "__main__":
    app()
   