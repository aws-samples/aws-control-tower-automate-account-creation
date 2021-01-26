locals {

  prefix = "${var.env}_makyr"

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