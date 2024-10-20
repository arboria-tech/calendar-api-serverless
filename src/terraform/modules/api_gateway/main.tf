resource "aws_apigatewayv2_integration" "this" {
  api_id             = var.api_id
  integration_type   = "AWS_PROXY"
  integration_method = "POST" # Precisa ser post pois é um post para o lambda, sempre.
  integration_uri    = var.lambda_invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "this" {
  api_id    = var.api_id
  route_key = "${var.method} ${var.path}"
  target    = "integrations/${aws_apigatewayv2_integration.this.id}"
}
