terraform {
  backend s3 {
    bucket = "aws-cis-pe-accounts-terraform-state"
    key = "aws_cis_pe_training_accounts.tfstate"
    region = "eu-west-2"
  }
}

#Project Maykr

provider "aws" {
  region = "eu-west-2"
}

module "apigateway" {
  source = "./apigateway"
  prefix = local.prefix
}

module "cloudformation" {
  source = "./cloudformation"
  prefix = local.prefix
}

module "cloudwatch" {
  source = "./cloudwatch"
  prefix = local.prefix
}

module "iam" {
  source = "./iam"
  prefix = local.prefix
}

module "lambda" {
  source = "./lambda"
  prefix = local.prefix
}

module "storage" {
  source = "./storage"
  prefix = local.prefix
}