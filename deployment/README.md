# Deployment Setup

This project uses GitHub Actions to deploy to a VPS. The workflow handles both the frontend (Svelte/Vite) and backend (FastAPI/Granian) deployments.

## Architecture

- **Backend**: FastAPI running under Granian, managed by systemd
- **Frontend**: Static files served by nginx from `/var/www/html/timely/`
- **Reverse Proxy**: nginx proxies API requests to the Granian backend

## GitHub Actions Secrets

You need to configure the following secrets in your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add these repository secrets:

| Secret Name    | Description                                      | Example                |
|----------------|--------------------------------------------------|------------------------|
| `VPS_HOST`     | Your VPS IP address or hostname                  | `192.168.1.100`        |
| `VPS_SSH_KEY`  | Private SSH key for authentication (full content)| `-----BEGIN OPENSSH...`|

### Generating an SSH Key for Deployment

On your local machine:

```bash
# Generate a dedicated deploy key
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/deploy_key -N ""

# Copy the public key to your VPS
ssh-copy-id -i ~/.ssh/deploy_key.pub ubuntu@YOUR_VPS_HOST

# Copy the private key content (this goes into VPS_SSH_KEY secret)
cat ~/.ssh/deploy_key
```

## VPS Prerequisites

Ensure the following on your VPS:

1. **Git repository** is cloned at `/home/ubuntu/programs/Time-organizer`
2. **Python venv** exists at `/home/ubuntu/programs/Time-organizer/backend/.venv`
3. **Systemd service** is set up at `/etc/systemd/system/time-organizer.service`
4. **Frontend directory** exists: `/var/www/html/timely/`
5. **Sudoers entry** for passwordless systemctl (add with `sudo visudo`):

```
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart time-organizer.service
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/systemctl status time-organizer.service
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/systemctl is-active time-organizer.service
```

## Triggering Deployments

Deployments are triggered automatically on:
- Push to the `main` branch
- Manual trigger via GitHub Actions UI (workflow_dispatch)

## Workflow Overview

1. **Build Frontend**: Installs dependencies and builds the Vite/Svelte app
2. **Deploy Backend**: 
   - SSHs into VPS
   - Pulls latest code
   - Updates Python dependencies
   - Restarts the systemd service
3. **Deploy Frontend**:
   - Syncs built assets to `/var/www/html/timely/`
4. **Verify**: Checks service status and lists deployed files