#from django.http import HttpResponse

from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware


import zipfile

import requests, json, base64
import hashlib
import lxml.html as html

from string import Template
from datetime import datetime
from io import BytesIO
from zipfile import ZipFile

import csv
import io
import os
import tempfile


app = FastAPI()
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:5000",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

image_id=85942988
#image_id=84306278
#image_id=80332546

##########################################
image_id = ''
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cookies = {}
dirpath = tempfile.mkdtemp()
cols = ['ID scan','ID','Фамилия','Имя','Отчество','Дата рождения/Возраст','Место рождения','Дата и место призыва','Последнее место службы','Воинское звание','Судьба','Дата смерти','Первичное место захоронения']
search_count = -9999

######################################
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
def getStringHash(id):
    h = hashlib.md5(str(id).encode()+b'db76xdlrtxcxcghn7yusxjcdxsbtq1hnicnaspohh5tzbtgqjixzc5nmhybeh')
    p = h.hexdigest()
    return str(p)
#####################################
def get_info(id_scan,id,cookies):
    cookies['showimage']='0'
    info_url = 'https://obd-memorial.ru/html/info.htm?id='+str(id)
    res3 = requests.get(info_url,cookies=cookies)
    doc = html.fromstring(res3.text)
    divs = {}
    for div in doc.find_class('card_parameter'):
        divs[div.getchildren()[0].text_content()] = div.getchildren()[1].text_content()
        #print ('%s: %s' % (div.getchildren()[0].text_content(), div.getchildren()[1].text_content()))
    list_col = []
    for col in cols:
        if(col in divs.keys()):
            list_col.append(divs[col])
        else:
            list_col.append('')
    list_col[1] = id
    list_col[0] = id_scan
    #print(str(list_col))
    return list_col
#####################################
def get_lists(image_id):
    info_url = 'https://obd-memorial.ru/html/info.htm?id={}'.format(image_id)
    list_id_images = []
    list_urls_infocards  = []
    res1 = requests.get(info_url)
    print(res1.status_code)
    cookies = {}
    if(res1.status_code==200):
        cookies['3fbe47cd30daea60fc16041479413da2']=res1.cookies['3fbe47cd30daea60fc16041479413da2']
        cookies['JSESSIONID']=res1.cookies['JSESSIONID']
        cookies['showimage']='0'
        img_info = 'https://obd-memorial.ru/html/getimageinfo?id={}'.format(image_id)
        response = requests.get(img_info)
        response_dict = json.loads(response.text)
        i=0
        for item in response_dict:
            i+=1
            #img_url="https://obd-memorial.ru/html/images3?id="+str(item['id'])+"&id1="+(getStringHash(item['id']))+"&path="+item['img']
            list_id_images.append({'id':item['id'],'img':item['img']})
            for id in item['mapData'].keys():
                info_url = 'https://obd-memorial.ru/html/info.htm?id='+str(id)
                list_urls_infocards.append(info_url)
    return(list_id_images,list_urls_infocards, cookies)
#####################################
def get_images(list_item_images):
    global cookies
    in_memory = BytesIO()
    zipObj = ZipFile(in_memory, "a")
    for item in list_item_images:
        info_url = 'https://obd-memorial.ru/html/info.htm?id={}'.format(str(item['id']))
        img_url="https://obd-memorial.ru/html/images3?id="+str(item['id'])+"&id1="+(getStringHash(item['id']))+"&path="+item['img']
        headers_302 = parse_file(BASE_DIR+'/header_302.txt')
        headers_302['Cookie'] = make_str_cookie(cookies)
        headers_302['Referer'] = info_url
        req302 = requests.get(img_url,headers=headers_302,cookies=cookies, allow_redirects = False)
        if(req302.status_code==302):
            params = {}
            params['id'] = str(item['id'])
            params['id1'] = getStringHash(item['id'])
            params['path'] = item['img']
            headers_img = parse_file(BASE_DIR+'/header_img.txt')
            headers_img['Referer'] = info_url
            #####################
            #print(item['id'])
            req_img = requests.get("https://cdn.obd-memorial.ru/html/images3",headers=headers_img,params=params,cookies=cookies,stream = True,allow_redirects = False )
            #####################
            if(req_img.status_code==200):
                name_jpg = str(item['id'])+'.jpg'
                zipObj.writestr(name_jpg, req_img.content)
        # fix for Linux zip files read in Windows
        for file in zipObj.filelist:
            file.create_system = 0
    zipObj.close()
    #response = Response(content_type="application/zip")
    #response["Content-Disposition"] = "attachment; filename="+str(image_id)+".zip"
    in_memory.seek(0)  
    return Response(content=in_memory.read(), media_type="application/zip" )  

#####################################
#           JPG !!!!!!!!!!         #
#####################################
def main_scan(image_id):
    list_images, list_infocards, cookies = get_lists(image_id)
    print('img count = ',len(list_images))
    print('info count = ',len(list_infocards))
    return get_images(list_images)
    #print('dirpath = '+dirpath)
#

#####################################
#           CSV !!!!!!!!!!         #
#####################################
def main_csv(image_id):
    if(image_id == None):
        return 'Ссылка на каталог -', ''
    info_url = 'https://obd-memorial.ru/html/info.htm?id={}'.format(image_id)
    img_info = 'https://obd-memorial.ru/html/getimageinfo?id={}'.format(image_id)
    res1 = requests.get(info_url, allow_redirects = True)

    in_memory = BytesIO()
    zipObj = ZipFile(in_memory, "a", zipfile.ZIP_DEFLATED)
    print(res1.status_code)
    if(res1.status_code==200):
        if(not '3fbe47cd30daea60fc16041479413da2' in res1.cookies):
            return 'no folder','Запись сводного документа не найдена' 
        cookies = {}
        cookies['3fbe47cd30daea60fc16041479413da2']=res1.cookies['3fbe47cd30daea60fc16041479413da2']
        cookies['JSESSIONID']=res1.cookies['JSESSIONID']
        #############################
        #   load list id's images   #
        #############################
        response = requests.get(img_info,cookies=cookies)
        response_dict = json.loads(response.text)
        print('response_dict = '+str(len(response_dict)))
        #############################
        #if(excel):
        columns = cols
        row_csv = []
        output = io.StringIO()

        ##############################
        writer = csv.writer(output, dialect='excel', quoting=csv.QUOTE_NONNUMERIC, delimiter=';')
        for col_num, column_title in enumerate(cols, 1):
            row_csv.append(column_title)
        writer.writerow(row_csv)
        # идем по списку id сканов
        for idict,item in enumerate(response_dict):
            if(len(item['mapData'])>0):
                for id in item['mapData'].keys():
                    row = get_info(item['id'],id,cookies)
                    row_csv = []
                    for col_num, cell_value in enumerate(row, 1):
                        row_csv.append(cell_value)
                    writer.writerow(row_csv)

        zipObj.writestr(str(image_id)+'_book.csv', output.getvalue().encode('cp1251'))
        # fix for Linux zip files read in Windows
        for file in zipObj.filelist:
            file.create_system = 0
    zipObj.close()
    in_memory.seek(0)    
    return Response(content=in_memory.read(), media_type="application/zip" )
#####################################
def checkType(value):
    if value is None:
        return ''
    else:
        return value

#####################################################
def getContent(military_unit, date_From, date_To):
    str_00 = 'bda88568a54f922fcdfc6dbf940e5d00'
    str_0b = '56105c9ab348522591eea18fbe4d080b'
    str_PNSESSIONID = 'PNSESSIONID'
    unit = '1256 гап'

    ##############################################
    #    Первый запрос - получаем 307 статус     #
    ##############################################
    html_string = '<html><table class="blueTable">'
    headers = parse_file(BASE_DIR+'/mu_header1.txt')
    cookies = parse_file(BASE_DIR+'/mu_cookie1.txt')
    url = 'https://pamyat-naroda.ru/'
    res1 = requests.get(url, allow_redirects=False)
    global search_count
    search_count = 0
    if(res1.status_code==200):
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
        headers = parse_file(BASE_DIR+'/mu_header2.txt')
        headers['Cookie'] = make_str_cookie(cookies)
        res2 = requests.get(url,cookies=cookies,headers=headers,allow_redirects = True)
        #######################################
        if(res2.status_code==200):
            print(res2.status_code)
            print(res2.cookies[str_00])
            ###########################################
            ##############   3-й запрос   #############
            ###########################################
            cookies = parse_json_file(BASE_DIR+'/mu_cookie3.txt')
            cookies[str_00] = res2.cookies[str_00]
            cookies[str_0b] = res1.cookies[str_0b]
            cookies[str_PNSESSIONID] = res1.cookies[str_PNSESSIONID]
            cookies['r'] = res1.cookies[str_0b]
            headers = parse_file(BASE_DIR+'/mu_header3.txt')
            headers['Cookie'] = make_str_cookie(cookies)
            headers['Content-Type'] = 'application/json'

            url3 = 'https://pamyat-naroda.ru/documents/'
            res3 = requests.get(url3,headers=headers,cookies=cookies)
            #print(res3.status_code)
            #print(res3.cookies[str_00])
            ############## 4-й запрос #############
            ############## 4-й запрос #############
            headers=parse_file(BASE_DIR+'/mu_header4.txt')
            headers['Content-Type'] = 'application/json'
            headers['Origin']='https://pamyat-naroda.ru'
            headers['Referer']='https://pamyat-naroda.ru/documents/'

            bs = res3.cookies[str_00]
            bs += "=" * ((4 - len(res3.cookies[str_00]) % 4) % 4)
            bs = base64.b64decode(bs).decode()
            a_bs = bs.split('XXXXXX')[0]
            b_bs = bs.split('XXXXXX')[1].split('YYYYYY')[0]
            data_t = Template('{"query":{"bool":{"should":[{"bool":{"should":[{"match_phrase":{"document_type":"Боевые донесения, оперсводки"}},{"match_phrase":{"document_type":"Боевые приказы и распоряжения"}},{"match_phrase":{"document_type":"Отчеты о боевых действиях"}},{"match_phrase":{"document_type":"Переговоры"}},{"match_phrase":{"document_type":"Журналы боевых действий"}},{"match_phrase":{"document_type":"Директивы и указания"}},{"match_phrase":{"document_type":"Приказы"}},{"match_phrase":{"document_type":"Постановления"}},{"match_phrase":{"document_type":"Доклады"}},{"match_phrase":{"document_type":"Рапорты"}},{"match_phrase":{"document_type":"Разведывательные бюллетени и донесения"}},{"match_phrase":{"document_type":"Сведения"}},{"match_phrase":{"document_type":"Планы"}},{"match_phrase":{"document_type":"Планы операций"}},{"match_phrase":{"document_type":"Карты"}},{"match_phrase":{"document_type":"Схемы"}},{"match_phrase":{"document_type":"Справки"}},{"match_phrase":{"document_type":"Прочие документы"}}]}},{"bool":{"should":[{"bool":{"must":[{"range":{"date_from":{"lte":"${finish_date}"}}},{"range":{"date_to":{"gte":"${start_date}"}}}],"boost":3}},{"bool":{"must":[{"range":{"document_date_b":{"lte":"${finish_date}"}}},{"range":{"document_date_f":{"gte":"${start_date}"}}}],"boost":7}}]}},{"bool":{"should":[{"match_phrase":{"authors_list.keyword":{"query":"${military_unit}","boost":50}}},{"match":{"document_name":{"query":"${military_unit}","type":"phrase","boost":30}}},{"match":{"authors":{"query":"${military_unit}","type":"phrase","boost":20}}},{"match":{"army_unit_label.division":{"query":"${military_unit}","type":"phrase","boost":10}}},{"nested":{"path":"page_magazine","query":{"bool":{"must":[{"match":{"page_magazine.podrs":{"query":"${military_unit}","type":"phrase"}}},{"range":{"page_magazine.date_from":{"lte":"${finish_date}"}}},{"range":{"page_magazine.date_to":{"gte":"${start_date}"}}}]}},"boost":4}}]}}],"minimum_should_match":3}},"_source":["id","document_type","document_number","document_date_b","document_date_f","document_name","archive","fond","opis","delo","date_from","date_to","authors","geo_names","operation_name","secr","image_path","delo_id","deal_type","operation_name"],"size":"${size}","from":"${_from}"}')
            #data_t= Template('{"query":{"bool":{"should":[{"bool":{"should":[{"match_phrase":{"document_type":"Боевые донесения, оперсводки"}},{"match_phrase":{"document_type":"Боевые приказы и распоряжения"}},{"match_phrase":{"document_type":"Отчеты о боевых действиях"}},{"match_phrase":{"document_type":"Переговоры"}},{"match_phrase":{"document_type":"Журналы боевых действий"}},{"match_phrase":{"document_type":"Директивы и указания"}},{"match_phrase":{"document_type":"Приказы"}},{"match_phrase":{"document_type":"Постановления"}},{"match_phrase":{"document_type":"Доклады"}},{"match_phrase":{"document_type":"Рапорты"}},{"match_phrase":{"document_type":"Разведывательные бюллетени и донесения"}},{"match_phrase":{"document_type":"Сведения"}},{"match_phrase":{"document_type":"Планы"}},{"match_phrase":{"document_type":"Планы операций"}},{"match_phrase":{"document_type":"Карты"}},{"match_phrase":{"document_type":"Схемы"}},{"match_phrase":{"document_type":"Справки"}},{"match_phrase":{"document_type":"Прочие документы"}}]}},{"bool":{"should":[{"bool":{"must":[{"range":{"date_from":{"lte":"${finish_date}"}}},{"range":{"date_to":{"gte":"${start_date}"}}}],"boost":3}},{"bool":{"must":[{"range":{"document_date_b":{"lte":"${finish_date}"}}},{"range":{"document_date_f":{"gte":"${start_date}"}}}],"boost":7}}]}}],"minimum_should_match":2}},"_source":["id","document_type","document_number","document_date_b","document_date_f","document_name","archive","fond","opis","delo","date_from","date_to","authors","geo_names","operation_name","secr","image_path","delo_id","deal_type","operation_name"],"size":"${size}","from":"${para_from}"}')

            data_ = data_t.safe_substitute(start_date=date_From,finish_date=date_To, military_unit=military_unit,size=10,_from=0)
            url4 = 'https://cdn.pamyat-naroda.ru/data/'+a_bs+'/'+b_bs+'/pamyat/document,map,magazine/_search'
            res4 = requests.post(url4,data=data_.encode('utf-8'),headers=headers,allow_redirects = True)
            if(res4.status_code==200):
                data = json.loads(res4.text)
                total = data['hits']['total']
                search_count = total
                hits = data['hits']['hits']
                divisor = 100
                one, two = divmod(total,divisor)
                x=0
                count=0
                print('total = ',total)
                html_string += '<thead><tr><th>N</th><th>Тип документа</th><th>Содержание</th><th>Период</th><th>Авторы</th><th>Дата документа</th><th>Архив</th><th>Фонд</th><th>Опись</th><th>Дело</th><th>Док</th></tr></thead>'
                html_string += '<tbody>'
                table_string = Template('<tr><td>${cnt}</td><td>${col1}</td><td>${col2}</td><td>${col3}</td><td>${col4}</td><td>${col5}</td><td>${col6}</td><td>${col7}</td><td>${col8}</td><td>${col9}</td><td>${col10}</td></tr>')
                a_result = []
                start=0
                stop=10
                step = 100
                for i in range(start,stop,step):
                    print(i,start, stop, step)
                    data_ = data_t.safe_substitute(start_date=date_From,finish_date=date_To, military_unit=military_unit,size=step,_from=i)
                    #print(data)
                    url4 = 'https://cdn.pamyat-naroda.ru/data/'+a_bs+'/'+b_bs+'/pamyat/document,map,magazine/_search'
                    res4 = requests.post(url4,data=data_.encode('utf-8'),headers=headers,allow_redirects = True)
                    if(res4.status_code==200):
                        data = json.loads(res4.text)
                        hits = data['hits']['hits']
                        #search_count += len(hits)
                        for hit in hits:
                            j_data = {}
                            src = hit['_source']
                            #print(type(src['date_from']))
                            count+=1
                            #data_string = table_string.safe_substitute(cnt=count,col1=checkType(src['document_type']),col2=checkType(src['document_name']),col3=checkType(src['date_from'])+'-'+checkType(src['date_to']),col4=checkType(src['authors']),col5=checkType(src['']),col6=checkType(src['archive']),col7=checkType(src['fond']),col8=checkType(src['opis']),col9=checkType(src['delo']),col10='<a href=https://pamyat-naroda.ru/documents/view/?id='+hit['_id']+' target="_blank">Док</a>')
                            j_data['document_type'] = checkType(src['document_type'])
                            j_data['document_name'] = checkType(src['document_name'])
                            j_data['authors'] = checkType(src['authors'])
                            j_data['document_date_f'] = checkType(src['document_date_f'])
                            j_data['archive'] = checkType(src['archive'])
                            j_data['fond'] = checkType(src['fond'])
                            j_data['opis'] = checkType(src['opis'])
                            j_data['delo'] = checkType(src['delo'])
                            a_result.append(j_data)

                            #html_string += data_string
                html_string+='</tbody></table></html>'
    return(a_result)

#####################################################
# 1330656
# 80332546
# 84306278
@app.get("/count")
async def ret_count():
    return [{'id': 987,'name': 'Felix','age':58}]

@app.get("/mil")
async def ret_mil():
    return getContent('1256 гап','1945-1-5','1945-5-30')

@app.get("/scan/{id}")
async def get_scan(id: str = None):
    if(id is None):
        html_content = """
        <html>
            <head>
                <title>obd</title>
            </head>
            <body>
                <h1>https://api-1945.herokuapp.com/scan/123456789</h1>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)
    else:
        return main_scan(id)

@app.get("/id/{id}")
async def read_root(id: str = None):
    if(id is None):
        html_content = """
        <html>
            <head>
                <title>obd</title>
            </head>
            <body>
                <h1>https://api-1945.herokuapp.com/id/123456789</h1>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)
    else:
        return main_csv(id)

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

