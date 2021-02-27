# -*- coding: utf-8 -*-
"""
Created on Sun Feb 21 13:35:04 2021

@author: Saki
"""
import pytz
from datetime import datetime, timedelta

CHINA_STD_UTC = pytz.timezone('Etc/GMT-8')
JAPAN_STD_UTC = pytz.timezone('Asia/Tokyo')


def chinese_time(year, month, day, hour, minute=0, seconds=0):
    # Initial the date at 0.
    day_start = datetime(year, month, day, 0, 0, 0,
                         tzinfo=CHINA_STD_UTC)
    return day_start + timedelta(hours=hour) + timedelta(minutes=minute) + \
        timedelta(seconds=seconds)


def japanese_time(year, month, day, hour, minute=0, seconds=0):
    # Initial the date at 0.
    day_start = datetime(year, month, day, 0, 0, 0,
                         tzinfo=JAPAN_STD_UTC)
    return day_start + timedelta(hours=hour) + timedelta(minutes=minute) + \
        timedelta(seconds=seconds)


def twitter_time(live_time):
    # Convert to Japan std time.
    jp_time = live_time.astimezone(JAPAN_STD_UTC)
    # Extract the hour time.
    render_hour = jp_time.hour
    if render_hour < 8:
        render_hour += 24
    # Generate the time.
    result = '{}時'.format(render_hour)
    if jp_time.minute > 0:
        result.append('{}分'.format(jp_time.minute))
    return result
