provider "aws" {
  region = var.aws_region
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = merge(
    {
      project     = var.project_name
      environment = var.environment
      managed_by  = "terraform"
    },
    var.tags
  )
}

module "network" {
  source               = "../../modules/network"
  name_prefix          = local.name_prefix
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  tags                 = local.common_tags
}

module "storage" {
  source      = "../../modules/storage"
  name_prefix = local.name_prefix
  tags        = local.common_tags
}

module "ecr" {
  source      = "../../modules/ecr"
  name_prefix = local.name_prefix
  tags        = local.common_tags
}

module "database" {
  source             = "../../modules/database"
  name_prefix        = local.name_prefix
  vpc_id             = module.network.vpc_id
  vpc_cidr           = var.vpc_cidr
  private_subnet_ids = module.network.private_subnet_ids
  db_name            = var.db_name
  db_username        = var.db_username
  tags               = local.common_tags
}

module "service" {
  source              = "../../modules/service"
  name_prefix         = local.name_prefix
  environment         = var.environment
  aws_region          = var.aws_region
  vpc_id              = module.network.vpc_id
  public_subnet_ids   = module.network.public_subnet_ids
  private_subnet_ids  = module.network.private_subnet_ids
  service_port        = var.service_port
  health_check_path   = var.health_check_path
  desired_count       = var.desired_count
  cpu                 = var.cpu
  memory              = var.memory
  container_image     = "${module.ecr.repository_url}:${var.image_tag}"
  candidate_weight    = var.candidate_weight
  artifact_bucket_arn = module.storage.artifact_bucket_arn
  db_endpoint         = module.database.address
  db_secret_arn       = module.database.secret_arn
  openai_secret_arn   = var.openai_secret_arn
  langsmith_secret_arn = var.langsmith_secret_arn
  tags                = local.common_tags
}

module "github_actions_role" {
  count = var.github_repository != "" && var.github_oidc_provider_arn != "" ? 1 : 0

  source                   = "../../modules/github_actions_role"
  name_prefix              = local.name_prefix
  github_repository        = var.github_repository
  github_oidc_provider_arn = var.github_oidc_provider_arn
  ecr_repository_arn       = module.ecr.repository_arn
  ecs_cluster_arn          = module.service.cluster_arn
  ecs_service_name         = module.service.service_name
  codedeploy_app_name      = module.service.codedeploy_app_name
  codedeploy_group_name    = module.service.codedeploy_deployment_group_name
  artifact_bucket_arn      = module.storage.artifact_bucket_arn
  passrole_arns            = module.service.passrole_arns
  tags                     = local.common_tags
}
