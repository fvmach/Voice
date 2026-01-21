#!/bin/bash

# Robust Node.js build script for Render
# This script ensures all Node.js dependencies are properly installed

echo "🚀 Starting Node.js build process..."

# Navigate to Conversations directory
cd Conversations || { echo "❌ Failed to find Conversations directory"; exit 1; }

echo "📍 Current directory: $(pwd)"
echo "📁 Contents: $(ls -la)"

# Clean any existing node_modules and package-lock
echo "🧹 Cleaning previous installations..."
rm -rf node_modules package-lock.json
rm -rf client/node_modules client/package-lock.json

# Install backend dependencies
echo "📦 Installing backend dependencies..."
npm cache clean --force
npm install --production --no-optional --verbose

# Check if express was installed
if [ ! -d "node_modules/express" ]; then
    echo "❌ Express not found, forcing installation..."
    npm install express cors dotenv helmet morgan multer twilio uuid --save
fi

# Install client dependencies
echo "📦 Installing client dependencies..."
cd client || { echo "❌ Failed to find client directory"; exit 1; }
npm install --production --no-optional --verbose

# Build the React app
echo "⚛️ Building React frontend..."
npm run build

# Return to parent directory
cd ..

echo "✅ Node.js build completed successfully!"
echo "📁 Backend modules: $(ls -la node_modules | wc -l) packages"
echo "📁 Frontend build: $(ls -la client/build 2>/dev/null | wc -l) files"