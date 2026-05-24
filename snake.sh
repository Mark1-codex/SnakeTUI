#!/bin/bash
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
source "$SCRIPT_DIR/.venv/bin/activate.fish"
sudo TERM=xterm-256color "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/snake.py"