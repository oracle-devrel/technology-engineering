#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

help() {
    echo "List of Apps:"
    for APP_DIR in `ls -d app* | sort -g`; do
      echo "-- APP: $APP_DIR -------------------------------------------"
      sudo systemctl status $APP_DIR --no-pager
    done 
    echo    
    echo "Command:"
    echo "- Help : ./helper.sh "
    echo "- App  : ./helper.sh <start/stop/restart/status> <app>"
}

APP_DIR=$2
if [ "$1" == "" ] || [ "$1" == "info" ]; then
  help
elif [ "$1" == "start" ]; then
  sudo systemctl start $APP_DIR
elif [ "$1" == "stop" ]; then
  sudo systemctl stop $APP_DIR
elif [ "$1" == "restart" ]; then
  sudo systemctl restart $APP_DIR
elif [ "$1" == "status" ]; then
  if [ "$APP_DIR" == "" ]; then
    for APP_DIR in `ls -d app* | sort -g`; do
      sudo systemctl status $APP_DIR --no-pager
    done 
  else
    sudo systemctl status $APP_DIR --no-pager
  fi
else
  help
  echo
  echo "ERROR: Unknown command: $1"
fi 
