from fastapi import FastAPI
import requests, base64, json
import urllib.parse
from string import Template
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/items/{app_type}")
async def read_item(app_type: str, unit: str = None, last_name: str = None, d_from: str = None, d_to: str = None):
    stat = ''
    content = ''
    if(app_type == 'heroes'):
        return {"app_type": app_type, 'last_name':last_name, "d_from": d_from, "d_to":d_to}
    elif(app_type=='documents'):
        if(unit is None):
                stat = "Error"
                content += 'Не заполнен параметр unit/'
        if(d_from is None):
                stat ="Error"
                content += 'Не заполнен параметр d_from/'
        if(d_to is None):
                stat ="Error"
                content += 'Не заполнен параметр d_to/'
        if(stat!='Error'):
               return {"status": 'success' ,'content': BASE_DIR}
    else:
        return {"action": 'not defined'}
