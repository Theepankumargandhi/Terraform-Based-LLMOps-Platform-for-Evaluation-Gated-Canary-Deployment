resource "random_password" "master_password" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name_prefix = "${var.name_prefix}-db-"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db-secret"
  })
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.master_password.result
    dbname   = var.db_name
  })
}

resource "aws_security_group" "db" {
  name_prefix = "${var.name_prefix}-db-"
  description = "Database security group"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db-sg"
  })
}

resource "aws_vpc_security_group_ingress_rule" "db_from_vpc" {
  security_group_id = aws_security_group.db.id
  cidr_ipv4         = var.vpc_cidr
  from_port         = 5432
  to_port           = 5432
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "db_all" {
  security_group_id = aws_security_group.db.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.name_prefix}-db-subnets"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db-subnets"
  })
}

resource "aws_db_instance" "this" {
  identifier                   = "${var.name_prefix}-postgres"
  engine                       = "postgres"
  engine_version               = "16.3"
  instance_class               = var.instance_class
  allocated_storage            = var.allocated_storage
  max_allocated_storage        = var.max_allocated_storage
  db_name                      = var.db_name
  username                     = var.db_username
  password                     = random_password.master_password.result
  db_subnet_group_name         = aws_db_subnet_group.this.name
  vpc_security_group_ids       = [aws_security_group.db.id]
  backup_retention_period      = 7
  multi_az                     = false
  publicly_accessible          = false
  deletion_protection          = false
  skip_final_snapshot          = true
  auto_minor_version_upgrade   = true
  storage_encrypted            = true
  apply_immediately            = true
  performance_insights_enabled = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-postgres"
  })
}
