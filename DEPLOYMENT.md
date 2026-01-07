# DigitalOcean App Platform Deployment Guide

This repository is configured to deploy on DigitalOcean App Platform.

## Files Added for Deployment

- **app.yaml** - DigitalOcean App Platform configuration file
- **Dockerfile** - Docker container configuration (optional, for custom builds)
- **.dockerignore** - Files to exclude from Docker image
- **requirements.txt** - Python dependencies

## Prerequisites

1. A DigitalOcean account
2. This GitHub repository linked to your DigitalOcean account
3. A Discord bot token (get from [Discord Developer Portal](https://discord.com/developers))

## Environment Variables Required

You'll need to set these in DigitalOcean:

- `DISCORD_TOKEN` - Your Discord bot token
- `MANAGEMENT_CHANNEL` - Your Discord management channel ID

## Deployment Steps

### Option 1: Deploy via DigitalOcean Console

1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Click **Create App**
3. Select **GitHub** and authorize your account
3. Select the `Nicolas-Oliver/ticker-bot` repository
5. Choose the `main` branch
6. DigitalOcean will auto-detect the `app.yaml` file
7. Add environment variables:
   - `DISCORD_TOKEN` - paste your Discord bot token
   - `MANAGEMENT_CHANNEL` - paste your management channel ID
8. Click **Create Resources** and deploy

### Option 2: Deploy via DigitalOcean CLI

```bash
# Install doctl CLI
brew install doctl  # or apt-get install doctl

# Authenticate
doctl auth init

# Deploy
doctl apps create --spec app.yaml
```

## After Deployment

1. Your Discord bot will start automatically
2. Ensure your bot is invited to your Discord server:
   - Use the invite link in your README.md
   - Or visit: `https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot`

## Monitoring

- View logs: Go to your app in DigitalOcean dashboard → Logs
- View deployments: Go to your app in DigitalOcean dashboard → Deployments
- View resource usage: Go to your app in DigitalOcean dashboard → Resources

## Updating

Simply push changes to the `main` branch - DigitalOcean will automatically detect and redeploy.

## Costs

DigitalOcean App Platform pricing:
- $0.00000198 per second (roughly ~$5-10/month for a simple bot)
- Or use a basic droplet for more control (~$4-6/month)

## Troubleshooting

### Bot doesn't respond
- Check that `DISCORD_TOKEN` is correct
- Check logs in DigitalOcean dashboard
- Ensure bot has proper permissions in Discord server

### Deployment fails
- Check that `requirements.txt` exists
- Verify `app.yaml` syntax is correct
- Check logs for build errors

### Environment variables not loading
- Ensure variables are set with correct names
- Restart the service after updating variables

## Local Testing

Before deploying, test locally:

```bash
pip install -r requirements.txt
DISCORD_TOKEN=your_token MANAGEMENT_CHANNEL=your_channel python main.py
```
