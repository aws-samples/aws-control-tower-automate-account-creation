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
Lambda to process batch account creation
'''
import logging
import os
from time import sleep
from random import randint
import boto3
import cfnresource

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
SC = boto3.client('servicecatalog')
DYNO = boto3.client('dynamodb')
STS = boto3.client('sts')
TABLE_NAME = os.environ.get("TABLE_NAME")
PRINCIPAL_ARN = os.environ.get("PRINCIPAL_ARN")
SLEEP = 10


def dyno_scan(table_name):
    '''Return list of OUs in the organization'''

    result = list()

    try:
        dyno_paginator = DYNO.get_paginator('scan')
        dyno_page_iterator = dyno_paginator.paginate(TableName=table_name)
    except Exception as exe:
        LOGGER.error('Unable to scan the table: %s', str(exe))

    for page in dyno_page_iterator:
        result += page['Items']

    return result


def get_items(status, negate=False):
    '''Get list of Valid entries to be provisioned'''

    result = list()
    items = dyno_scan(TABLE_NAME)

    for item in items:
        if negate:
            if item['Status']['S'] != status:
                result.append(item)
        else:
            if item['Status']['S'] == status:
                result.append(item)

    return result


def get_portfolio_id(prod_id):
    ''' Find the Portfolio Id of AWS Control Tower Account Factory '''

    af_name = 'AWS Control Tower'
    key = 'ProviderName'
    output = None
    port_list = []

    try:
        port_list = SC.list_portfolios_for_product(
            ProductId=prod_id)['PortfolioDetails']
    except Exception as exe:
        LOGGER.error('Unable to find Product Id: %s', str(exe))

    for item in port_list:
        if key in item:
            if item[key] == af_name:
                output = item['Id']
                break
        else:
            LOGGER.warning('Unexepected output recieved. Skipping: %s', item)

    if not output:
        LOGGER.error('Unable to find Product Id: %s', str(port_list))

    return output


def get_product_id():
    ''' Find the Product Id of AWS Control Tower Account Factory '''

    filters = {'Owner': ['AWS Control Tower']}
    af_product_name = 'AWS Control Tower Account Factory'
    key = 'ProductViewSummary'
    output = None
    search_list = []

    try:
        search_list = SC.search_products_as_admin(
            Filters=filters)['ProductViewDetails']
    except Exception as exe:
        LOGGER.error('Unable to find Product Id: %s', str(exe))

    for item in search_list:
        if key in item:
            if item[key]['Name'] == af_product_name:
                output = item[key]['ProductId']
                break
        else:
            LOGGER.warning('Unexepected output recieved. Skipping: %s', item)

    if not output:
        LOGGER.error('Unable to find Product Id: %s', str(search_list))

    return output


def list_principals_in_portfolio(port_id):
    '''List all prinicpals associated with a portfolio'''

    pri_info = list()
    pri_list = list()

    try:
        sc_paginator = SC.get_paginator('list_principals_for_portfolio')
        sc_page_iterator = sc_paginator.paginate(PortfolioId=port_id)
    except Exception as exe:
        LOGGER.error('Unable to get prinicpals list: %s', str(exe))

    for page in sc_page_iterator:
        pri_list += page['Principals']

    for item in pri_list:
        pri_info.append(item['PrincipalARN'])

    return pri_info


def associate_principal_portfolio(principal, port_id):
    '''Associate a pricipal to portfolio if doesn't exist'''

    result = True
    pri_list = list_principals_in_portfolio(port_id)

    if principal not in pri_list:
        try:
            result = SC.associate_principal_with_portfolio(
                PortfolioId=port_id, PrincipalARN=principal,
                PrincipalType='IAM')
            LOGGER.info('Associated %s to %s. Sleeping %s sec', principal,
                        port_id, SLEEP)
            sleep(SLEEP)
        except Exception as exe:
            LOGGER.error('Unable to associate a principal: %s', str(exe))
            result = False

    return result


def disassociate_principal_portfolio(principal, port_id):
    '''Associate a pricipal to portfolio if doesn't exist'''

    result = True
    pri_list = list_principals_in_portfolio(port_id)

    if principal in pri_list:
        try:
            result = SC.disassociate_principal_from_portfolio(
                PortfolioId=port_id, PrincipalARN=principal)
            LOGGER.info('Disassociated %s to %s', principal,
                        port_id)
        except Exception as exe:
            LOGGER.error('Unable to disassociate a principal: %s', str(exe))
            result = False

    return result


def generate_input_params(item):
    '''Generate the input param in format required for SC'''

    record = [
        {'Value': item['SSOUserEmail']['S'], 'Key': 'SSOUserEmail'},
        {'Value': item['SSOUserFirstName']['S'], 'Key': 'SSOUserFirstName'},
        {'Value': item['SSOUserLastName']['S'], 'Key': 'SSOUserLastName'},
        {'Value': item['OrgUnit']['S'], 'Key': 'ManagedOrganizationalUnit'},
        {'Value': item['AccountName']['S'], 'Key': 'AccountName'},
        {'Value': item['AccountEmail']['S'], 'Key': 'AccountEmail'}
        ]

    return record


def get_provisioning_artifact_id(prod_id):
    ''' Query for Provisioned Artifact Id '''

    pa_list = list()
    output = None

    try:
        pa_list = SC.describe_product_as_admin(
            Id=prod_id)['ProvisioningArtifactSummaries']
    except Exception as exe:
        LOGGER.error("Unable to find the Provisioned Artifact Id: %s",
                     str(exe))

    if len(pa_list) > 0:
        output = pa_list[-1]['Id']
    else:
        LOGGER.error("Unable to find the Provisioned Artifact Id: %s",
                     str(pa_list))

    return output


def generate_provisioned_product_name(data):
    ''' Generate Provisioned product name from data '''

    result = None

    for i in data:
        if i['Key'] == 'AccountName':
            result = 'AccountLaunch-'+i['Value']

    return result


def generate_account_name(data):
    ''' Generate AccountName from data '''

    result = None

    for i in data:
        if i['Key'] == 'AccountName':
            result = i['Value']

    return result


def provision_new_account():
    '''Provision new SC account'''

    valid_items = get_items('VALID')
    result = "FAILED"
    prod_id = get_product_id()
    input_params = list()
    pa_id = get_provisioning_artifact_id(prod_id)
    port_id = get_portfolio_id(prod_id)
    associate_principal_portfolio(PRINCIPAL_ARN, port_id)

    if len(valid_items) > 0:
        item = valid_items[0]
        input_params = generate_input_params(item)
        prov_prod_name = generate_provisioned_product_name(input_params)
        try:
            output = SC.provision_product(
                ProductId=prod_id, ProvisioningArtifactId=pa_id,
                ProvisionedProductName=prov_prod_name,
                ProvisioningParameters=input_params,
                ProvisionToken=str(randint(1000000000000, 9999999999999)))
            result = output['RecordDetail']['ProvisionedProductId']
        except Exception as exe:
            LOGGER.error('SC product provisioning failed: %s', str(exe))
            sleep(60)
            result = str(exe)
    else:
        LOGGER.info('No more Account found to provision')

    return(result, input_params)


def get_item_from_table(account_name):
    '''Return true if Value exists'''

    result = None

    try:
        result = DYNO.get_item(TableName=TABLE_NAME,
                               Key={'AccountName': {'S': account_name}})
    except Exception as exe:
        LOGGER.error('Item not exist %s', str(exe))

    return result


def sc_initial_failure(input_params, message):
    '''Update DynamoDB Table with SC Failure'''

    result = None
    account_name = generate_account_name(input_params)
    account_id = 'NOT_APPLICABLE'
    cmd_status = 'NOT_PROVISIONED'
    try:
        result = update_account_status(account_name, account_id,
                                       cmd_status, message)
        LOGGER.info('Update record %s, %s, %s',
                    account_name, account_id, cmd_status)
    except Exception as exe:
        LOGGER.error('Unable to update record for: %s,%s',
                     account_name, str(exe))

    return result


def update_account_status(account_name, account_id, cmd_status, message):
    '''Update DynamoDB Table with account status'''
    result = None

    key = {
        "AccountName": {"S": account_name}
        }
    updates = {
        "Status": {"Value": {"S": cmd_status}},
        "Message": {"Value": {"S": message}},
        "AccountId": {"Value": {"S": account_id}}
        }
    get_item = get_item_from_table(account_name)

    if get_item:
        try:
            result = DYNO.update_item(TableName=TABLE_NAME,
                                      Key=key, AttributeUpdates=updates,
                                      ReturnValues="UPDATED_NEW")
        except Exception as exe:
            LOGGER.error('Unable to update the item: %s', str(exe))

    return result


def get_pp_status(pp_id):
    '''Return the provisioned product state and error message (if any)'''

    status = None
    message = None

    try:
        result = SC.describe_provisioned_product(
            Id=pp_id)['ProvisionedProductDetail']
        status = result['Status']
        if 'StatusMessage' in result:
            message = result['StatusMessage']
    except Exception as exe:
        LOGGER.error("Unable to get provisioned product status: %s", str(exe))

    return(status, message)


def process_cft_event(event):
    '''Handle the initial trigger from Cloudformation'''

    create_new_account = False
    LOGGER.info('Lambda Event: %s', event)
    request_type = event['RequestType']
    if request_type == 'Create':
        create_new_account = True
    elif request_type == 'Delete':
        prod_id = get_product_id()
        port_id = get_portfolio_id(prod_id)
        disassociate_principal_portfolio(PRINCIPAL_ARN, port_id)
    else:
        LOGGER.info('%s request received. No action taken', request_type)

    return create_new_account


def process_dynamodb_event(event):
    '''Skip INSERT operation to avoid race condition with Lambda trigger'''

    result = False
    event_name = event['Records'][0]['eventName']

    if event_name != 'INSERT':
        LOGGER.info('DynamoDB Event Recieved: %s', event)
        result = True
    else:
        LOGGER.info('DynamoDB %s received. No action taken', event_name)
        result = False

    return result


def process_lifecycle_event(event):
    '''Handle Control Tower Life Cycle Event'''

    update_result = None

    LOGGER.info('LC Event: %s', event)
    service_event = event['detail']['serviceEventDetails']
    new_account = service_event['createManagedAccountStatus']
    cmd_status = new_account['state']
    account_id = new_account['account']['accountId']
    account_name = new_account['account']['accountName']
    message = new_account['message']

    try:
        update_result = update_account_status(account_name, account_id,
                                              cmd_status, message)
    except Exception as exe:
        LOGGER.error('Unable to update the record %s: %s',
                     account_name, str(exe))

    LOGGER.info('Update Status for %s : %s', account_name, update_result)


def lambda_handler(event, context):
    '''Parse the previous event and trigger next account creation'''
    pp_id = None
    create_new_account = False

    if 'RequestType' in event:
        event_source = 'cloudformation'
        create_new_account = process_cft_event(event)
    elif 'Records' in event:
        event_source = 'dynamodb'
        create_new_account = process_dynamodb_event(event)
    elif event['source'] == 'aws.controltower':
        event_source = 'controltower'
        process_lifecycle_event(event)
    else:
        LOGGER.warning('Unknown Event recieved: %s', event)

    if create_new_account:
        (pp_id, input_params) = provision_new_account()

        if pp_id.startswith('pp-'):
            (status, message) = get_pp_status(pp_id)
            iteration = 1
            while iteration <= 3:
                if status != 'UNDER_CHANGE':
                    sc_initial_failure(input_params, message)
                    iteration = 4
                else:
                    LOGGER.info('Check-%s: %s', iteration, status)
                    sleep(30)
                    (status, message) = get_pp_status(pp_id)
                iteration += 1
        elif len(input_params) == 0:
            LOGGER.info('Provisioning the batch completed')
            pass_items = get_items('SUCCEEDED')
            fail_items = get_items('SUCCEEDED', True)
            fail_count = len(fail_items)
            invld_items = get_items('INVALID')
            LOGGER.info('SUCCESS: %s Entries, %s', len(pass_items), pass_items)
            LOGGER.info('TOTAL FAILED: %s Entries, %s', fail_count, fail_items)
            LOGGER.warning('%s of %s FAILED DUE TO INVALID Entires, %s',
                           len(invld_items), fail_count, invld_items)
        else:
            sc_initial_failure(input_params, pp_id)
            LOGGER.info('SC Product Launch Failed: %s', input_params)

    if event_source == 'cloudformation':
        response = {}
        cfnresource.send(event, context, cfnresource.SUCCESS,
                         response, "CustomResourcePhysicalID")
