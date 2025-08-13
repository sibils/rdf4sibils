#!/bin/bash

this_dir=$(dirname $0)
config_dir=$this_dir/../config

conf_file="${config_dir}/$(hostname).config"
if [ ! -f "$conf_file" ]; then
  echo Cannot find config file: $conf_file
  echo Trying to read default.config file
  conf_file="default.config"
  if [ ! -f "$conf_file" ]; then
    echo Error: cannot find config file: $conf_file
    exit 1
  fi
fi
source $conf_file

action=$1
host=$(hostname)
server=$FASTAPI_SERVER
port=$FASTAPI_PORT
scope=$FASTAPI_ROOT_PATH
workers=$FASTAPI_WORKERS
mypython=$FASTAPI_PYTHON

#pattern="gunicorn.main:app"
pattern="gunicorn"


if [ "$server" == "" ]; then
  server=$host
  echo "FASTAPI_SERVER undefined, set to default hostname"
fi
if [ "$workers" == "" ]; then
  workers=4
  echo "FASTAPI_WORKERS undefined, set to default (4)"
fi

echo ""
echo "conf_file : $conf_file"
echo "action    : $action"
echo "host      : $host"
echo "server    : $server"
echo "port      : $port"
echo "scope     : $scope"
echo "workers   : $workers"
echo "mypython  : $mypython"
echo "pattern   : $pattern"


if [ "$action" == "start" ]; then
  echo "Starting FASTAPI"
  gunicorn main:app --worker-class uvicorn.workers.UvicornWorker \
  --workers $workers  --bind $server:$port --timeout 600 \
  --daemon \
  --access-logfile cellapi.log --error-logfile cellapi.log --capture-output
  
  sleep 2
  #nohup $mypython main.py -s $server -p $port -r $scope -l True > cellapi.log 2>&1 &
  pids=$(pgrep -f $pattern)
  pretty_pids=$(echo $pids | tr '\n', ' ')
  echo "Started, FASTAPI process has pid(s) $pretty_pids"
  echo done

elif [ "$action" == "debug" ]; then
  echo "Starting FASTAPI mono worker, mode reload"
  $mypython main.py -s $server -p $port -r $scope -l True

elif [ "$action" == "status" ]; then
  pids=$(pgrep -f $pattern)
  if [ "$pids" == "" ]; then
    echo "Stopped, no FASTAPI process running"
    exit
  else
    pretty_pids=$(echo $pids | tr '\n', ' ')
    echo "Running, FASTAPI process has pid(s) $pretty_pids"
    exit
  fi

elif [ "$action" == "stop" ]; then
  echo "Stopping FASTAPI"
  pids=$(pgrep -f $pattern)
  if [ "$pids" == "" ]; then
    echo "Oups, found no process to kill"
    exit 3
  else
    pretty_pids=$(echo $pids | tr '\n', ' ')
    echo "Killing pid(s) $pretty_pids"
    kill $pids
    for T in 1 2 3 4 5 6 7 8 9 10; do
      pids=$(pgrep -f $pattern)
      if [ "$pids" == "" ]; then
        break;
      fi
      echo -e ".\c"
      sleep 1
    done
    echo "."
    pids=$(pgrep -f $pattern)
    if [ "$pids" != "" ]; then  
      pretty_pids=$(echo $pids | tr '\n', ' ')
      echo "Could not stop process $pretty_pids smoothly"
      echo "Killing -9 process(es) $pretty_pids"
      kill -9 $pids
      for T in 1 2 3 4 5 6 7 8 9 10; do
        pids=$(pgrep -f $pattern)
        if [ "$pids" == "" ]; then
          break;
        fi
        echo -e ".\c"
      done
      pids=$(pgrep -f $pattern)
      if [ "$pids" != "" ]; then  
        pretty_pids=$(echo $pids | tr '\n', ' ')
        echo "Oups, could not kill process(es) $pids"
        exit 4
      fi
    fi
    echo Done
  fi

else
  echo "Error: Don't know what to do, usage: $0 start|stop|status"
  exit 2
fi


