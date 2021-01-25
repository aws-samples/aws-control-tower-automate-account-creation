import boto3
import json
import logging
import os

def check_existing_user(email, table):
    resp = table.get_item(
            Key={
                'email' : email
            }
        )

    if 'Item' in resp:
        return True
    else:
        return False
    

def lambda_handler(event, context):

    LOGGER = logging.getLogger()
    LOGGER.setLevel(logging.INFO)
    
    table_name = os.environ.get("TABLE_NAME")
    dynamodb = boto3.resource(table_name)
    table = dynamodb.Table('new-users')
    
    email = event['email']
    fname = event['fname']
    lname = event['lname']
    
    if check_existing_user(email, table) == False:
        new_item = {
            'AccountName': fname+'.'+lname,
            'SSOUserEmail': email,
            'AccountEmail': email,
            'SSOUserFirstName': fname,
            'SSOUserLastName': lname,
            'OrgUnit': 'Custom',
            'Status': 'VALID',
            'AccountId': '',
            'Message': ''
        }
        
        table.put_item(Item=new_item)
        LOGGER.info('added user: '+ email)
        
    else:
        LOGGER.info('A request was made by a user that already exists in the database.')