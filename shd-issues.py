#!/usr/bin/env python3

import boto3
import json
import decimal
import string
import time
from datetime import date,datetime
from dateutil import relativedelta,parser
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

#used to determine if event is related to something in SHD
suffix = "_OPERATIONAL_ISSUE"

def diff_dates(date1, date2):
    date1 = datetime.strptime(date1, "%Y-%m-%d %H:%M:%S")
    date2 = datetime.strptime(date2, "%Y-%m-%d %H:%M:%S")
    return abs(date2-date1).seconds

class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super(DatetimeEncoder, obj).default(obj)
        except TypeError:
            return str(obj)


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
    print len(events)
    for event in events :
        strEventTypeCode = event['eventTypeCode']
        if strEventTypeCode.endswith(suffix):
            strArn = (event['arn'])
            strUpdate = (event['lastUpdatedTime'])
            strUpdate = parser.parse(strUpdate)
            strUpdate = strUpdate.strftime("%Y-%m-%d %H:%M:%S")
            now = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
            print diff_dates(strUpdate, now)
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
    print datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"- API call was not successful:",(json_events['ResponseMetadata']['HTTPStatusCode'])
