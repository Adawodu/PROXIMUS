# Deploying PROXIMUS to GCP

A single Compute Engine VM runs the whole stack with `docker compose`: **api**,
**agent**, **web** (nginx), and **caddy** (automatic HTTPS). The voice agent
connects *outbound* to LiveKit Cloud, and Telnyx SIP terminates at LiveKit — so
this VM never handles raw SIP/RTP media and only needs ports **80/443** open.

Target: **https://proximus.jonnymate.com**

## 0. Prerequisites (once)

```bash
# Authenticate as the account that owns the jonny-mate project:
gcloud auth login

export PROJECT=<jonny-mate-project-id>     # fill in
export REGION=us-west1                      # near the LiveKit US West region
export ZONE=us-west1-b

gcloud config set project "$PROJECT"
gcloud services enable compute.googleapis.com
```

## 1. Static IP + firewall

```bash
gcloud compute addresses create proximus-ip --region="$REGION"
export IP=$(gcloud compute addresses describe proximus-ip --region="$REGION" --format='value(address)')
echo "Static IP: $IP"

# Public web ingress (HTTP for the ACME challenge + HTTPS):
gcloud compute firewall-rules create proximus-web \
  --allow=tcp:80,tcp:443 --direction=INGRESS \
  --target-tags=proximus --source-ranges=0.0.0.0/0

# SSH via IAP (no public 22 needed):
gcloud compute firewall-rules create proximus-ssh-iap \
  --allow=tcp:22 --direction=INGRESS \
  --target-tags=proximus --source-ranges=35.235.240.0/20
```

## 2. DNS

Point an **A record** for `proximus.jonnymate.com` at `$IP`. Caddy will not get
a cert until this resolves.

## 3. Create the VM

`e2-medium` (4 GB) has headroom to *build* the images on-box. `e2-small` (2 GB)
works only if you pre-build images and just pull them.

```bash
gcloud compute instances create proximus \
  --zone="$ZONE" --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud \
  --tags=proximus --address="$IP" --boot-disk-size=20GB
```

## 4. Provision the box

```bash
gcloud compute ssh proximus --zone="$ZONE" --tunnel-through-iap
# on the VM:
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2 git
sudo usermod -aG docker "$USER" && newgrp docker
git clone https://github.com/Adawodu/PROXIMUS.git && cd PROXIMUS
git checkout feat/gcp-deploy
```

## 5. Secrets

Copy your filled-in `.env` up (never commit it). From your laptop:

```bash
gcloud compute scp .env proximus:~/PROXIMUS/.env --zone="$ZONE" --tunnel-through-iap
```

Before starting, make sure `.env` has:
- `API_KEY=<a strong random value>`  (protects the API; also baked into the dashboard)
- `SIP_PROVIDER=telnyx` + all Telnyx / LiveKit / Deepgram / Cartesia / Anthropic keys
- `CORS_ORIGINS` can stay default — the browser is same-origin via nginx.

## 6. Launch

```bash
docker compose -f deploy/docker-compose.prod.yml up -d --build
docker compose -f deploy/docker-compose.prod.yml ps
```

## 7. Verify

```bash
curl -s https://proximus.jonnymate.com/api/health          # {"status":"healthy",...}
docker compose -f deploy/docker-compose.prod.yml logs agent | grep "registered worker"
```

Then open **https://proximus.jonnymate.com**, confirm the dashboard loads and
lists resumes/calls, and place one test call end-to-end.

## Cutover note (fully-cloud)

Once the VM agent shows `registered worker`, **stop any local agent worker** —
otherwise both compete for the same inbound calls on the shared LiveKit project.

## Access control

The dashboard's API key lives in the client bundle, so it is *not* a real gate.
For a public deployment, enable Caddy `basic_auth` in `deploy/Caddyfile` (a hash
recipe is in the comments) or front the VM with Google IAP.
