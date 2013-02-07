import http.client
import urllib
import json

def imagesearch(searchString, safe="off"):
    conn = http.client.HTTPSConnection('ajax.googleapis.com')
    req = urllib.parse.urlencode({'v': '1.0', 'safe': safe, 'q': searchString})
    conn.connect()
    conn.request('GET', '/ajax/services/search/images?' + req)
    
    response = conn.getresponse()
    responseStr = response.read().decode('UTF-8')
    data = json.loads(responseStr)['responseData']
    try:
        print(data['results'][0]['unescapedUrl'])
        return (data['results'][0]['unescapedUrl'])
    except IndexError:
        return "no results"
imagesearch('okay face')
