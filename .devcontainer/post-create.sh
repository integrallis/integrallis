#!/bin/bash

set -e

echo "Setting up Integrallis development environment..."

# Navigate to workspace
cd /workspace

# ============================================================
# Install Claude Code CLI
# ============================================================
echo "Updating npm and installing Claude Code CLI..."
npm install -g npm@latest
npm install -g @anthropic-ai/claude-code

# Configure Claude Code with dangerously-skip-permissions by default
echo "Configuring Claude Code..."
mkdir -p /home/vscode/.claude
cat > /home/vscode/.claude/settings.json << 'EOF'
{
  "permissions": {
    "allow": [
      "Bash(*)",
      "Read(*)",
      "Write(*)",
      "Edit(*)",
      "Grep(*)",
      "Glob(*)",
      "WebFetch(*)",
      "WebSearch(*)",
      "TodoWrite(*)",
      "NotebookEdit(*)"
    ],
    "deny": []
  },
  "autoApprove": true
}
EOF

# Create convenience alias for claude with --dangerously-skip-permissions
echo 'alias claude="claude --dangerously-skip-permissions"' >> /home/vscode/.bashrc
echo 'alias claude="claude --dangerously-skip-permissions"' >> /home/vscode/.zshrc 2>/dev/null || true

echo ""
echo "============================================================"
echo "  Integrallis Dev Environment Ready!"
echo "============================================================"
echo ""
echo "Claude Code is installed and configured with --dangerously-skip-permissions"
echo "Just run: claude"
echo ""
