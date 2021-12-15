#
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

'''
This lamdba validates the input file and updates the dynamodb as needed
'''

import os
import re
import logging
import csv
from urllib.request import urlopen
import boto3
from botocore.exceptions import ClientError

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
DYNO = boto3.client('dynamodb')
ORG = boto3.client('organizations')
SSS = boto3.client('s3')
TABLE_NAME = os.environ.get("TABLE_NAME")
BUCKET_NAME = os.environ.get("BATCH_BUCKET_NAME")
KEY_NAME = os.environ.get("BATCH_KEY_NAME")

def dyno_scan():
    '''Return list of OUs in the organization'''

    result = list()

    try:
        dyno_paginator = DYNO.get_paginator('scan')
        dyno_page_iterator = dyno_paginator.paginate(TableName=TABLE_NAME)
    except ClientError as exe:
        LOGGER.error('Unable to scan the table: %s', str(exe))

    for page in dyno_page_iterator:
        result += page['Items']

    return result

def get_items(status):
    '''Get list of Valid entries to be provisioned'''

    result = list()
    items = dyno_scan()

    for item in items:
        if item['Status']['S'] == status:
            result.append(item)

    return result

def list_org_roots():
    '''List organization roots'''

    value = None
    root_info = list()

    try:
        root_info = ORG.list_roots()
    except ClientError as exe:
        LOGGER.error('Allowed only on Organizations root: %s', str(exe))

    if 'Roots' in root_info:
        value = root_info['Roots'][0]['Id']
    else:
        LOGGER.error('Unable to find valid root: %s ', root_info)

    return value

def list_of_ous():
    '''Return list of OUs in the organization'''

    result = list()
    account_list = list()
    root_id = list_org_roots()

    try:
        org_paginator = ORG.get_paginator(
            'list_organizational_units_for_parent')
        org_page_iterator = org_paginator.paginate(ParentId=root_id)
    except ClientError as exe:
        LOGGER.error('Unable to get Accounts list: %s', str(exe))

    for page in org_page_iterator:
        result += page['OrganizationalUnits']

    for item in result:
        account_list.append(item['Name'])

    return account_list

def list_ou_names():
    '''
    Return list of OU Names
    '''

    return get_ou_map().values()

def list_children(parent_id, c_type='ORGANIZATIONAL_UNIT'):
    '''
    List all children for a OU
    '''

    result = list()

    try:
        paginator = ORG.get_paginator('list_children')
        iterator = paginator.paginate(ParentId=parent_id,
                                     ChildType=c_type)
    except ClientError as exe:
        LOGGER.error('Unable to get children: %s', str(exe))

    for page in iterator:
        result += page['Children']

    return result

def get_child_ous(prev_level):
    '''
    Return all child OUs
    '''

    result = list()

    for item in prev_level:
        child = list_children(item['Id'])
        if len(child) > 0:
            result += list_children(item['Id'])

    return result

def get_ou_map():
    '''
    Return ou-id:ou-name mapping dict
    '''

    ou_map = dict()
    root_id=list_org_roots()
    lvl_one = list_children(root_id)
    lvl_two = get_child_ous(lvl_one)
    lvl_three = get_child_ous(lvl_two)
    lvl_four = get_child_ous(lvl_three)
    lvl_five = get_child_ous(lvl_four)
    result = lvl_one + lvl_two + lvl_three + lvl_four + lvl_five


    for item in result:
        ou_id=item['Id']
        ou_info=ORG.describe_organizational_unit(OrganizationalUnitId=ou_id)
        ou_name=ou_info['OrganizationalUnit']['Name']
        ou_map[ou_id] = ou_name

    return ou_map

def list_of_accounts():
    '''Return list of accounts in the organization'''

    account_list = list()

    # root_id = list_org_roots()

    try:
        org_paginator = ORG.get_paginator('list_accounts')
        org_page_iterator = org_paginator.paginate()
    except ClientError as exe:
        LOGGER.error('Unable to get Accounts list: %s', str(exe))

    for page in org_page_iterator:
        account_list += page['Accounts']

    return account_list

def validate_org_unit(org_unit):
    '''Return True if Org exists'''

    orgexist = False
    ou_list = list_ou_names()
    ou_name = org_unit.split('(ou-')[0].rstrip()

    if ou_name in ou_list:
        orgexist = True

    return orgexist

def is_email_exists(email):
    '''Return True if email exists in current organization'''

    accounts = list_of_accounts()
    for account in accounts:
     if account['Email'] == email:
        return True

    return False

def is_existing_account(email, accountName):
    '''Return True if specified input matches with any existing account in current organization'''

    accounts = list_of_accounts()
    for account in accounts:
        if account['Email'] == email and account['Name'] == accountName:
            return True
    return False


def validateinput(row):
    '''Return validation status and error list if found any'''

    error_list = list()

    emailexpression = r'[^\s@]+@[^\s@]+\.[^\s@]+'
    fields = ['AccountName', 'AccountEmail', 'SSOUserEmail',
              'OrgUnit', 'SSOUserFirstName', 'SSOUserLastName']

    for field in fields:
        if row[field] == 'None':
            error_list.append(field + "is a required field.")

    
    if is_existing_account(row['AccountEmail'], row['AccountName']):
        LOGGER.warn("Account email - " + row['AccountEmail'] 
            + " and Account Name - " + row['AccountName'] 
            + " already exists")
        cmd_status = 'ALREADY_EXISTS' # Don't update dynamo db table for existing accounts. Leave as is
        return ('ALREADY_EXISTS', error_list)
    else:
        if len(row['AccountName']) > 50:
            error_list.append("AccountName should be less than 50 characters., ")
        if len(row['AccountEmail']) < 7:
            error_list.append("AccountEmail should be more than 6 characters., ")
        if len(row['SSOUserEmail']) < 7:
            error_list.append("SSOUserEmail should be more than 6 characters., ")
        if re.match(emailexpression, row['AccountEmail']) is None:
            error_list.append("AccountEmail is not valid., ")
        if re.match(emailexpression, row['SSOUserEmail']) is None:
            error_list.append("SSOUserEmail is not valid., ")
        if not validate_org_unit(row['OrgUnit']):
            error_list.append("OrgUnit " + row['OrgUnit'] + " is not valid")
        if is_email_exists(row['AccountEmail']):
            # check if requested email is already in use for someother account
            error_list.append("Account email - " + row['AccountEmail']
                          + " in use by another account")

    if len(error_list) > 0:
        cmd_status = 'INVALID'
        LOGGER.info('Validation status %s and error message %s ',
                    cmd_status, error_list)
    else:
        cmd_status = 'VALID'
        LOGGER.info('Validation status %s',
                    cmd_status)
    
    return (cmd_status, error_list)


def read_file(name, key_name='sample.csv', method='s3'):
    '''Return file content if exist'''

    LOGGER.info('BUCKET NAME: %s, KEY NAME: %s', name, key_name)
    result = None
    try:
        if method == 's3':
            body = SSS.get_object(Bucket=name,
                                  Key=key_name)['Body']
            result = body.read().decode('utf-8')
        elif method == 'https':
            file = urlopen(name)
            result = file.read().decode('utf-8')
        else:
            raise Exception('UNSUPPORTED_METHOD')
    except ClientError as exe:
        LOGGER.error('Unable to read the file/url: %s', str(exe))

    return result


def validate_update_dyno(content, table_name):
    '''Validate and update dyno table'''

    response = False

    for row in csv.DictReader(content.splitlines()):
        (cmd_status, errormsg) = validateinput(row)
        try:
            # Only update dynamo db for new valid / invalid account entries
            if cmd_status == 'VALID' or cmd_status == 'INVALID':
                response = DYNO.put_item(
                    Item={
                        'AccountName': {'S': row['AccountName'], },
                        'SSOUserEmail': {'S': row['SSOUserEmail'], },
                        'AccountEmail': {'S': row['AccountEmail'], },
                        'SSOUserFirstName': {'S': row['SSOUserFirstName'], },
                        'SSOUserLastName': {'S': row['SSOUserLastName'], },
                        'OrgUnit': {'S': row['OrgUnit'], },
                        'Status': {'S': cmd_status},
                        'AccountId': {'S': 'UNKNOWN'},
                        'Message': {'S': str(errormsg)}
                    },
                    TableName=table_name,
                )
        except ClientError as exe:
            LOGGER.error('Unable to update the table: %s', str(exe))

    return response


def account_handler(event, context):
    '''Lambda Handler'''

    # Read S3 contents
    fcontent = read_file(BUCKET_NAME, KEY_NAME)

    if fcontent:
        update_response = validate_update_dyno(fcontent, TABLE_NAME)

        if update_response:
            LOGGER.info(update_response)
                

        if len(get_items('INVALID')) > 0:
                LOGGER.warning('INVALID Entries: %s', get_items('INVALID'))
        
    else:
        response = {"error": "Failed to load the data"}
        LOGGER.error(response)
