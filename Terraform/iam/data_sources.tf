data "aws_iam_policy" "AWSLambdaBasicExecutionRole" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy" "AmazonDynamoDBFullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

data "aws_iam_policy" "CloudWatchLogsFullAccess" {
  arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

data "aws_iam_policy" "AWSOrganizationsReadOnlyAccess" {
  arn = "arn:aws:iam::aws:policy/AWSOrganizationsReadOnlyAccess"
}

data "aws_iam_policy" "CloudWatchEventsFullAccess" {
  arn = "arn:aws:iam::aws:policy/CloudWatchEventsFullAccess"
}

data "aws_iam_policy" "AWSServiceCatalogAdminReadOnlyAccess" {
  arn = "arn:aws:iam::aws:policy/AWSServiceCatalogAdminReadOnlyAccess"
}

data "aws_iam_policy" "AWSServiceCatalogEndUserFullAccess" {
  arn = "arn:aws:iam::aws:policy/AWSServiceCatalogEndUserFullAccess"
}

data "aws_iam_policy_document" "lambda_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "signup_validation_role_policy_doc" {
  statement {
    sid = "DynamoDb"
    actions = [
      "dynamodb:BatchGetItem",
      "dynamodb:PutItem",
      "dynamodb:GetItem",
      "dynamodb:UpdateItem"
    ]

    resources = [
      var.dynamodb_table
    ]
  }
}

data "aws_iam_policy_document" "account_creation_role_policy_doc" {
  statement {
    sid = "SSO_SSO-Directory_servicecatalog_controltower_s3_organizations"
    actions = [
      "sso:CreateApplicationInstance",
      "sso:ProvisionApplicationInstanceForAWSAccount",
      "sso:ProvisionApplicationProfileForAWSAccountInstance",
      "sso:ProvisionSAMLProvider",
      "sso:ListPermissionSets",
      "sso:ListDirectoryAssociations",
      "sso:DescribeRegisteredRegions",
      "sso:AssociateProfile",
      "sso-directory:CreateUser",
      "sso:GetApplicationInstance",
      "sso:UpdateProfile",
      "sso:GetPermissionSet",
      "sso:CreateProfile",
      "sso:CreateTrust",
      "sso-directory:DescribeDirectory",
      "sso:GetProfile",
      "sso:ListProfileAssociations",
      "sso:GetTrust",
      "sso:GetSSOStatus",
      "sso-directory:ListMembersInGroup",
      "sso-directory:DescribeGroups",
      "sso-directory:SearchGroups",
      "sso-directory:SearchUsers",
      "sso-directory:GetUserPoolInfo",
      "servicecatalog:DisassociatePrincipalFromPortfolio",
      "servicecatalog:AssociatePrincipalWithPortfolio",
      "s3:GetObject",
      "organizations:DescribeOrganization",
      "controltower:CreateManagedAccount",
      "controltower:DescribeManagedAccount",
      "controltower:DeregisterManagedAccount"
    ]
    resources = ["*"]
  }
}