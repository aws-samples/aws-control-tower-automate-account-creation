resource "aws_lambda_function" "signup_validation" {
  function_name = "${local.prefix}_signup"
  description = "The lambda function which will validate all entries of the signup form and insert them into the DyanmoDb table."
  s3_bucket = aws_s3_bucket.deployment_bucket.bucket
  role = aws_iam_role.signup_validation_role.arn
  handler = "signup_validation.lambda_handler"
  runtime = "python3.8"
}

resource "aws_lambda_function" "account_creation" {
  function_name = "${local.prefix}_account_creation"
  description = "The lambda function which will create accounts from details in a DynamoDb table."
  s3_bucket = aws_s3_bucket.deployment_bucket.bucket
  role = aws_iam_role.account_creation_role.arn
  handler = "account_creation.lambda_handler"
  runtime = "python3.8"
}