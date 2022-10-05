#!/bin/bash

docker exec $1 bash -c 'rm -f /var/lib/mysql/dump.sql'