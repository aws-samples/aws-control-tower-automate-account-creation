locals {
  prefix = var.prefix
}

variable "prefix" {
  type = string
}

variable "billing_mode" {
  type = string
  description = "Billing mode for the dynamodb table - valid values are 'PROVISIONED' and 'PAY_PER_REQUEST'."
  default = "PAY_PER_REQUEST"
}