output "alb_dns_name" {
  value = aws_lb.this.dns_name
}

output "cluster_arn" {
  value = aws_ecs_cluster.this.arn
}

output "cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "service_name" {
  value = aws_ecs_service.this.name
}

output "codedeploy_app_name" {
  value = aws_codedeploy_app.this.name
}

output "codedeploy_deployment_group_name" {
  value = aws_codedeploy_deployment_group.this.deployment_group_name
}

output "service_security_group_id" {
  value = aws_security_group.service.id
}

output "execution_role_arn" {
  value = aws_iam_role.ecs_execution.arn
}

output "task_role_arn" {
  value = aws_iam_role.task.arn
}

output "task_definition_family" {
  value = aws_ecs_task_definition.this.family
}

output "passrole_arns" {
  value = [aws_iam_role.ecs_execution.arn, aws_iam_role.task.arn]
}
