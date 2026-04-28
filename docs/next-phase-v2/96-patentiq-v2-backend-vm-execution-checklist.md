# PatentIQ V2 Backend VM Execution Checklist

## Purpose

This runbook translates the VM migration recommendation into a concrete execution checklist.

It keeps the current PatentIQ runtime model intact:

1. Blob stays canonical,
2. the current backend and bootstrap container images are reused,
3. the frontend can remain on Azure Container Apps,
4. the backend moves to a VM so DuckDB serves from local block storage instead of Azure Files.

This checklist started from the original target shape, but the actual executable fallback on `2026-04-28` is:

1. region:
   - `switzerlandnorth`
2. initial bring-up SKU:
   - `Standard_D2s_v3`
3. current live SKU after in-place resize:
   - `Standard_D4s_v3`
4. data disk:
   - `Premium_LRS`
   - `256 GiB`
5. public IP:
   - VM-managed public IP at creation time
   - current live resource name: `patentiq-backend-vmPublicIP`

The original target shape is still recorded below for reference.

Observed fallback execution result:

1. the full runtime release and HF cache were successfully materialized on the VM-attached local disk,
2. the backend container started successfully and was reachable externally on port `8000`,
3. semantic and lightweight runtime endpoints were fast,
4. the analytics-heavy `pending-grants` route stopped timing out and returned `200`,
5. but it still remained slow enough on `Standard_D2s_v3` that a larger VM shape was still needed,
6. the VM was then resized in place to `Standard_D4s_v3`,
7. the public topology stayed the same because the VM identity, disks, and static IP did not change.

This checklist is written for the current Azure state:

1. resource group:
   - `patent-data`
2. original target region:
   - `germanywestcentral`
3. storage account:
   - `patentiq`
4. blob container:
   - `patentiq-data`
5. ACR:
   - `patentiqacr`
6. backend image tag:
   - `2026-04-28-aca4`
7. bootstrap image tag:
   - `2026-04-28-aca4`
8. active runtime release:
   - `2026-04-25-runtime-current`

---

## Target Shape

Provision:

1. one Linux VM
2. one attached `256 GiB` data disk
3. one static public IP

Recommended names:

1. VM:
   - `patentiq-backend-vm`
2. public IP:
   - `patentiq-backend-ip`
3. data disk:
   - `patentiq-backend-data`
4. actual fallback disk:
   - `patentiq-backend-data-p15`

Original recommended SKU:

1. `Standard_D4s_v5`

Original recommended disk:

1. `Premium SSD v2`
2. `256 GiB`

Actual fallback used:

1. initial:
   - `Standard_D2s_v3`
2. current live:
   - `Standard_D4s_v3`
3. `Premium SSD P15`
4. `256 GiB`

Important sizing note:

1. this is enough for one active `full` runtime copy plus HF cache and temp space,
2. but it is not generous for parallel staging or long rollback retention,
3. if you later want more operational headroom, the first expansion step should be the data disk, not the VM CPU.

---

## Step 0: Verify Premium SSD v2 Availability

Premium SSD v2 can have zonal constraints.

Check disk SKU support in `germanywestcentral`:

```bash
az vm list-skus \
  --resource-type disks \
  --location germanywestcentral \
  --query "[?name=='PremiumV2_LRS'].{name:name,zones:locationInfo[0].zones}" \
  -o table
```

If `PremiumV2_LRS` is available with a zone, use that same zone consistently for:

1. VM
2. public IP
3. disk

Assumption in the examples below:

1. zone `1`

If Premium SSD v2 is unavailable or rejected in your region/zone, fallback is:

1. `P15 LRS` `256 GiB`

Actual execution result:

1. the fallback disk path was required,
2. because `PremiumV2_LRS` disks can only attach to zonal VMs,
3. and the successful fallback VM had to be created regionally rather than zonally.

---

## Step 1: Create Static Public IP

```bash
az network public-ip create \
  --resource-group patent-data \
  --name patentiq-backend-ip \
  --location germanywestcentral \
  --sku Standard \
  --zone 1
```

---

## Step 2: Create Backend VM

Use Ubuntu LTS and assign a system-managed identity.

```bash
az vm create \
  --resource-group patent-data \
  --name patentiq-backend-vm \
  --location germanywestcentral \
  --zone 1 \
  --image Ubuntu2204 \
  --size Standard_D4s_v5 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-address patentiq-backend-ip \
  --public-ip-sku Standard \
  --assign-identity
```

Open required ports:

```bash
az vm open-port --resource-group patent-data --name patentiq-backend-vm --port 22
az vm open-port --resource-group patent-data --name patentiq-backend-vm --port 80
az vm open-port --resource-group patent-data --name patentiq-backend-vm --port 443
```

You can postpone `80/443` if you want to validate backend on an internal port first.

---

## Step 3: Create and Attach Data Disk

Create the disk:

```bash
az disk create \
  --resource-group patent-data \
  --name patentiq-backend-data \
  --location germanywestcentral \
  --zone 1 \
  --sku PremiumV2_LRS \
  --size-gb 256
```

Attach it:

```bash
az vm disk attach \
  --resource-group patent-data \
  --vm-name patentiq-backend-vm \
  --name patentiq-backend-data
```

If you are using the fallback classic disk tier:

```bash
az disk create \
  --resource-group patent-data \
  --name patentiq-backend-data \
  --location germanywestcentral \
  --zone 1 \
  --sku Premium_LRS \
  --size-gb 256
```

---

## Step 4: Assign Azure Roles To The VM Identity

Get scopes and principal id:

```bash
VM_PRINCIPAL_ID=$(az vm show \
  --resource-group patent-data \
  --name patentiq-backend-vm \
  --query identity.principalId \
  -o tsv)

ACR_ID=$(az acr show \
  --resource-group patent-data \
  --name patentiqacr \
  --query id \
  -o tsv)

STORAGE_ID=$(az storage account show \
  --resource-group patent-data \
  --name patentiq \
  --query id \
  -o tsv)
```

Grant image-pull and Blob-read access:

```bash
az role assignment create \
  --assignee-object-id "$VM_PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role AcrPull \
  --scope "$ACR_ID"

az role assignment create \
  --assignee-object-id "$VM_PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Reader" \
  --scope "$STORAGE_ID"
```

Note:

1. the current bootstrap script still uses the storage connection string,
2. so the Blob Reader role is future-proofing and useful for direct `azcopy` operations,
3. but the checklist below uses the current bootstrap container contract as-is.

---

## Step 5: SSH Into The VM

Get the public IP:

```bash
VM_IP=$(az network public-ip show \
  --resource-group patent-data \
  --name patentiq-backend-ip \
  --query ipAddress \
  -o tsv)

echo "$VM_IP"
```

SSH:

```bash
ssh azureuser@"$VM_IP"
```

---

## Step 6: Prepare The Data Disk On The VM

Inside the VM:

Check devices:

```bash
lsblk
ls -l /dev/disk/azure/scsi1/
```

Assume the attached disk is:

1. `/dev/disk/azure/scsi1/lun0`

Partition and format:

```bash
sudo parted /dev/disk/azure/scsi1/lun0 --script mklabel gpt
sudo parted /dev/disk/azure/scsi1/lun0 --script mkpart primary ext4 0% 100%
sudo mkfs.ext4 /dev/disk/azure/scsi1/lun0-part1
```

Mount path:

```bash
sudo mkdir -p /srv/patentiq-data
sudo mount /dev/disk/azure/scsi1/lun0-part1 /srv/patentiq-data
```

Persist mount:

```bash
sudo blkid /dev/disk/azure/scsi1/lun0-part1
```

Copy the UUID and append:

```bash
echo 'UUID=<uuid-from-blkid> /srv/patentiq-data ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab
```

Create runtime directories:

```bash
sudo mkdir -p /srv/patentiq-data/artifacts
sudo mkdir -p /srv/patentiq-data/hf-home
sudo mkdir -p /srv/patentiq-data/logs
sudo chown -R azureuser:azureuser /srv/patentiq-data
```

---

## Step 7: Install Docker And AzCopy

Inside the VM:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
```

Log out and back in, or run:

```bash
newgrp docker
```

Install AzCopy:

```bash
cd /tmp
curl -L https://aka.ms/downloadazcopy-v10-linux -o azcopy.tgz
tar -xzf azcopy.tgz
sudo cp ./azcopy_linux_amd64_*/azcopy /usr/local/bin/
azcopy --version
```

---

## Step 8: Authenticate To Azure From The VM

Use the VM managed identity:

```bash
az login --identity
az acr login --name patentiqacr
```

At this point the VM can pull backend images from ACR.

---

## Step 9: Create Backend Runtime Env File

The current bootstrap image still expects the Azure storage connection string.

Create a local env file on the VM:

```bash
sudo mkdir -p /etc/patentiq
sudo nano /etc/patentiq/backend.env
```

Contents:

```bash
ACR_LOGIN_SERVER=patentiqacr.azurecr.io
BACKEND_IMAGE=patentiqacr.azurecr.io/patentiq-backend-v2:2026-04-28-aca4
BOOTSTRAP_IMAGE=patentiqacr.azurecr.io/patentiq-bootstrap:2026-04-28-aca4

PATENTIQ_BOOTSTRAP_SOURCE_MODE=azure_blob
PATENTIQ_BOOTSTRAP_PROFILE=full
PATENTIQ_BOOTSTRAP_TARGET_ROOT=/artifacts
PATENTIQ_BOOTSTRAP_LOG_PATH=/artifacts/logs/artifact-init.log
PATENTIQ_BOOTSTRAP_HF_HOME=/hf-home
PATENTIQ_BOOTSTRAP_PREFETCH_HF_MODELS=true
PATENTIQ_BOOTSTRAP_ALLOW_UNPINNED_HF_MODELS=true
PATENTIQ_BOOTSTRAP_OVERWRITE=false

PATENTIQ_AZURE_STORAGE_ACCOUNT_URL=https://patentiq.blob.core.windows.net
PATENTIQ_AZURE_STORAGE_CONTAINER=patentiq-data
PATENTIQ_AZURE_ACTIVE_RELEASE_BLOB=manifests/active_release.json
PATENTIQ_AZURE_CONNECTION_STRING_ENV=AZURE_STORAGE_CONNECTION_STRING
AZURE_STORAGE_CONNECTION_STRING=<storage-connection-string>

HF_HOME=/hf-home
HF_HUB_CACHE=/hf-home/hub
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1

PATENTIQ_BACKEND_PORT=8000
PATENTIQ_V2_RUNTIME_PROFILE=azure_vm
PATENTIQ_V2_REPO_ROOT=/app
PATENTIQ_V2_ARTIFACT_MODE=local_fs
PATENTIQ_V2_ETL_DATA_ROOT=/artifacts/releases/2026-04-25-runtime-current
PATENTIQ_V2_LOCAL_ARTIFACT_ROOT=/artifacts/releases/2026-04-25-runtime-current/serving
PATENTIQ_V2_SERVING_MANIFEST_PATH=/artifacts/releases/2026-04-25-runtime-current/serving/serving_snapshot_manifest.json
PATENTIQ_V2_DUCKDB_PATH=/tmp/patentiq_v2.duckdb
PATENTIQ_V2_CACHE_DIR=/tmp/backend-cache
PATENTIQ_V2_PENDING_GRANT_CACHE_DIR=/tmp/pending-grant-cache
PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED=false
```

Lock permissions:

```bash
sudo chmod 600 /etc/patentiq/backend.env
```

---

## Step 10: Run One-Time Bootstrap To Local Disk

This reuses the existing bootstrap image and release contract, but now the target is local block storage.

```bash
set -a
source /etc/patentiq/backend.env
set +a

docker run --rm \
  --env-file /etc/patentiq/backend.env \
  -v /srv/patentiq-data/artifacts:/artifacts \
  -v /srv/patentiq-data/hf-home:/hf-home \
  "$BOOTSTRAP_IMAGE"
```

Expected result:

1. `/srv/patentiq-data/artifacts/releases/2026-04-25-runtime-current/...`
2. `/srv/patentiq-data/hf-home/models/...`
3. bootstrap log:
   - `/srv/patentiq-data/artifacts/logs/artifact-init.log`

Quick validation:

```bash
du -sh /srv/patentiq-data/artifacts/releases/2026-04-25-runtime-current
du -sh /srv/patentiq-data/hf-home
tail -n 50 /srv/patentiq-data/artifacts/logs/artifact-init.log
```

---

## Step 11: Start Backend Container

Initial manual run:

```bash
set -a
source /etc/patentiq/backend.env
set +a

docker run -d \
  --name patentiq-backend-v2 \
  --restart unless-stopped \
  --env-file /etc/patentiq/backend.env \
  -p 8000:8000 \
  -v /srv/patentiq-data/artifacts:/artifacts \
  -v /srv/patentiq-data/hf-home:/hf-home \
  "$BACKEND_IMAGE"
```

Check:

```bash
docker ps
docker logs -f patentiq-backend-v2
curl http://127.0.0.1:8000/health
```

---

## Step 12: Validate Critical Routes

From inside the VM:

```bash
curl 'http://127.0.0.1:8000/api/v1/semantic/families/suggestions?q=yamaha&vector_space=claims&limit=5'

curl 'http://127.0.0.1:8000/api/v1/semantic/families/search?family_id=38134276&vector_space=claims&limit=5'

curl 'http://127.0.0.1:8000/api/v1/portfolios/YAMAHA_CORPORATION/overview'

curl 'http://127.0.0.1:8000/api/v1/portfolios/YAMAHA_CORPORATION/pending-grants?page=1&page_size=5'

curl 'http://127.0.0.1:8000/api/v1/market-intelligence/overview'
```

These are the most important checks because:

1. semantic verifies vector/model access,
2. portfolio overview verifies core serving,
3. `pending-grants` verifies the large analytics DB performance path,
4. market overview verifies another analytics-backed route family.

---

## Step 13: Install Systemd Units

Once the manual run is validated, formalize it.

## Bootstrap Unit

Create:

```bash
sudo nano /etc/systemd/system/patentiq-bootstrap.service
```

```ini
[Unit]
Description=PatentIQ runtime bootstrap
After=docker.service network-online.target
Wants=network-online.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
EnvironmentFile=/etc/patentiq/backend.env
ExecStart=/usr/bin/docker run --rm \
  --env-file /etc/patentiq/backend.env \
  -v /srv/patentiq-data/artifacts:/artifacts \
  -v /srv/patentiq-data/hf-home:/hf-home \
  ${BOOTSTRAP_IMAGE}

[Install]
WantedBy=multi-user.target
```

## Backend Unit

Create:

```bash
sudo nano /etc/systemd/system/patentiq-backend.service
```

```ini
[Unit]
Description=PatentIQ backend container
After=docker.service patentiq-bootstrap.service network-online.target
Requires=docker.service
Requires=patentiq-bootstrap.service

[Service]
Type=simple
EnvironmentFile=/etc/patentiq/backend.env
ExecStartPre=-/usr/bin/docker rm -f patentiq-backend-v2
ExecStart=/usr/bin/docker run \
  --name patentiq-backend-v2 \
  --env-file /etc/patentiq/backend.env \
  -p 8000:8000 \
  -v /srv/patentiq-data/artifacts:/artifacts \
  -v /srv/patentiq-data/hf-home:/hf-home \
  ${BACKEND_IMAGE}
ExecStop=/usr/bin/docker stop patentiq-backend-v2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable patentiq-bootstrap.service
sudo systemctl enable patentiq-backend.service
sudo systemctl start patentiq-backend.service
```

---

## Step 14: Add Reverse Proxy

Use either Caddy or Nginx.

Simplest production shape:

1. backend container listens on `127.0.0.1:8000` or host `8000`
2. Caddy/Nginx publishes `443`
3. `api.patentiq.app` points to the VM public IP

Suggested first cut:

1. use Caddy
2. terminate TLS at Caddy
3. reverse proxy to `localhost:8000`

---

## Step 15: Cut Over Cloudflare

Current intent:

1. frontend remains on ACA
2. backend API moves to VM

Cloudflare change:

1. update `api.patentiq.app`
2. point it to the VM public IP
3. keep frontend DNS unchanged

Safer cutover sequence:

1. validate backend directly on VM public IP / hostname first
2. then update `api.patentiq.app`
3. then validate frontend against the new backend target

---

## Step 16: Post-Cutover Checks

After DNS cutover:

1. `/health`
2. semantic suggestions
3. semantic family search
4. portfolio overview
5. `pending-grants`
6. one market-intelligence route
7. one publication route
8. frontend portfolio and market pages

If `pending-grants` is materially faster on the VM than ACA, the migration has achieved its main goal.

---

## Optional Hardening Later

This checklist deliberately keeps the current contract and images.

Later improvements can include:

1. replace connection-string bootstrap with managed-identity-aware bootstrap
2. add release-retention cleanup rules on the data disk
3. add a smaller analytics-serving artifact for specific hot endpoints
4. put the backend VM behind a load balancer or ingress if horizontal resilience ever becomes necessary

For now, the simplest successful state is:

1. one backend VM
2. one attached local data disk
3. Blob-backed bootstrap to local disk
4. backend container serving DuckDB locally
