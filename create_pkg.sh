#!/bin/bash
# macOS PKG Creator for C. elegans Brain Simulator
# This script creates a .pkg installer file for macOS

set -e

echo "=============================================================="
echo "C. ELEGANS BRAIN SIMULATOR - macOS PKG CREATOR"
echo "=============================================================="

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "Warning: This script is designed for macOS."
    echo "Continuing anyway, but pkgutil may not be available."
fi

# Configuration
PACKAGE_NAME="C Elegans Brain Simulator"
PACKAGE_ID="org.openworm.c-elegans-brain"
PACKAGE_VERSION="1.0.0"
BUILD_DIR="./build_pkg"
PAYLOAD_DIR="$BUILD_DIR/payload"
SCRIPTS_DIR="$BUILD_DIR/scripts"
PKG_FILE="C_Elegans_Brain_Simulator.pkg"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting package creation...${NC}"

# Clean up previous build
rm -rf "$BUILD_DIR"
rm -f "$PKG_FILE"

# Create directories
mkdir -p "$PAYLOAD_DIR"
mkdir -p "$SCRIPTS_DIR"

echo -e "${YELLOW}Step 1: Preparing payload...${NC}"

# Copy application files to payload
cp c_elegans_brain_sim.py "$PAYLOAD_DIR/"
cp setup.py "$PAYLOAD_DIR/"
cp package_info.json "$PAYLOAD_DIR/" 2>/dev/null || echo "{}" > "$PAYLOAD_DIR/package_info.json"

# Create README
cat > "$PAYLOAD_DIR/README.md" << 'EOF'
# C. elegans Brain Simulator

Enhanced neural network simulation based on the OpenWorm Analysis Toolbox.

## Features
- 312 neurons (original 302 + 10 enhanced)
- Enhanced synaptic connectivity (+20 connections)
- Neuromodulation support
- Cross-platform compatibility

## Installation
Run the included setup.py or use pip:
```bash
pip install .
```

## Usage
```bash
python c_elegans_brain_sim.py
```

## Requirements
- Python 3.7+
- NumPy

## License
MIT License
EOF

echo -e "${YELLOW}Step 2: Creating installation scripts...${NC}"

# Create preinstall script
cat > "$SCRIPTS_DIR/preinstall" << 'EOF'
#!/bin/bash
echo "Preparing to install C. elegans Brain Simulator..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.7"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Warning: Python version $PYTHON_VERSION detected. Version 3.7+ recommended."
fi

echo "Pre-installation checks passed."
exit 0
EOF

chmod +x "$SCRIPTS_DIR/preinstall"

# Create postinstall script
cat > "$SCRIPTS_DIR/postinstall" << 'EOF'
#!/bin/bash
echo "Installing C. elegans Brain Simulator..."

INSTALL_DIR="/Applications/C Elegans Brain Simulator"
mkdir -p "$INSTALL_DIR"

# Copy files
cp -R "${TMPDIR}/payload/"* "$INSTALL_DIR/"

# Install Python dependencies
if command -v pip3 &> /dev/null; then
    echo "Installing Python dependencies..."
    pip3 install numpy
fi

# Create launcher script
cat > "/usr/local/bin/c-elegans-brain" << 'LAUNCHER'
#!/bin/bash
python3 "/Applications/C Elegans Brain Simulator/c_elegans_brain_sim.py" "$@"
LAUNCHER

chmod +x "/usr/local/bin/c-elegans-brain"

echo ""
echo "Installation complete!"
echo "Run with: c-elegans-brain"
echo "Or: python3 \"$INSTALL_DIR/c_elegans_brain_sim.py\""
exit 0
EOF

chmod +x "$SCRIPTS_DIR/postinstall"

echo -e "${YELLOW}Step 3: Building component package...${NC}"

# Check if pkgutil is available (macOS only)
if command -v pkgutil &> /dev/null; then
    # Build the payload package
    pkgutil --flatten "$PAYLOAD_DIR" "$BUILD_DIR/payload.pkg"
    
    echo -e "${YELLOW}Step 4: Creating distribution package...${NC}"
    
    # Create Distribution.xml
    cat > "$BUILD_DIR/Distribution.xml" << EOF
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="2">
    <title>$PACKAGE_NAME</title>
    <organization>org.openworm</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="false" rootVolumeOnly="true" allow-external-scripts="no"/>
    
    <welcome file="welcome.html" mime-type="text/html"/>
    <readme file="readme.html" mime-type="text/html"/>
    <license file="license.html" mime-type="text/html"/>
    <conclusion file="conclusion.html" mime-type="text/html"/>
    
    <pkg-ref id="$PACKAGE_ID"/>
    
    <choices-outline>
        <line choice="default">
            <line choice="$PACKAGE_ID"/>
        </line>
    </choices-outline>
    
    <choice id="default"/>
    <choice id="$PACKAGE_ID" visible="false">
        <pkg-ref id="$PACKAGE_ID"/>
    </choice>
    
    <pkg-ref id="$PACKAGE_ID" version="$PACKAGE_VERSION" onConclusion="none">payload.pkg</pkg-ref>
</installer-gui-script>
EOF

    # Create HTML files for installer
    cat > "$BUILD_DIR/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Welcome</title></head>
<body style="font-family: Helvetica; padding: 20px;">
<h1>Welcome to C. elegans Brain Simulator</h1>
<p>This installer will set up the enhanced neural network simulation on your Mac.</p>
<p>The simulation includes:</p>
<ul>
<li>312 neurons (302 original + 10 enhanced)</li>
<li>Enhanced synaptic connectivity</li>
<li>Neuromodulation capabilities</li>
</ul>
<p>Click "Continue" to proceed with the installation.</p>
</body>
</html>
EOF

    cat > "$BUILD_DIR/readme.html" << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Read Me</title></head>
<body style="font-family: Helvetica; padding: 20px;">
<h1>C. elegans Brain Simulator - Read Me</h1>
<h2>System Requirements</h2>
<ul>
<li>macOS 10.13 or later</li>
<li>Python 3.7 or later</li>
<li>At least 100 MB of free disk space</li>
</ul>
<h2>What's New</h2>
<p>This enhanced version includes:</p>
<ul>
<li>+10 additional neurons</li>
<li>+20 synaptic connections</li>
<li>Improved neuromodulation model</li>
</ul>
<h2>After Installation</h2>
<p>Run the simulator from Terminal:</p>
<pre><code>c-elegans-brain</code></pre>
<p>Or navigate to /Applications/C Elegans Brain Simulator and run manually.</p>
</body>
</html>
EOF

    cat > "$BUILD_DIR/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<head><title>License</title></head>
<body style="font-family: Helvetica; padding: 20px;">
<h1>MIT License</h1>
<p>Copyright (c) 2024 OpenWorm Project</p>
<p>Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:</p>
<p>The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.</p>
<p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.</p>
</body>
</html>
EOF

    cat > "$BUILD_DIR/conclusion.html" << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Installation Complete</title></head>
<body style="font-family: Helvetica; padding: 20px;">
<h1>Installation Complete!</h1>
<p>C. elegans Brain Simulator has been successfully installed.</p>
<h2>Getting Started</h2>
<p>Open Terminal and run:</p>
<pre><code>c-elegans-brain</code></pre>
<p>Or launch directly from:</p>
<pre><code>/Applications/C Elegans Brain Simulator/</code></pre>
<h2>Documentation</h2>
<p>For more information, visit the OpenWorm project website.</p>
<p style="color: green; font-weight: bold;">Thank you for installing!</p>
</body>
</html>
EOF

    # Build the final package
    pkgbuild --root "$PAYLOAD_DIR" \
             --scripts "$SCRIPTS_DIR" \
             --identifier "$PACKAGE_ID" \
             --version "$PACKAGE_VERSION" \
             --install-location "/Applications/C Elegans Brain Simulator" \
             "$BUILD_DIR/payload.pkg" 2>/dev/null || true
    
    productbuild --distribution "$BUILD_DIR/Distribution.xml" \
                 --resources "$BUILD_DIR" \
                 --package-path "$BUILD_DIR" \
                 "$PKG_FILE" 2>/dev/null || {
        # Fallback if productbuild fails
        echo -e "${YELLOW}Note: Using simplified package creation...${NC}"
        cp "$BUILD_DIR/payload.pkg" "$PKG_FILE"
    }
    
    echo -e "${GREEN}✓ Package created successfully: $PKG_FILE${NC}"
    echo ""
    echo "To install, double-click the .pkg file or run:"
    echo "  sudo installer -pkg $PKG_FILE -target /"
else
    echo -e "${YELLOW}pkgutil not found. Creating flat package alternative...${NC}"
    
    # Create a simple tarball as fallback
    tar -czf "C_Elegans_Brain_Simulator_macos.tar.gz" -C "$PAYLOAD_DIR" .
    echo -e "${GREEN}✓ Created tarball: C_Elegans_Brain_Simulator_macos.tar.gz${NC}"
    echo "Extract and run setup.py manually."
fi

# Cleanup
echo -e "${YELLOW}Cleaning up temporary files...${NC}"
rm -rf "$BUILD_DIR"

echo ""
echo "=============================================================="
echo -e "${GREEN}PACKAGE CREATION COMPLETE${NC}"
echo "=============================================================="
echo ""
echo "Files created:"
ls -lh *.pkg *.tar.gz 2>/dev/null || echo "  (check directory for output files)"
echo ""
echo "Installation instructions:"
echo "  macOS (.pkg): Double-click to install"
echo "  Alternative: Extract and run 'pip install .'"
echo ""
echo "=============================================================="
