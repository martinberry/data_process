#!/bin/bash -ex

if [ $# -ne 2 ]; then
	echo "Error: src trg"
	exit 1
fi
src=$1
trg=$2
align=phrase_pair

run_anymalign=0
run_filter=1

if [ $run_anymalign -eq 1 ]; then
	date +"Time  %Y-%m-%d %H:%M:%S  anymalign"
	python anymalign.py -w -t 43200 -n 3 -N 12 -i 2 -S 5000000 ${src} ${trg} 1>${align} 2>log.anymalign.py &
fi

if [ $run_filter -eq 1 ]; then
	date +"Time  %Y-%m-%d %H:%M:%S  filter"
	python filter.py ${align}
fi

