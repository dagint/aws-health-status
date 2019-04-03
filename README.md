# aws-health-status

## Description
Script polls the AWS Health API (personal health dashboard) to send notifications about status health dashboard events.  Scheduling script to run every minute via cron or converting this to lambda and scheduled with cloudwatch events to regularly poll the Status Health Dashboard.  This will only report on the last 4 hours but will capture anything new if you are running this regularly (every x minutes).  Dynamodb stores the most recent event data arn, time added, lastupdated, and TTL.  

The current TTL value is 4 hours, but can be changed to longer if needed.  The dynamodb table data is set expired an hour after default 4 hours (5 hours) if there has been no updates.

## Requirements
1. Python Modules -> boto3, json, decimal, requests, configparser, datetime
2. SNSTopic Arn -> configure notification how you would like (text message, email)
3. Chime or webhook url -> used to post messages to webhook enabled system
4. DynamoDB Table -> Script uses table name "SHD_operational_issues"
 * The table will need to be created
 * table has TTL enabled with the name of "ttl"
 * arn is the primary key and it uses the default table settings
 * Columns: arn, added, lastUpdatedTime, ttl
 * The ttl will expire the data using the variable intSeconds + 1 hour.  If you are using defaults it will be expire the table row after 5 hours

## Configuration Items
* Create and update config.ini or rename config.ini.sample in the same directory as the script and update snsTopicArn and WebHookURL.
* You can enable or disable sns/webhook notifications
* You can filter regions if you only care about specific regions.  Don't forget to include global as these can effect you and are not tied to a specific region

## Setup
after you get all the requirements done and you have tested the script you can use cron to schedule it to run every minute

## Policy
* Update account number and specific the correct ARN for Dynamodb and SNSTopic
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "NeededPerms",
            "Effect": "Allow",
            "Action": [
                "health:*",
                "dynamodb:ListTables"
            ],
            "Resource": "*"
        },
        {
            "Sid": "SNSTopic",
            "Effect": "Allow",
            "Action": "sns:Publish",
            "Resource": "arn:aws:sns:us-east-1:<accountnumber>:page-me"
        },
        {
            "Sid": "GrantAccessSHDTable",
            "Effect": "Allow",
            "Action": [
                "dynamodb:UpdateTimeToLive",
                "dynamodb:PutItem",
                "dynamodb:DeleteItem",
                "dynamodb:GetItem",
                "dynamodb:Scan",
                "dynamodb:Query",
                "dynamodb:UpdateItem",
                "dynamodb:UpdateTable",
                "dynamodb:GetRecords"
            ],
            "Resource": "arn:aws:dynamodb:us-east-1:<accountnumber>:table/SHD_operational_issues"
        }
    ]
}
```

## TODO
- create a cloudformation template to provision needed resources and policies
- lots of clean up work needed
- documentation needs more work
