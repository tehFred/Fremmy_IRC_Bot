import logging
import time

rootLogger = logging.getLogger

class Seen:
    def __init__(self, config, channel):


        self.channel = channel
        self.savePath = os.path.join(config.get('savePath', 'seen'), "{channel}.pyobj".format(channel=channel))
        if os.path.exists(self.savePath):
            self.seenMap = pickle.load(open(self.savePath, 'rb'))
        else:
            self.seenMap = {}

    def __del__(self):
        self.save()

    def save(self):
        pickle.dump(self.seenMap, open(self.savePath, "wb"))
        rootLogger.info("Saved seenMap for {channel}".format(channel=self.channel)



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
        extra = (" {time} ago they left with the message: {message}".format(time=timeConvert(timeleft), message=leaveMap[luser]['msg']))
    return ("The person with the nick {user} last spoke {time} ago.{extra}".format(user=searchuser, time=timeConvert(timeseen), extra=extra))
