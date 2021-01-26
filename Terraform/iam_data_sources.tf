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