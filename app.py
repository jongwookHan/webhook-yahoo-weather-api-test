#-*-coding:utf-8-*-
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
    
    baseurl = "http://query.yahooapis.com/v1/public/yql?"
    
   
    
    now = datetime.datetime.now()
    now_tuple = now.timetuple()
    now_date = str(now_tuple.tm_mday) + " " + getMonthName(int(now_tuple.tm_mon)) + " " + str(now_tuple.tm_year)
    
    parameter_date = getDateFromParameter(req)
    
    if now_date == parameter_date:
        yql_query = makeYqlQuery(req)
    else:
        yql_query = makeForecastYqlQuery(req)
        
    if yql_query is None:
        return {}
    
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
    result = urlopen(yql_url).read()
    data = json.loads(result)
    
    
    if now_date == parameter_date:
        res = makeWebhookResult(data)
    else:
        res = makeWebhookForecastResult(data)
    
    return res


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("lc_city")
    if city is None:
        city = parameters.get("lc_wcity")
        if city is None:
            return None
        return city

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "') and u='c'"

def makeForecastYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("lc_city")
    if city is None:
        city = parameters.get("lc_wcity")
        if city is None:
            return None
        return city
    
    parameter_date = getDateFromParameter(req)
    
    return "select item.forecast, location from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "') and u='c' and item.forecast.date=" + "'" + parameter_date + "'"
    

def getDateFromParameter(req):    
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
    
    result = req.get("result")
    parameters = result.get("parameters")
    
    now = datetime.datetime.now()
    now_tuple = now.timetuple()
    
    day = parameters.get("dt_day")
    if day is None:
        day = now_tuple.tm_mday
    else:
        if day in day_word_map:
            compare_day = now + datetime.timedelta(days=day_word_map[day])
            compare_day_tuple = compare_day.timetuple()
            
            global date_word
            date_word = getEnglishDayWord(day)
            
            return str(compare_day_tuple.tm_mday) + " " + getMonthName(int(compare_day_tuple.tm_mon)) + " " + str(compare_day_tuple.tm_year)
        else:
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
 
    global date_word
    date_word = str(day) + " " + getMonthName(int(month)) + " " + str(year)
 
    return str(day) + " " + getMonthName(int(month)) + " " + str(year)

def getMonthName(month):
    month_map = {
        1:"Jan",
        2:"Feb",
        3:"Mar",
        4:"Apr",
        5:"May",
        6:"Jun",
        7:"Jul",
        8:"Aug",
        9:"Sep",
        10:"Oct",
        11:"Nov",
        12:"Dec"
    }
    return month_map[month]



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
        "displayText": speech,
        #"data": data,
        # "contextOut": [],
        "source": ""
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
    location = channel.get('location')
    if (location is None) or (item is None):
        return {}

    forecast = item.get('forecast')
    if forecast is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = date_word + " in " + location.get('city') + ": " + forecast.get("text") +  ". the highs is " + forecast.get("high") + " and the lows is " + forecast.get("low")

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        #"data": data,
        # "contextOut": [],
        "source": ""
    }

def getEnglishDayWord(day_word):
    english_day_word_map = {
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
    
    if day_word in english_day_word_map:
        return english_day_word_map[day_word]
    else:
        return day_word


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
