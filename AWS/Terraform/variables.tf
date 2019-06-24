variable "identifier" {
  default     = "hive-rds"
  description = "Identifier for your DB"
}

variable "storage" {
  default     = "10"
  description = "Storage size in GB"
}

variable "instance_class" {
  default     = "db.t2.micro"
  description = "Instance class"
}

variable "db_name" {
  default     = "hive"
  description = "db name"
}

variable "username" {
  default     = "root"
  description = "Master username"
}

variable "password" {
  default     = "rootpassword"
  description = "Master user password"
}
