#!/usr/bin/env bash
sudo docker run --rm -it -v "$(pwd)":/data -p 8877:8080 maptiler/tileserver-gl:latest
