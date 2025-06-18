#!/bin/bash

# Audio2Sub Deployment Script
# Supports CPU, GPU, and MPS (Apple Silicon) deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to detect system
detect_system() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [[ $(uname -m) == "arm64" ]]; then
            echo "macos_arm64"
        else
            echo "macos_intel"
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# Function to check if NVIDIA GPU is available
check_nvidia_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi &> /dev/null && echo "true" || echo "false"
    else
        echo "false"
    fi
}

# Function to recommend device configuration
recommend_device() {
    local system=$(detect_system)
    local has_nvidia=$(check_nvidia_gpu)
    
    case $system in
        "macos_arm64")
            echo "mps"
            ;;
        "macos_intel")
            echo "cpu"
            ;;
        "linux")
            if [[ "$has_nvidia" == "true" ]]; then
                echo "gpu"
            else
                echo "cpu"
            fi
            ;;
        *)
            echo "cpu"
            ;;
    esac
}

# Function to build whisper.cpp (if not available)
build_whisper_cpp() {
    print_status "Checking for whisper.cpp..."
    
    if ! command -v whisper &> /dev/null; then
        print_warning "whisper.cpp not found. Installing..."
        
        # Check if whisper.cpp source exists in parent directory
        if [[ -d "../whisper.cpp" ]]; then
            print_status "Found whisper.cpp source in parent directory"
            cd ../whisper.cpp
            make clean
            make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
            cd - > /dev/null
        else
            print_status "Cloning whisper.cpp..."
            git clone https://github.com/ggerganov/whisper.cpp.git ../whisper.cpp
            cd ../whisper.cpp
            make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
            cd - > /dev/null
        fi
        
        # Create symlink or copy binary
        if [[ -f "../whisper.cpp/main" ]]; then
            ln -sf "$(pwd)/../whisper.cpp/main" /usr/local/bin/whisper 2>/dev/null || \
            cp "../whisper.cpp/main" ./whisper
            print_success "whisper.cpp installed successfully"
        else
            print_error "Failed to build whisper.cpp"
            return 1
        fi
    else
        print_success "whisper.cpp is already available"
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p uploads results models
    print_success "Directories created"
}

# Function to deploy with specified device
deploy() {
    local device=$1
    local compose_file="docker-compose.${device}.yml"
    
    print_status "Deploying Audio2Sub with ${device} configuration..."
    
    # Check if compose file exists
    if [[ ! -f "$compose_file" ]]; then
        print_error "Docker compose file $compose_file not found!"
        return 1
    fi
    
    # Stop any existing containers
    print_status "Stopping existing containers..."
    docker-compose -f docker-compose.cpu.yml down 2>/dev/null || true
    docker-compose -f docker-compose.gpu.yml down 2>/dev/null || true
    docker-compose -f docker-compose.mps.yml down 2>/dev/null || true
    
    # Build and start services
    print_status "Building and starting services..."
    docker-compose -f "$compose_file" up --build -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Health check
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s http://localhost:8000/ping > /dev/null 2>&1; then
            print_success "Services are ready!"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            print_error "Services failed to start within timeout"
            docker-compose -f "$compose_file" logs
            return 1
        fi
        
        print_status "Attempt $attempt/$max_attempts - waiting for services..."
        sleep 2
        ((attempt++))
    done
    
    print_success "Audio2Sub deployed successfully with ${device} configuration!"
    print_status "API available at: http://localhost:8000"
    print_status "API docs available at: http://localhost:8000/docs"
    print_status "Flower monitoring at: http://localhost:5555"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [DEVICE]"
    echo ""
    echo "DEVICE options:"
    echo "  cpu    - CPU-only deployment (compatible with all systems)"
    echo "  gpu    - NVIDIA GPU deployment (requires NVIDIA Docker)"
    echo "  mps    - Apple Silicon MPS deployment (for Apple Silicon Macs)"
    echo "  auto   - Automatically detect and use optimal device (default)"
    echo ""
    echo "Examples:"
    echo "  $0 cpu     # Deploy with CPU"
    echo "  $0 gpu     # Deploy with NVIDIA GPU"
    echo "  $0 mps     # Deploy with Apple Silicon MPS"
    echo "  $0 auto    # Auto-detect optimal device"
    echo "  $0         # Same as auto"
}

# Main script
main() {
    print_status "Audio2Sub Deployment Script"
    print_status "============================"
    
    # Parse command line arguments
    local device=${1:-auto}
    
    case $device in
        "cpu"|"gpu"|"mps")
            ;;
        "auto")
            device=$(recommend_device)
            print_status "Auto-detected device: $device"
            ;;
        "help"|"-h"|"--help")
            show_usage
            exit 0
            ;;
        *)
            print_error "Invalid device: $device"
            show_usage
            exit 1
            ;;
    esac
    
    # System information
    print_status "System: $(detect_system)"
    print_status "NVIDIA GPU: $(check_nvidia_gpu)"
    print_status "Selected device: $device"
    
    # Pre-deployment checks
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed!"
        exit 1
    fi
    
    # Special checks for GPU deployment
    if [[ "$device" == "gpu" ]]; then
        if [[ "$(check_nvidia_gpu)" != "true" ]]; then
            print_warning "NVIDIA GPU not detected, but GPU deployment requested"
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_status "Deployment cancelled"
                exit 0
            fi
        fi
    fi
    
    # Create directories
    create_directories
    
    # Build whisper.cpp if needed
    # build_whisper_cpp
    
    # Deploy
    deploy "$device"
    
    print_success "Deployment completed successfully!"
    print_status "Next steps:"
    print_status "1. Open http://localhost:8000/docs to test the API"
    print_status "2. Upload audio/video files for transcription"
    print_status "3. Monitor tasks at http://localhost:5555 (Flower)"
    print_status "4. Check logs with: docker-compose -f docker-compose.${device}.yml logs -f"
}

# Run main function
main "$@"
