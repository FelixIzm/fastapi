from fastapi import FastAPI
import requests, base64, json
import urllib.parse,pprint
from string import Template
from datetime import datetime
import os
from flask_cors import CORS, cross_origin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


app = FastAPI()

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

cookies = {}
headers={}

str_00 = 'bda88568a54f922fcdfc6dbf940e5d00'
str_0b = '56105c9ab348522591eea18fbe4d080b'
str_PNSESSIONID = 'PNSESSIONID'
unit = '1256 гап'

#####################################
def parse_file (name_file):
    dict_ = {}
    f = open(name_file, 'r')
    s = f.read()
    dict_={}
    list_ = s.splitlines()
    for item in list_:
        items = item.split(":")
        dict_[items[0]] = items[1].lstrip()
    return dict_
#####################################
def parse_json_file(json_file):
    with open(json_file) as json_file:
        return json.load(json_file)
#####################################
def make_str_cookie(cookies):
    str_cook = ''
    for key, value in cookies.items():
        str_cook += '{0}={1};'.format(key,value)
    return str_cook
#####################################

def getContent(military_unit, date_From, date_To):
    ##############################################
    #    Первый запрос - получаем 307 статус     #
    ##############################################
    html_string = ''
    headers = parse_file(BASE_DIR+'/mu_files/mu_header1.txt')
    cookies = parse_file(BASE_DIR+'/mu_files/mu_cookie1.txt')
    url = 'https://pamyat-naroda.ru/'
    res1 = requests.get(url, allow_redirects=False)
    if(res1.status_code==307):
        #print('*********  1  **********')
        #print(res1.status_code)
        #print(res1.cookies[str_00])
        # Получили переменные из кук
        cookie_PNSESSIONID = res1.cookies['PNSESSIONID']
        cookie_00 = res1.cookies[str_00]
        cookie_0b = res1.cookies[str_0b]
        #####################################################
        # готовим 2-й запрос, посылаем с получанными куками #
        #####################################################
        #print('')
        #print('*********  2  **********')
        cookies = {}
        cookies[str_00]=cookie_00
        cookies[str_0b]=cookie_0b
        cookies[str_PNSESSIONID] = cookie_PNSESSIONID
        cookies['BITRIX_PN_DATALINE_LNG'] = 'ru'
        headers = parse_file(BASE_DIR+'/mu_files/mu_header2.txt')
        headers['Cookie'] = make_str_cookie(cookies)
        res2 = requests.get(url,cookies=cookies,headers=headers,allow_redirects = True)
        #######################################
        if(res2.status_code==200):
            print(res2.status_code)
            print(res2.cookies[str_00])
            ###########################################
            ##############   3-й запрос   #############
            ###########################################
            #print('')
            #print("*********  3  **********")
            cookies = parse_json_file(BASE_DIR+'/mu_files/mu_cookie3.txt')
            cookies[str_00] = res2.cookies[str_00]
            cookies[str_0b] = res1.cookies[str_0b]
            cookies[str_PNSESSIONID] = res1.cookies[str_PNSESSIONID]
            cookies['r'] = res1.cookies[str_0b]
            headers = parse_file(BASE_DIR+'/mu_files/mu_header3.txt')
            headers['Cookie'] = make_str_cookie(cookies)
            headers['Content-Type'] = 'application/json'

            url3 = 'https://pamyat-naroda.ru/documents/'
            res3 = requests.get(url3,headers=headers,cookies=cookies)
            print(res3.status_code)
            print(res3.cookies[str_00])
            ############## 4-й запрос #############
            #print('')
            #print('*********  4  ************')
            headers=parse_file(BASE_DIR+'/mu_files/mu_header4.txt')
            headers['Content-Type'] = 'application/json'
            headers['Origin']='https://pamyat-naroda.ru'
            headers['Referer']='https://pamyat-naroda.ru/documents/'

            bs = res3.cookies[str_00]
            bs += "=" * ((4 - len(res3.cookies[str_00]) % 4) % 4)
            bs = base64.b64decode(bs).decode()
            a_bs = bs.split('XXXXXX')[0]
            b_bs = bs.split('XXXXXX')[1].split('YYYYYY')[0]
            data_t = Template('{"query":{"bool":{"should":[{"bool":{"should":[{"match_phrase":{"document_type":"Боевые донесения, оперсводки"}},{"match_phrase":{"document_type":"Боевые приказы и распоряжения"}},{"match_phrase":{"document_type":"Отчеты о боевых действиях"}},{"match_phrase":{"document_type":"Переговоры"}},{"match_phrase":{"document_type":"Журналы боевых действий"}},{"match_phrase":{"document_type":"Директивы и указания"}},{"match_phrase":{"document_type":"Приказы"}},{"match_phrase":{"document_type":"Постановления"}},{"match_phrase":{"document_type":"Доклады"}},{"match_phrase":{"document_type":"Рапорты"}},{"match_phrase":{"document_type":"Разведывательные бюллетени и донесения"}},{"match_phrase":{"document_type":"Сведения"}},{"match_phrase":{"document_type":"Планы"}},{"match_phrase":{"document_type":"Планы операций"}},{"match_phrase":{"document_type":"Карты"}},{"match_phrase":{"document_type":"Схемы"}},{"match_phrase":{"document_type":"Справки"}},{"match_phrase":{"document_type":"Прочие документы"}}]}},{"bool":{"should":[{"bool":{"must":[{"range":{"date_from":{"lte":"${finish_date}"}}},{"range":{"date_to":{"gte":"${start_date}"}}}],"boost":3}},{"bool":{"must":[{"range":{"document_date_b":{"lte":"${finish_date}"}}},{"range":{"document_date_f":{"gte":"${start_date}"}}}],"boost":7}}]}},{"bool":{"should":[{"match_phrase":{"authors_list.keyword":{"query":"${military_unit}","boost":50}}},{"match":{"document_name":{"query":"${military_unit}","type":"phrase","boost":30}}},{"match":{"authors":{"query":"${military_unit}","type":"phrase","boost":20}}},{"match":{"army_unit_label.division":{"query":"${military_unit}","type":"phrase","boost":10}}},{"nested":{"path":"page_magazine","query":{"bool":{"must":[{"match":{"page_magazine.podrs":{"query":"${military_unit}","type":"phrase"}}},{"range":{"page_magazine.date_from":{"lte":"${finish_date}"}}},{"range":{"page_magazine.date_to":{"gte":"${start_date}"}}}]}},"boost":4}}]}}],"minimum_should_match":3}},"_source":["id","document_type","document_number","document_date_b","document_date_f","document_name","archive","fond","opis","delo","date_from","date_to","authors","geo_names","operation_name","secr","image_path","delo_id","deal_type","operation_name"],"size":10,"from":0}')

            data_ = data_t.safe_substitute(start_date=date_From,finish_date=date_To, military_unit=military_unit,size=10,para_from=0)
            url4 = 'https://cdn.pamyat-naroda.ru/data/'+a_bs+'/'+b_bs+'/pamyat/document,map,magazine/_search'
            res4 = requests.post(url4,data=data_.encode('utf-8'),headers=headers)
            if(res4.status_code==200):
                data = json.loads(res4.text)
                total = data['hits']['total']
                hits = data['hits']['hits']
                #print(hits[0]['_source'])
                #for key, value in hits[0].items():
                #    print (key, value)
                divisor = 100
                one, two =divmod (total,divisor)
                #print(one, two)
                x=0
                table={}
                while(x< one*divisor):
                    #print(divisor, x, total)
                    data_ = data_t.safe_substitute(start_date=date_From,finish_date=date_To, military_unit=military_unit,size=divisor,para_from=x)
                    url4 = 'https://cdn.pamyat-naroda.ru/data/'+a_bs+'/'+b_bs+'/pamyat/document,map,magazine/_search'
                    res4 = requests.post(url4,data=data_.encode('utf-8'),headers=headers)
                    if(res4.status_code==200):
                        data = json.loads(res4.text)
                        hits = data['hits']['hits']
                        rows=[]
                        for hit in hits:
                            col = {}
                            #print(hit['_source'])
                            src = hit['_source']
                            data_string = table_string.safe_substitute(col1=src['document_type'],col2=src['document_name'],col3=src['date_from']+'-'+src['date_to'],col4=src['authors'],col5=src['document_date_f'],col6=src['archive'],col7=src['fond'],col8=src['opis'],col9=src['delo'],col10='<a href=https://pamyat-naroda.ru/documents/view/?id='+hit['_id']+' target="_blank">Док</a>')
                            col["col1"]= src['document_type']
                            col['col2'] = src['document_name']
                            col['col3'] = src['date_from']+' - '+src['date_to']
                            col['col4'] = src['authors']
                            col['col5'] = src['document_date_f']
                            col['col6'] = src['archive']
                            col['col7'] = src['fond']
                            col['col8'] = src['opis']
                            col['col9'] = src['delo']
                            col['col10'] = 'https://pamyat-naroda.ru/documents/view/?id='+hit['_id']
                            rows.append(col)
                    x+=divisor
                data_ = data_t.safe_substitute(start_date=date_From,finish_date=date_To, military_unit=military_unit,size=two,para_from=x)
                url4 = 'https://cdn.pamyat-naroda.ru/data/'+a_bs+'/'+b_bs+'/pamyat/document,map,magazine/_search'
                res4 = requests.post(url4,data=data_.encode('utf-8'),headers=headers)
                if(res4.status_code==200):
                    data = json.loads(res4.text)
                    hits = data['hits']['hits']
                    rows=[]
                    for hit in hits:
                        col = {}
                        src = hit['_source']
                        col["col1"]= src['document_type']
                        col['col2'] = src['document_name']
                        col['col3'] = src['date_from']+' - '+src['date_to']
                        col['col4'] = src['authors']
                        col['col5'] = src['document_date_f']
                        col['col6'] = src['archive']
                        col['col7'] = src['fond']
                        col['col8'] = src['opis']
                        col['col9'] = src['delo']
                        col['col10'] = 'https://pamyat-naroda.ru/documents/view/?id='+hit['_id']
                        rows.append(col)
    table.__setitem__("rows",rows)
    return(table)




@app.get("/")
@cross_origin()
async def read_root():
    return {"Hello": "World"}

#https://api-1945.herokuapp.com/items?documents&unit=147%20сд&de_from=555$d_to=4444
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
               return {"status": 'success' ,'table': getContent('1256 гап','1945-05-01','1945-05-31')}
        else:
               return {'status':stat, 'message':content}
    else:
        return {"action": 'not defined'}
