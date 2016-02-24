#!/bin/bash

basedir=`dirname $0`
datadir=/data
input=input

function usage {
	echo "CAMR parser runner"
    echo
	echo "usage: $0 [--amrfmt] [--preserve] [--input NAME] [--output NAME]"
    echo
	echo "--amrfmt       expect input file to be in AMR format"
	echo "--preserve     preserve pre-processed file and parsed AMR (before post-processing)"
	echo "--preserve-all preserve all intermediate files"
	echo "--input NAME   input filename relative to data directory (default: $input)"
	echo "--output NAME  output filename relative to data directory (default: $input.final)"
	echo
	echo "required docker configuration: mount input and output file directory to $datadir"
	echo
	echo "for input and output:"
	echo "* input file must be mounted to $datadir/input"
	echo "* output file must be mounted to $datadir/output.final"
	echo
	echo "note: requires up to 18GB of RAM"
	echo
}

for arg in $@; do
    if [ "$arg" == "--help" ] || [ "$arg" == "-h" ]; then
        usage
        exit 0
    fi
done

preserve=0

while [ $# -gt 0 ]; do
	if [ "$1" == "--" ]; then
		shift
		# break
    elif [ "$1" == "--input" ]; then
		shift
		input="$1"
        shift
    elif [ "$1" == "--output" ]; then
		shift
		output="$1"
        shift
    elif [ "$1" == "--amrfmt" ] || [ "$1" == "--amr" ]; then
		amrfmt="--amrfmt"
        shift
    elif [ "$1" == "--plain" ]; then
		amrfmt=
        shift
    elif [ "$1" == "--preserve" ] && [ $preserve -eq 0 ]; then
		preserve=1
        shift
    elif [ "$1" == "--preserve-all" ]; then
		preserve=2
        shift
	else
		echo "unknown argument: $1"
		exit 1
	fi
done

function clean {
	local base="$1"
	# echo "Cleaning $base"
	if [ "${base: -4}" == ".amr" ]; then
		# ends with .amr
		rm -f "$base.tok" 2> /dev/null
		rm -f "$base.tok.aligned" 2> /dev/null
	else
		# does not end with .amr
		rm -f "$base.amr.tok" 2> /dev/null
		rm -f "$base.amr.tok.aligned" 2> /dev/null
	fi
	rm -f "$base.sent" 2> /dev/null
	rm -f "$base.sent.prp" 2> /dev/null
	rm -f "$base.sent.tok" 2> /dev/null
	rm -f "$base.sent.tok.charniak.parse" 2> /dev/null
	rm -f "$base.sent.tok.charniak.parse.dep" 2> /dev/null
}

if [ ! -f "$datadir/$input" ]; then
	echo "error: input file not found: $input"
	exit 1
fi

input="$datadir/$input"

if [ "$output" == "" ]; then
	output_parsed="$input.parsed"
	output_final="$input.final"
else
	output_parsed="$input.parsed"
	output_final="$datadir/$output"
fi

if [ "$amrfmt" == "" ]; then
	plain="--plain"
fi

cd $basedir
basedir=.

echo -n "Preprocessing ... "
$basedir/preprocess.py $plain "$input" > "$input.preprocessed" 2> $datadir/preprocess.log
if [ $? -eq 0 ]; then
	echo "ok"
else
	echo "error"
	echo "--- begin of preprocess.log ---"
	cat $datadir/preprocess.log
	echo "--- end of preprocess.log ---"
	echo "note: preprocess did run with errors"
	echo
	exit 1
fi

time $basedir/amr_parsing.py --model $basedir/model.m.bz2 --mode parse $amrfmt "$input.preprocessed" -o "$output_parsed" -W
if [ $? -ne 0 ]; then
	echo "Error parsing"
	exit 1
fi
if [ $preserve -lt 1 ]; then
	rm -f "$input.preprocessed"
fi
if [ $preserve -lt 2 ]; then
	clean "$input.preprocessed"
fi

# Post-processing
echo -n "Post-processing ... "
$basedir/postprocess.py "$output_parsed" > "$output_final" 2> $datadir/postprocess.log
if [ $? -eq 0 ]; then
	echo "ok"
	if [ $preserve -lt 1 ]; then
		rm -f "$output_parsed"
	fi
else
	echo "error"
	echo "--- begin of postprocess.log ---"
	cat $datadir/postprocess.log
	echo "--- end of postprocess.log ---"
	echo "note: postprocess did run with errors"
	echo
	exit 1
fi
