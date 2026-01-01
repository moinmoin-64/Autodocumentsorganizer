#!/bin/bash
# TypeScript Compilation Script for Linux/WSL
# Kompiliert alle .ts Dateien zu JavaScript

echo "🔨 TypeScript Compilation Started..."

# Check if tsc is installed
if ! command -v tsc &> /dev/null; then
    echo "❌ TypeScript not installed. Install with: npm install -g typescript"
    exit 1
fi

# Create dist directory if it doesn't exist
DIST_DIR="app/static/js/dist"
mkdir -p "$DIST_DIR"
echo "✅ Dist directory ready: $DIST_DIR"

# Type check first (no output, just validation)
echo "📋 Type checking..."
tsc --noEmit
if [ $? -ne 0 ]; then
    echo "❌ Type check failed!"
    exit 1
fi
echo "✅ Type check passed"

# Compile TypeScript to JavaScript
echo "⚙️  Compiling TypeScript..."
tsc

if [ $? -ne 0 ]; then
    echo "❌ Compilation failed!"
    exit 1
fi

echo "✅ Compilation successful!"

# Verify output files
FILE_COUNT=$(find "$DIST_DIR" -name "*.js" -type f | wc -l)

echo ""
echo "📊 Compilation Results:"
echo "  📁 Output directory: $DIST_DIR"
echo "  📄 JavaScript files generated: $FILE_COUNT"
echo "  📍 Destination: app/static/js/dist/*.js"

if [ "$FILE_COUNT" -gt 0 ]; then
    echo ""
    echo "📋 Generated files:"
    find "$DIST_DIR" -name "*.js" -type f | sort | while read file; do
        basename=$(basename "$file")
        echo "    ✓ $basename"
    done
else
    echo "⚠️  Warning: No JavaScript files were generated!"
fi

echo ""
echo "🎉 Build complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Update HTML imports to use 'js/dist/' directory"
echo "  2. Run tests: pytest tests/"
echo "  3. Test in browser"
