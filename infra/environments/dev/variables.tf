variable "project_name" {
  description = "Project name prefix."
  type        = string
  default     = "llmops-canary-platform"
}

variable "environment" {
  description = "Environment name."
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "Primary VPC CIDR block."
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDRs for public subnets."
  type        = list(string)
  default     = ["10.42.0.0/24", "10.42.1.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDRs for private subnets."
  type        = list(string)
  default     = ["10.42.10.0/24", "10.42.11.0/24"]
}

variable "db_name" {
  description = "RDS database name."
  type        = string
  default     = "llmops"
}

variable "db_username" {
  description = "RDS database username."
  type        = string
  default     = "llmops_admin"
}

variable "service_port" {
  description = "Container port exposed by the API."
  type        = number
  default     = 8080
}

variable "health_check_path" {
  description = "ALB health check path."
  type        = string
  default     = "/healthz"
}

variable "desired_count" {
  description = "Desired ECS task count."
  type        = number
  default     = 2
}

variable "cpu" {
  description = "Fargate CPU units."
  type        = number
  default     = 512
}

variable "memory" {
  description = "Fargate memory in MiB."
  type        = number
  default     = 1024
}

variable "image_tag" {
  description = "Container image tag pushed to ECR."
  type        = string
  default     = "bootstrap"
}

variable "candidate_weight" {
  description = "Local application-level canary routing percentage."
  type        = number
  default     = 10
}

variable "openai_secret_arn" {
  description = "Optional secret ARN containing OPENAI_API_KEY."
  type        = string
  default     = ""
}

variable "langsmith_secret_arn" {
  description = "Optional secret ARN containing LANGSMITH_API_KEY."
  type        = string
  default     = ""
}

variable "github_repository" {
  description = "GitHub owner/repository for OIDC deployments."
  type        = string
  default     = ""
}

variable "github_oidc_provider_arn" {
  description = "Existing GitHub Actions OIDC provider ARN."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags applied to resources."
  type        = map(string)
  default     = {}
}
