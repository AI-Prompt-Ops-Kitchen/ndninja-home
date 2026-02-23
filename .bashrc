export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/.npm-global/bin:$PATH"
export PATH=/home/ndninja/.opencode/bin:$PATH
. "$HOME/.cargo/env"

# Load API keys from .env (gitignored)
[ -f "$HOME/.env" ] && set -a && source "$HOME/.env" && set +a

# CLI tools (zoxide + eza)
eval "$(zoxide init bash)"
alias lg='lazygit'
alias ls='eza --icons --group-directories-first'
alias ll='eza --icons --group-directories-first -la'
alias lt='eza --icons --group-directories-first --tree --level=2'
