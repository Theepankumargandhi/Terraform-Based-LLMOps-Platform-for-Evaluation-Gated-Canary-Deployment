variable "name_prefix" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "service_port" {
  type = number
}

variable "health_check_path" {
  type = string
}

variable "desired_count" {
  type = number
}

variable "cpu" {
  type = number
}

variable "memory" {
  type = number
}

variable "container_image" {
  type = string
}

variable "candidate_weight" {
  type = number
}

variable "artifact_bucket_arn" {
  type = string
}

variable "db_endpoint" {
  type = string
}

variable "db_secret_arn" {
  type = string
}

variable "openai_secret_arn" {
  type    = string
  default = ""
}

variable "langsmith_secret_arn" {
  type    = string
  default = ""
}

variable "deployment_config_name" {
  type    = string
  default = "CodeDeployDefault.ECSCanary10Percent5Minutes"
}

variable "tags" {
  type = map(string)
}
