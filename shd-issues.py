#!/usr/bin/env python3

import boto3
import json
import decimal
import string
import time
from datetime import datetime
from dateutil import parser
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

#used to determine if event is related to something in SHD
strSuffix = "_OPERATIONAL_ISSUE"
# ignore events past the x number of seconds 14400 = 4 hours
intSeconds = 86400 #14400
#set standard date time format used throughout
strDTMFormat = "%Y-%m-%d %H:%M:%S"

def diff_dates(strDate1, strDate2):
    intSecs = 0
    strDate1 = datetime.strptime(strDate1, strDTMFormat)
    strDate2 = datetime.strptime(strDate2, strDTMFormat)
    if abs(strDate2-strDate1).days >= 1:
        intSecs = abs(strDate2-strDate1).days * 86400
    intSecs = intSecs + abs(strDate2-strDate1).seconds
    return intSecs

class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super(DatetimeEncoder, obj).default(obj)
        except TypeError:
            return str(obj)

#matches aws health api json date format
def default(obj):
    """Default JSON serializer."""
    import calendar, datetime

    if isinstance(obj, datetime.datetime):
        if obj.utcoffset() is not None:
            obj = obj - obj.utcoffset()
        millis = int(
            calendar.timegm(obj.timetuple()) * 1000 +
            obj.microsecond / 1000
        )
        return millis
    raise TypeError('Not sure how to serialize %s' % (obj,))

# creates health object as client
client = boto3.client('health')

response = client.describe_events (
  filter={
    'eventTypeCategories': [
      'issue',
    ]
  },
)

json_pre = json.dumps(response, cls=DatetimeEncoder)
json_events = json.loads (json_pre)

if (json_events['ResponseMetadata']['HTTPStatusCode']) == 200:
    events = json_events.get('events')
    for event in events :
        strEventTypeCode = event['eventTypeCode']
        if strEventTypeCode.endswith(strSuffix):
            strArn = (event['arn'])
            strUpdate = (event['lastUpdatedTime'])
            strUpdate = parser.parse(strUpdate)
            strUpdate = strUpdate.strftime(strDTMFormat)
            now = datetime.strftime(datetime.now(),strDTMFormat)
            if diff_dates(strUpdate, now) < intSeconds:
                print diff_dates(strUpdate, now),' ',strUpdate,' ', now
                print "%s %s" % (strArn, strUpdate)
                event_details = client.describe_event_details (
                eventArns=[
                    strArn,
                    ]
                )
                json_event_details = json.dumps(event_details, cls=DatetimeEncoder)
                parsed_event_details = json.loads (json_event_details)
                #print (parsed_event_details['successfulSet'][0]['eventDescription']['latestDescription'])#print parsed_event_details
else:
    print datetime.now().strftime(strDTMFormat),"- API call was not successful:",(json_events['ResponseMetadata']['HTTPStatusCode'])
