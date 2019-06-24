resource "simple_security_group" "default" {
  name        = "simple_security_group"
  description = "Some Simple Security Group Description"
  vpc_id      = "vpc-2986bd4f"

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "TCP"
    cidr_blocks = ["${var.home_office}"]
  }

  tags = {
    Name = "Some Simple Security Group Tag"
  }
}

