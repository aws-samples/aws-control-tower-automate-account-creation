locals {
  prefix = var.prefix
}

variable "prefix" {
  type = string
}

variable "dynamodb_table" {
  type = string
}