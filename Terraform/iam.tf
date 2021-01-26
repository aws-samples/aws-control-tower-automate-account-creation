#Roles

resource "aws_iam_role" "signup_validation_role" {
  name = "${local.prefix}_signup_validation_role"
}

resource "aws_iam_role" "account_creation_role" {
  name = "${local.prefix}_account_creation_role"
}

#Custom Policies

resource "aws_iam_policy" "signup_validation_policy" {
  name = "signup_validation_role_policy"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DynamoDb",
            "Effect": "Allow",
            "Action": [
                "dynamodb:BatchGetItem",
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:UpdateItem"
            ],
            "Resource": "arn:aws:dynamodb:eu-west-2:123456789123:table/table1"
        }
    ]
}
EOF
}
  

resource "aws_iam_policy" "account_creation_policy" {
  name = "${local.prefix}_account_creation_policy"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DynamoDb",
            "Effect": "Allow",
            "Action": [
                "dynamodb:BatchGetItem",
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:UpdateItem"
            ],
            "Resource": "arn:aws:dynamodb:eu-west-2:123456789123:table/table1"
        }
    ]
}
EOF
}

#Role Policy Attachments

resource "aws_iam_role_policy_attachment" "signup_validation_role_policy_attachment_main" {
  role = aws_iam_role.signup_validation_role.name
  policy_arn = aws_iam_policy.signup_validation_role_policy.arn
}

resource "aws_iam_role_policy_attachment" "signup_validation_role_policy_attachment_AWSLambdaBasicExecutionRole" {
  role = "AWSLambdaBasicExecutionRole"
  policy_arn = data.aws_iam_policy.AWSLambdaBasicExecutionRole.arn
}

resource "aws_iam_role_policy_attachment" "account_creation_role_policy_attachment_main" {
  role = "AWSLambdaBasicExecutionRole"
  policy_arn = aws_iam_policy.signup_validation_role_policy.arn
}

resource "aws_iam_role_policy_attachment" "account_creation_role_policy_attachment_AWSLambdaBasicExecutionRole" {
  role = "AWSLambdaBasicExecutionRole"
  policy_arn = data.aws_iam_policy.AWSLambdaBasicExecutionRole.arn
}
