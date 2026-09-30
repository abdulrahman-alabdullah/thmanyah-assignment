locals {
  tiers = {
    public = { cidr = "10.10.0.0/16", subnet = "10.10.10.0/24", host = "10.10.10.10" }
    apps   = { cidr = "10.20.0.0/16", subnet = "10.20.10.0/24", host = "10.20.10.10" }
    dbs    = { cidr = "10.30.0.0/16", subnet = "10.30.10.0/24", host = "10.30.10.10" }
  }
  private = { for k, v in local.tiers : k => v if k != "public" }
  peerings = {
    public_apps = { left = "public", right = "apps" }
    public_dbs  = { left = "public", right = "dbs" }
    apps_dbs    = { left = "apps", right = "dbs" }
  }
  peer_routes = merge(
    { for k, v in local.peerings : "${k}_left" => { peer = k, source = v.left, destination = v.right } },
    { for k, v in local.peerings : "${k}_right" => { peer = k, source = v.right, destination = v.left } }
  )
}
data "aws_availability_zones" "available" {
  state = "available"
}
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-arm64-server-*"]
  }
  filter {
    name   = "architecture"
    values = ["arm64"]
  }
}
resource "aws_vpc" "tier" {
  for_each             = local.tiers
  cidr_block           = each.value.cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "assessment-${each.key}" }
}
resource "aws_subnet" "tier" {
  for_each                = local.tiers
  vpc_id                  = aws_vpc.tier[each.key].id
  cidr_block              = each.value.subnet
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = each.key == "public"
  tags                    = { Name = "assessment-${each.key}-workload" }
}
resource "aws_internet_gateway" "tier" {
  for_each = local.tiers
  vpc_id   = aws_vpc.tier[each.key].id
}
resource "aws_route_table" "tier" {
  for_each = local.tiers
  vpc_id   = aws_vpc.tier[each.key].id
}
resource "aws_route_table_association" "tier" {
  for_each       = local.tiers
  subnet_id      = aws_subnet.tier[each.key].id
  route_table_id = aws_route_table.tier[each.key].id
}
resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.tier["public"].id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.tier["public"].id
}
# VPC peering cannot transit an internet/NAT gateway in another VPC.
# Each private VPC therefore has its own public egress subnet and NAT gateway.
resource "aws_subnet" "egress" {
  for_each          = local.private
  vpc_id            = aws_vpc.tier[each.key].id
  cidr_block        = cidrsubnet(each.value.cidr, 8, 20)
  availability_zone = data.aws_availability_zones.available.names[0]
  tags              = { Name = "assessment-${each.key}-egress" }
}
resource "aws_route_table" "egress" {
  for_each = local.private
  vpc_id   = aws_vpc.tier[each.key].id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.tier[each.key].id
  }
}
resource "aws_route_table_association" "egress" {
  for_each       = local.private
  subnet_id      = aws_subnet.egress[each.key].id
  route_table_id = aws_route_table.egress[each.key].id
}
resource "aws_eip" "nat" {
  for_each = local.private
  domain   = "vpc"
}
resource "aws_nat_gateway" "tier" {
  for_each      = local.private
  allocation_id = aws_eip.nat[each.key].id
  subnet_id     = aws_subnet.egress[each.key].id
  depends_on    = [aws_internet_gateway.tier]
}
resource "aws_route" "private_internet" {
  for_each               = local.private
  route_table_id         = aws_route_table.tier[each.key].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.tier[each.key].id
}
resource "aws_vpc_peering_connection" "tier" {
  for_each    = local.peerings
  vpc_id      = aws_vpc.tier[each.value.left].id
  peer_vpc_id = aws_vpc.tier[each.value.right].id
  auto_accept = true
  tags        = { Name = "assessment-${each.key}" }
}
resource "aws_route" "peer" {
  for_each                  = local.peer_routes
  route_table_id            = aws_route_table.tier[each.value.source].id
  destination_cidr_block    = local.tiers[each.value.destination].cidr
  vpc_peering_connection_id = aws_vpc_peering_connection.tier[each.value.peer].id
}
resource "aws_security_group" "tier" {
  for_each = local.tiers
  name     = "assessment-${each.key}"
  vpc_id   = aws_vpc.tier[each.key].id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.tier["public"].id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}
resource "aws_vpc_security_group_ingress_rule" "bootstrap_ssh" {
  security_group_id = aws_security_group.tier["public"].id
  cidr_ipv4         = var.admin_cidr
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}
resource "aws_vpc_security_group_ingress_rule" "vpn" {
  security_group_id = aws_security_group.tier["public"].id
  cidr_ipv4         = var.admin_cidr
  from_port         = 51820
  to_port           = 51820
  ip_protocol       = "udp"
}
resource "aws_vpc_security_group_ingress_rule" "private_ssh" {
  for_each          = local.private
  security_group_id = aws_security_group.tier[each.key].id
  cidr_ipv4         = "${local.tiers.public.host}/32"
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}
resource "aws_vpc_security_group_ingress_rule" "app" {
  security_group_id = aws_security_group.tier["apps"].id
  cidr_ipv4         = "${local.tiers.public.host}/32"
  from_port         = 8000
  to_port           = 8000
  ip_protocol       = "tcp"
}
resource "aws_vpc_security_group_ingress_rule" "database" {
  security_group_id = aws_security_group.tier["dbs"].id
  cidr_ipv4         = "${local.tiers.apps.host}/32"
  from_port         = 5432
  to_port           = 5432
  ip_protocol       = "tcp"
}
resource "aws_key_pair" "assessment" {
  key_name   = "thmanyah-assessment"
  public_key = var.ssh_public_key
}
resource "aws_instance" "tier" {
  for_each                    = local.tiers
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.tier[each.key].id
  private_ip                  = each.value.host
  associate_public_ip_address = each.key == "public"
  vpc_security_group_ids      = [aws_security_group.tier[each.key].id]
  key_name                    = aws_key_pair.assessment.key_name
  source_dest_check           = each.key != "public"
  metadata_options {
    http_tokens = "required"
  }
  root_block_device {
    encrypted   = true
    volume_type = "gp3"
    volume_size = each.key == "dbs" ? 30 : 12
  }
  tags       = { Name = "assessment-${each.key}" }
  depends_on = [aws_route.private_internet, aws_route.peer]
}
