#!/bin/bash

export LC_ALL=C

cat jold | cut -f1 | sort | uniq > cold
cat jnew | cut -f1 | sort | uniq > cnew

cat jold jnew | sort | uniq -d > jdup
cat jold jdup | sort | uniq -u > jolduniq
cat jnew jdup | sort | uniq -u > jnewuniq

cat cold cnew | sort | uniq -d > cdup
cat cold cdup | sort | uniq -u > colduniq
cat cnew cdup | sort | uniq -u > cnewuniq

python filter.py
