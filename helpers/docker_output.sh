#!/bin/bash

mkdir -p $1/docker_out
docker ps | tail -n+2 | awk '{print $1}' | xargs -I{} docker inspect -f '{{ .Mounts }}' {} > $1/docker_out/daily_$(date +%d)_volumes.txt
docker ps > $1/docker_out/daily_$(date +%d)_ps.txt
