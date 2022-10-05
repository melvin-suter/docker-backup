#!/bin/bash

docker exec $1 bash -c '/usr/bin/mysqldump --all-databases --password="$MYSQL_ROOT_PASSWORD" > /var/lib/mysql/dump.sql'