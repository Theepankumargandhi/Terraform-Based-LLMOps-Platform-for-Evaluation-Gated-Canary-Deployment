variable "name_prefix" {
  type = string
}

variable "github_repository" {
  type = string
}

variable "github_oidc_provider_arn" {
  type = string
}

variable "ecr_repository_arn" {
  type = string
}

variable "ecs_cluster_arn" {
  type = string
}

variable "ecs_service_name" {
  type = string
}

variable "codedeploy_app_name" {
  type = string
}

variable "codedeploy_group_name" {
  type = string
}

variable "artifact_bucket_arn" {
  type = string
}

variable "passrole_arns" {
  type = list(string)
}

variable "tags" {
  type = map(string)
}
