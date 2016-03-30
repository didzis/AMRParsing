#!/bin/bash
cd `dirname $0`
# stanforddir="./stanford-corenlp-*/"
# stanforddir=`echo $stanforddir`
stanforddir="./stanford-corenlp/"
# jsonjar="./json-*.jar"
# jsonjar=`echo $jsonjar`
# if [[ pipe.java -nt pipe.class ]]; then
	# javac -cp "$stanforddir*:$jsonjar:./" pipe.java 
	javac -cp "$stanforddir*:./*:./" pipe.java 
	if [ $? -ne 0 ]; then
		exit 1
	fi
# fi
java -Xmx2g -cp "$stanforddir*:./" pipe $*
