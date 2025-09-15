Write-Host "Stopping TaskRunnerX services..."

# Kill processes
Get-Process | Where-Object {$_.ProcessName -like "*uvicorn*"} | Stop-Process -Force
Get-Process | Where-Object {$_.CommandLine -like "*taskrunnerx*"} | Stop-Process -Force

docker-compose down

Write-Host "Services stopped."
