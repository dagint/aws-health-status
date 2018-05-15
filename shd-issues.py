#!/usr/bin/env python3

import boto3
import json
import decimal
import string
#import time
from datetime import date,datetime


suffix = "_OPERATIONAL_ISSUE"

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


client = boto3.client('health')

response = client.describe_events (
  filter={
    'eventStatusCodes': [
      'closed',
    ],
    'regions': [
      'us-east-1','us-east-2',
    ],
    'eventTypeCategories': [
      'issue',
    ]
  },
)

json_pre = json.dumps(response, default=default)
json_events = json.loads (json_pre)

print (json_events['ResponseMetadata']['HTTPStatusCode'])
#print (json_events['events'])

events = json_events.get('events')
print len(events)
for event in events :
    strEventTypeCode = event['eventTypeCode']
    if strEventTypeCode.endswith(suffix):
        strArn = (event['arn'])
        strUpdate = (event['lastUpdatedTime'])

        print "%s %s" % (strArn, strUpdate)
        event_details = client.describe_event_details (
        eventArns=[
            strArn,
            ]
        )
        json_event_details = json.dumps(event_details, default=default)
        parsed_event_details = json.loads (json_event_details)
        print (parsed_event_details['successfulSet'][0]['eventDescription']['latestDescription'])#print parsed_event_details

    #print json_event_details
