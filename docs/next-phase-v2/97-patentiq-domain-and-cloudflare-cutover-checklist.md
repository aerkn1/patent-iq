# PatentIQ Domain And Cloudflare Cutover Checklist

## Purpose

This note defines the concrete domain cutover path for the current deployment split:

1. frontend stays on Azure Container Apps,
2. backend runs on the VM host,
3. Cloudflare fronts the public domains,
4. Name.com remains the registrar.

The intended production URLs are:

1. `https://www.patentiq.app`
   - frontend
2. `https://api.patentiq.app`
   - backend
3. `https://patentiq.app`
   - redirect to `https://www.patentiq.app`

---

## Current Infra State

Frontend:

1. Azure Container App:
   - `patentiq-frontend-v2`
2. current default hostname:
   - Azure-managed ACA hostname

Backend:

1. VM public IP:
   - `172.161.2.87`
2. backend process:
   - container bound on `:8000`
3. Nginx role:
   - terminate TLS on `:443`
   - reverse proxy to `127.0.0.1:8000`

---

## Step 1: Move DNS Authority To Cloudflare

Add `patentiq.app` to Cloudflare.

Cloudflare will assign two authoritative nameservers for the zone.

At Name.com:

1. open the domain,
2. go to `Manage Nameservers`,
3. remove the current nameservers,
4. add the two Cloudflare nameservers,
5. save changes.

References:

1. Name.com nameserver change:
   - https://cs.name.com/hc/en-us/articles/205934547-Changing-nameservers-for-DNS-management
2. Cloudflare nameserver update:
   - https://developers.cloudflare.com/dns/nameservers/update-nameservers/

Propagation may take up to about `24h`.

---

## Step 2: Frontend Domain On ACA

Use `www.patentiq.app` for the frontend.

In Cloudflare DNS:

1. create `CNAME`:
   - name: `www`
   - target: ACA frontend generated hostname
2. keep it `DNS only` while using ACA managed certificates
3. add ACA ownership-validation `TXT`:
   - name: `asuid.www`
   - value: ACA-provided verification token

Reason:

1. ACA managed cert issuance for a subdomain requires a `CNAME` directly to the container app hostname,
2. Cloudflare proxying must stay off during issuance and renewal.

Reference:

1. https://learn.microsoft.com/en-us/azure/container-apps/custom-domains-managed-certificates

Then in ACA:

1. add custom domain `www.patentiq.app`
2. issue the managed certificate
3. verify `https://www.patentiq.app`

Actual value used during the live cutover:

1. ACA frontend hostname:
   - `patentiq-frontend-v2.greenbush-c9aa3b9e.germanywestcentral.azurecontainerapps.io`

---

## Step 3: Backend DNS On Cloudflare

In Cloudflare DNS create:

1. `A` record:
   - name: `api`
   - value: `172.161.2.87`
   - start as `DNS only`

Do not proxy it yet.

First bring up the origin certificate and Nginx TLS on the VM.

---

## Step 4: Install Cloudflare Origin Certificate On The VM

In Cloudflare dashboard:

1. go to `SSL/TLS` -> `Origin Server`
2. create an Origin CA certificate
3. include hostname:
   - `api.patentiq.app`
4. download/copy:
   - certificate
   - private key

Install them on the VM:

1. cert path:
   - `/etc/patentiq/certs/api.patentiq.app.pem`
2. key path:
   - `/etc/patentiq/certs/api.patentiq.app.key`

Reference:

1. https://developers.cloudflare.com/ssl/origin-configuration/origin-ca/

---

## Step 5: Configure Nginx On The VM

Repo template:

1. [azure/backend.vm.nginx.conf](./../../azure/backend.vm.nginx.conf)

Expected behavior:

1. `:80`
   - redirect to HTTPS
2. `:443`
   - terminate TLS
   - proxy to `http://127.0.0.1:8000`

Important backend header forwarding:

1. `Host`
2. `X-Forwarded-For`
3. `X-Forwarded-Proto=https`

After placing the config:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## Step 6: Cloudflare SSL Mode

Once the VM origin certificate is installed and Nginx serves `443` correctly:

1. set Cloudflare SSL mode to:
   - `Full (strict)`

Reference:

1. https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/

After that, switch the `api` DNS record to `Proxied`.

Observed public behavior during the cutover:

1. some local resolvers may temporarily keep the direct VM IP cached,
2. public resolvers should eventually show Cloudflare anycast IPs for `api.patentiq.app`,
3. once proxied, browser clients should no longer see the Cloudflare Origin CA certificate directly.

---

## Step 7: Backend CORS

The backend must allow the frontend origins.

Recommended production origins:

1. `https://www.patentiq.app`
2. `https://patentiq.app`

The VM backend start script now stages:

1. `PATENTIQ_V2_CORS_ORIGINS`

with both production origins plus local dev origins.

---

## Step 8: Repoint Frontend Runtime Config

The frontend image reads the API base URL at container startup.

Update ACA frontend env:

1. `NEXT_PUBLIC_API_BASE_URL=https://api.patentiq.app`

Then restart or revise the ACA frontend app.

No image rebuild is required.

---

## Step 9: Apex Redirect

Use `patentiq.app` only as a redirect to `www`.

Recommended supporting DNS state:

1. keep an apex `@` record present in Cloudflare,
2. keep that apex record `Proxied`,
3. a practical target is the ACA frontend hostname via Cloudflare CNAME flattening.

Recommended Cloudflare rule:

1. source:
   - `https://patentiq.app/*`
2. target:
   - `https://www.patentiq.app/${1}`
3. status:
   - `301`

Reference:

1. https://developers.cloudflare.com/rules/url-forwarding/examples/redirect-root-to-www/

---

## Step 10: Lock Down The VM

After `api.patentiq.app` works through Cloudflare and Nginx:

1. remove public access to port `8000`
2. keep:
   - `22`
   - `80`
   - `443`

Long-term preferred:

1. `22` restricted to admin IPs
2. `80/443` public
3. backend process only reachable through Nginx locally

---

## Validation Checklist

1. `https://www.patentiq.app`
   - frontend loads
2. `https://api.patentiq.app/health`
   - returns `200`
3. frontend browser network calls hit `https://api.patentiq.app`
4. no browser mixed-content errors
5. no CORS errors
6. semantic suggestions work
7. portfolio overview works
8. compare works
9. pending-grants still returns successfully

## Final Live DNS State

1. `www`
   - `CNAME`
   - `patentiq-frontend-v2.greenbush-c9aa3b9e.germanywestcentral.azurecontainerapps.io`
   - `DNS only`
2. `asuid.www`
   - `TXT`
   - ACA verification token
3. `api`
   - `A`
   - `172.161.2.87`
   - `Proxied`
4. `@`
   - proxied apex host used for the redirect rule

---

## Practical Recommendation

Cut over in this order:

1. Cloudflare zone + nameserver switch
2. `www` frontend custom domain on ACA
3. VM origin certificate + Nginx for `api`
4. backend CORS
5. frontend API base URL repoint
6. apex redirect
7. close VM port `8000`
