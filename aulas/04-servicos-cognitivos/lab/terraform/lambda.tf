# Lambda Python 3.12 + Function URL + LabRole (timeout 60 s: a transcrição é assíncrona).
# O Terraform publica um "placeholder"; o código real (com dependências) é
# publicado no lab com pip install -t . + aws lambda update-function-code.

data "archive_file" "placeholder" {
  type        = "zip"
  output_path = "${path.module}/.build/placeholder.zip"

  source {
    filename = "function_app.py"
    content  = <<-PY
      import json
      def lambda_handler(event, context):
          return {"statusCode": 200, "headers": {"Content-Type": "application/json"},
                  "body": json.dumps({"status": "placeholder",
                                      "msg": "Publique o código real: veja o Lab 2 do guia"})}
    PY
  }
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.nome}-cognitivo"
  retention_in_days = 7
}

resource "aws_lambda_function" "cognitivo" {
  function_name = "${local.nome}-cognitivo"
  role          = data.aws_iam_role.lab.arn
  runtime       = "python3.12"
  handler       = "function_app.lambda_handler"
  filename      = data.archive_file.placeholder.output_path
  timeout       = 60
  memory_size   = 512

  environment {
    variables = {
      DATA_BUCKET             = aws_s3_bucket.data.bucket
      MONGO_SECRET_ID         = aws_secretsmanager_secret.mongo.name
      POWERTOOLS_SERVICE_NAME = "qc-cognitivo"
    }
  }

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

resource "aws_lambda_function_url" "cognitivo" {
  function_name      = aws_lambda_function.cognitivo.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST"]
    allow_headers = ["content-type"]
  }
}

# Desde out/2025, uma Function URL pública precisa de InvokeFunctionUrl E InvokeFunction
resource "aws_lambda_permission" "url_publica" {
  statement_id           = "FunctionUrlPublica"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.cognitivo.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "terraform_data" "url_invoke" {
  triggers_replace = [aws_lambda_function.cognitivo.arn]

  provisioner "local-exec" {
    command = <<-EOT
      aws lambda add-permission --region ${var.region} \
        --function-name ${aws_lambda_function.cognitivo.function_name} \
        --statement-id FunctionUrlInvoke \
        --action lambda:InvokeFunction --principal '*' \
        --invoked-via-function-url >/dev/null 2>&1 \
      || echo "Permissão FunctionUrlInvoke já existe (ou CLI antigo) — seguindo."
    EOT
  }
}
