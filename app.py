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
    if req.get("result").get("action") != "yahooWeatherForecast":
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

    now_str = str(now_tuple.tm_mday) + " " + getMonthName(now_tuple.tm_mon) + " " + str(now_tuple.tm_year)
    day_str = getDateStrFromParameter(req)
    
    if now_str == day_str:
        res = makeWebhookResult(data)
    else:
        res = makeWebhookForecastResult(data)   

    return res


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("lc-city")
    if city is None:
        city = parameters.get("lc-wcity")
        if(city is None):
            return None
        return city

    now = datetime.datetime.now()
    now_tuple = now.timetuple()

    now_str = str(now_tuple.tm_mday) + " " + getMonthName(now_tuple.tm_mon) + " " + str(now_tuple.tm_year)
    day_str = getDateStrFromParameter(req)
    
    if now_str == day_str:
        query = "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "') and u='c'"
    else:
        query = "select item.forecast, location from weather.forecast where woeid in (select woeid from geo.places(1) where text='"+ city +"') and u='c' and item.forecast.date='" + day_str +"'"
        
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

    speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech
        # "data": data,
        # "contextOut": [],
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
    city = location.get('city')
    ###str(date) + " in " + str(city) + " : " + str(forecast.get('text'))
    speech = str(date_word) + " in " + str(city) + " : " + str(forecast.get('text')) + ". the highs is " + str(forecast.get('high')) + " C and the lows is " + str(forecast.get('low')) + " C"
    
    print("Response:")
    print(speech)
    
    return {
        "speech": speech,
        "displayText": speech
    }


def getDateStrFromParameter(req):
    result = req.get("result")
    parameters = result.get("parameters")
    
    global date_word
    
    day_word_map = {
        u"오늘":0,
        u"금일":0,
        u"내일":1,
        u"명일":1,
        u"모레":2,
        u"내일모레":2,
        u"글피":3,
        u"그글피":4,
        u"그그글피":5        
    }
    
    day = parameters.get("dt_day")
    if day is None:
        now = datetime.datetime.now()
        now_tuple = now.timetuple()
        day = str(now_tuple.tm_mday) + " " + getMonthName(now_tuple.tm_mon) + " " + str(now_tuple.tm_year)
        return day
    
    day = unicode(day)
    
    if (day in day_word_map) is True:
        now = datetime.datetime.now()
        parameter_day = now + datetime.timedelta(days=int(day_word_map[day]))
        parameter_day_tuple = parameter_day.timetuple()
        
        date_word = getEnglishDateName(day)
        
        day = str(parameter_day_tuple.tm_mday) + " " + getMonthName(parameter_day_tuple.tm_mon) + " " + str(parameter_day_tuple.tm_year)
    else:
        now = datetime.datetime.now()
        now_tuple = now.timetuple()
        day = day.replace("일","")
        
        month = parameters.get("dt_month")
        if month is None:
            month = now_tuple.tm_mon
        else:
            month = month.replace("월","")
        
        year = parameters.get("dt_year")
        if year is None:
            year = now_tuple.tm_year
        else:
            year = year.replace("년","")
        
        day = str(day) + " " + getMonthName(int(month)) + " " + str(year)
        
        date_word = day     
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

def getEnglishDateName(date_word):
    day_map = {
       u"오늘":"Today",
        u"금일":"Today",
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
