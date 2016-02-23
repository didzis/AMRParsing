#!/bin/bash

function usage {
	echo "Clean up after training/parsing (remove preprocessed intermediate data)"
    echo
    echo "usage: $0 [data/model dir or file] [dir or file] ..."
	echo
	echo "Default: will clean directory \"data\""
	echo
}

for arg in $@; do
    if [ "$arg" == "--help" ] || [ "$arg" == "-h" ]; then
        usage
        exit 0
    fi
done

for arg in $@; do
    if [ "$arg" == "--" ]; then
		break
	fi
    if [ "${arg: :1}" == "-" ]; then
		echo "error: unknown argument: $arg"
		exit 1
    fi
done

function clean {
	local base="$1"
	echo "Cleaning $base"
	if [ "${base: -4}" == ".amr" ]; then
		# ends with .amr
		rm -rf "$base.tok" 2> /dev/null
		rm -rf "$base.tok.aligned" 2> /dev/null
	else
		# does not end with .amr
		rm -rf "$base.amr.tok" 2> /dev/null
		rm -rf "$base.amr.tok.aligned" 2> /dev/null
	fi
	rm -rf "$base.parsed" 2> /dev/null
	rm -rf "$base.sent" 2> /dev/null
	rm -rf "$base.sent.prp" 2> /dev/null
	rm -rf "$base.sent.tok" 2> /dev/null
	rm -rf "$base.sent.tok.charniak.parse" 2> /dev/null
	rm -rf "$base.sent.tok.charniak.parse.dep" 2> /dev/null
}

function clean_dir {
	local base="$1"
	if [ -f "$base/train" ]; then
		clean "$base/train"
	fi
	if [ -f "$base/training" ]; then
		clean "$base/training"
	fi
	if [ -f "$base/dev" ]; then
		clean "$base/dev"
	fi
	if [ -f "$base/test" ]; then
		clean "$base/test"
	fi
}

if [ $# -eq 0 ]; then
	clean_dir "data"
else
	for arg in $@; do
		if [ "$arg" == "--" ]; then
			continue
		fi
		if [ -d "$arg" ]; then
			clean_dir $arg
		else
			clean $arg
		fi
	done
fi
