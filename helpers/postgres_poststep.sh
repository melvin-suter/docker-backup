#!/bin/bash

docker exec $1 bash -c 'rm -f $PGDATA/dump.sql'