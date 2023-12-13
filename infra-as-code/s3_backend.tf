terraform {
  backend "s3" {
    bucket  = "dev-neurolake"
    key     = "terraform/test-lake-monitoring/terraform.tfstate"
    region  = "us-east-1"
    profile = "dlfa-dev"
  }
}