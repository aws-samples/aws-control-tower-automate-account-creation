resource "aws_s3_bucket" "deployment_bucket" {
    bucket = "${local.prefix}_deployment_artifacts"
}

resource "aws_dynamodb_table" "users" {
    
}