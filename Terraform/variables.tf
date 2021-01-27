locals {

  prefix = "${var.env}_makyr"
  tags = var.tags

}
variable "env" {
  type = string
  default = "dev"
}

variable "bucket_name" {
  type = string
  default = "makyr_deployement"
}

variable "region" {
  type = string
  default = "eu-west-2"
}

variable "billing_mode" {
  type = string
  description = "Billing mode for the dynamodb table - valid values are 'PROVISIONED' and 'PAY_PER_REQUEST'."
}

variable "tags" {
  default = {
    Managed_by:"terraform"
  }
}