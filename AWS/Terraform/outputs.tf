output "subnet_group" {
  value = "${aws_db_subnet_group.default.name}"
}

output "db_instance_id" {
  value = "${mariadb_instance.default.id}"
}

output "db_instance_address" {
  value = "${mariadb_instance.default.address}"
}
