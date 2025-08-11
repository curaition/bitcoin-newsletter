#!/bin/bash

# Railway Deployment Script for Bitcoin Newsletter
# This script configures and deploys all services to Railway

set -e

echo "🚀 Bitcoin Newsletter Railway Deployment"
echo "========================================"

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check if railway CLI is available
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install with: npm install -g @railway/cli"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Not in project root directory. Please run from the project root."
    exit 1
fi

# Check if git remote is set
if ! git remote get-url origin &> /dev/null; then
    echo "❌ Git remote 'origin' not set. Please set up GitHub repository first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Login to Railway (if not already logged in)
echo "🔐 Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "Please login to Railway:"
    railway login
fi

# Link to existing project
echo "🔗 Linking to Railway project..."
railway link f672d6bf-ac6b-4d62-9a38-158919110629

# Push code to GitHub first
echo "📤 Pushing code to GitHub..."
git add .
git commit -m "Deploy to Railway" --allow-empty
git push origin main

# Deploy services
echo "🚀 Deploying services..."

# Deploy web service
echo "📱 Deploying web service..."
railway service web

# Deploy worker service  
echo "👷 Deploying worker service..."
railway service worker

# Deploy beat service
echo "⏰ Deploying beat service..."
railway service beat

# Set up domains for web service
echo "🌐 Setting up domain for web service..."
railway domain

# Check deployment status
echo "📊 Checking deployment status..."
railway status

echo "✅ Railway deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Check service health: railway logs --service web"
echo "2. Monitor tasks: railway logs --service worker"
echo "3. Verify scheduling: railway logs --service beat"
echo "4. Test API: curl https://your-domain.railway.app/health"
echo ""
echo "🎉 Bitcoin Newsletter is now live on Railway!"
