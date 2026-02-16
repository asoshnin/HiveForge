#!/bin/bash

# Safe Git Sync Script for HiveForge
# SAFETY-CRITICAL: Confirms before destructive operations

set -euo pipefail  # Exit on error, undefined vars, pipe failures

REPO_URL="https://github.com/asoshnin/HiveForge.git"
TASKS_FILE="tasks.md"
BACKUP_BRANCH="backup-$(date +%Y%m%d_%H%M%S)"

trap 'echo "⚠️ Script interrupted. Manual recovery may be needed."; exit 1' INT TERM

log_info() { echo "ℹ️  $*"; }
log_warn() { echo "⚠️  $*" >&2; }
log_error() { echo "❌ $*" >&2; }
log_success() { echo "✅ $*"; }

# Verify we're in a git repo
if [ ! -d .git ]; then
    log_error "Not a git repository. Aborting."
    exit 1
fi

# Verify remote URL matches expected
CURRENT_REMOTE=$(git config --get remote.origin.url 2>/dev/null || echo "")
if [ -z "$CURRENT_REMOTE" ]; then
    log_error "No remote 'origin' configured. Aborting."
    exit 1
fi

if [ "$CURRENT_REMOTE" != "$REPO_URL" ]; then
    log_error "Remote URL mismatch!"
    log_error "  Expected: $REPO_URL"
    log_error "  Got:      $CURRENT_REMOTE"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warn "Aborting."
        exit 1
    fi
fi

# Verify current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log_info "Current branch: $CURRENT_BRANCH"

# Create safety backup
log_info "Creating backup branch: $BACKUP_BRANCH"
git branch "$BACKUP_BRANCH" || {
    log_error "Failed to create backup branch"
    exit 1
}

# Fetch remote
log_info "Fetching remote changes..."
if ! git fetch origin; then
    log_error "Failed to fetch from remote"
    exit 1
fi

# Stash with explicit verification
log_info "Stashing local changes..."
STASH_OUTPUT=$(git stash push -m "auto-stash before sync $(date +%Y%m%d_%H%M%S)" 2>&1) || {
    log_warn "No changes to stash (or stash failed): $STASH_OUTPUT"
}

# Pull with error handling
log_info "Pulling remote changes..."
if ! git pull --rebase origin "$CURRENT_BRANCH" 2>&1 | tee pull_output.txt; then
    log_error "Pull failed! Checking for conflicts..."
    if git diff --name-only --diff-filter=U | grep -q .; then
        log_error "MERGE CONFLICTS DETECTED!"
        log_error "Aborting rebase. Review conflicts manually:"
        git rebase --abort 2>/dev/null || true
        log_info "Restoring stash..."
        git stash pop 2>/dev/null || log_warn "Could not restore stash"
        exit 1
    else
        log_error "Unknown pull failure. Aborting."
        exit 1
    fi
fi

# Restore stash with explicit error handling
log_info "Restoring stashed changes..."
if [ -n "$STASH_OUTPUT" ] && echo "$STASH_OUTPUT" | grep -q "Saved working directory"; then
    if ! git stash pop; then
        log_error "Failed to restore stash! Stash is still available:"
        git stash list
        exit 1
    fi
fi

# Generate commit message
generate_commit_message() {
    if [ ! -f "$TASKS_FILE" ]; then
        log_warn "$TASKS_FILE not found. Using generic message."
        echo "WIP: Sync current state of Steering Assistant feature"
        return 0
    fi

    {
        echo "feat: Progress on Steering Assistant feature"
        echo ""
        echo "Completed tasks:"
        grep -E '^\s*-\s*\[x\]' "$TASKS_FILE" | sed 's/- \[x\] /- /' || true
    }
}

# Stage changes
log_info "Staging all changes..."
git add -A

# Show status
log_info "Current status:"
git status --short

# Check if there are changes to commit
if git diff --cached --quiet; then
    log_success "No changes to commit"
else
    COMMIT_MSG=$(generate_commit_message)
    
    log_info "=== COMMIT MESSAGE PREVIEW ==="
    echo "$COMMIT_MSG"
    log_info "==============================="
    
    # User confirmation before commit
    read -p "Proceed with commit and push? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warn "Aborting commit and push"
        git reset HEAD .
        exit 1
    fi
    
    log_info "Committing..."
    if ! git commit -m "$COMMIT_MSG"; then
        log_error "Commit failed"
        exit 1
    fi
fi

# Push with explicit branch
log_info "Pushing to remote ($CURRENT_BRANCH)..."
if ! git push -u origin "$CURRENT_BRANCH"; then
    log_error "Push failed!"
    log_warn "Backup branch available: $BACKUP_BRANCH"
    exit 1
fi

log_success "=== Sync complete ==="
log_success "Backup branch (for recovery): $BACKUP_BRANCH"
log_success "You can delete it later with: git branch -d $BACKUP_BRANCH"

rm -f pull_output.txt
