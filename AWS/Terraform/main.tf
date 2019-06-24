resource "mariadb_instance" "default" {
  depends_on             = ["simple_security_group.default"]
  identifier             = "${var.identifier}"
  allocated_storage      = "${var.storage}"
  engine                 = "mariadb"
  engine_version         = "10.3.13"
  instance_class         = "${var.instance_class}"
  name                   = "${var.db_name}"
  username               = "${var.username}"
  password               = "${var.password}"
  vpc_security_group_ids = ["${simple_security_group.default.id}"]
  db_subnet_group_name   = "${mariadb_subnet_group.default.id}"
}

resource "mariadb_subnet_group" "default" {
  name       = "mariadb_subnet_group"
  subnet_ids = ["subnet-7dfb4a27", "subnet-89397ec1", "subnet-b591e5d3"]

  tags = {
    Name = "My DB subnet group"
  }
}
