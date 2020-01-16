from fastapi import FastAPI
import requests, base64, json
import urllib.parse
from string import Template
from datetime import datetime
import os


app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}