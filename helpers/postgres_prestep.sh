#!/bin/bash

docker exec $1 bash -c 'pg_dumpall -c -U postgres > $PGDATA/dump.sql'