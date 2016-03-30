#!/bin/bash
cd `dirname $0`
if [[ pipe.java -nt pipe.class ]]; then
	javac -cp "./*:./" pipe.java 
fi
java -Xmx2g -cp "./*:./" pipe
