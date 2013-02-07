def timeConvert(seconds, negative=False):
    if negative:
        sec = int(seconds*-1)
    else:
        sec = int(seconds)
    days = int(sec/24/60/60)
    hours =  int((sec - (days*24*60*60))/60/60)
    mins =  int((sec/60)%60)
    secs =  int(sec%60)
    and0 = ""
    and1 = ""
    and2 = ""
    
    if days == 0:
        daysection = ""
    elif days == 1:
        daysection = ("{days} day".format(days=days))
    else:
        daysection = ("{days} days".format(days=days))

    if sec < 3600:        
        hoursection = ""
    elif hours == 1:
        hoursection = ("{hours} hour".format(hours=hours))
    else:
        hoursection = ("{hours} hours".format(hours=hours))
        
    if sec < 60:
        minsection = ""
    elif mins == 1:
        minsection = ("{mins} minute".format(mins=mins))
    else:
        minsection = ("{mins} minutes".format(mins=mins))

    if secs == 1:
        secsection = ("{secs} second".format(secs=secs))
    else:
        secsection = ("{secs} seconds".format(secs=secs))

    if sec >=60:
        and2 = " and "

    if sec >= 3600:
        secsection = ""
        and2 = ""
        and1 = " and "
        
    if sec >= 86400:
        secsection = ""
        minsection = ""
        and1 = ""
        and0 = " and "
    
    return ("{days}{and0}{hours}{and1}{mins}{and2}{secs}").format(days=daysection, hours=hoursection, mins=minsection, secs=secsection, and2=and2, and1=and1, and0=and0)
