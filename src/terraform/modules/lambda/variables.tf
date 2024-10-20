variable "function_name" {
  type = string
}

variable "role_arn" {
  type = string
}

variable "handler" {
  type = string
  default = "lambda_function.lambda_handler"
}

variable "timeout" {
  type = number
  default = 15
}

variable "zip_file" {
  type = string
}

variable "layers" {
  type = list(string)
}

variable "environment_variables" {
  type = map(string)
}

variable "api_gw_execution_arn" {
  type = string
}
