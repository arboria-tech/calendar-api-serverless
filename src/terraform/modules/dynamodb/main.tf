resource "aws_dynamodb_table" "this" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = var.hash_key_name

  # Adiciona a chave de ordenação se ela for fornecida
  range_key = var.range_key_name != "" ? var.range_key_name : null

  attribute {
    name = var.hash_key_name
    type = var.hash_key_type
  }

  # Adiciona a chave de ordenação se ela for fornecida
  dynamic "attribute" {
    for_each = var.range_key_name != "" ? [1] : []
    content {
      name = var.range_key_name
      type = var.range_key_type
    }
  }
}
