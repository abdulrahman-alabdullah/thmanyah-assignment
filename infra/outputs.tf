output "public_ip" {
  value = aws_instance.tier["public"].public_ip
}
output "architecture" {
  value = {
    vpcs               = { for k, v in aws_vpc.tier : k => v.cidr_block }
    private_hosts      = { for k, v in aws_instance.tier : k => v.private_ip }
    vpn_client_address = "10.99.0.2/32"
  }
}
output "ansible_inventory" {
  value = {
    all = {
      vars = { ansible_user = "ubuntu" }
      children = {
        proxy = { hosts = { gateway = { ansible_host = aws_instance.tier["public"].public_ip } } }
        apps  = { hosts = { application = { ansible_host = local.tiers.apps.host } } }
        dbs   = { hosts = { database = { ansible_host = local.tiers.dbs.host } } }
      }
    }
  }
}
