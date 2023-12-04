#!/usr/bin/env python
# Check if there's a config file
try: 
    from config import timezone, latitude, longitude, daysToCalculate
# Generate a placeholder if there isn't
except ModuleNotFoundError:
    print("Could not find config.py.")
    config = open("config.py", "w")
    # Write this stuff to the config file
    config.write("""from skyfield.api import N, E, S, W
# Enter your own timezone and coordinates here
# for timezone names, see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
timezone  = 'Australia/Sydney' 
latitude  = -33.86514 * N 
longitude = 151.20990 * E
daysToCalculate = 3
""")
    config.close()
    print("You need to manually edit that file, unless you want my placeholder data.")
    exit()

import datetime as dt
import sys
from zoneinfo import ZoneInfo
from skyfield import almanac
from skyfield.api import wgs84, load

args = sys.argv # Any command line arguments
args.pop(0) # This would just be the command itself

# The location you want to calculate for- edit in config.py
# (generated when running this for the first time)
tz = ZoneInfo(timezone)
place = wgs84.latlon(latitude, longitude)
debug = False # Verify the calculated hours match actual sunrise/sunset
found = False # used for "yep that's the right time, we can stop now"

# Convert a datetime into seconds since midnight
def toSeconds(list):
    hours = int(list.strftime("%H"))
    minutes = int(list.strftime("%M"))
    seconds = int(list.strftime("%S"))
    return (hours * 3600) + (minutes * 60) + seconds

# Figure out local midnight.
now = dt.datetime.now().astimezone(tz)
midnightStart = now.replace(hour=0, minute=0, second=0, microsecond=0)
# after midnight and before sunrise, we actually want the day that started yesterday
midnightStart = midnightStart - dt.timedelta(days=1)
# No special arguments, proceed as normal
if len(args) == 0:
    days = daysToCalculate
    clockMode = False
else:
# special clock mode
# the secret is that you can just type whatever you want atm
# evnetually i'm gonna make it be "clock" or smth, but
# i'm not gonna worry about it until/unless i add other options
    days = 1
    clockMode = True
# make sure we get night hour info for the last day
midnightEnd = midnightStart + dt.timedelta(days=2+days)

# I don't totally understand this, but it works
ts = load.timescale()
t0 = ts.from_datetime(midnightStart)
t1 = ts.from_datetime(midnightEnd)
eph = load('de421.bsp')
t, y = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(eph, place))
# Convert to local time
t = t.astimezone(tz)

# A list for each hour of the day
# Only calculated for the current day
moments = [[], [], [], [], [], [], [], [], [], [], [], [],
           [], [], [], [], [], [], [], [], [], [], [], []]

# The start times of each hour: we know the first one is sunrise/set
hourTime = []
hourLength = [] # seconds per hour
dayNightDuration = [] # seconds per [day, night]
momentLength = [] # seconds per [daytime moment, nighttime moment]
index = 0
count = 0
endEarly = False
for i in range(days+1):
    if i == 0:
        # today sunrise was in the past
        # this means yesterday's day is irrelevant
        if t[index+2] < now:
            index = index + 2
            continue
        else: 
            # the current day started before midnight 
            # this means we have one day too many
            endEarly == True

    # i wonder if this is wrong? it seems to be working but i'm sus
    if i != range(days) or (i >= range(days) and endEarly == False):

        # seconds in a day / night
        dayNightDuration.append( [toSeconds(t[index+1]) - toSeconds(t[index]),
                        86400 - toSeconds(t[index+1]) + toSeconds(t[index+2])])

        # todo: this but way more optimal, and adding all the values at once
        hourTime.append([t[index], "", "", "", "", "", "", "", "", "", "", "",
                        t[index+1], "", "", "", "", "", "", "", "", "", "", ""])

        hourLength.append([dayNightDuration[count][0] / 12, dayNightDuration[count][1] / 12])
        count = count + 1
        index = index + 2
    else:
        print("ono")
# Seconds per moment 
momentLength = [hourLength[0][0] / 40, hourLength[0][1] / 40]

for day in range(days):
    # Make sure your math lines up with the actual sunrise and sunset
    if debug:
        print("    Sunrise    Sunset")
        print(t[0].strftime("    %I:%M:%S %p") + "   " + t[1].strftime("%I:%M:%S %p"))
    if not clockMode:
        print(hourTime[day][0].strftime("\n%b %d"))
        print("    Day hours     Night hours")
    for hour in range(24):
        if hour < 23: # make sure hourTime only has 24 things in it per day
            if hour < 12: # use daytime hour / moment lengths
                length = hourLength[day][0]
                mLength = momentLength[0]
            else: # use night time hour/moment lengths
                length = hourLength[day][1]
                mLength = momentLength[1]
            hourTime[day][hour+1] = hourTime[day][hour] + dt.timedelta(seconds = length)

        # Add the time of each moment to the list we made for it's hour
        for moment in range(40):
            moments[hour].append(
                    hourTime[day][hour] + 
                    dt.timedelta(seconds = mLength*(moment)))
            if debug:
                print(str(moment+1).zfill(2) + "  "  + 
                      moments[hour][moment].strftime("%I:%M:%S") + "      " + 
                      moments[hour][moment].strftime("%I:%M:%S"))
    hourCount = 0
    momentCount = 0

    for hour in range(12):
        if not clockMode:
            dayInfo = hourTime[day][hour].strftime("%I:%M:%S %p")
            nightInfo = hourTime[day][hour+12].strftime("%I:%M:%S %p")
            print(str(hour+1).zfill(2) + "  " + str(dayInfo) + "   " + str(nightInfo))

    for hour in hourTime[hourCount]:
        if moments[hourCount][-1] <= now:
            # Skip hour, because the last moment in it is in the past
            hourCount = hourCount + 1
        else:
            # The current time is inside the current hour
            currentHour = hour
            # needed for when you've just ticked over to a new hour
            # (otherwise lastMoment isn't set right)
            lastMoment = moments[hourCount][0]
            while not found:
                for moment in moments:
                    if moments[hourCount][momentCount] <= now:
                        # This moment is in the past
                        lastMoment = moment
                    else:
                        # This moment is in the future
                        # which means the last one is the current one
                        currentMoment = lastMoment
                        hourCount = hourCount + 1 # counting from 1
                        if hourCount > 12:
                            hourCount = hourCount - 12
                        if momentCount > 0:
                            momentCount = momentCount - 1
                        found = True
                        break
                    momentCount = momentCount + 1
            break

    if clockMode:
        print(str(hourCount).zfill(2) + ":" +  str(momentCount).zfill(2))
if not clockMode: 
    print("\nOutput " + str(days) + " days successfully.")
            
