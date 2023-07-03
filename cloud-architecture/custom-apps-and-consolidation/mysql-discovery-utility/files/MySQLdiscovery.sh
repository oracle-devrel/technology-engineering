#!/bin/bash
#############################################################
--# Copyright (c) 2023, Oracle and/or its affiliates.
--# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
--# Purpose: Discovery Script for MySQL Databases. 
--# This script is to be executed at the discovery phase before planning for migration/upgrade.
--# Version  :  1.1
--# USAGE    :  sh <filename.sh> .
--# @author: Ajay Rao.
##############################################################

NOW=$(date +"%m")
TIMESTAMP=$(date +"%F")

#. ./setmy.env

cd /tmp
cat /dev/null > DB_REPORT.html

printf '<b><u><font size="9" color="RED"><center>' >> DB_REPORT.html
printf 'MySQL POC  DATABASE SERVER AND INSTANCE DETAILS</center></b></u></font>' >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html


printf '<b><p align="right"><font color="MidnightBlue"> ' >>DB_REPORT.html
date >> DB_REPORT.html
printf '</p></font></b>' >> DB_REPORT.html


printf '<b><p><font size="6" color="Orange"><b><p align="left">  Server Details :- </p></font></b> ' >> DB_REPORT.html
printf '<font color="MidnightBlue"><b><p align="left">  HOSTNAME NAME  ' >> DB_REPORT.html
hostname  >> DB_REPORT.html


printf '<br>' >> DB_REPORT.html
printf ' IP ADDRESS        ' >>DB_REPORT.html
hostname -i >> DB_REPORT.html
printf '</b></font></p>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">  Source Operating System and Version details  </p></b></font>' >>DB_REPORT.html
printf '<pre>' >> DB_REPORT.html
cat /etc/os-release | grep CPE_NAME >> DB_REPORT.html
printf '</b></font></pre></p>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">  Source Kernel version details  </p></b></font>' >>DB_REPORT.html
printf '<pre>' >> DB_REPORT.html
uname -a >> DB_REPORT.html
printf '</b></font></pre></p>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">  CPU DETAILS   </p></b></font>' >>DB_REPORT.html
printf '<pre>' >> DB_REPORT.html
lscpu | grep -i Architecture  >> DB_REPORT.html
lscpu | grep -i mode >> DB_REPORT.html
lscpu | grep -i list >> DB_REPORT.html
lscpu | grep -i family >> DB_REPORT.html
lscpu | grep -i MHz >> DB_REPORT.html
lscpu | grep -i Thread >> DB_REPORT.html
lscpu | grep -i Socket >> DB_REPORT.html
printf '</b></font></pre></p>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">  CPU USAGE  </p></b></font>' >>DB_REPORT.html
printf '<pre>' >> DB_REPORT.html
mpstat 2 2  >> DB_REPORT.html
printf '</b></font></pre></p>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">  MEMORY DETAILS  </p></b></font>' >>DB_REPORT.html
printf '<pre>' >> DB_REPORT.html
free -m >> DB_REPORT.html
printf '</b></font></pre></p>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">  FILE SYSTEM DETAILS  </p></b></font>' >>DB_REPORT.html
printf '<pre>' >> DB_REPORT.html
df -h /usr >> DB_REPORT.html
#For Data Directory and binlogs
df -h /var/lib/mysql>> DB_REPORT.html
df -h /           >> DB_REPORT.html
printf '</b></font></pre></p>' >> DB_REPORT.html


printf '<font color="MidnightBlue"><b><p align="left">  CRON DETAILS  </p></b></font>' >>DB_REPORT.html
printf '<pre>' >> DB_REPORT.html
service crond status >> DB_REPORT.html
crontab -l >> DB_REPORT.html
printf '</b></font></pre></p>' >> DB_REPORT.html

#MySQL DB details

dbuser=$1
dbpwd=$2

printf '<b><p><font size="6" color="Orange"><b><p align="left">  MYSQL Database Details :- </p></font><b> ' >> DB_REPORT.html
printf '<font color="MidnightBlue"><b><p align="left">  DATABASES </p></b></font>' >>DB_REPORT.html
printf '<pre>' >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -N -e "show databases;"  >> DB_REPORT.html
printf '</b></font>' >> DB_REPORT.html
printf '</pre></p>' >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">   MYSQL SERVER STATUS </p></b></font>' >> DB_REPORT.html
printf '<pre>' >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -N -e "\s\G" >> DB_REPORT.html
printf '</b></font></pre></p>' >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html


printf '<font color="MidnightBlue"><b><p align="left">   TOTAL SIZE OF ALL DATABASES </p></b></font>'  >> DB_REPORT.html
#printf '<br>' >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -H -e "SELECT   table_schema, ROUND(SUM(data_length+index_length)/1024/1024) AS total_mb, ROUND(SUM(data_length)/1024/1024) AS data_mb, ROUND(SUM(index_length)/1024/1024) AS index_mb, COUNT(*) AS tables, CURDATE() AS today FROM     information_schema.tables where table_schema not in ('information_schema','sys','mysql','performance_schema') GROUP BY table_schema ORDER BY 2 DESC;" >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">   CHARACTER SET OF POC DATABASE </p></b></font>' >> DB_REPORT.html
#printf '<br>' >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -H -e "SELECT SCHEMA_NAME,DEFAULT_CHARACTER_SET_NAME,DEFAULT_COLLATION_NAME FROM information_schema.SCHEMATA where SCHEMA_NAME not in ('information_schema','sys','mysql','performance_schema');" >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">   DEFAULT STORAGE ENGINE OF POC DATABASE </p></b></font>' >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -H -e "select ENGINE,SUPPORT,COMMENT,TRANSACTIONS, SAVEPOINTS from information_schema.engines where SUPPORT='DEFAULT';" >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">   REPLICATION STATUS OF POC DATABASE </p></b></font>' >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -H -e "SELECT SERVICE_STATE FROM performance_schema.replication_connection_status;" >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -H -e "SELECT SERVICE_STATE FROM performance_schema.replication_applier_status;" >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">   VIEW DETAILS OF POC MySQL INSTANCE </p></b></font>' >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -H -e " select * from information_schema.tables where table_type='VIEW' and TABLE_SCHEMA != 'sys';" >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">   PARTITIONING DETAILS OF POC MySQL INSTANCE </p></b></font>' >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -H -e " select TABLE_SCHEMA,TABLE_NAME,PARTITION_NAME from information_schema.PARTITIONS where TABLE_SCHEMA not in ('information_schema','sys','mysql','performance_schema') ;" >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">   BACKUP DETAILS OF BASH2 MySQL DATABASE INSTANCE </p></b></font>' >> DB_REPORT.html
#printf '<pre>' >> DB_REPORT.html
ls -lrth /root/Ajay/backups/*.sql | tail >>DB_REPORT.html

#ls -lrth $BACKUP_DIR/mysql*.gz >>DB_REPORT.html
printf '</pre><br>' >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html

#printf '<font color="MidnightBlue"><b><p align="left">   MYSQL INSTANCE GLOBAL VARIABLES </p></b></font>' >> DB_REPORT.html
#printf '<pre>' >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -N -e "show global variables" | sed 's/\t/","/g;s/^/"/;s/$/"/' > /tmp/globalvariables.csv
sed -i -e '1i"Variable","Value"' /tmp/globalvariables.csv
#printf '</b></font></pre></p>' >> DB_REPORT.html
#printf '<br>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">   CLUSTER STATUS OF POC DATABASE </p></b></font>' >> DB_REPORT.html
grep -e address -e cluster /etc/my.cnf >> DB_REPORT.html
#mysql -u$dbuser -p$dbpwd -H -e "show status --cluster" >> DB_REPORT.html
#mysql -u$dbuser -p$dbpwd -H -e "show status --operation" >> DB_REPORT.html
#mysql -u$dbuser -p$dbpwd -H -e "show status --process" >> DB_REPORT.html
#mysql -u$dbuser -p$dbpwd -H -e "show status --progress" >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -H -e "show status \G" >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">   GALERA CLUSTER STATUS OF MySQL Instance </p></b></font>' >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -H -e "SHOW GLOBAL STATUS LIKE 'wsrep_%';" >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">   MASTER_SLAVE Information OF MySQL Instance </p></b></font>' >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -H -e "show master status\G;" >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -H -e "show slave status \G;" >> DB_REPORT.html
mysql -u$dbuser -p$dbpwd -H -e "show slave hosts;" >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html

printf '<font color="MidnightBlue"><b><p align="left">   Table Repairs check Information OF MySQL Instance </p></b></font>' >> DB_REPORT.html
mysqlcheck -c -u$dbuser -p$dbpwd --all-databases >> DB_REPORT.html
printf '<br>' >> DB_REPORT.html

printf '<br>' >> DB_REPORT.html

printf '<b><font size="6" color="RED"><center> ------------End Health Check Report------------ </center></b></font>' >> DB_REPORT.html

