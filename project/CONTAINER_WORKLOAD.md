# Azure container application workload (sample)

This folder includes a **numbered playbook sequence** that provisions a small **Azure Container Apps** sample behind optional **Azure Front Door (Standard)**, plus **Azure Container Registry**, **Azure SQL**, and a **storage account**. The running app serves a single HTML page that highlights **Red Hat Ansible Automation Platform on Azure** and lists the main resource names.

Workflow job templates can call these playbooks in order later; this document only describes the playbooks and variables.

## Ansible Automation Platform (import as a project)

- **Source control**: Point a **Project** at this repository (branch you use for demos). Use the **repository root** as the project base so `ansible.cfg` and `collections/requirements.yml` resolve the same way as when you run locally from that root.
- **Collections**: `collections/requirements.yml` lists `azure.azcollection`. Either enable **galaxy** / **Automation Hub** collection sync on the project, or install the same collection (and its Python dependencies) into your **execution environment** image.
- **Job templates**: Set **Playbook** to a path relative to the project root, for example `project/00_create_workload_resource_group.yml`, then `project/01_create_storage_and_acr.yml`, and so on. Each playbook is self-contained (`hosts: localhost`, `connection: local`).
- **Inventory**: Use an inventory that includes `localhost` (Controller’s *Demo Inventory* / *localhost* pattern is typical). These playbooks do not target remote hosts.
- **Credentials**: Attach an Azure credential (or equivalent extra variables / credential plugin) compatible with `azure.azcollection` (same as the rest of this repo).
- **Playbook 03**: The execution environment (or path on the execution node) must include the **Azure CLI** (`az`) and a valid `az login` session if you rely on CLI auth, because `az acr import` is used before the ARM deployment.
- **Check mode**: Playbook **03** skips the `az acr import` and ARM deployment when Ansible **check mode** is enabled, and prints a short notice instead.

## Playbook order

| Order | File | Purpose |
|------:|------|---------|
| 00 | `00_create_workload_resource_group.yml` | Resource group |
| 01 | `01_create_storage_and_acr.yml` | Storage account + Azure Container Registry (admin enabled for demo pulls) |
| 02 | `02_create_azure_sql.yml` | Azure SQL logical server, Basic database, firewall rule for Azure services |
| 03 | `03_create_container_apps_sample.yml` | `az acr import` + ARM deployment: Log Analytics, Container Apps environment, public Container App |
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
- **Azure CLI** (`az`) available on the controller host and **signed in** (`az login`). Playbook **03** uses `az acr import` to copy `python:3.12-alpine` from Docker Hub into your ACR before the Container App is deployed.
- **Globally unique** names in `project/vars/container_workload_defaults.yml` (storage account, ACR, SQL server) adjusted for your subscription before the first deploy.

## Variables

Defaults live in `project/vars/container_workload_defaults.yml`. Override in `env/extravars`, with `-e`, or in Automation Controller surveys. At minimum, set a strong **`aca_sql_admin_password`** for real environments; the sample default is only for local testing.

Important names:

- **`container_workload_resource_group_name`** — all resources for this demo share this group (until you split them in a future workflow).
- **`aca_storage_account_name`**, **`aca_acr_name`**, **`aca_sql_server_name`** — must be unique where Azure requires it (storage: lowercase alphanumeric only; length limits apply).

## Application content

- HTML is rendered from `project/templates/container_workload/demo_index.html.j2` (Red Hat fonts, simple layout, resource table).
- The Container App runs **`python:3.12-alpine`** from your ACR; startup decodes a **base64** page payload stored as an app **secret** (see ARM template `project/templates/container_workload/arm_container_app.json.j2`).
- The page uses **JavaScript** to show `location.hostname` so you can see whether you hit the app **directly** (`*.azurecontainerapps.io`) or via **Front Door** (`*.azurefd.net`) after playbook 04.

## Front Door and “firewall”

Playbook **04** uses **Azure Front Door Standard** (`standard_azurefrontdoor` on a CDN profile). That is the usual “edge” entry in solution diagrams. **Web Application Firewall** policies are a **Premium** concern; this sample does not attach a WAF policy so the template stays small. You can extend playbook 04 later with `azure_rm_afdruleset` and related modules if you move to Premium.

## Teardown

```bash
ansible-playbook project/99_destroy_workload_resource_group.yml
```

This removes the resource group created for this workload (including SQL server, ACR, and deployments). Ensure `container_workload_resource_group_name` points only at this demo before running it.
