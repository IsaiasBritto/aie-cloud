# EC2 com Docker: MongoDB 7.0 + Mongo Express 1.0.2 (imagens do ECR Public).
#
# A porta 27017 fica aberta para a internet porque a Lambda roda FORA da VPC e
# sai por IPs da AWS que mudam. O banco continua protegido por senha — e o
# exercício 1.3 discute o certo em produção (Lambda na VPC + security group).

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_security_group" "mongo" {
  name        = "${local.nome}-mongo"
  description = "MongoDB (Lambda e CloudShell) e Mongo Express com senha"
  vpc_id      = data.aws_vpc.padrao.id

  ingress {
    description = "MongoDB"
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Mongo Express"
    from_port   = 8081
    to_port     = 8081
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "mongo" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = var.mongo_instance_type
  vpc_security_group_ids      = [aws_security_group.mongo.id]
  associate_public_ip_address = true

  metadata_options {
    http_tokens = "required"
  }

  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/mongo-user-data.sh.tftpl", {
    mongo_password    = local.mongo_admin_pass
    mongo_ui_password = local.mongo_express_pass
  })

  tags = {
    Name = "${local.nome}-mongo"
  }
}
