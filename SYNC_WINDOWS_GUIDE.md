# Windows Git Sync Guide

## Quick Start

**One-time setup:**
```powershell
# Allow script execution (run once)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**To sync your project:**
```powershell
# Navigate to your project
cd D:\Users\asosh\playground\_KIRO\HiveForge

# Run the sync script
.\sync.ps1
```

## What It Does

1. Verifies you're in a git repository
2. Creates a backup branch (for safety)
3. Stages all changes
4. Shows you a preview of the commit message
5. Asks for confirmation before committing
6. Pushes to GitHub

## Options

**Skip confirmations (auto-approve):**
```powershell
.\sync.ps1 -Force
```

## Troubleshooting

**"cannot be loaded because running scripts is disabled"**
- Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Then try again

**"Not a git repository"**
- Make sure you're in the correct folder with `.git` directory

**"No remote 'origin' configured"**
- Your repo doesn't have a GitHub remote set up
- Run: `git remote add origin https://github.com/yourusername/yourrepo.git`

## Comparison: sync.sh vs sync.ps1

| Feature | sync.sh (Mac/Linux) | sync.ps1 (Windows) |
|---------|-------------------|-------------------|
| Language | Bash | PowerShell |
| Backup branch | ✅ | ✅ |
| Confirmation prompts | ✅ | ✅ |
| Auto-commit message | ✅ | ✅ |
| Force flag | ❌ | ✅ (-Force) |

## Notes

- Both scripts create a backup branch before pushing (for recovery if needed)
- Delete backup branches later with: `git branch -d backup-YYYYMMDD_HHMMSS`
- The script works with any GitHub repository, not just HiveForge
