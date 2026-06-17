# Script to start all EPM System services on a Windows OS.
# In FSDR Script Parameters field provide path to the script, ie: /home/opc/fsdrscripts/start_services.sh
# In FSDR Script User field enter: opc

# Stop OHS

cd $MIDDLEWARE_HOME/user_projects/epmsystem1/httpConfig/ohs/bin
./stopComponent.sh ohs_component

# Delay after stopping OHS
sleep 20

# Stop Node Manager
cd $MIDDLEWARE_HOME/user_projects/epmsystem1/httpConfig/ohs/bin
./stopNodemanager.sh

# Delay after stopping Node Manager
sleep 20

# Stop Managed Servers in EPMSystem1
cd $MIDDLEWARE_HOME/user_projects/epmsystem1/bin/
./stop.sh

# Delay after stopping Managed Servers
sleep 120

# Stop WebLogic Server
cd $MIDDLEWARE_HOME/user_projects/domains/EPMSystem/bin
./stopWeblogic.sh

# Delay after stopping Managed Servers
sleep 60
