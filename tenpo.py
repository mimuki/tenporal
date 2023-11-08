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
daysToCalculate = 3""")
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
days = daysToCalculate # How many days of data you want
debug = False # Verify the calculated hours match actual sunrise/sunset

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
midnightEnd = midnightStart + dt.timedelta(days=(days+1))

# I don't totally understand this, but it works
ts = load.timescale()
t0 = ts.from_datetime(midnightStart)
t1 = ts.from_datetime(midnightEnd)
eph = load('de421.bsp')
t, y = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(eph, place))
# Convert to local time
t = t.astimezone(tz)

# Split sunrises and sunsets into seperate lists
sunrises, sunsets = t[::2], t[1::2]
dayMoments = []
nightMoments = []

# For each day requested
for i in range (days):
    # seconds in a day
    dayDuration = toSeconds(sunsets[i]) - toSeconds(sunrises[i])
    # post sunset + pre sunrise, because a night passes over midnight
    nightDuration = 86400 - toSeconds(sunsets[i]) + toSeconds(sunrises[i+1]) 

    # Seconds per hour
    dayHourLength = dayDuration / 12
    nightHourLength = nightDuration / 12
    # Seconds per moment 
    # TODO: implement these
    dayMomentLength = dayHourLength / 40
    nightMomentLength = nightHourLength / 40
    dayMoments.append([])
    nightMoments.append([])
    # The start times of each hour: we know the first one is sunrise/set
    dayHourTime = [sunrises[i]]
    nightHourTime = [sunsets[i]]

    print(sunrises[i].strftime("\n%b %d"))
    # Make sure your math lines up with the actual sunrise and sunset
    if debug:
        print("    Sunrise    Sunset")
        print(
                sunrises[i].strftime("    %I:%M:%S %p") + "   " + 
                sunsets[i].strftime("%I:%M:%S %p"))

    print("    Day hours     Night hours")
    for hour in range(12):
        if hour < 11: # make sure xHourtime[] only has 12 things in it
            # Make the next hour equal 
            # the current hour + the number of seconds in an hour
            dayHourTime.append(
                    dayHourTime[hour] + dt.timedelta(seconds = dayHourLength))
            nightHourTime.append(
                    nightHourTime[hour] + dt.timedelta(seconds = nightHourLength))

        dayInfo = dayHourTime[hour].strftime("%I:%M:%S %p")
        nightInfo = nightHourTime[hour].strftime("%I:%M:%S %p")
        print(str(hour+1).zfill(2) + "  " + dayInfo + "   " + nightInfo)
        # Add a list for each hour of the day/night
        dayMoments[i].append([])
        nightMoments[i].append([])

        # Add the time of each moment to the list we just made for it's hour
        for moment in range(40):
            dayMoments[i][hour].append(
                    dayHourTime[hour] + 
                    dt.timedelta(seconds = dayMomentLength*(moment)))
            nightMoments[i][hour].append(
                    nightHourTime[hour] + 
                    dt.timedelta(seconds = nightMomentLength*(moment)))
            if debug:
                print(str(moment+1).zfill(2) + "  "  + 
                      dayMoments[i][hour][moment].strftime("%I:%M:%S") + "      " + 
                      nightMoments[i][hour][moment].strftime("%I:%M:%S"))


