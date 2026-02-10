#!/bin/bash

set -e

echo "==========================================="
echo "Server Landing Page Deployment Script"
echo "==========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker is installed"

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available. Please install Docker Compose."
    exit 1
fi
print_success "Docker Compose is available"

# Create server-landing network if it doesn't exist
echo ""
echo "Setting up Docker networks..."
if ! docker network ls | grep -q "server-landing"; then
    docker network create server-landing
    print_success "Created server-landing network"
else
    print_warning "server-landing network already exists"
fi

# Create prompt-reverser network if it doesn't exist
if ! docker network ls | grep -q "prompt-reverser"; then
    docker network create prompt-reverser
    print_success "Created prompt-reverser network"
else
    print_warning "prompt-reverser network already exists"
fi

# Check if .env exists
echo ""
if [ ! -f .env ]; then
    print_warning ".env file not found. Copying from .env.example..."
    cp .env.example .env
    print_success "Created .env file"
else
    print_success ".env file exists"
fi

# Stop system nginx if running
echo ""
echo "Checking system nginx..."
if systemctl is-active --quiet nginx; then
    print_warning "System nginx is running. You may want to stop it:"
    echo "  sudo systemctl stop nginx"
    echo "  sudo systemctl disable nginx"
    read -p "Do you want to stop system nginx now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl stop nginx
        sudo systemctl disable nginx
        print_success "Stopped and disabled system nginx"
    fi
else
    print_success "System nginx is not running"
fi

# Build and start containers
echo ""
echo "Building and starting containers..."
docker compose build
print_success "Built containers"

echo ""
docker compose up -d
print_success "Started containers"

# Wait for services to be ready
echo ""
echo "Waiting for services to start..."
sleep 5

# Check if nginx is responding
echo ""
echo "Checking service health..."
if curl -f http://100.77.248.9:80 &> /dev/null; then
    print_success "Server landing page is accessible at http://100.77.248.9:80"
else
    print_error "Server landing page is not accessible. Check logs with: docker compose logs"
    exit 1
fi

# Check backend API
if curl -f http://100.77.248.9:80/api/health &> /dev/null; then
    print_success "Backend API is responding"
else
    print_warning "Backend API is not responding yet"
fi

echo ""
echo "==========================================="
echo "Deployment complete!"
echo "==========================================="
echo ""
echo "Access the landing page at: http://100.77.248.9:80"
echo ""
echo "Useful commands:"
echo "  View logs:        docker compose logs -f"
echo "  Stop services:    docker compose down"
echo "  Restart services: docker compose restart"
echo "  View status:      docker compose ps"
echo ""
