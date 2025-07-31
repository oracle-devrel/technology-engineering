# Script to start all EPM System services on a Windows OS.
# In FSDR Script Parameters field provide path to the script, ie: /home/opc/fsdrscripts/start_services.sh
# In FSDR Script User field enter: opc

# Start WebLogic Server
cd $MIDDLEWARE_HOME/user_projects/domains/EPMSystem/bin
./startWeblogic.sh

# Delay for WebLogic to fully start
sleep 300

# Start Managed Servers in EPMSystem1
cd $MIDDLEWARE_HOME/user_projects/epmsystem1/bin/
./start.sh

# Delay after starting Managed Servers
sleep 30

# Start Node Manager
cd $MIDDLEWARE_HOME/user_projects/epmsystem1/httpConfig/ohs/bin
./startNodemanager.sh

# Delay after starting Node Manager
sleep 30

# Start OHS
cd $MIDDLEWARE_HOME/user_projects/epmsystem1/httpConfig/ohs/bin
./startComponent.sh ohs_component
