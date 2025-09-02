#!/bin/bash
# Fly.io Deployment Script for Pharmacy Finder

echo "🚀 Deploying Pharmacy Finder to Fly.io"
echo "======================================"

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl not found. Install from: https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Login to Fly.io
echo "🔐 Logging into Fly.io..."
flyctl auth login

# Initialize app (if not already done)
if [ ! -f "fly.toml" ]; then
    echo "📝 Initializing Fly.io app..."
    flyctl launch --no-deploy
fi

# Set secrets (API keys)
echo "🔑 Setting API secrets..."
echo "⚠️  You'll need to provide your API keys:"

read -p "Enter OpenAI API Key: " -s openai_key
echo
flyctl secrets set OPENAI_API_KEY="$openai_key"

read -p "Enter Google Maps API Key (optional): " -s gmaps_key
echo
if [ -n "$gmaps_key" ]; then
    flyctl secrets set GOOGLE_MAPS_API_KEY="$gmaps_key"
fi

read -p "Enter Anthropic API Key (optional): " -s anthropic_key
echo
if [ -n "$anthropic_key" ]; then
    flyctl secrets set ANTHROPIC_API_KEY="$anthropic_key"
fi

# Set Redis URL if using external Redis
read -p "Enter Redis URL (or press Enter to skip): " redis_url
if [ -n "$redis_url" ]; then
    flyctl secrets set REDIS_URL="$redis_url"
fi

# Deploy the application
echo "🚀 Deploying application..."
flyctl deploy

# Check deployment status
echo "✅ Deployment complete!"
echo "🌐 Your app should be available at: https://$(flyctl info --json | jq -r '.Hostname')"
echo "🔍 Check logs with: flyctl logs"
echo "📊 Monitor with: flyctl status"

echo ""
echo "📋 Post-deployment checklist:"
echo "- ✅ Test the /health endpoint"
echo "- ✅ Test pharmacy search functionality"  
echo "- ✅ Test AI agent responses"
echo "- ✅ Test Google Maps integration (if enabled)"
echo "- ✅ Monitor logs for any errors"
