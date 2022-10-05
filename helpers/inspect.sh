#!/bin/bash

docker inspect -f '{{ .Mounts }}' $1 | sed -E 's;\[\{(.*)\}\];\1;' | sed -E 's;\} \{;\n;'