#!/usr/bin/env python3

import boto3
import json
import decimal
import requests
import configparser
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

# if left blank it will use all regions.  if you are specifying specific regions use comma's with no spaces
# if you are interested in global services you will need to include them in the list
# this is a dictionary object and should be stored in the format example
# example dictRegions = ['us-east-1','us-east-2','global']
#dictRegions = ['us-east-1','us-east-2','global']
dictRegions = ""

config = configparser.ConfigParser()
config.read('config.ini')

snsTopic = config['default']['snsTopicArn']
webHookURL = config['default']['webHookURL']

def diff_dates(strDate1, strDate2):
    intSecs = float(strDate2)-float(strDate1)
    return intSecs

def update_ddb(objTable, strArn, strUpdate, now):
    response = objTable.put_item(
      Item ={
        'arn' : strArn,
        'lastUpdatedTime' : strUpdate,
        'added' : now,
        'ttl' : int(now) + int(intSeconds) + 3600
      }
    )

def get_healthMessage(awshealth, event):
    event_details = awshealth.describe_event_details (
      eventArns=[
        strArn,
      ]
    )
    json_event_details = json.dumps(event_details, cls=DatetimeEncoder)
    parsed_event_details = json.loads (json_event_details)
    healthMessage = (parsed_event_details['successfulSet'][0]['eventDescription']['latestDescription'])#print parsed_event_deta
    healthMessage = '\n' + healthMessage + '\n\nService: ' + str(event['service']) + '\nRegion: ' + str(event['region']) + '\nStatus: ' + str(event['statusCode'])
    phdURL = 'https://phd.aws.amazon.com/phd/home?region=us-east-1#/event-log?eventID=' + strArn + '&eventTab=details&layout=vertical'
    healthMessage = healthMessage + '\n\nPHD URL: ' + phdURL
    return healthMessage

def send_sns(healthMessage, eventName, snsTopic):
    snsClient = boto3.client('sns')
    snsPub = snsClient.publish(
      Message = str(healthMessage),
      Subject = str(eventName),
      TopicArn = snsTopic
    )

def get_healthSubject(event):
    eventTypeCode = str(event['eventTypeCode'])
    service = str(event['service'])
    region =  str(event['region'])
    eventName = eventTypeCode + ' - ' + service + ' - ' + region
    return eventName

def send_webhook(updatedOn, subject, healthMessage, entryURL):
	updatedOn = str(updatedOn)
	subject = str(subject)
	healthMessage = str(healthMessage)
	message = str(":fire: " + subject + " posted an update on " + updatedOn + "\n"
		"-------------------------------------\n" +
		healthMessage + "\n")
	#print(message)

	json.dumps(message)
	chime_message = {'Content': message}
	
	try:
		req = requests.post(entryURL, data=json.dumps(chime_message))
	except HTTPError:
		return False
	return True

	
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
awshealth = boto3.client('health')

dynamodb = boto3.resource("dynamodb", region_name='us-east-1')

SHDIssuesTable = dynamodb.Table('SHD_operational_issues')

strFilter = {'eventTypeCategories': ['issue',]}

if dictRegions != "":
	strFilter = {
		'eventTypeCategories': [
			'issue',
		],
		'regions': 
			dictRegions
	}

response = awshealth.describe_events (
  filter=
    strFilter
  ,
)

json_pre = json.dumps(response, cls=DatetimeEncoder)
json_events = json.loads (json_pre)

if (json_events['ResponseMetadata']['HTTPStatusCode']) == 200:
  events = json_events.get('events')
  for event in events :
    #print ("events for")
    strEventTypeCode = event['eventTypeCode']
    if strEventTypeCode.endswith(strSuffix):
      strArn = (event['arn'])
      strUpdate = parser.parse((event['lastUpdatedTime']))
      #strUpdate = parser.parse(strUpdate)
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
          isItemResponse = response.get('Item')
          if isItemResponse == None:
            print (datetime.now().strftime(strDTMFormat2)+": record not found")
            update_ddb(SHDIssuesTable, strArn, strUpdate, now)
            healthMessage = get_healthMessage(awshealth, event)
            eventName = get_healthSubject(event)
            print ("eventName: ", eventName)
            print ("healthMessage: ",healthMessage)
            send_sns(healthMessage, eventName, snsTopic)
            send_webhook(datetime.now().strftime(strDTMFormat2), eventName, healthMessage, webHookURL)

          else:
            item = response['Item']
            if item['lastUpdatedTime'] != strUpdate:
              print (datetime.now().strftime(strDTMFormat2)+": last Update is different")
              update_ddb(SHDIssuesTable, strArn, strUpdate, now)
              healthMessage = get_healthMessage(awshealth, event)
              eventName = get_healthSubject(event)
              print ("eventName: ", eventName)
              print ("healthMessage: ",healthMessage)
              send_sns(healthMessage, eventName, snsTopic)
              send_webhook(datetime.now().strftime(strDTMFormat2), eventName, healthMessage, webHookURL)
else:
  print (datetime.now().strftime(strDTMFormat2)+"- API call was not successful: "+(json_events['ResponseMetadata']['HTTPStatusCode']))
