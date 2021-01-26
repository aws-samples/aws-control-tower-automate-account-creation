terraform {
  backend s3 {
    bucket = "aws-cis-pe-accounts-terraform-state"
    key = "aws_cis_pe_training_accounts.tfstate"
    region = "eu-west-2"
  }
}

#Project Maykr

provider "aws" {
}