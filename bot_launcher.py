#!/usr/bin/env python
import sys
import socket
import select
import configparser
import random
import time
import datetime
import http.client
import urllib.parse
import urllib.request
import urllib.error
import json
import logging
import logging.handlers
import os.path
import pickle
import signal

from bs4 import BeautifulSoup
import bot.streetgeek.insult
import bot.nicetime
import bot.streetgeek.roll

config = configparser.ConfigParser()
config.read("config.ini")

rawUser = ""
seenMap = {}
leaveMap = {}
userToUserMap = {}
formatTime = None
timeseen = 0
server_address = config.get("server","address")
server_port = config.get("server","port")
server_port = int(server_port)
NICK = config.get("user", "nick")
USERNAME = config.get("user", "username")
REALNAME = config.get("user", "realname")
LOG_PATH = config.get("logging","path")
CHANNELS = (config.get("server","channels")).split(',')
REMOTEPASS = (config.get("remote","password"))
NICK_ATTEMPTS = 0

namesList={}
namesListTemp={}

fragResponse=['giraffes have neck boners','polar bears are left handed, and always dress in white','you cant get lung cancer from smoking blunts?','In virtual reality tests, an overwhelming number of people kill one person in order to save five bullets.','The custom of shaking hands with strangers when theres jizz on your hands is frowned upon in many cultures.','omg ive been eating gay squid','fair enough though, its so dark down where they are','The common lilly, zantedeschia aetheopica, once fucked chinos mum.','i feel sorry for the ones that attack those curved mirrors on driveways and train stations','yeah, i didnt take much of a break between the 2nd and 3rd faps','The biggest black holes shouldnt exist; those things are gross and we could do without them.','The sound you hear when you crack your knuckles is the sound of tiny firecrackers going off.','Male bottlenose dolphins are sometimes whorphins, sometimes exclusively dolphags.','Rats show altruism: Some of the worlds richest rats have given many millions of dollars to help fellow rats in need.','In space, jizz forms spherical blobs rather than butterfly-shaped splashes.','One of three exploding lakes in the world is Lake Kivu in Democratic Republic of Congo, due to terrorism.','A massive surge of adrenaline from deep grief can bring on a fatal heart attack. Ironically, the cure is an injection of adrenalin into the heart.','Corals are under threat from 22 kinds of emerging diseases. Thanks to your mum, they also have herpes.','250 grams of bread? is that some kind of shocking statistic?','Noise pollution is forcing some birds to sing at higher frequencies, making them ugly.','A ducks quack doesnt echo, and no one knows why this piece of internet trivia bullshit didnt die off in 1998.','providing it started with gay prison rape','In Scotland you are on the wrong side of the law if you are horny and in possession of a cow.','The fastest motion of any joint in any athlete is my pelvis in bed with ya mum.']

logFormat = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
channelLogFormat = logging.Formatter("%(asctime)s %(name)s %(message)s", "%Y-%m-%d %H:%M:%S")
logFile = logging.handlers.RotatingFileHandler(os.path.join(LOG_PATH, 'fremmy.log'), backupCount=10, encoding="UTF-8")
logFile.setFormatter(logFormat)
logFile.setLevel(logging.DEBUG)
logFile.doRollover()

logConsole = logging.StreamHandler()
logConsole.setFormatter(logFormat)
logConsole.setLevel(logging.INFO)

rootLogger = logging.getLogger('')
rootLogger.setLevel(logging.DEBUG)
rootLogger.addHandler(logConsole)
rootLogger.addHandler(logFile)

chLoggers = {}
chRollers = {}

rootLogger.info('Logger initialised')

def log(line, send=False):
    try:
        (param,message) = line.strip(':').split(':', 1)
    except ValueError:
        message = None
        param = (line.strip(':'))
    params = param.strip().split(' ')
    (server,code,me,junk,channel) = (None,None,None,None,None)
    if len(params) == 5:
        (server,code,me,junk,channel) = params
    elif len(params) == 4:
        (server,code,me,channel) = params
    elif len(params) == 3:
        (server,code,channel) = params
    elif len(params) == 2:
        (server,code) = params
    else:
        server = params[0]
        
    try:
        user = server.split("!")
        user = user[0]
        if channel == NICK:
            channel = user
    except ValueError:
        user = None
    if send:
        rootLogger.info("SEND: '{message}'".format(message=line))
        
        # Log that the bot sent a messaage to a channel
        if code in chLoggers:
            nick = "<{}>".format(NICK)
            chLoggers[code].info("{nick:>20}|{message}".format(nick=nick, message=message)) 
    else:
        rootLogger.info("RECV: '{message}'".format(message=line))
        if code == "PRIVMSG":
            onRecv(user)
        if code == "NICK":
            onNickChangeMessage(user, message)
        
        # Log that the bot received a message in a channel
        if channel in chLoggers:
            user = "<{}>".format(user)
            chLoggers[channel].info("{user:>20}|{message}".format(user=user, message=message)) 

def send(connection, message):
    connection.send(message.encode() + b"\r\n")
    log(message, send=True)

def sendUser(connection, nick, username, realname):
    send(connection, "NICK %s" % (nick,))
    send(connection, "USER %s 8 * :%s" % (username, realname))

def onRecv(user):
    seenMap[user.lower()] = {'at': datetime.datetime.now()}

def onLeave(user, message):
    leaveMap[user.lower()] = {'at': datetime.datetime.now(), 'msg': message}

def getNames(channel):
    send(connection, "NAMES {channel}".format(channel=channel))

def onNickChangeMessage(oldUser, newUser):
    oldUser = oldUser.lower()
    userToUserMap[oldUser] = newUser
    newUser = newUser.lower()
    if oldUser in seenMap.keys():
        seenMap[newUser] = seenMap[oldUser]
        del seenMap[oldUser]
    
def seen(user, searchuser, channel, search=False):
    luser = user.lower()
    extra = ""
    if not luser in seenMap.keys():
        if luser in userToUserMap.keys():
            return seen(userToUserMap[luser], searchuser, channel, True)
        else:
            return ("Sorry, I don't know of a {user}.".format(user=user))
    timeseen = (seenMap[luser]['at']-datetime.datetime.now()).total_seconds()
    if luser in namesList[channel]:
        if search:
            knownas = (", known as {user}".format(user=user))
        else:
            knownas = ""
        extra = (" {user} is currently in this channel now{knownas}.".format(user=searchuser, knownas=knownas))
    if luser not in namesList[channel]:
        timeleft = (leaveMap[luser]['at']-datetime.datetime.now()).total_seconds()
        extra = (" {time} ago they left with the message: {message}".format(time=bot.nicetime.timeConvert(timeleft, True), message=leaveMap[luser]['msg']))
    return ("The person with the nick {user} last spoke {time} ago.{extra}".format(user=searchuser, time=bot.nicetime.timeConvert(timeseen, True), extra=extra))

def imagesearch(searchString, safe="off"):
    conn = http.client.HTTPSConnection('ajax.googleapis.com')
    req = urllib.parse.urlencode({'v': '1.0', 'safe': safe, 'q': searchString})
    conn.connect()
    conn.request('GET', '/ajax/services/search/images?' + req)
    
    response = conn.getresponse()
    responseStr = response.read().decode('UTF-8')
    data = json.loads(responseStr)['responseData']
    try:
        return (data['results'][0]['unescapedUrl'])
    except IndexError:
        return "no results"

def getVideoMeta(videourl):
    if videourl.find("?") < 0:
        return False
    urlParts = videourl.split('?')
    params = urlParts[1].split('&')
    videoID = None
    for param in params:
        bits = param.split('=')
        if bits[0] == 'v':
            videoID = bits[1].split('#',1)[0]

    if videoID == None:
        return False
       
    conn = http.client.HTTPConnection("www.youtube.com")
    path = '/watch?' + urllib.parse.urlencode({'v': videoID})
    conn.connect()
    conn.request('GET', path)
    
    response = conn.getresponse()
    if response.status != http.client.OK:
        return False
    doc = BeautifulSoup(response.read())
    
    try:
        title = doc.title.string.strip()[:-9].strip()    
        views = str(doc.find('span', 'watch-view-count'))
        views = views.strip()[38:-10]
        if str(doc.find('img', 'icon-watch-stats-like')) != 'None':
            trash,up,trash,down,trash = str(doc.find('img', 'icon-watch-stats-like')).split('\n',5)
            likes = up.split('>')[1].strip()[:-6]
            dislikes = down.split('>')[1].strip()[:-6]
            stats = " - ({likes} likes - {dislikes} dislikes)".format(likes=likes, dislikes=dislikes)
        else:
            stats = ""            
    except AttributeError:
        return False
    return ("{title} ({views} Views){stats}".format(title=title, views=views, stats=stats))

def getImageMeta(imageurl):
    if imageurl.find("/") < 0:
        return False
    imgsplit = imageurl.strip()[imageurl.find("imgur.com"):].split(".",2)
    imgID = imgsplit[1].split("/",2)
    if imgID[1] == "gallery":
        imageID = imgID[2]
    elif imgID[1] == "a":
        return False
    else:
        imageID = imgID[1]
                
    if imgID[1] == None:
        return False

    path = ("/gallery/{img}".format(img=imageID))
    try:
        response = urllib.request.urlopen("http://imgur.com{path}".format(path=path))
    except urllib.error.HTTPError:
        return False
    
    if response.status != http.client.OK:
        return False
    doc = BeautifulSoup(response.read())
    
    try:
        title = doc.title.string.strip()

    except AttributeError:
        return False
    try:
        likes = ("{likes}".format(likes=doc.find('div', 'positive')))
        likes = likes.strip()[likes.find('title='):].split('"')
        likes = likes[1]
        dislikes = ("{dislikes}".format(dislikes=doc.find('div', 'negative')))
        dislikes = dislikes.strip()[dislikes.find('title='):].split('"')
        dislikes = dislikes[1]
        metrics = ("- {likes}, {dislikes}".format(likes=likes,dislikes=dislikes))
    except (AttributeError, IndexError):
        metrics = ""

    try:
        if doc.find(id="stats-submit-source-reddit") != None:
            if str(doc.find(id="stats-submit-source-reddit")).find("href") >= 0:
                source = str(doc.find(id="stats-submit-source-reddit")).strip()[66:-20]
                reddit = ("- View comments on reddit ({reddit})".format(reddit=source))
            else:
                reddit = ""
        elif doc.find(id="stats-reddit") != None:
            if str(doc.find(id="stats-reddit")).find("href") >= 0:
                source = str(doc.find(id="stats-reddit")).strip()[22:-47]
                reddit = ("- View comments on reddit ({reddit})".format(reddit=source))
            else:
                reddit = ""
        else:
            reddit = ""
    except (AttributeError, IndexError):
        reddit = ""         
        
    link = ("http://imgur.com{url}".format(url=path))
    return((title.strip()[:-8]), link, metrics, reddit)

def privMsg(channel, user, message):
    trigger = message.split(" ",1)
    if trigger[0] == '!seen':
        if len(trigger) == 2:
            nickquery = trigger[1].split(" ")
            send(connection, "PRIVMSG {channel} :{nick}: {seen}".format(channel=channel, nick=user, seen=seen(nickquery[0], nickquery[0], channel)))
    if trigger[0] == '!roll' and channel in chRollers:
        if len(trigger) == 2:
            if trigger[1] == 'mine':
                send(connection, "NOTICE {channel} :{nick}: {rollresult}".format(channel=channel, nick=user, rollresult=chRollers[channel].mine(user)))
            elif trigger[1] == 'top':
                send(connection, "NOTICE {channel} :{nick}: {rollresult}".format(channel=channel, nick=user, rollresult=chRollers[channel].top()))
        else:
            rollmessage = chRollers[channel].roll(user)
            if rollmessage:
                send(connection, "NOTICE {channel} :{nick}: {rollresult}".format(channel=channel, nick=user, rollresult=rollmessage))
    if trigger[0] == '!image':
        if len(trigger) > 1:
            send(connection, "NOTICE {channel} :{image1}".format(channel=channel, image1=imagesearch(trigger[1])))
    if message.find("youtube.com") > 0:
        vidsplit = message.strip()[message.find("youtube.com"):].split(" ",1)
        video = getVideoMeta(vidsplit[0])
        if video != False:
            send(connection, "NOTICE {channel} :[YouTube] {videoData}".format(channel=channel, videoData=video))
    if message.find("imgur.com") > 0:
        if line.find("gallery") < 0:
            message = message.strip()
            urlsplit = message.strip()[message.find("imgur.com"):].split(" ",1)
            imagetitle = getImageMeta(urlsplit[0])
            print(imagetitle)
            if imagetitle != False:
                send(connection, "NOTICE {channel} :[Imgur] {one} - {two} {likes}".format(channel=channel, one=imagetitle[0], two=imagetitle[1], likes=imagetitle[2]))
    if message.find("imgur.com/gallery") > 0:
        message = message.strip()
        urlsplit = message.strip()[message.find("imgur.com/gallery"):].split(" ",1)
        getImageMeta(urlsplit[0])
        imagetitle = getImageMeta(urlsplit[0])
        if imagetitle != False:
            send(connection, "NOTICE {channel} :[Imgur] {one} {likes}".format(channel=channel, one=imagetitle[0], likes=imagetitle[2]))
    if trigger[0] == '!die':
        if user == 'Fred':
            if len(trigger) == 2:
                if trigger[1] == REMOTEPASS:
                    save()
                    connection.close()
                    sys.exit(0)
    if trigger[0] == '!reconnect':
        if trigger[1]:
            if user == 'Fred':
                passsplit = trigger[1].split(" ",1)
                if len(passsplit) == 2:
                    if passsplit[1] == REMOTEPASS:
                        joinChannel(passsplit[0])
    if message.find("le tired") > -1:
        send(connection, "PRIVMSG {channel} :well have a nap, THEN FIRE ZE MISSLES!".format(channel=channel))
    if message.find("fremmy") > -1:
        if user == "chino":
            send(connection, "PRIVMSG {channel} :{user}, you fucking thundercunt.".format(channel=channel, user=user))
        else:
            send(connection, "PRIVMSG {channel} :{user}, {insultresult}".format(channel=channel, user=user, insultresult=bot.streetgeek.insult.insult()))
    if trigger[0] == '!frag':
        fragmessage = fragResponse[random.randint(0, len(fragResponse) - 1)]
        send(connection, "NOTICE {channel} :[The word of Frag] {text}".format(channel=channel, text=fragmessage))                        
    if trigger[0] == '!ping':
        send(connection, "PRIVMSG {channel} :pong".format(channel=channel))
    if trigger[0] == '!SAGRN':
        send(connection, "NOTICE {channel} :http://paging1.sacfs.org/".format(channel=channel))
    if trigger[0] == '!weather':
        send(connection, "NOTICE {channel} :Weather radar for Adelaide: http://www.bom.gov.au/products/IDR643.loop.shtml#skip".format(channel=channel))
    if trigger[0] == '!help':
        send(connection, "NOTICE {channel} :Available commands to use: !ping, !roll, !roll [mine|top], !seen %user%, !image %search%, !weather, !SAGRN, !frag, !help".format(channel=user))
    if trigger[0] == '!saveall':
        if user == 'Fred':
            if len(trigger) > 1:
                if trigger[1] == REMOTEPASS:
                    save()
def save():
    pickle.dump(seenMap, open("seenMap.pyobj", "wb"))
    rootLogger.info("Saved seenMap")
    pickle.dump(leaveMap, open("leaveMap.pyobj", "wb"))
    rootLogger.info("Saved leaveMap")
    for channel in chRollers.values():
        channel.save()

def handleExit(signum, frame):
    rootLogger.error('Got SIGTERM, exiting...')
    save()
    sys.exit()

def joinChannel(channel):
    chLoggers[channel] = logging.getLogger(channel)
    chLoggers[channel].propagate = False
    chLoggers[channel].setLevel(logging.DEBUG)
    logFile = logging.FileHandler(os.path.join(LOG_PATH, '{channel}.log'.format(channel=channel)), encoding="UTF-8")
    logFile.setFormatter(channelLogFormat)    
    chLoggers[channel].addHandler(logFile)
    
    chRollers[channel] = bot.streetgeek.roll.Roll(channel, config)
    
    send(connection, "JOIN {channel}".format(channel=channel))

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handleExit)
    rootLogger.info("starting")
    timeouts = time.time() - 60
    buff = ""
    pingtimeout = 0
    seenMap = pickle.load(open("seenMap.pyobj", 'rb'))
    rootLogger.info("Loading seenMap")
    leaveMap = pickle.load(open("leaveMap.pyobj", 'rb'))
    rootLogger.info("Loading leaveMap")
    try:
        while True:        
            try:
                rootLogger.info("Connecting...")
                connection = socket.socket()
                connection.connect((server_address, server_port))
                connection.setblocking(False)                
                sendUser(connection, NICK, USERNAME, REALNAME)
                
                lastMessageTime = time.time()
                connectionTimeout = 0
                while connectionTimeout < 300:
                    rlist, wlist, xlist = select.select([connection], [], [], 5) # Only wait for 5 seconds(?) then do the below anyway
                    del wlist
                    del xlist
                    
                    if len(rlist) > 0:
                        if rlist[0] == connection:
                            try:
                                buff = buff + connection.recv(1024).decode('ASCII')
                            except UnicodeDecodeError:
                                continue
                            except KeyboardInterrupt:
                                connection.close()
                                sys.exit(0)
                            if buff.find("\r\n") < 0:
                                continue
                            
                            lines = buff.split("\r\n")
                            
                            if not buff.endswith("\r\n"):
                                buff = lines.pop()
                            else:
                                buff = ""
                                
                            lastMessageTime = time.time() # We got a message! Yeey!
                            
                            for line in lines:
                                if line.strip() == "":
                                    continue
                                log(line)
                                try:
                                    (param,message) = line.lstrip(':').split(':', 1)
                                except ValueError:
                                    message = None
                                    param = (line.strip(':'))
                                params = param.strip().split(' ')
                                (server,code,me,junk,channel) = (None,None,None,None,None)
                                if len(params) == 5:
                                    (server,code,me,junk,channel) = params
                                elif len(params) == 4:
                                    (server,code,me,channel) = params
                                elif len(params) == 3:
                                    (server,code,channel) = params
                                elif len(params) == 2:
                                    (server,code) = params
                                else:
                                    server = params[0]
                                try:
                                    user = server.split("!")
                                    user = user[0]
                                    if channel == NICK:
                                        channel = user
                                except ValueError:
                                    user = None
                                if code == '353':
                                    if not channel in namesListTemp.keys():
                                        namesListTemp[channel] = []
                                    for name in message.strip().split(" ",):
                                        if not name[0:1].isalpha():
                                            name = name[1:] 
                                        namesListTemp[channel].append(name.lower())
                                elif code == '366':
                                    namesList[channel] = namesListTemp[channel]
                                    namesListTemp[channel] = []
                                elif server == ('PING'):
                                    send(connection, "PONG :%s" % (line[6:len(line)].strip()))
                                elif line.endswith(":Nickname is already in use."):
                                    sendUser(connection, NICK + str(NICK_ATTEMPTS), USERNAME, REALNAME)
                                    NICK_ATTEMPTS += 1
                                    if NICK_ATTEMPTS > 5:
                                        break
                                elif code == 'PART':
                                    getNames(channel)
                                    onLeave(user, message)
                                elif code == 'QUIT':
                                    onLeave(user, message)
                                    for channel in namesList.keys():
                                        getNames(channel)
                                elif code == 'JOIN':
                                    if not user == NICK:
                                        getNames(message.strip())
                                elif code == 'NICK':
                                    for channel in namesList.keys():
                                        getNames(channel)
                                elif code == 'PRIVMSG':
                                    privMsg(channel, user, message)
                                elif line.endswith("End of /MOTD command."):
                                    for channel in CHANNELS:
                                        joinChannel(channel)
                    else:
                        connectionTimeout = time.time() - lastMessageTime
                        
                        if connectionTimeout > 150:
                            rootLogger.info("Pinging server...")
                            send(connection, 'PING :' + str(time.time()))

            except(socket.error) as e:
                 rootLogger.info(e)
            connection.close()
            rootLogger.info("Delaying reconnection attempt by 30 seconds")
            time.sleep(30)
    except Exception as e:
        save()
        raise(e)
        sys.exit(1)
        
    save()
    sys.exit(0)
    
