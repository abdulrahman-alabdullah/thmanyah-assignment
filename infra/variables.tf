variable "region" {
  type    = string
  default = "eu-west-1"
}
variable "admin_cidr" {
  description = "Your current public IPv4 address with /32, for bootstrap SSH and VPN only."
  type        = string
  validation {
    condition     = can(cidrhost(var.admin_cidr, 0)) && endswith(var.admin_cidr, "/32")
    error_message = "Supply one IPv4 /32 address."
  }
}
variable "ssh_public_key" {
  description = "Public SSH key only. Keep the private key outside this repository."
  type        = string
}
variable "instance_type" {
  type    = string
  default = "t4g.small"
}
