#!/bin/sh

tests=(\
	examples/c1.py\
	examples/b1.py\
	examples/pdb1.py\
	examples/cu1.py\
	examples/pdbwa1.py\
);
for t in ${tests[@]}; do
	pytest $t -s;
	[ "$?" -eq 1 ] && exit 1;
done
exit 0;
