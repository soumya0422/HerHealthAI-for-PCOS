param(
    [string]$remote = "https://github.com/soumya0422/HerHealthAI.git",
    [string]$branch = "main"
)

# Usage: ./push_repo.ps1 -remote <git_url>

function ExitWith($msg) {
    Write-Error $msg
    exit 1
}

# Check git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    ExitWith "git is not installed or not in PATH. Please install git (https://git-scm.com/) and rerun this script."
}

# Ensure .gitignore exists
if (-not (Test-Path .gitignore)) {
    @"
.env
artifacts/
__pycache__/
*.pyc
.vscode/
*.sqlite
"@ | Out-File -Encoding utf8 .gitignore
}

# Initialize repo if needed
if (-not (Test-Path .git)) {
    git init
}

# Add and commit
git add .

# If there are no commits yet, create initial commit
$hasCommit = $false
try {
    git rev-parse --verify HEAD > $null 2>&1
    $hasCommit = $true
} catch {
    $hasCommit = $false
}

if (-not $hasCommit) {
    git commit -m "Initial commit: Streamlit frontend + FastAPI backend (do not commit secrets)" --allow-empty
} else {
    try {
        git commit -m "Update project"
    } catch {
        Write-Output "No changes to commit"
    }
}

# Set remote
$existing = git remote get-url origin 2>$null
if ($existing) {
    Write-Output "Remote 'origin' already set to $existing"
    if ($existing -ne $remote) {
        Write-Output "Updating remote 'origin' to $remote"
        git remote remove origin
        git remote add origin $remote
    }
} else {
    git remote add origin $remote
}

# Push
Write-Output "Pushing to $remote on branch $branch (you may be prompted for credentials)..."
try {
    git branch -M $branch
    git push -u origin $branch
    Write-Output "Push complete."
} catch {
    ExitWith "Push failed: $_"
}
