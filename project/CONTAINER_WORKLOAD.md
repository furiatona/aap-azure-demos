# Azure container application workload (sample)

This folder includes a **numbered playbook sequence** that provisions a small **Azure Container Apps** sample behind optional **Azure Front Door (Standard)**, plus **Azure Container Registry**, **Azure SQL**, and a **storage account**. The running app serves a single HTML page that highlights **Red Hat Ansible Automation Platform on Azure** and lists the main resource names.

Workflow job templates can call these playbooks in order later; this document only describes the playbooks and variables.

## Ansible Automation Platform (import as a project)

- **Source control**: Point a **Project** at this repository (branch you use for demos). Use the **repository root** as the project base so `ansible.cfg` and `collections/requirements.yml` resolve the same way as when you run locally from that root.
- **Collections**: `collections/requirements.yml` lists `azure.azcollection`. Either enable **galaxy** / **Automation Hub** collection sync on the project, or install the same collection (and its Python dependencies) into your **execution environment** image.
- **Job templates**: Set **Playbook** to a path relative to the project root, for example `project/00_create_workload_resource_group.yml`, then `project/01_create_storage_and_acr.yml`, and so on. Each playbook is self-contained (`hosts: localhost`, `connection: local`).
- **Inventory**: Use an inventory that includes `localhost` (Controller’s *Demo Inventory* / *localhost* pattern is typical). These playbooks do not target remote hosts.
- **Credentials**: Attach an Azure credential (or equivalent extra variables / credential plugin) compatible with `azure.azcollection` (same as the rest of this repo).
- **Playbook 03**: The execution environment must include the **Azure CLI** (`az`). The playbook performs **`az login --service-principal`** using the **Microsoft Azure Resource Manager** credential env vars (`AZURE_CLIENT_ID`, `AZURE_SECRET`, `AZURE_TENANT`, `AZURE_SUBSCRIPTION_ID`) before `az acr import`.
- **Check mode**: Playbook **03** skips Azure CLI login, `az acr import`, and ARM deployment when Ansible **check mode** is enabled, and prints a short notice instead.

## Playbook order

| Order | File | Purpose |
|------:|------|---------|
| 00 | `00_create_workload_resource_group.yml` | Resource group |
| 01 | `01_create_storage_and_acr.yml` | Storage account + Azure Container Registry (admin enabled for demo pulls) |
| 02 | `02_create_azure_sql.yml` | Azure SQL logical server, Basic database, firewall rule for Azure services |
| 03 | `03_create_container_apps_sample.yml` | `az acr import` (default: **ECR Public** mirror of `library/python`, not Docker Hub) + ARM: Log Analytics, Container Apps env, app |
| 04 | `04_create_front_door_standard.yml` | Azure Front Door Standard profile, endpoint, origin (HTTPS to the app), default route |
| 99 | `99_destroy_workload_resource_group.yml` | Deletes the whole resource group |

Run from the **repository root** (`azure-demos/`) so paths match Ansible Runner conventions, for example:

```bash
cd /path/to/azure-demos
ansible-playbook project/00_create_workload_resource_group.yml
ansible-playbook project/01_create_storage_and_acr.yml
# … continue through 04 as needed
```

## Prerequisites

- `azure.azcollection` installed (for example `ansible-galaxy collection install azure.azcollection`).
- Azure credentials configured for Ansible (for example `~/.azure/credentials` as in the main project README).
- **Azure CLI** (`az`) on the execution environment (Controller EE image). Playbook **03** runs `az acr import`; it first runs **`az login --service-principal`** using the same variables **AAP injects** for the Microsoft Azure Resource Manager credential (`AZURE_CLIENT_ID`, `AZURE_SECRET`, `AZURE_TENANT`, `AZURE_SUBSCRIPTION_ID`). For **local** runs without those env vars, run **`az login`** once so the CLI has a session, or export the same `AZURE_*` / `ARM_*` variables.
- **Globally unique** names in `project/vars/container_workload_defaults.yml` (storage account, ACR, SQL server) adjusted for your subscription before the first deploy.

## Variables

Defaults live in `project/vars/container_workload_defaults.yml`. Override in `env/extravars`, with `-e`, or in Automation Controller surveys. At minimum, set a strong **`aca_sql_admin_password`** for real environments; the sample default is only for local testing.

Important names:

- **`container_workload_resource_group_name`** — all resources for this demo share this group (until you split them in a future workflow).
- **`aca_storage_account_name`**, **`aca_acr_name`**, **`aca_sql_server_name`** — must be unique where Azure requires it (storage: lowercase alphanumeric only; length limits apply).

## Application content

- HTML is rendered from `project/templates/container_workload/demo_index.html.j2` (Red Hat fonts, simple layout, resource table).
- The Container App runs **`python:3.12-bookworm`** in ACR (layers imported from **`aca_image_import_source`**, default **`mcr.microsoft.com/devcontainers/python:1-3.12-bookworm`** to avoid anonymous 429 limits on Docker Hub / ECR Public when ACR pulls the manifest). Import is retried (`aca_acr_import_retries` / `aca_acr_import_delay_seconds`). Startup decodes a **base64** page via **`python3`** (see ARM template `project/templates/container_workload/arm_container_app.json.j2`).
- The page uses **JavaScript** to show `location.hostname` so you can see whether you hit the app **directly** (`*.azurecontainerapps.io`) or via **Front Door** (`*.azurefd.net`) after playbook 04.

## Front Door and “firewall”

Playbook **04** uses **Azure Front Door Standard** (`standard_azurefrontdoor` on a CDN profile). The CDN **profile** must be created with **`location: global`** (required by that SKU; it still lives in your resource group). **Web Application Firewall** policies are a **Premium** concern; this sample does not attach a WAF policy so the template stays small. You can extend playbook 04 later with `azure_rm_afdruleset` and related modules if you move to Premium.

## Teardown

```bash
ansible-playbook project/99_destroy_workload_resource_group.yml
```

This removes the resource group created for this workload (including SQL server, ACR, and deployments). Ensure `container_workload_resource_group_name` points only at this demo before running it.
