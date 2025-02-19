from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from elasticsearch import Elasticsearch
import os
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from fastapi import Form

app = FastAPI()

load_dotenv()

# Access environment variables
ES_URL = os.getenv('ES_URL')
ES_API_KEY = os.getenv('ES_API_KEY')

SUGGEST_INDEX_NAME = "suggest_index"
SEARCH_INDEX_NAME = "search_index"
RERANKER_ID = "my-elastic-reranker"
CROSS_ENCODER_ENABLED = False

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_index():
    """
    Serve the 'index.html' file at the root URL ("/").
    """
    return FileResponse("static/index.html")

def get_search_query(searchInput: str):
    """
    Construct the search query for Elasticsearch.
    """
    cross_encoder_query = {
        "size": 10,
        "_source": "false",
        "fields": ["title", "specialty", "profile", "address", "gender", "age", "phone"],
        "retriever": {
            "text_similarity_reranker": {
                "retriever": 
                {
                    "standard": {
                        "query": {
                            "bool": { 
                                "should": [
                                    {"semantic": {
                                        "field": "profile_semantic",
                                        "query": f"{searchInput}"
                                    }},
                                    {"multi_match": {
                                        "query": f"{searchInput}",
                                        "fields": ["profile", "specialty", "title", "gender", "address", "phone"]
                                    }}
                                ]
                            }
                        }
                    }
                },
                "field": "profile",
                "inference_id": RERANKER_ID,
                "inference_text": searchInput,
                "rank_window_size": 20
            }
        }
    }
    rrf_query = {
        "size": 10,
        "_source": "false",
        "fields": ["title", "specialty", "profile", "address", "gender", "age", "phone"],
        "retriever": {
            "rrf": {
                "retrievers": [
                    {
                    "standard": {
                        "query": {
                        "semantic": {
                            "field": "profile_semantic",
                            "query": f"{searchInput}"
                        }
                        }
                    }
                    },
                    {
                    "standard": {
                        "query": {
                            "multi_match": {
                                "query": f"{searchInput}",
                                "fields": ["profile", "specialty", "title", "gender", "address", "phone"]
                            }
                        }
                    }
                    }
                ],
                "rank_window_size": 20,
                "rank_constant": 100
                }
            }
    }
    if CROSS_ENCODER_ENABLED:
        print("Using cross-encoder query")
        return cross_encoder_query
    else:
        print("Using rrf query")
        return rrf_query

@app.post("/search")
def search(searchInput: str = Form(...)):
    """
    Endpoint to handle search form submission.
    """
    es = Elasticsearch(ES_URL,api_key=ES_API_KEY)

    query = get_search_query(searchInput)

    response = es.search(index=SEARCH_INDEX_NAME, body=query)
    print("search response: ", response)

    # Extract only the hits fields
    hits = response.get('hits', {}).get('hits', [])
    hits_fields = [hit.get('fields', {}) for hit in hits]
    return {"hits": hits_fields}

@app.get("/autocomplete")
def get_autocomplete(query: str = Query(None)):
    
    """
    Endpoint to provide autocomplete suggestions using Elasticsearch completion suggester.
    """

    if not query:
        return JSONResponse([])
    
    # The completion suggester query
    es = Elasticsearch(ES_URL,api_key=ES_API_KEY)
    es_query = {
        "suggest": {
            "suggestions": {  # 'suggestions' is an arbitrary name
                "prefix": query,  # The partial query from the user
                "completion": {
                    "skip_duplicates": True, 
                    "field": "suggest",
                    "fuzzy": {  # optional fuzzy matching settings - up to 2 character changes (must be 0-2)
                        "fuzziness": 2
                    }
                }
            }
        }
    }

    # Execute search
    result = es.search(index=SUGGEST_INDEX_NAME, body=es_query)

    # Parse the suggestions
    suggestions = []

    for suggest_item in result["suggest"]["suggestions"]:
        for option in suggest_item["options"]:
            # "text" will be the suggested completion string
            suggestions.append(option["text"])

    # Return suggestions as a JSON array of objects with a 'label' property
    print("autocomplete suggestions: ", suggestions)
    return JSONResponse(suggestions)