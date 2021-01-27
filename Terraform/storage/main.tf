resource "aws_dynamodb_table" "users" {
    name = "${var.prefix}_users"
    billing_mode = var.billing_mode
    hash_key = "AccountName"
    stream_enabled = true
    stream_view_type = "NEW_AND_OLD_IMAGES"
    attribute {
      name = "${var.prefix}_AccountName"
      type = "S"
    }
}
resource "aws_s3_bucket" "deployment_bucket" {
    bucket = "${var.prefix}_deployment_artifacts"
}

resource "aws_s3_bucket_object" "signup_validation_s3_object" {
  bucket = aws_s3_bucket.deployment_bucket.bucket
  key = "signup_validation.zip"
  source = "./lambda_code/signup_validation.zip"
}

resource "aws_s3_bucket_object" "account_creation_s3_object" {
  bucket = aws_s3_bucket.deployment_bucket.bucket
  key = "account_creation.zip"
  source = "./lambda_code/account_creation.zip"
}