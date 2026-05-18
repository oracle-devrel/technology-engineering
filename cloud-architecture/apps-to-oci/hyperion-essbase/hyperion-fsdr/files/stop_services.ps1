#ps1

# Script to start all EPM System services on a Windows OS.
# In FSDR Script Parameters field provide path to PowerShell and to the script, ie: C:\Windows\System32\WindowsPowerShell\v1.0\Powershell.exe c:\scripts\stop_services.ps1
# FSDR Script User field leave empty, as it is not required for Windows OS scripts.

# Stop OHS
cd C:\Oracle\Middleware\user_projects\epmsystem1\httpConfig\ohs\bin
Start-Process -FilePath ".\stopComponent.cmd" -ArgumentList "ohs_component"

# Delay
Start-Sleep -Seconds 30

# Stop Node Manager
cd C:\Oracle\Middleware\user_projects\epmsystem1\httpConfig\ohs\bin
Start-Process -FilePath ".\stopNodemanager.cmd"

# Delay
Start-Sleep -Seconds 30

# Stop Managed Servers in EPMSystem1
cd C:\Oracle\Middleware\user_projects\epmsystem1\bin\
Start-Process -FilePath ".\stop.bat"

# Delay
Start-Sleep -Seconds 120

# Stop WebLogic Server
cd C:\Oracle\Middleware\user_projects\domains\EPMSystem\bin
Start-Process -FilePath ".\stopWeblogic.cmd"

# Delay
Start-Sleep -Seconds 60
