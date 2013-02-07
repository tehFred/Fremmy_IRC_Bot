import logging
import time
import os.path
import pickle
import random

NEG_RESPONSE=['dam spiked the wrong drink, you aint sleeping','keep coding','keep up the procrastination','keep watching the monkey pr0n','Keep your pants on, no nookie for you','Not tonight, you have a headache?','SLEEP IS FOR LOSERS! and ironically you lost and have to stay up','There is klingons on your starboard bow, its going to be a long night','you need more Jolt, you aint sleeping']
POS_RESPONSE=['all IRC and no sleep  makes... bugger it /quit before i kick you','Bed. The final frontier. Stand by, you are about to be beamed horizontal','enough with the Jolt, your going to sleep','PANTS OFF, ITS TIME FOR BED!','stop procrastinating you are going to bed','stop teh coding your are going to bed','stop watching pr0n, you are going to bed','that roll had roofies in it, your going to sleep','you are getting very sleepy... unless i spiked the wrong drink']

rootLogger = logging.getLogger('')

class Roll:
    def __init__(self, channel, config, timeout=60):
        self.timeout = timeout
        self.lastRoll = time.time() - self.timeout
        
        self.channel = channel
        self.savePath = os.path.join(config.get('savePath', 'rolls'), "{channel}.pyobj".format(channel=channel))
        if os.path.exists(self.savePath):
            self.rollList = pickle.load(open(self.savePath, 'rb'))
        else:
            self.rollList = {}

    def __del__(self):
        self.save()
    
    def save(self):
       pickle.dump(self.rollList, open(self.savePath, "wb"))
       rootLogger.info("Saved rolldata for {channel}".format(channel=self.channel))
        
    def roll(self, user):
        if (time.time() - self.lastRoll) < self.timeout:
            return None
        
        self.lastRoll = time.time()
                
        x = random.randint(1,20)
        if not user in self.rollList.keys():
            self.rollList[user] = []
        self.rollList[user].append(x)
        message = None
        if x<15:
            message = NEG_RESPONSE[random.randint(0, len(NEG_RESPONSE) - 1)]
            return ("{message}, you only rolled {roll}".format(message=message, roll=x))
        else:
            message = POS_RESPONSE[random.randint(0, len(POS_RESPONSE) - 1)]
            return ("{message}, you rolled {roll}!".format(message=message, roll=x))
        
    def top(self):
        tempRollList={}
        for user,data in self.rollList.items():
            y = 0
            z = 0
            average = 0
            for rolls in data:
                y = y+rolls
                z = z+1
                average = int(y/z)
            tempRollList[user] = {'rolls': z, 'average': average}
        highest = None
        highestVal = 0
        avg = 0
        for user,details in tempRollList.items():
            if details['rolls'] > highestVal:
                highest = user
                highestVal = details['rolls']
                avg = details['average']
        return ("Biggest roller: {user} on {roll} rolls, with an average of {avg}.".format(user=highest, roll=highestVal, avg=avg))
        
    def mine(self, user):
        y = 0
        z = 0
        average = 0
        if not user in self.rollList.keys():
            return("You have no roll history")
        for rolls in self.rollList[user]:
            y = y+rolls
            z = z+1
            average = (y/z)
        return ("You have rolled {z} times, for a total of {y}. Your roll average is {x}.".format(y=y, z=z, x=average))
