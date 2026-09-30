FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends samba smbclient cifs-utils xfsprogs fio util-linux procps prometheus-node-exporter && rm -rf /var/lib/apt/lists/*
COPY smb.conf /etc/samba/smb.conf
COPY entrypoint.sh probe.py xfs-demo.sh /lab/
RUN chmod +x /lab/*.sh
ENTRYPOINT ["/lab/entrypoint.sh"]
