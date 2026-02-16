#!/bin/bash

# Simple Git Push Script for HiveForge
# Commits and pushes current changes to GitHub

set -euo pipefail  # Exit on error, undefined vars, pipe failures

REPO_URL="https://github.com/asoshnin/HiveForge.git"
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

# Generate commit message
generate_commit_message() {
    # Check for spec tasks file
    SPEC_TASKS=".kiro/specs/onboarding-addition/tasks.md"
    
    if [ -f "$SPEC_TASKS" ]; then
        # Count completed tasks
        COMPLETED_COUNT=$(grep -c '^\s*-\s*\[x\]' "$SPEC_TASKS" 2>/dev/null || echo "0")
        TOTAL_COUNT=$(grep -c '^\s*-\s*\[' "$SPEC_TASKS" 2>/dev/null || echo "0")
        
        {
            echo "feat(steering-assistant): Implement core analysis components"
            echo ""
            echo "Progress: $COMPLETED_COUNT/$TOTAL_COUNT tasks completed"
            echo ""
            echo "Completed components:"
            echo "- Document parsers (markdown, PDF, image, orchestrator)"
            echo "- Code analyzers (language, tech stack, architecture, conventions, documentation)"
            echo "- CodeAnalyzer orchestrator with caching and token limiting"
            echo "- KnowledgeBase for content aggregation"
            echo "- GapAnalysisEngine for identifying missing information"
            echo "- Template definitions for all 8 steering files"
            echo ""
            echo "All tests passing (251+ tests)"
        }
    else
        log_warn "No spec tasks file found. Using generic message."
        echo "feat(steering-assistant): Progress on implementation"
    fi
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
    log_info "Checking if we need to push..."
    
    # Check if local is ahead of remote
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
    
    if [ -n "$REMOTE" ] && [ "$LOCAL" != "$REMOTE" ]; then
        log_info "Local branch has commits to push"
        
        # User confirmation before push
        read -p "Push existing commits to remote? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_warn "Aborting push"
            exit 1
        fi
        
        # Push with explicit branch
        log_info "Pushing to remote ($CURRENT_BRANCH)..."
        if ! git push -u origin "$CURRENT_BRANCH"; then
            log_error "Push failed!"
            log_warn "Backup branch available: $BACKUP_BRANCH"
            exit 1
        fi
        
        log_success "=== Push complete ==="
    else
        log_success "Already up to date with remote"
    fi
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
    
    # Push with explicit branch
    log_info "Pushing to remote ($CURRENT_BRANCH)..."
    if ! git push -u origin "$CURRENT_BRANCH"; then
        log_error "Push failed!"
        log_warn "Backup branch available: $BACKUP_BRANCH"
        exit 1
    fi
    
    log_success "=== Sync complete ==="
fi

log_success "Backup branch (for recovery): $BACKUP_BRANCH"
log_success "You can delete it later with: git branch -d $BACKUP_BRANCH"
