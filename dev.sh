#!/bin/bash
# Development Server with TypeScript Watch Mode

set -e

echo "🚀 Starting development environment..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check dependencies
echo -e "${BLUE}📦 Checking dependencies...${NC}"
if ! command -v tsc &> /dev/null; then
    echo -e "${YELLOW}Installing TypeScript...${NC}"
    npm install -g typescript
fi

if ! command -v concurrently &> /dev/null; then
    echo -e "${YELLOW}Installing concurrently...${NC}"
    npm install concurrently
fi

echo -e "${GREEN}✅ All dependencies available${NC}"
echo ""

# Start development mode
echo -e "${BLUE}🎯 Starting development mode...${NC}"
echo "   TypeScript: Watch mode active"
echo "   Flask: Development server"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop${NC}"
echo ""

concurrently \
    --names "tsc,flask" \
    --prefix "[{name}]" \
    "npm run watch" \
    "npm run serve"
