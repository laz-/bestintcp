#!/usr/bin/make

__init__.py: bestintcp.py
	awk 'BEGIN {output=1;} // {if (output) { print;}} /^# BEGIN bestinctp.py/ {output=0;}' < __init__.py > init.tmp
	cat init.tmp bestintcp.py > __init__.py
	rm init.tmp
