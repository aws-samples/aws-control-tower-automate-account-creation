output "dynamodb_table" {
  value = module.storage.users_table_arn
}

output "signup_validation_lambda_function_arn" {
  value = module.lambda.signup_validation_lambda_function_arn
}

output "account_creation_lambda_function_arn" {
  value = module.lambda.account_creation_lambda_function_arn
}