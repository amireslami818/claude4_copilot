# GitHub Push Guide - Football Bot Project

This guide explains how to properly commit and push changes to the GitHub repository, especially when dealing with large files and Git LFS (Large File Storage).

## Quick Reference Commands

```bash
# 1. Configure Git (one-time setup)
git config --global user.name "alextrx818"
git config --global user.email "alextrx818@users.noreply.github.com"

# 2. Set correct remote URL
git remote set-url origin https://github.com/alextrx818/Copilot_Claude4.git

# 3. Standard push workflow
git status                    # Check what's changed
git add .                     # Add all changes
git commit -m "Your message"  # Commit with descriptive message
git push origin main          # Push to GitHub
```

## Common Issues and Solutions

### Problem 1: Permission Denied (SSH)
**Error:** `Permission denied (publickey)`

**Solution:** Switch to HTTPS authentication
```bash
git remote set-url origin https://github.com/alextrx818/Copilot_Claude4.git
```

### Problem 2: Git LFS Objects Not Found
**Error:** `Your push referenced at least X unknown Git LFS objects`

**Solution:** Push LFS objects first, then regular commits
```bash
git lfs push --all origin     # Push large files first
git push origin main          # Then push regular commits
```

### Problem 3: Wrong Remote Repository
**Error:** Repository doesn't exist or access denied

**Solution:** Verify and update remote URL
```bash
git remote -v                 # Check current remote
git remote set-url origin https://github.com/alextrx818/Copilot_Claude4.git
```

## Step-by-Step Push Process

### 1. Initial Setup (One-time only)
```bash
# Configure your Git identity
git config --global user.name "alextrx818"
git config --global user.email "alextrx818@users.noreply.github.com"

# Set the correct remote repository
git remote set-url origin https://github.com/alextrx818/Copilot_Claude4.git

# Verify remote is correct
git remote -v
```

### 2. Check Current Status
```bash
# See what files have changed
git status

# See what commits are ahead/behind
git log --oneline -5
```

### 3. Add and Commit Changes
```bash
# Add all changes
git add .

# Or add specific files
git add filename1.json filename2.py

# Commit with descriptive message
git commit -m "Update football bot data - latest pipeline run"

# Check status after commit
git status
```

### 4. Push to GitHub
```bash
# Standard push
git push origin main

# If LFS errors occur, push LFS first
git lfs push --all origin
git push origin main
```

## Understanding Git LFS in This Project

This project uses Git LFS for large JSON data files (like `step1.json`, `step4.json`, etc.) that can be 40MB+ in size.

### Files Tracked by LFS:
- `*.json` files over 100MB
- Large data output files
- Binary files

### LFS Commands:
```bash
# Check LFS status
git lfs status

# Push all LFS objects
git lfs push --all origin

# See which files are tracked by LFS
git lfs ls-files
```

## Troubleshooting Authentication

### For HTTPS (Recommended)
When pushing, Git will prompt for:
- **Username:** `alextrx818`
- **Password:** Your GitHub personal access token (not your account password)

### Creating a Personal Access Token:
1. Go to GitHub.com → Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` permissions
3. Copy and save the token securely
4. Use this token as your password when prompted

## Common Workflow Examples

### After Making Code Changes:
```bash
git status
git add .
git commit -m "Fix: Improve error handling in step2 processor"
git push origin main
```

### After Pipeline Data Updates:
```bash
git status
git add step*.json
git commit -m "Data: Update football match data - $(date +%Y-%m-%d)"
git push origin main
```

### Emergency: Force Push (Use Carefully):
```bash
# Only if you're sure and working alone
git push --force origin main
```

## Repository Structure

```
Copilot_Claude4/
├── Football_bot/           # Main project directory
│   ├── step1.json         # Large LFS file (~40MB)
│   ├── step2/
│   │   └── step2.json     # Large LFS file
│   ├── step3/
│   │   └── step3.json     # Large LFS file
│   ├── continuous_orchestrator.py
│   ├── health_monitor.py
│   └── ...
└── .gitattributes         # LFS configuration
```

## Best Practices

### 1. Commit Messages
- Use descriptive messages
- Include what was changed and why
- Examples:
  - `"Fix: Resolve API timeout in step1 data fetcher"`
  - `"Data: Update match results for May 30, 2025"`
  - `"Feature: Add health monitoring alerts"`

### 2. Before Pushing
- Always run `git status` first
- Check that you're on the correct branch (`main`)
- Verify remote is correct (`git remote -v`)

### 3. After Errors
- Read the error message carefully
- Check if it's an LFS issue (push LFS first)
- Verify authentication and permissions
- Ensure repository URL is correct

## Emergency Recovery

### If Push is Rejected:
```bash
# Pull latest changes first
git pull origin main

# Resolve any conflicts
# Then push again
git push origin main
```

### If Repository is Out of Sync:
```bash
# Fetch latest from GitHub
git fetch origin

# Reset to match GitHub (WARNING: loses local changes)
git reset --hard origin/main

# Or merge changes
git merge origin/main
```

## Contact and Support

- **Repository:** https://github.com/alextrx818/Copilot_Claude4.git
- **Username:** alextrx818
- **Project:** Football Bot - Multi-Step Data Processing Pipeline

## Version History

- **v1.0** (May 30, 2025): Initial push guide created
- Covers basic Git operations, LFS handling, and authentication

---

**Note:** Always ensure you have proper authentication set up before attempting to push to GitHub. Keep your personal access token secure and never share it publicly.
