#ps1

# Script to start all EPM System services on a Windows OS.
# In FSDR Script Parameters field provide path to PowerShell and to the script, ie: C:\Windows\System32\WindowsPowerShell\v1.0\Powershell.exe c:\scripts\start_services.ps1
# FSDR Script User field leave empty, as it is not required for Windows OS scripts.

# Start WebLogic Server
cd C:\Oracle\Middleware\user_projects\domains\EPMSystem\bin
Start-Process -FilePath ".\startWeblogic.cmd"

# Delay for WebLogic to fully start
Start-Sleep -Seconds 300

# Start Managed Servers in EPMSystem1
cd C:\Oracle\Middleware\user_projects\epmsystem1\bin\
Start-Process -FilePath ".\start.bat"

# Delay after starting Managed Servers
Start-Sleep -Seconds 30

# Start Node Manager
cd C:\Oracle\Middleware\user_projects\epmsystem1\httpConfig\ohs\bin
Start-Process -FilePath ".\startNodemanager.cmd"

# Delay after starting Node Manager
Start-Sleep -Seconds 30

# Start OHS
cd C:\Oracle\Middleware\user_projects\epmsystem1\httpConfig\ohs\bin
Start-Process -FilePath ".\startComponent.cmd" -ArgumentList "ohs_component"
