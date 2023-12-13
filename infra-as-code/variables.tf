variable "aws_region" {
  type        = string
  description = ""
  default     = "us-east-1"
}

variable "aws_profile" {
  type        = string
  description = ""
  default     = "dlfa-dev"
}

variable "environment" {
  description = "Environment to create the resources ('dev' or 'prd'). Must be written in lower case."
  type        = string
  default     = "dev"
}

variable "base_step_function_name" {
  description = "Name of the BASE StepFunction responsible for building queries and running them sequentially on Athena."
  type        = string
  default     = "governanca_dados_monitoring_lake_base"
}

variable "step_function_name" {
  description = "Name of the COMPLETE StepFunction responsible for calling the BASE StepFunction for each question."
  type        = string
  default     = "governanca_dados_monitoring_lake"
}