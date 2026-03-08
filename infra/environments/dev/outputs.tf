output "alb_dns_name" {
  value       = module.service.alb_dns_name
  description = "Public DNS name of the application load balancer."
}

output "ecr_repository_url" {
  value       = module.ecr.repository_url
  description = "ECR repository URL for container pushes."
}

output "artifact_bucket_name" {
  value       = module.storage.artifact_bucket_name
  description = "S3 bucket for evaluation reports and deployment artifacts."
}

output "database_secret_arn" {
  value       = module.database.secret_arn
  description = "Secrets Manager ARN containing database credentials."
}

output "codedeploy_app_name" {
  value       = module.service.codedeploy_app_name
  description = "CodeDeploy application name."
}

output "codedeploy_deployment_group_name" {
  value       = module.service.codedeploy_deployment_group_name
  description = "CodeDeploy deployment group name."
}

output "ecs_task_family" {
  value       = module.service.task_definition_family
  description = "ECS task definition family used by the deploy workflow."
}

output "github_actions_role_arn" {
  value       = try(module.github_actions_role[0].role_arn, null)
  description = "OIDC role ARN for GitHub Actions deployments."
}
