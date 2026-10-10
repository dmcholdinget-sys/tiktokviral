export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$PWD/.local/browsers}"
# Load local defaults without overwriting injected environment bindings.
# Values are literal strings; shell expansion and command substitution are never evaluated.
while IFS='=' read -r setup_name setup_value || [ -n "$setup_name" ]; do
  if [[ "$setup_name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] && [[ ! -v "$setup_name" ]]; then
    export "$setup_name=$setup_value"
  fi
done < .env
unset setup_name setup_value
