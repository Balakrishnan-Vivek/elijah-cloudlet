#!/bin/bash

wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
gunzip GeoLiteCity.dat.gz
mkdir -p ./register_server/ds/network/db/
mv GeoLiteCity.dat ./register_server/ds/network/db/
