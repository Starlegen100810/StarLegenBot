# ----- watch-and-push.ps1 -----
$folder = "C:\StarLegenBot"

Write-Host "Watching $folder ... Ctrl+C to stop."

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $folder
$watcher.Filter = "*.py"
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

# Action on change
$action = {
    Write-Host "[$(Get-Date -Format T)] Change detected, pushing to GitHub..."
    git add .
    git commit -m "Auto update" --allow-empty
    git push
}

# Register event handlers
Register-ObjectEvent $watcher Changed -Action $action | Out-Null
Register-ObjectEvent $watcher Created -Action $action | Out-Null
Register-ObjectEvent $watcher Deleted -Action $action | Out-Null
Register-ObjectEvent $watcher Renamed -Action $action | Out-Null

# Keep alive
while ($true) { Start-Sleep -Seconds 5 }
