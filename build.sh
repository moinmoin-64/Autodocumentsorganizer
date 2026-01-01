#!/bin/bash
# TypeScript Build Script for OrganisationsAI

set -e

echo "🔨 Building TypeScript..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if TypeScript is installed
if ! command -v tsc &> /dev/null; then
    echo -e "${YELLOW}⚠️  TypeScript not found. Installing...${NC}"
    npm install -g typescript
fi

echo -e "${BLUE}📦 Compiling TypeScript files...${NC}"
tsc

echo -e "${BLUE}✅ Type checking...${NC}"
tsc --noEmit

echo -e "${GREEN}✅ Build complete!${NC}"
echo ""
echo "Output directory: dist/"
echo "Source maps: dist/**/*.js.map"
echo "Type declarations: dist/**/*.d.ts"
echo ""
echo "📊 Build statistics:"
find dist -name "*.js" | wc -l
echo "JavaScript files generated"
