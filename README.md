# Quickstart 
This demo is packaged with a sample data set that was used for a custom "find a doctor" demo that was originally built to agument a customer workshop.
This code can be modified to support ANY use case. The demo showcases the following features:

1. Suggesters - AKA autocomplete
2. Full Text Search - "profile", "specialty", "title", "gender", "address", "phone" 
3. Semantic Search - "profile" vectorized via E5
4. Elastic Reranker or RRF - You can toggle between the 2 options by changing `CROSS_ENCODER_ENABLED` in app.py

## Setup

Create a `.env` file that has the following properties:

```
ES_URL=YOUR_ES_URL
ES_API_KEY=YOUR_API_KEY
```

Open a terminal and run the following commands

### Install dependencies

```
pip install poetry
poetry install
```

### Setup Elasticsearch indexes

```
python elastic_index_manager.py setup
```

### Run web application
```
poetry run uvicorn app:app --reload 
```

Open a browser to [http://localhost:8000](http://localhost:8000)

Type the following text to trigger multiple suggestions:

```imm```

Type the following text to trigger a single suggestion with fuzzy match:

```hart```

Change from elastic reranker to RRF by editing `app.py`. Change the value of `CROSS_ENCODER_ENABLED` from `True` to `False'. You can also 
change the reranker settings to alter the behavior or RRF or cross encoder reranker. 

## Teardown

CTRL+C the terminal shell that is running the fastapi application.

### Delete the indexes in Elasticsearch
```
python elastic_index_manager.py teardown
```

## Customize with different data

It's very hard to create an end to end demo with swappable data but you can alter the code to work with a different use case
with a few tweaks. This demo features a super simplistic web front end. It is just a single index.html page with embedded CSS styles
and javascript for making calls to `/search` and `/autocomplete`. Customizing this demo involves the following:

1. Modify [./suggest_index.jsonl](./suggest_index.jsonl) with the suggestions that you want in suggest index.
2. Modify [./search_index.jsonl](./search_index.jsonl) with the data that you want in the search index. 

If you just want to modify suggestions, you can hand edit [./suggest_index.jsonl](./suggest_index.jsonl) and rerun ```python elastic_index_manager.py reload```.
There is no need to restart the application. Your new suggestions should display. 

### If you change the field names/types in search_index.jsonl
3. You will need to update the /search function in [./app.py](./app.py)
4. You will need to update `recordDiv.innerHTML` in [./static/index.html](./static/index.html)
