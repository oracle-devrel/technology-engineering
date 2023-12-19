conn sys/"Oracle_4U"@myoracledb:1521/sales_app_root as sysdba
alter pluggable database NORTH_APP_PDB close immediate; 
alter pluggable database EAST_APP_PDB close immediate; 
drop pluggable database NORTH_APP_PDB including datafiles; 
drop pluggable database EAST_APP_PDB including datafiles; 
conn / as sysdba
alter pluggable database SALES_APP_ROOT close immediate; 
drop pluggable database SALES_APP_ROOT including datafiles; 
exit