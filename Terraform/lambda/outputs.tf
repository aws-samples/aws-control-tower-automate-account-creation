output "signup_validation_lambda_function_arn" {
  value = aws_lambda_function.signup_validation.arn
}

output "account_creation_lambda_function_arn" {
  value = aws_lambda_function.account_creation.arn
}