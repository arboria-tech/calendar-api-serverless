variable "table_name" {
  type = string
}

variable "hash_key_name" {
  type = string
}

variable "hash_key_type" {
  type = string
  default = "S"
}

variable "range_key_name" {
  type    = string
  default = ""
}

variable "range_key_type" {
  type    = string
  default = ""  # Define um valor padrão vazio para o tipo da chave de ordenação
}
