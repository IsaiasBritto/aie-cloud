# DynamoDB — o NoSQL da QC. On-demand: paga por requisição, sem capacidade parada.
# Chave de partição produto_id: todas as reviews de um produto ficam na mesma "gaveta".
resource "aws_dynamodb_table" "reviews" {
  name         = "${local.nome}-reviews"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "produto_id"
  range_key    = "review_id"

  attribute {
    name = "produto_id"
    type = "N"
  }

  attribute {
    name = "review_id"
    type = "S"
  }
}
