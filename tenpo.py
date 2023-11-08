#!/usr/bin/env python
# Check if there's a config file
try: 
    from config import timezone, latitude, longitude
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
""")
    config.close()
    print("You need to manually edit that file, unless you want my placeholder data.")
    exit()

import datetime as dt
from zoneinfo import ZoneInfo
from skyfield import almanac
from skyfield.api import wgs84, load

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
# we +1 days, otherwise we wouldn't get night hour info for the last day
midnightEnd = midnightStart + dt.timedelta(days=2)

# I don't totally understand this, but it works
ts = load.timescale()
t0 = ts.from_datetime(midnightStart)
t1 = ts.from_datetime(midnightEnd)
eph = load('de421.bsp')
t, y = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(eph, place))
# Convert to local time
t = t.astimezone(tz)

# seconds in a day
dayDuration = toSeconds(t[1]) - toSeconds(t[0])
# post sunset + pre sunrise, because a night passes over midnight
nightDuration = 86400 - toSeconds(t[1]) + toSeconds(t[3]) 

# Seconds per hour
dayHourLength = dayDuration / 12
nightHourLength = nightDuration / 12
# Seconds per moment 
dayMomentLength = dayHourLength / 40
nightMomentLength = nightHourLength / 40
# A list for each hour of the day
moments  = [[], [], [], [], [], [], [], [], [], [], [], [],
            [], [], [], [], [], [], [], [], [], [], [], []]
# The start times of each hour: we know the first one is sunrise/set
hourTime = [t[0], "", "", "", "", "", "", "", "", "", "", "",
            t[1], "", "", "", "", "", "", "", "", "", "", ""]


# Make sure your math lines up with the actual sunrise and sunset
if debug:
    print(t[0].strftime("\n%b %d"))
    print("    Sunrise    Sunset")
    print(t[0].strftime("    %I:%M:%S %p") + "   " + t[1].strftime("%I:%M:%S %p"))

    print("    Day hours     Night hours")
for hour in range(12):
    if hour < 11: # make sure xHourtime[] only has 12 things in it
        # Make the next hour equal 
        # the current hour + the number of seconds in an hour
        hourTime[hour+1] = hourTime[hour] + dt.timedelta(seconds = dayHourLength)
        hourTime[hour+13] = hourTime[hour+12] + dt.timedelta(seconds = nightHourLength)
    if debug: 
        dayInfo = hourTime[hour].strftime("%I:%M:%S %p")
        nightInfo = hourTime[hour+12].strftime("%I:%M:%S %p")
        print(str(hour+1).zfill(2) + "  " + dayInfo + "   " + nightInfo)


    # Add the time of each moment to the list we just made for it's hour
    for moment in range(40):
        moments[hour].append(
                hourTime[hour] + 
                dt.timedelta(seconds = dayMomentLength*(moment)))
        moments[hour+12].append(
                hourTime[hour+12] + 
                dt.timedelta(seconds = nightMomentLength*(moment)))
        if debug:
            print(str(moment+1).zfill(2) + "  "  + 
                  moments[hour][moment].strftime("%I:%M:%S") + "      " + 
                  moments[hour][moment].strftime("%I:%M:%S"))
hourCount = 0
momentCount = 0

for hour in hourTime:
    if moments[hourCount][-1] <= now:
        # Skip hour, because the last moment in it is in the past
        hourCount = hourCount + 1
    else:
        # The current time is inside the current hour
        currentHour = hour
        lastMoment = moments[hourCount][0]
        while not found:
            for moment in moments:
                if moments[hourCount][momentCount] <= now:
                    # This hour is in the past
                    lastMoment = moment
                else:
                    # This hour is in the future
                    # which means the last one is the current one
                    currentMoment = lastMoment
                    momentCount = momentCount - 1
                    found = True
                    break
                momentCount = momentCount + 1
        break

print(str(hourCount).zfill(2) + ":" +  str(momentCount).zfill(2))
        
