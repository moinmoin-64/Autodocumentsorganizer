#!/bin/bash

################################################################################
# OrganisationsAI - Linux Installation Script
# Unterstützt: Ubuntu 20.04+, Debian 11+, CentOS 8+, Fedora 34+
# 
# Verwendung: chmod +x install_linux.sh && ./install_linux.sh
################################################################################

set -e  # Exit on error

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variablen
PYTHON_VERSION="3.11"
NODE_VERSION="20"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"

################################################################################
# Funktionen
################################################################################

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_step() {
    echo -e "${BLUE}→ $1${NC}"
}

# Detect Linux Distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
        echo "$OS"
    elif type lsb_release >/dev/null 2>&1; then
        lsb_release -si
    elif [ -f /etc/lsb-release ]; then
        grep DISTRIB_ID /etc/lsb-release | cut -d '=' -f 2
    else
        echo "Unknown"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

################################################################################
# System Check
################################################################################

check_system() {
    print_header "System Check"
    
    DISTRO=$(detect_distro)
    print_step "Erkannte Distribution: $DISTRO"
    
    # Check sudo
    if ! sudo -v >/dev/null 2>&1; then
        print_error "sudo-Rechte erforderlich. Bitte mit sudo ausführen."
        exit 1
    fi
    
    print_success "sudo-Rechte verfügbar"
}

################################################################################
# Install System Dependencies
################################################################################

install_system_deps() {
    print_header "System Dependencies Installation"
    
    if command_exists apt-get; then
        # Debian/Ubuntu
        print_step "Updating package manager..."
        sudo apt-get update -qq
        
        print_step "Installing system dependencies..."
        sudo apt-get install -y \
            build-essential \
            libssl-dev \
            libffi-dev \
            python3-dev \
            python3.11 \
            python3.11-venv \
            python3-pip \
            git \
            curl \
            wget \
            zip \
            unzip \
            sqlite3 \
            redis-server \
            postgresql-client \
            libpq-dev
            
        print_success "System dependencies (Debian/Ubuntu) installed"
        
    elif command_exists yum; then
        # CentOS/Fedora/RHEL
        print_step "Installing system dependencies..."
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y \
            python3.11 \
            python3.11-devel \
            python3-pip \
            git \
            curl \
            wget \
            zip \
            sqlite-devel \
            openssl-devel \
            libffi-devel \
            redis \
            postgresql-devel
            
        print_success "System dependencies (CentOS/Fedora) installed"
        
    elif command_exists brew; then
        # macOS (if running on macOS)
        print_step "Installing system dependencies (macOS)..."
        brew install python@3.11 node redis postgresql
        print_success "System dependencies (macOS) installed"
        
    else
        print_error "Unterstützte Package Manager nicht gefunden (apt, yum, brew)"
        exit 1
    fi
}

################################################################################
# Install Node.js and npm
################################################################################

install_nodejs() {
    print_header "Node.js Installation"
    
    if command_exists node; then
        NODE_VER=$(node --version)
        print_step "Node.js bereits installiert: $NODE_VER"
    else
        print_step "Installing Node.js $NODE_VERSION..."
        
        if command_exists apt-get; then
            # NodeSource repository (Debian/Ubuntu)
            curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | sudo -E bash -
            sudo apt-get install -y nodejs
        elif command_exists yum; then
            # NodeSource repository (CentOS/Fedora)
            curl -fsSL https://rpm.nodesource.com/setup_${NODE_VERSION}.x | sudo bash -
            sudo yum install -y nodejs
        fi
        
        print_success "Node.js installiert: $(node --version)"
    fi
    
    # Update npm
    print_step "Updating npm..."
    npm install -g npm@latest
    print_success "npm updated: $(npm --version)"
}

################################################################################
# Create Python Virtual Environment
################################################################################

create_venv() {
    print_header "Python Virtual Environment"
    
    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment bereits vorhanden: $VENV_DIR"
        read -p "Erneut erstellen? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
        else
            print_step "Using existing venv"
            source "$VENV_DIR/bin/activate"
            return 0
        fi
    fi
    
    print_step "Creating Python $PYTHON_VERSION virtual environment..."
    python${PYTHON_VERSION} -m venv "$VENV_DIR"
    
    print_success "Virtual environment erstellt: $VENV_DIR"
    
    # Activate venv
    source "$VENV_DIR/bin/activate"
    print_success "Virtual environment activated"
}

################################################################################
# Install Python Dependencies
################################################################################

install_python_deps() {
    print_header "Python Dependencies"
    
    if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
        print_error "requirements.txt nicht gefunden!"
        exit 1
    fi
    
    source "$VENV_DIR/bin/activate"
    
    print_step "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    
    print_step "Installing Python packages from requirements.txt..."
    pip install -r "$PROJECT_DIR/requirements.txt"
    
    print_success "Python dependencies installed"
}

################################################################################
# Install Node.js Dependencies
################################################################################

install_node_deps() {
    print_header "Node.js Dependencies"
    
    if [ ! -f "$PROJECT_DIR/package.json" ]; then
        print_warning "package.json nicht gefunden - überspringe npm install"
        return 0
    fi
    
    print_step "Installing npm packages..."
    cd "$PROJECT_DIR"
    npm ci --prefer-offline
    
    print_success "Node.js dependencies installed"
}

################################################################################
# Compile TypeScript
################################################################################

compile_typescript() {
    print_header "TypeScript Compilation"
    
    if [ ! -f "$PROJECT_DIR/tsconfig.json" ]; then
        print_warning "tsconfig.json nicht gefunden - überspringe TypeScript compilation"
        return 0
    fi
    
    if ! command_exists tsc; then
        print_step "Installing TypeScript globally..."
        npm install -g typescript
    fi
    
    cd "$PROJECT_DIR"
    print_step "Compiling TypeScript..."
    npx tsc
    
    if [ $? -eq 0 ]; then
        print_success "TypeScript compilation erfolgreich"
    else
        print_error "TypeScript compilation fehlgeschlagen"
        exit 1
    fi
}

################################################################################
# Database Setup
################################################################################

setup_database() {
    print_header "Database Setup"
    
    source "$VENV_DIR/bin/activate"
    cd "$PROJECT_DIR"
    
    if [ ! -f "$PROJECT_DIR/main.py" ]; then
        print_warning "main.py nicht gefunden - überspringe database setup"
        return 0
    fi
    
    print_step "Running database migrations..."
    
    if [ -f "$PROJECT_DIR/migrate_passwords.py" ]; then
        python "$PROJECT_DIR/migrate_passwords.py" || true
    fi
    
    if [ -f "$PROJECT_DIR/migrate_to_sqlalchemy.py" ]; then
        python "$PROJECT_DIR/migrate_to_sqlalchemy.py" || true
    fi
    
    print_success "Database setup abgeschlossen"
}

################################################################################
# Environment Configuration
################################################################################

setup_environment() {
    print_header "Environment Configuration"
    
    if [ -f "$PROJECT_DIR/.env" ]; then
        print_warning ".env Datei bereits vorhanden"
    else
        print_step "Creating .env file..."
        cat > "$PROJECT_DIR/.env" << 'EOF'
# Flask Configuration
FLASK_APP=main.py
FLASK_ENV=development
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False

# Database
DATABASE_URL=sqlite:///./data/database.db
SQLALCHEMY_DATABASE_URI=sqlite:///./data/database.db

# Redis
REDIS_URL=redis://localhost:6379

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Features
ENABLE_OFFLINE_MODE=True
ENABLE_PWA=True
EOF
        print_success ".env Datei erstellt"
        print_warning "Bitte .env Datei überprüfen und anpassen!"
    fi
}

################################################################################
# Create Data Directories
################################################################################

create_directories() {
    print_header "Creating Data Directories"
    
    mkdir -p "$PROJECT_DIR/data"
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/uploads"
    mkdir -p "$PROJECT_DIR/app/static/js/dist"
    
    print_success "Directories created"
}

################################################################################
# Redis Setup (Optional)
################################################################################

setup_redis() {
    print_header "Redis Configuration"
    
    if command_exists redis-server; then
        print_step "Redis found: $(redis-server --version)"
        
        # Check if Redis is running
        if redis-cli ping >/dev/null 2>&1; then
            print_success "Redis is running"
        else
            print_warning "Redis is not running"
            read -p "Start Redis server? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo systemctl start redis-server
                print_success "Redis started"
            fi
        fi
    else
        print_warning "Redis not installed. Optional feature skipped."
    fi
}

################################################################################
# Verification
################################################################################

verify_installation() {
    print_header "Installation Verification"
    
    errors=0
    
    # Check Python
    if command_exists python3; then
        py_ver=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python $py_ver"
    else
        print_error "Python not found"
        ((errors++))
    fi
    
    # Check Node.js
    if command_exists node; then
        node_ver=$(node --version)
        print_success "Node.js $node_ver"
    else
        print_error "Node.js not found"
        ((errors++))
    fi
    
    # Check npm
    if command_exists npm; then
        npm_ver=$(npm --version)
        print_success "npm $npm_ver"
    else
        print_error "npm not found"
        ((errors++))
    fi
    
    # Check TypeScript
    if command_exists tsc; then
        tsc_ver=$(tsc --version)
        print_success "TypeScript $tsc_ver"
    else
        print_warning "TypeScript not found in PATH"
    fi
    
    # Check venv
    if [ -d "$VENV_DIR" ]; then
        print_success "Virtual environment: $VENV_DIR"
    else
        print_error "Virtual environment not found"
        ((errors++))
    fi
    
    # Check project files
    if [ -f "$PROJECT_DIR/main.py" ]; then
        print_success "main.py found"
    else
        print_error "main.py not found"
        ((errors++))
    fi
    
    if [ -f "$PROJECT_DIR/package.json" ]; then
        print_success "package.json found"
    else
        print_error "package.json not found"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        print_success "All checks passed!"
        return 0
    else
        print_error "$errors checks failed"
        return 1
    fi
}

################################################################################
# Main Installation Flow
################################################################################

main() {
    clear
    print_header "🚀 OrganisationsAI Linux Installation"
    
    echo "Project Directory: $PROJECT_DIR"
    echo "Python Version: $PYTHON_VERSION"
    echo "Node.js Version: $NODE_VERSION"
    echo ""
    
    read -p "Fortfahren mit Installation? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Installation abgebrochen"
        exit 0
    fi
    
    check_system
    install_system_deps
    install_nodejs
    create_venv
    install_python_deps
    install_node_deps
    compile_typescript
    create_directories
    setup_environment
    setup_redis
    setup_database
    verify_installation
    
    if [ $? -eq 0 ]; then
        print_header "✅ Installation Erfolgreich!"
        
        echo ""
        echo "Nächste Schritte:"
        echo ""
        echo "1. Environment aktivieren:"
        echo "   source $VENV_DIR/bin/activate"
        echo ""
        echo "2. Development Server starten:"
        echo "   python main.py"
        echo ""
        echo "3. Oder mit npm:"
        echo "   npm run dev"
        echo ""
        echo "4. Application öffnen:"
        echo "   http://localhost:5000"
        echo ""
        
    else
        print_error "Installation fehlgeschlagen!"
        exit 1
    fi
}

# Run main function
main "$@"
