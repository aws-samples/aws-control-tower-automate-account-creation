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
import cfnresource

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
DYNO = boto3.client('dynamodb')
ORG = boto3.client('organizations')
SSS = boto3.client('s3')
TABLE_NAME = os.environ.get("TABLE_NAME")
BUCKET_NAME = os.environ.get("BATCH_BUCKET_NAME")
KEY_NAME = os.environ.get("BATCH_KEY_NAME")


def dyno_scan(table_name):
    '''Return list of OUs in the organization'''

    result = list()

    try:
        dyno_paginator = DYNO.get_paginator('scan')
        dyno_page_iterator = dyno_paginator.paginate(TableName=table_name)
    except ClientError as exe:
        LOGGER.error('Unable to scan the table: %s', str(exe))

    for page in dyno_page_iterator:
        result += page['Items']

    return result


def get_items(status):
    '''Get list of Valid entries to be provisioned'''

    result = list()
    items = dyno_scan(TABLE_NAME)

    for item in items:
        if item['Status']['S'] == status:
            result.append(item)

    return result


def list_org_roots():
    '''
    List organization roots
    '''

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
    '''
    Return list of OUs in the organization
    '''

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
    '''
    Return list of accounts in the organization
    '''

    result = list()
    account_list = list()

    root_id = list_org_roots()

    try:
        org_paginator = ORG.get_paginator('list_accounts_for_parent')
        org_page_iterator = org_paginator.paginate(ParentId=root_id)
    except ClientError as exe:
        LOGGER.error('Unable to get Accounts list: %s', str(exe))

    for page in org_page_iterator:
        result += page['Accounts']

    for item in result:
        account_list.append(item['Email'])

    return account_list


def validate_org_unit(org_unit, ou_list=None):
    '''
    Return True if Org exists
    '''

    orgexist = False
    if not ou_list:
        ou_list = list_ou_names()

    ou_name = org_unit.split('(ou-')[0].rstrip()

    if ou_name in ou_list:
        orgexist = True

    return orgexist


def is_email_exists(email):
    '''
    Return True if email exists in current organization
    '''

    emailexist = False
    email_list = list_of_accounts()

    if email in email_list:
        emailexist = True
    return emailexist


def validateinput(row, ou_info=None):
    '''
    Return validation status and error list if found any
    '''

    error_list = list()
    validation = 'VALID'
    emailexpression = r'[^\s@]+@[^\s@]+\.[^\s@]+'
    fields = ['AccountName', 'AccountEmail', 'SSOUserEmail',
              'OrgUnit', 'SSOUserFirstName', 'SSOUserLastName']

    for field in fields:
        if row[field] == 'None':
            error_list.append(field + "is a required field.")

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
    if not validate_org_unit(row['OrgUnit'], ou_info):
        error_list.append("OrgUnit " + row['OrgUnit'] + " is not valid")
    if is_email_exists(row['AccountEmail']):
        error_list.append("Account email - " + row['AccountEmail']
                          + " in use by another account")

    if len(error_list) > 0:
        validation = 'INVALID'
        LOGGER.info('Validation status %s and error message %s ',
                    validation, error_list)

    return (validation, error_list)


def read_file(name, key_name='sample.csv', method='s3'):
    '''
    Return file content if exist
    '''

    LOGGER.info('BUCKET NAME: %s, KEY NAME: %s', name, key_name)
    result = None
    try:
        if method == 's3':
            LOGGER.info('METHOD: %s', method)
            body = SSS.get_object(Bucket=name,
                                  Key=key_name)['Body']
            result = body.read().decode('utf-8-sig')
        elif method == 'https':
            file = urlopen(name)
            result = file.read().decode('utf-8-sig')
        else:
            raise Exception('UNSUPPORTED_METHOD')
    except ClientError as exe:
        LOGGER.error('Unable to read the file/url: %s', str(exe))

    return result


def validate_update_dyno(content, table_name):
    '''
    Validate and update dyno table
    '''

    response = False
    ou_info = list_ou_names()

    for row in csv.DictReader(content.splitlines()):
        (validation, errormsg) = validateinput(row, ou_info)
        LOGGER.info('Inserting Row: %s in %s, %s',
                    row['AccountName'], row['OrgUnit'], str(errormsg))
        try:
            response = DYNO.put_item(
                Item={
                    'AccountName': {'S': row['AccountName'], },
                    'SSOUserEmail': {'S': row['SSOUserEmail'], },
                    'AccountEmail': {'S': row['AccountEmail'], },
                    'SSOUserFirstName': {'S': row['SSOUserFirstName'], },
                    'SSOUserLastName': {'S': row['SSOUserLastName'], },
                    'OrgUnit': {'S': row['OrgUnit'], },
                    'Status': {'S': validation},
                    'AccountId': {'S': 'UNKNOWN'},
                    'Message': {'S': str(errormsg)}
                },
                TableName=table_name,
                )
        except ClientError as exe:
            LOGGER.error('Unable to update the table: %s', str(exe))

    return response


def account_handler(event, context):
    '''
    Lambda Handler
    '''

    result = False

    if event['RequestType'] == 'Create':
        fcontent = read_file(BUCKET_NAME, KEY_NAME)

        if fcontent:
            LOGGER.info('Updating DynamoDB: %s', TABLE_NAME)
            update_response = validate_update_dyno(fcontent, TABLE_NAME)

            if update_response:
                result = True

            if len(get_items('INVALID')) > 0:
                LOGGER.warning('INVALID Entries: %s', get_items('INVALID'))
    else:
        result = True

    if result is True:
        response = {}
        cfnresource.send(event, context, cfnresource.SUCCESS,
                         response, "CustomResourcePhysicalID")
    else:
        response = {"error": "Failed to load the data"}
        LOGGER.error(response)
        cfnresource.send(event, context, cfnresource.FAILED,
                         response, "CustomResourcePhysicalID")
