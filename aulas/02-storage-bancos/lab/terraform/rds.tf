# RDS PostgreSQL — o banco relacional da QC (e, com pgvector, o Vector DB do Lab 3B)

resource "aws_security_group" "rds" {
  name        = "${local.nome}-rds"
  description = "PostgreSQL liberado apenas para o IP do CloudShell"
  vpc_id      = data.aws_vpc.padrao.id

  ingress {
    description = "PostgreSQL a partir do CloudShell"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [local.meu_ip_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "qc" {
  identifier     = local.nome
  engine         = "postgres"
  engine_version = "16" # versão principal; a AWS escolhe a menor versão padrão (com pgvector)
  instance_class = "db.t3.micro"

  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = "qcdb"
  username = "qcadmin"
  password = var.db_password

  publicly_accessible    = true # só para o lab: o security group restringe ao seu IP
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 0    # sem backup automático no lab (custo)
  skip_final_snapshot     = true # destroy sem snapshot final
  deletion_protection     = false
  apply_immediately       = true
}
