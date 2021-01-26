resource "aws_s3_bucket" "deployment_bucket" {
    bucket = "${var.prefix}_deployment_artifacts"
}

resource "aws_dynamodb_table" "users" {
    
}