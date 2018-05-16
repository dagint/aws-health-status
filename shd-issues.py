#!/usr/bin/env python3

import boto3
import json
import decimal
import string
import time
from datetime import date,datetime
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

#used to determine if event is related to something in SHD
suffix = "_OPERATIONAL_ISSUE"

#will serialize the date/time to make it easier to work with
def SerializeDateTime(obj):
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

json_pre = json.dumps(response, default=SerializeDateTime)
json_events = json.loads (json_pre)

if (json_events['ResponseMetadata']['HTTPStatusCode']) == 200:
    events = json_events.get('events')
    print len(events)
    for event in events :
        strEventTypeCode = event['eventTypeCode']
        if strEventTypeCode.endswith(suffix):
            strArn = (event['arn'])
            strUpdate = (event['lastUpdatedTime'])
            print strUpdate,' ',SerializeDateTime(datetime.now()),' ',datetime.now()
            print "%s %s" % (strArn, strUpdate)
            event_details = client.describe_event_details (
            eventArns=[
                strArn,
                ]
            )
            json_event_details = json.dumps(event_details, default=SerializeDateTime)
            parsed_event_details = json.loads (json_event_details)
            #print (parsed_event_details['successfulSet'][0]['eventDescription']['latestDescription'])#print parsed_event_details
else:
    print datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"- API call was not successful:",(json_events['ResponseMetadata']['HTTPStatusCode'])
