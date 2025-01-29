provider "aws" {
  region = "us-east-1"
}

# ----------------------------------------
# Criação de Recursos
# ----------------------------------------

# Cria o bucket S3
module "s3_bucket" {
  source      = "./modules/s3"
  bucket_name = "g-calendar-arboria-tech"
}

# ----------------------------------------
# IAM Roles e Permissões
# ----------------------------------------

# Cria a role IAM para as Lambdas
resource "aws_iam_role" "lambda_role" {
  name = "lambda_calendar_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Effect = "Allow"
      Sid    = ""
    }]
  })
}

# Anexa políticas gerenciadas amplas à role
resource "aws_iam_role_policy_attachment" "lambda_full_access_s3" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
  role       = aws_iam_role.lambda_role.name

  depends_on = [aws_iam_role.lambda_role]
}

resource "aws_iam_role_policy_attachment" "lambda_full_access_dynamodb" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
  role       = aws_iam_role.lambda_role.name

  depends_on = [aws_iam_role.lambda_role]
}

resource "aws_iam_role_policy_attachment" "lambda_full_access_cognito" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonCognitoPowerUser"
  role       = aws_iam_role.lambda_role.name

  depends_on = [aws_iam_role.lambda_role]
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name

  depends_on = [aws_iam_role.lambda_role]
}

# ----------------------------------------
# Criação de Lambda Layers
# ----------------------------------------

# Cria a Lambda Layer
resource "aws_lambda_layer_version" "google_calendar_layer" {
  filename            = "./deployments/google_calendar_layer.zip"
  layer_name          = "google-calendar-layer"
  compatible_runtimes = ["python3.11"]
  source_code_hash    = filebase64sha256("./deployments/google_calendar_layer.zip")
}

# ----------------------------------------
# Criação de Lambdas
# ----------------------------------------

# Cria a Lambda de post google-calendar
module "lambda_google_calendar_credentials_callback" {
  source        = "./modules/lambda"
  function_name = "google_calendar_credentials_callback"
  role_arn      = aws_iam_role.lambda_role.arn
  zip_file      = "./deployments/google_calendar_credentials_callback.zip"
  layers = [
    aws_lambda_layer_version.google_calendar_layer.arn
  ]
  environment_variables = {
    S3_BUCKET_NAME = module.s3_bucket.bucket_name
    REDIRECT_URI   = "${aws_apigatewayv2_stage.default.invoke_url}google-calendar-credentials-callback"
  }
  api_gw_execution_arn = aws_apigatewayv2_api.http_api.execution_arn
}

# Cria a Lambda de save google-calendar
module "lambda_redirect_google_credentials" {
  source        = "./modules/lambda"
  function_name = "redirect_google_credentials"
  role_arn      = aws_iam_role.lambda_role.arn
  zip_file      = "./deployments/redirect_google_credentials.zip"
  layers = [
    aws_lambda_layer_version.google_calendar_layer.arn
  ]
  environment_variables = {
    REDIRECT_URI = "${aws_apigatewayv2_stage.default.invoke_url}google-calendar-credentials-callback"
  }
  api_gw_execution_arn = aws_apigatewayv2_api.http_api.execution_arn
}

# Lambda de get calendar events
module "lambda_get_calendar_events" {
  source        = "./modules/lambda"
  function_name = "get_calendar_events"
  role_arn      = aws_iam_role.lambda_role.arn
  zip_file      = "./deployments/get_calendar_events.zip"
  layers = [
    aws_lambda_layer_version.google_calendar_layer.arn
  ]
  environment_variables = {
    S3_BUCKET_NAME = module.s3_bucket.bucket_name
  }
  api_gw_execution_arn = aws_apigatewayv2_api.http_api.execution_arn
}

# Lambda de create calendar event
module "lambda_create_calendar_event" {
  source        = "./modules/lambda"
  function_name = "create_calendar_event"
  role_arn      = aws_iam_role.lambda_role.arn
  zip_file      = "./deployments/create_calendar_event.zip"
  layers = [
    aws_lambda_layer_version.google_calendar_layer.arn
  ]
  environment_variables = {
    S3_BUCKET_NAME = module.s3_bucket.bucket_name
  }
  api_gw_execution_arn = aws_apigatewayv2_api.http_api.execution_arn
}

# ----------------------------------------
# API Gateway
# ----------------------------------------

# Cria o API Gateway
resource "aws_apigatewayv2_api" "http_api" {
  name          = "http-api-google-calendar"
  protocol_type = "HTTP"
}

# Stage da API
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

# Configura os endpoints do API Gateway
module "api_gateway_google_calendar_credentials_callback" {
  source            = "./modules/api_gateway"
  api_id            = aws_apigatewayv2_api.http_api.id
  method            = "GET"
  path              = "/google-calendar-credentials-callback"
  lambda_invoke_arn = module.lambda_google_calendar_credentials_callback.lambda_invoke_arn
}

module "api_gateway_redirect_google_credentials" {
  source            = "./modules/api_gateway"
  api_id            = aws_apigatewayv2_api.http_api.id
  method            = "POST"
  path              = "/redirect-google-credentials"
  lambda_invoke_arn = module.lambda_redirect_google_credentials.lambda_invoke_arn
}

module "api_gateway_get_calendar_events" {
  source            = "./modules/api_gateway"
  api_id            = aws_apigatewayv2_api.http_api.id
  method            = "POST"
  path              = "/get-calendar-events"
  lambda_invoke_arn = module.lambda_get_calendar_events.lambda_invoke_arn
}

module "api_gateway_create_calendar_event" {
  source            = "./modules/api_gateway"
  api_id            = aws_apigatewayv2_api.http_api.id
  method            = "POST"
  path              = "/create-calendar-event"
  lambda_invoke_arn = module.lambda_create_calendar_event.lambda_invoke_arn
}