# AWS Lambda (Python 3.12) + Function URL, com a LabRole como execution role.
# O Terraform publica a v1-mock; nos labs você troca o código com
# "aws lambda update-function-code" (v1-mock → v2-s3).

data "archive_file" "v1_mock" {
  type        = "zip"
  source_dir  = "${path.module}/../function/v1-mock"
  output_path = "${path.module}/.build/v1-mock.zip"
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.nome}-catalogo"
  retention_in_days = 7 # FinOps: log sem retenção é custo para sempre
}

resource "aws_lambda_function" "catalogo" {
  function_name = "${local.nome}-catalogo"
  role          = data.aws_iam_role.lab.arn
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  filename      = data.archive_file.v1_mock.output_path
  timeout       = 15
  memory_size   = 256

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.catalogo.bucket
      CSV_KEY     = aws_s3_object.produtos.key
    }
  }

  # O código muda pelo CLI durante a aula: o Terraform não deve desfazer o deploy
  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

# URL HTTPS pública da função (sem API Gateway)
resource "aws_lambda_function_url" "catalogo" {
  function_name      = aws_lambda_function.catalogo.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["GET"]
  }
}

# Desde out/2025, uma Function URL pública precisa de DUAS permissões na
# política da função: InvokeFunctionUrl e InvokeFunction (esta só via URL).
resource "aws_lambda_permission" "url_publica" {
  statement_id           = "FunctionUrlPublica"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.catalogo.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

# A segunda permissão usa o CLI porque a condição InvokedViaFunctionUrl é
# recente e nem toda versão do provider aws a expõe.
resource "terraform_data" "url_invoke" {
  triggers_replace = [aws_lambda_function.catalogo.arn]

  provisioner "local-exec" {
    command = <<-EOT
      aws lambda add-permission --region ${var.region} \
        --function-name ${aws_lambda_function.catalogo.function_name} \
        --statement-id FunctionUrlInvoke \
        --action lambda:InvokeFunction --principal '*' \
        --invoked-via-function-url >/dev/null 2>&1 \
      || echo "Permissão FunctionUrlInvoke já existe (ou CLI antigo) — seguindo."
    EOT
  }
}
