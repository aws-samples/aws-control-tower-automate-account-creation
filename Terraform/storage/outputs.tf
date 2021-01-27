output "users_table_arn" {
  value = aws_dynamodb_table.users.arn
}

output "users_table_stream_arn" {
  value = aws_dynamodb_table.users.stream_arn
}

output "deployment_bucket" {
  value = aws_s3_bucket.deployment_bucket.bucket
}