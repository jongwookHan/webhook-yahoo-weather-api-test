# coding: utf8
#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os
import datetime
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    if req.get("result").get("action") != "weather":
        return {}
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    
    yql_query = makeYqlQuery(req)
    if yql_query is None:
        return {}
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
    result = urlopen(yql_url).read()    
    data = json.loads(result)
    
    now = datetime.datetime.now()
    now_tuple = now.timetuple()

    now_str = ((now_tuple.tm_mday < 10) and (str(0) + str(now_tuple.tm_mday)) or (str(now_tuple.tm_mday)))+ " " + getMonthName(now_tuple.tm_mon) + " " + str(now_tuple.tm_year)
    
    day_str = getDateStrFromParameter(req)
    
    if now_str == day_str:
        res = makeWebhookResult(data)
    else:
        res = makeWebhookForecastResult(data)   

    return res


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("sys_lc_city")
    if city is None:
        city = parameters.get("sys_lc_wcity")
        if(city is None):
            return None
    global global_city
    global_city = city
    

    now = datetime.datetime.now()
    now_tuple = now.timetuple()
    #(a>b) and x or y
    now_str = ((now_tuple.tm_mday < 10) and (str(0) + str(now_tuple.tm_mday)) or (str(now_tuple.tm_mday)))+ " " + getMonthName(now_tuple.tm_mon) + " " + str(now_tuple.tm_year)
    day_str = getDateStrFromParameter(req)
    
    if now_str == day_str:
        query = "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "') and u='c'"
    else:
        query = "select item.forecast, location from weather.forecast where woeid in (select woeid from geo.places(1) where text='"+ city +"') and u='c' and item.forecast.date='" + day_str +"'"
    print(query);
    return query


def makeWebhookResult(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "오늘 " + global_city + " 날씨는 " + getKoreanWeatherCondition(condition.get('code')) + "이고, 기온은 " + condition.get('temp') + " " + units.get('temperature') + " 입니다."

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample-customized"
    }

def makeWebhookForecastResult(data):
    query = data.get('query')
    if query is None:
        return {}
    
    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')   
    if item is None:
        return {}
    
    location = channel.get('location')
    if location is None:
        return {}
    
    forecast = item.get('forecast')
    if forecast is None:
        return {}
    
    date = forecast.get('date')
    city = unicode(global_city)
    ###str(date) + " in " + str(city) + " : " + str(forecast.get('text'))
    speech = str(date_word) +" " + str(city) + u" 날씨는 " + getKoreanWeatherCondition(forecast.get('code')) + u"이고, 최고기온은 " + str(forecast.get('high')) + u" C , 최저기온은 " + str(forecast.get('low')) + u" C 입니다."
    
    print("Response:")
    print(speech)
    
    return {
        "speech": speech,
        "displayText": speech,
        "source": "apiai-weather-webhook-sample-customized"
    }


def getDateStrFromParameter(req):
    result = req.get("result")
    parameters = result.get("parameters")
    
    global date_word
    
    day_word_map = {
        u"오늘":0,
        u"금일":0,
        u"현재":0,
        u"내일":1,
        u"명일":1,
        u"모레":2,
        u"내일모레":2,
        u"글피":3,
        u"그글피":4,
        u"그그글피":5        
    }
    
    day = parameters.get("sys_dt_day")
    if day is None:
        now = datetime.datetime.now()
        now_tuple = now.timetuple()
        day = ((now_tuple.tm_mday < 10) and (str(0) + str(now_tuple.tm_mday)) or (str(now_tuple.tm_mday))) + " " + getMonthName(now_tuple.tm_mon) + " " + str(now_tuple.tm_year)
        return day
    
    day = unicode(day)
    
    if (day in day_word_map) is True:
        now = datetime.datetime.now()
        parameter_day = now + datetime.timedelta(days=int(day_word_map[day]))
        parameter_day_tuple = parameter_day.timetuple()
        
        date_word = day
        day = ((parameter_day_tuple.tm_mday < 10) and (str(0) + str(parameter_day_tuple.tm_mday)) or (str(parameter_day_tuple.tm_mday))) + " " + getMonthName(parameter_day_tuple.tm_mon) + " " + str(parameter_day_tuple.tm_year)
    else:
        now = datetime.datetime.now()
        now_tuple = now.timetuple()
        
        date_word = day
        
        day = day.replace("일","")
        
        month = parameters.get("sys_dt_month")
        if month is None:
            month = now_tuple.tm_mon
        else:
            date_word = month + " " + date_word
            month = month.replace("월","")
            
        year = parameters.get("sys_dt_year")
        if year is None:
            year = now_tuple.tm_year
        else:
            date_word = year + " " + date_word
            year = year.replace("년","")
            
        if int(day) < now_tuple.tm_mday:
            month = str(int(month) + 1)
            if int(month) > 13 : 
                year = str(int(year) + 1)
                month = str(1)      
            
        day = ((int(day) < 10) and (str(0) + str(day)) or (str(day))) + " " + getMonthName(int(month)) + " " + str(year)
        
             
    return day

def getMonthName(month):
    month_map = {
        1 :'Jan',
        2 :'Feb',
        3 :'Mar',
        4 :'Apr',
        5 :'May',
        6 :'Jun',
        7 :'Jul',
        8 :'Aug',
        9 :'Sep',
        10:'Oct',
        11:'Nov',
        12:'Dec'       
    }
    return month_map[month]     

def getKoreanWeatherCondition(weatherCondition):
    korean_weather_map = {
        "0":u"토네이도",
        "1 Storm":u"열대성 폭풍",
        "2":u"허리케인",
        "3":u"뇌우 및 진눈깨비",
        "4":u"뇌우",
        "5":u"진눈깨비",
        "6":u"진눈깨비",
        "7":u"진눈깨비",
        "8":u"진눈깨비",
        "9":u"이슬비",
        "10":u"비",
        "11":u"소나기",
        "12":u"소나기",
        "13":u"눈",
        "14":u"눈소나기",
        "15":u"눈",
        "16":u"눈",
        "17":u"우박",
        "18":u"진눈깨비",
        "19":u"먼지많음",
        "20":u"안개",
        "21":u"옅은 안개",
        "22":u"짙은 안개",
        "23":u"강풍",
        "24":u"바람이 많이 붐",
        "25":u"추움",
        "26":u"흐림",
        "27":u"대체로 흐림(밤)",
        "28":u"대체로 흐림(낮)",
        "29":u"부분적 흐림(밤)",
        "30":u"부분적 흐림(낮)",
        "31":u"맑음(밤)",
        "32":u"맑음(낮)",
        "33":u"갬(밤)",
        "34":u"갬(낮)",
        "35":u"진눈깨비",
        "36":u"더움",
        "37":u"고립성 뇌우",
        "38":u"산발성 뇌우",
        "39":u"산발성 뇌우",
        "40":u"산발성 소나기",
        "41":u"폭설",
        "42":u"부분적 눈소나기",
        "43":u"폭설",
        "44":u"부분적 흐림",
        "45":u"소나기(뇌우)",
        "46":u"눈소나기",
        "47":u"고립성 소나기(뇌우)"
    }
    return korean_weather_map[weatherCondition]

def getEnglishDateName(date_word):
    day_map = {
       u"오늘":"Today",
        u"금일":"Today",
        u"현재":"Now",
        u"내일":"Tomorrow",
        u"명일":"Tomorrow",
        u"모레":"The day after tomorrow",
        u"내일모레":"The day after tomorrow",
        u"글피":"Two days after tommorrow",
        u"그글피":"Three days after tomorrow",
        u"그그글피":"Four days after tomorrow"    
    }
    return day_map[date_word]

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')
