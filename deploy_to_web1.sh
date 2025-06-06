# upload codebase to remote server with rsync
# source: ./
# destination: /opt/deploy_dashboard/
# exclude: .venv/, .vscode/, .DS_Store

# rsync options:
# -a: archive mode; equals -rlptgoD (no -H,-A,-X)
# -v: verbose
# -z: compress file data during the transfer
# -h: output numbers in a human-readable format
# --no-o: omit owner
# --no-g: omit group
# --delete: delete extraneous files from destination dirs
# --rsync-path='sudo rsync': run rsync as root on the remote machine
# exclude: --exclude='pattern'
# rsync -avzh --no-o --no-g --delete --exclude='.venv/' --exclude='.vscode/' --exclude='.DS_Store' --rsync-path='sudo rsync' . web1:/opt/deploy_dashboard/
# rsync -avzh --no-o --no-g --exclude='data/' --exclude='.venv/' --exclude='.vscode/' --exclude='.git/' --exclude='.DS_Store' --exclude='__pycache__' --rsync-path='sudo rsync' . web1:/opt/deploy_dashboard/
rsync -avzh \
  --no-o --no-g \
  --exclude='.venv/' \
  --exclude='data/' \
  --exclude='.vscode/' \
  --exclude='.DS_Store' \
  --exclude='__pycache__' \
  . henry.lin@web1:/opt/deploy_dashboard/