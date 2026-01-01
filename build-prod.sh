#!/bin/bash
# Production Build Script

set -e

echo "🏗️  Building for production..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Clean
echo -e "${BLUE}🧹 Cleaning old build...${NC}"
rm -rf dist/

# Step 2: Type check
echo -e "${BLUE}🔍 Type checking...${NC}"
tsc --noEmit || {
    echo -e "${RED}❌ Type check failed${NC}"
    exit 1
}

# Step 3: Compile
echo -e "${BLUE}🔨 Compiling TypeScript...${NC}"
tsc --sourceMap false

# Step 4: Verify
echo -e "${BLUE}✅ Verifying build...${NC}"
if [ ! -d "dist" ]; then
    echo -e "${RED}❌ Build failed: dist directory not created${NC}"
    exit 1
fi

JS_COUNT=$(find dist -name "*.js" | wc -l)
if [ "$JS_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ Build failed: no JavaScript files generated${NC}"
    exit 1
fi

# Step 5: Report
echo -e "${GREEN}✅ Production build complete!${NC}"
echo ""
echo "📊 Build Report:"
echo "   JavaScript files: $JS_COUNT"
echo "   Size: $(du -sh dist | cut -f1)"
echo "   Output: dist/"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "   1. Run tests: npm run test:all"
echo "   2. Deploy: python main.py"
echo "   3. Monitor: Check health endpoint"
