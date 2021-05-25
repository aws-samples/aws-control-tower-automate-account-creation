#!/bin/bash
echo
echo "new_account_handler.py"
echo "======================"
pylint new_account_handler.py  |grep '^Your code has been rated'
echo
echo "account_create.py"
echo "================="
pylint account_create.py | grep '^Your code has been rated'
echo
echo "Packging the files"
echo "======== === ====="
zip -r ct_batchcreation_lambda.zip new_account_handler.py cfnresource.py 
zip -r ct_account_create_lambda.zip account_create.py cfnresource.py
echo
for region in $(aws ec2 describe-regions --query 'Regions[*].RegionName' --output text)
do
echo "Copying to $region"
echo "======= == ========="
aws s3 cp ct_account_create_lambda.zip s3://marketplace-sa-resources-ct-${region}/ --acl public-read --profile d_mysc
aws s3 cp ct_batchcreation_lambda.zip s3://marketplace-sa-resources-ct-${region}/ --acl public-read --profile d_mysc
echo
done
