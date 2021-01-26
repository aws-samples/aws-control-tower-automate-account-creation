resource "aws_api_gateway_rest_api" "signup_form_api" {
  name        = "${local.prefix}_signup_api"
  description = "The Signup API form"
}