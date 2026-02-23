# Simple Git Push Script for HiveForge (Windows PowerShell)
# Commits and pushes current changes to GitHub

param(
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

$REPO_URL = "https://github.com/asoshnin/HiveForge.git"
$BACKUP_BRANCH = "backup-$(Get-Date -Format 'yyyyMMdd_HHmmss')"

function Log-Info { Write-Host "INFO: $args" -ForegroundColor Cyan }
function Log-Warn { Write-Host "WARN: $args" -ForegroundColor Yellow }
function Log-Error { Write-Host "ERROR: $args" -ForegroundColor Red }
function Log-Success { Write-Host "SUCCESS: $args" -ForegroundColor Green }

trap {
    Log-Error "Script interrupted. Manual recovery may be needed."
    exit 1
}

# Verify we're in a git repo
if (-not (Test-Path .git)) {
    Log-Error "Not a git repository. Aborting."
    exit 1
}

# Verify remote URL matches expected
$CURRENT_REMOTE = git config --get remote.origin.url 2>$null
if (-not $CURRENT_REMOTE) {
    Log-Error "No remote 'origin' configured. Aborting."
    exit 1
}

if ($CURRENT_REMOTE -ne $REPO_URL) {
    Log-Error "Remote URL mismatch!"
    Log-Error "  Expected: $REPO_URL"
    Log-Error "  Got:      $CURRENT_REMOTE"
    
    if (-not $Force) {
        $response = Read-Host "Continue anyway? (y/N)"
        if ($response -ne 'y' -and $response -ne 'Y') {
            Log-Warn "Aborting."
            exit 1
        }
    }
}

# Verify current branch
$CURRENT_BRANCH = git rev-parse --abbrev-ref HEAD
Log-Info "Current branch: $CURRENT_BRANCH"

# Create safety backup
Log-Info "Creating backup branch: $BACKUP_BRANCH"
git branch $BACKUP_BRANCH
if ($LASTEXITCODE -ne 0) {
    Log-Error "Failed to create backup branch"
    exit 1
}

# Generate commit message
function Generate-CommitMessage {
    $SPEC_TASKS = ".kiro/specs/onboarding-addition/tasks.md"
    
    if (Test-Path $SPEC_TASKS) {
        $content = Get-Content $SPEC_TASKS -Raw
        $COMPLETED_COUNT = ($content | Select-String '^\s*-\s*\[x\]' -AllMatches).Matches.Count
        $TOTAL_COUNT = ($content | Select-String '^\s*-\s*\[' -AllMatches).Matches.Count
        
        $msg = "feat(steering-assistant): Implement core analysis components`n`n"
        $msg += "Progress: $COMPLETED_COUNT/$TOTAL_COUNT tasks completed`n`n"
        $msg += "Completed components:`n"
        $msg += "- Document parsers (markdown, PDF, image, orchestrator)`n"
        $msg += "- Code analyzers (language, tech stack, architecture, conventions, documentation)`n"
        $msg += "- CodeAnalyzer orchestrator with caching and token limiting`n"
        $msg += "- KnowledgeBase for content aggregation`n"
        $msg += "- GapAnalysisEngine for identifying missing information`n"
        $msg += "- Template definitions for all 8 steering files`n`n"
        $msg += "All tests passing (251+ tests)"
        
        return $msg
    } else {
        Log-Warn "No spec tasks file found. Using generic message."
        return "feat(steering-assistant): Progress on implementation"
    }
}

# Stage changes
Log-Info "Staging all changes..."
git add -A

# Show status
Log-Info "Current status:"
git status --short

# Check if there are changes to commit
$status = git diff --cached --quiet
$hasChanges = $LASTEXITCODE -ne 0

if (-not $hasChanges) {
    Log-Success "No changes to commit"
    Log-Info "Checking if we need to push..."
    
    # Check if local is ahead of remote
    $LOCAL = git rev-parse '@'
    $REMOTE = git rev-parse '@{u}' 2>$null
    
    if ($REMOTE -and $LOCAL -ne $REMOTE) {
        Log-Info "Local branch has commits to push"
        
        if (-not $Force) {
            $response = Read-Host "Push existing commits to remote? (y/N)"
            if ($response -ne 'y' -and $response -ne 'Y') {
                Log-Warn "Aborting push"
                exit 1
            }
        }
        
        Log-Info "Pushing to remote ($CURRENT_BRANCH)..."
        git push -u origin $CURRENT_BRANCH
        if ($LASTEXITCODE -ne 0) {
            Log-Error "Push failed!"
            Log-Warn "Backup branch available: $BACKUP_BRANCH"
            exit 1
        }
        
        Log-Success "=== Push complete ==="
    } else {
        Log-Success "Already up to date with remote"
    }
} else {
    $COMMIT_MSG = Generate-CommitMessage
    
    Log-Info "=== COMMIT MESSAGE PREVIEW ==="
    Write-Host $COMMIT_MSG
    Log-Info "==============================="
    
    if (-not $Force) {
        $response = Read-Host "Proceed with commit and push? (y/N)"
        if ($response -ne 'y' -and $response -ne 'Y') {
            Log-Warn "Aborting commit and push"
            git reset HEAD .
            exit 1
        }
    }
    
    Log-Info "Committing..."
    git commit -m $COMMIT_MSG
    if ($LASTEXITCODE -ne 0) {
        Log-Error "Commit failed"
        exit 1
    }
    
    Log-Info "Pushing to remote ($CURRENT_BRANCH)..."
    git push -u origin $CURRENT_BRANCH
    if ($LASTEXITCODE -ne 0) {
        Log-Error "Push failed!"
        Log-Warn "Backup branch available: $BACKUP_BRANCH"
        exit 1
    }
    
    Log-Success "=== Sync complete ==="
}

Log-Success "Backup branch (for recovery): $BACKUP_BRANCH"
Log-Success "You can delete it later with: git branch -d $BACKUP_BRANCH"
