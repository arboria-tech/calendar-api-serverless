resource "aws_lambda_function" "this" {
  function_name = var.function_name
  role          = var.role_arn
  handler       = var.handler
  runtime       = "python3.11"
  timeout       = var.timeout

  filename      = var.zip_file

  # Layer
  layers = var.layers

  environment {
    variables = var.environment_variables
  }

  source_code_hash = filebase64sha256(var.zip_file)
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowAPIGatewayInvoke-${var.function_name}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gw_execution_arn}/*/*"
}
