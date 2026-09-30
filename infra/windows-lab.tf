# Optional short-lived Windows host for cross-platform SMB acceptance tests.
variable "enable_windows_lab" {
  type    = bool
  default = false
}
data "aws_ami" "windows_lab" {
  count       = var.enable_windows_lab ? 1 : 0
  most_recent = true
  owners      = ["801119661308"]
  filter {
    name   = "name"
    values = ["Windows_Server-2022-English-Core-Base-*"]
  }
}
resource "aws_iam_role" "windows_lab" {
  count       = var.enable_windows_lab ? 1 : 0
  name_prefix = "thmanyah-assessment-windows-"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole"
  }] })
}
resource "aws_iam_role_policy_attachment" "windows_ssm" {
  count      = var.enable_windows_lab ? 1 : 0
  role       = aws_iam_role.windows_lab[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
resource "aws_iam_instance_profile" "windows_lab" {
  count       = var.enable_windows_lab ? 1 : 0
  name_prefix = "thmanyah-assessment-windows-"
  role        = aws_iam_role.windows_lab[0].name
}
resource "aws_security_group" "windows_lab" {
  count       = var.enable_windows_lab ? 1 : 0
  name_prefix = "thmanyah-assessment-windows-"
  vpc_id      = aws_vpc.tier["public"].id
  ingress {
    from_port   = 445
    to_port     = 445
    protocol    = "tcp"
    cidr_blocks = ["${local.tiers.apps.host}/32"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_vpc_security_group_ingress_rule" "linux_smb_lab" {
  count             = var.enable_windows_lab ? 1 : 0
  security_group_id = aws_security_group.tier["apps"].id
  cidr_ipv4         = "10.10.10.20/32"
  from_port         = 445
  to_port           = 445
  ip_protocol       = "tcp"
}
resource "aws_instance" "windows_lab" {
  count                       = var.enable_windows_lab ? 1 : 0
  ami                         = data.aws_ami.windows_lab[0].id
  instance_type               = "t3.medium"
  subnet_id                   = aws_subnet.tier["public"].id
  private_ip                  = "10.10.10.20"
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.windows_lab[0].id]
  iam_instance_profile        = aws_iam_instance_profile.windows_lab[0].name
  metadata_options {
    http_tokens = "required"
  }
  root_block_device {
    encrypted             = true
    volume_type           = "gp3"
    volume_size           = 30
    delete_on_termination = true
  }
  credit_specification {
    cpu_credits = "standard"
  }
  tags       = { Name = "assessment-windows-smb" }
  depends_on = [aws_iam_role_policy_attachment.windows_ssm, aws_route.peer]
}
output "windows_lab_instance_id" {
  value = var.enable_windows_lab ? aws_instance.windows_lab[0].id : null
}
