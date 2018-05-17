#!/usr/bin/env python3

import boto3
import json
import decimal
#import string
#import time
from datetime import datetime
from dateutil import parser
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

#used to determine if event is related to something in SHD
strSuffix = "_OPERATIONAL_ISSUE"
# ignore events past the x number of seconds 14400 = 4 hours
intSeconds = 14400 #14400
#set standard date time format used throughout
strDTMFormat2 = "%Y-%m-%d %H:%M:%S"
strDTMFormat = '%s'

snsTopic = "arn:aws:sns:us-east-1:505657850914:page-ginterm"
# if left blank it will use all regions.  if you are specifying specific regions use comma's with no spaces
# if you are interested in global services you will need to include them in the list
# example strRegions = "us-east-1,us-east-2,global"
#strRegions = 'us-east-1,us-east-2'

def diff_dates(strDate1, strDate2):
    intSecs = float(strDate2)-float(strDate1)
    return intSecs

class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super(DatetimeEncoder, obj).default(obj)
        except TypeError:
            return str(obj)

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

# creates health object as client
client = boto3.client('health')

dynamodb = boto3.resource("dynamodb", region_name='us-east-1')

snsClient = boto3.client('sns')

SHDIssuesTable = dynamodb.Table('SHD_operational_issues')

strFilter = {'eventTypeCategories': ['issue',]}

response = client.describe_events (
  filter=
    strFilter
  ,
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
        try:
          response = SHDIssuesTable.get_item(
            Key = {
              'arn' : strArn
            }
          )
        except ClientError as e:
          print(e.response['Error']['Message'])
        else:
          #print response
          isItemResponse = response.get('Item')
          if isItemResponse == None:
            print ("record not found")
            response = SHDIssuesTable.put_item(
              Item ={
                'arn' : strArn,
                'lastUpdatedTime' : strUpdate,
                'added' : now,
                'ttl' : int(now) + int(intSeconds) + 3600
              }
            )

          else:
            item = response['Item']
            if item['lastUpdatedTime'] != strUpdate:
              print ("last Update is different")
              event_details = client.describe_event_details (
                eventArns=[
                  strArn,
                ]   
              )
              json_event_details = json.dumps(event_details, cls=DatetimeEncoder)
              parsed_event_details = json.loads (json_event_details)
              healthMessage = (parsed_event_details['successfulSet'][0]['eventDescription']['latestDescription'])#print parsed_event_deta
              statusCode = (event['statusCode'])
              region = (event['region'])
              eventTypeCode = (event['eventTypeCode'])
              startTime = (event['startTime'])
              lastUpdatedTime = (event['lastUpdatedTime'])
              Category = (event['eventTypeCategory'])
              Service = (event['service'])
              eventName = str(eventTypeCode), ' - ', str(Service), ' - ', str(region)
              healthMessage = '\n' + healthMessage + '\n\nService: ' + str(Service) + '\nRegion: ' + str(region) + '\nStatus: ' + str(statusCode)
              print (healthMessage)
              response = SHDIssuesTable.put_item(
                Item ={
                  'arn' : strArn,
                  'lastUpdatedTime' : strUpdate,
                  'added' : now,
                  'ttl' : int(now) + int(intSeconds) +  3600
                }
              )
              snsPub = snsClient.publish(
                Message = str(healthMessage),
                Subject = str(eventName),
                TopicArn = snsTopic
              )
              #print("GetItem succeeded:")
              #print(json.dumps(item, indent=4, cls=DecimalEncoder))
              #print len(response)
              #bFound = False
              #isItemResponse = response.get('Item')
              #print isItemResponse
              #if isItemResponse == None:
                #print "record not found"
                #response = SHDIssuesTable.put_item(
                  #Item ={
                              #      'arn' : strArn,
                              #      'lastUpdatedTime' : strUpdate,
                  # 'added' : now
                              #      }
                              #)

                #else:  
                            #   for i in response[u'Items']:
                #      if i.arn == strArn :
                #         print "arn match"
                      #if int(i.lastupdate) != int(strUpdate):
                      #   print "last update does not match"
              
                #print diff_dates(strUpdate, now),' ',strUpdate,' ', now
                            #print "%s %s" % (strArn, strUpdate)
                            #event_details = client.describe_event_details (
                            #eventArns=[
                            #    strArn,
                            #    ]
                            #)
                            #json_event_details = json.dumps(event_details, cls=DatetimeEncoder)
                            #parsed_event_details = json.loads (json_event_details)
                            #print (parsed_event_details['successfulSet'][0]['eventDescription']['latestDescription'])#print parsed_event_details
else:
  print (datetime.now().strftime(strDTMFormat2),"- API call was not successful:",(json_events['ResponseMetadata']['HTTPStatusCode']))
