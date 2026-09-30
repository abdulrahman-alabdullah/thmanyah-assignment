# AWS deployment procedure

Assessment acceptance status (30 September 2026): a reviewed Terraform deployment created the three VPCs and temporary test hosts in `eu-west-1`. VPN/private reachability, public application read/write, PostgreSQL restore, and a second Ansible run with zero changes passed. The test stack and its S3 buckets were then destroyed; no assessment VPCs, running instances, or NAT gateways remain. Evidence is indexed in `docs/TRACEABILITY.md`. The steps below explain how to reproduce a future deployment; they create billable resources and require a fresh cost review and cleanup.

## Prepare credentials and configuration

1. Use an IAM identity with the required EC2, VPC and S3 permissions. Configure AWS CLI through SSO or another temporary credential method. Do not store access keys in Terraform files. Select `eu-west-1`, or another region after checking feature availability.
2. Create a separate SSH key (`ssh-keygen -t ed25519 -f ~/.ssh/thmanyah-assessment`). Keep its private half outside the repository. Copy `terraform.tfvars.example` to `terraform.tfvars`; enter the public key and your current public IPv4 `/32` for `admin_cidr`.
3. Run `terraform init`, `terraform fmt -check`, `terraform validate`, and `terraform plan -out=assessment.tfplan` from `infra/`. Review the three VPCs, five subnets, three peers, three instances, two NAT gateways, addresses and two S3 buckets. Run `terraform apply assessment.tfplan` only when prepared to incur the charges. Terraform state and plan files may contain sensitive infrastructure information; do not publish them.
4. Export inventory: `terraform output -json ansible_inventory > ansible/inventory.yml`. JSON is valid Ansible YAML inventory.

## Bootstrap the VPN before configuring private hosts

5. Install the WireGuard app on macOS and add an empty tunnel. It generates a client private/public key pair. Keep the private key in WireGuard and copy only the public key into the Ansible vault configuration.
6. Copy `ansible/vault.yml.example` to `ansible/vault.yml`, enter a random database password and the WireGuard client public key, and run `ansible-vault encrypt ansible/vault.yml`. Install collections with `ansible-galaxy collection install -r ansible/requirements.yml`.
7. From `infra/ansible/`, configure the reachable gateway first:

```sh
ansible-playbook -i inventory.yml site.yml --limit gateway \
  --private-key ~/.ssh/thmanyah-assessment --ask-vault-pass
```

8. Obtain the gateway public IP from Terraform and its WireGuard public key with `ssh -i ~/.ssh/thmanyah-assessment ubuntu@PUBLIC_IP 'sudo wg show wg0 public-key'`. This prints a public key, not the server private key.
9. Complete the macOS tunnel:

```ini
[Interface]
PrivateKey = CLIENT_PRIVATE_KEY_ALREADY_IN_WIREGUARD
Address = 10.99.0.2/32
[Peer]
PublicKey = SERVER_PUBLIC_KEY
Endpoint = PUBLIC_IP:51820
AllowedIPs = 10.10.0.0/16, 10.20.0.0/16, 10.30.0.0/16
PersistentKeepalive = 25
```

10. Activate the tunnel, confirm a recent handshake, and test SSH to `10.20.10.10` and `10.30.10.10`. Run the full playbook with the same key and vault password. Run it a second time and inspect the recap for unexpected changes. The assessment deployment's second run reported zero changes on all three Linux hosts; a new deployment should repeat this check.

## Verify isolation and application behavior

11. From the public Nginx address, GET `/health/ready`, POST a JSON `message` to `/api/notes`, then GET the list and verify the same record. Private application and database EC2 instances must have no public IP addresses.
12. Disconnect the VPN and verify that private SSH access fails; reconnect and verify it succeeds. PostgreSQL port 5432 accepts the application host only. VPN administrators inspect PostgreSQL through SSH and a local `psql` session over its Unix socket, rather than opening database ingress to everyone on the VPN.
13. Restart the application service and database instance and confirm recovery. Test backup restoration. Inspect security groups, subnet route tables and `sudo wg show`; save redacted evidence.
14. HTTP is used for this assessment demonstration. For production, put TLS on Nginx with a real hostname/certificate, use database TLS, remove public bootstrap SSH after the VPN is established, add centralized logging and multi-AZ recovery. The current design deliberately runs one instance per tier in one availability zone and provides no HA guarantee.

## Routing rationale and cleanup

The three peers are direct: public↔apps, public↔dbs, apps↔dbs. VPC peering is non-transitive. The direct public↔dbs route lets the gateway reach the DB for VPN administration; the direct apps↔dbs route carries application queries. WireGuard masquerades VPN client traffic to the gateway's private address, so private SSH security-group rules allow that single address. Source/destination checking is disabled on the forwarding gateway.

Private instances fetch updates through a NAT gateway in their own VPC. A peered VPC cannot borrow the public VPC's internet or NAT gateway. Both NAT gateways, their public addresses, EC2 instances, EBS storage and data transfer can incur charges even while the application is idle. Confirm current regional prices before deployment. Destroy the test infrastructure after evidence is saved and the review access requirement is satisfied. Versioned, non-empty S3 buckets are protected from automatic destruction and require a deliberate retention/cleanup decision.

Sources: [VPC peering restrictions](https://docs.aws.amazon.com/vpc/latest/peering/invalid-peering-configurations.html), [Terraform AWS provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs), [WireGuard quick start](https://www.wireguard.com/quickstart/).
