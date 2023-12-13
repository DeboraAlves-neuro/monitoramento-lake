provider "aws" {
  region  = "us-east-1"
  profile = "dlfa-dev"
  default_tags {
    tags = {
      Environment = "${upper(var.environment)}"
      Client      = "NEUROLAKE"
      Project     = "MONITORAMENTO_NEUROLAKE"
      Product     = "NEUROLAKE"
      Squad       = "GOVERNANCE"
      CreatedBy   = "DLFA_DEV"
    }
  }
}