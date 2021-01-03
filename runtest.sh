#!/bin/sh

tests=(\
	examples/c1.py\
	examples/b1.py\
	examples/pdb1.py\
	examples/cu1.py\
	examples/bwa1.py\
);
for t in ${tests[@]}; do
	pytest $t;
	[ "$?" -eq 1 ] && exit 1;
done
exit 0;
