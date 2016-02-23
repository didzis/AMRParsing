#!/bin/bash

destdir=data
srcdir=golds
errlog=prepare.log

function usage {
    echo "Prepare training data from gold training,dev,test fileset"
    echo
    echo "usage: $0 [--srcdir <src dir>] [--train <src fn>] [--dev <src fn>] [--test <src fn>] [--log <error.log>] [dest dir]"
    echo
	echo "--srcdir DIR  source directory where to find training|train,dev,test files (default: golds)"
	echo "--train FILE  specify trainng source file individually (default: golds/train or golds/training)"
	echo "--dev FILE    specify dev source file individually (default: golds/dev)"
	echo "--test FILE   specify test source file individually (default: golds/test)"
	echo "--log FILE    specify error log file (default: $errlog)"
	echo
	echo "Default destination directory: $destdir"
    echo
	echo "NOTE: Requires Python 3.3+"
	echo
}

for arg in $@; do
    if [ "$arg" == "--help" ] || [ "$arg" == "-h" ]; then
        usage
        exit 0
    fi
done

# if [ "`which python3`" == "" ]; then
# 	echo "error: requires Python 3.3+"
# 	exit 1
# fi

function check_srcdir {
	if [ -f "$srcdir/training" ]; then
		trainfile="$srcdir/training"
	elif [ -f "$srcdir/train" ]; then
		trainfile="$srcdir/train"
	fi
	if [ -f "$srcdir/dev" ]; then
		devfile="$srcdir/dev"
	fi
	if [ -f "$srcdir/test" ]; then
		testfile="$srcdir/test"
	fi
}

check_srcdir

default_destdir="$destdir"
platinum=0

while [ $# -gt 0 ]; do
    if [ "$1" == "--" ]; then
        shift
        # break
    elif [ "$1" == "--srcdir" ]; then
        shift
		if [ -d "$1" ]; then
			srcdir="$1"
			check_srcdir
		else
			echo "error: invalid source directory: $1"
		fi
        shift
    elif [ "$1" == "--train" ]; then
        shift
		if [ -f "$1" ]; then
			trainfile="$1"
		else
			echo "error: invalid train file: $1"
		fi
        shift
    elif [ "$1" == "--dev" ]; then
        shift
		if [ -f "$1" ]; then
			devfile="$1"
		else
			echo "error: invalid dev file: $1"
		fi
        shift
    elif [ "$1" == "--test" ]; then
        shift
		if [ -f "$1" ]; then
			testfile="$1"
		else
			echo "error: invalid test file: $1"
		fi
        shift
    elif [ "$1" == "--platinum" ]; then
        shift
		platinum=1
    elif [ "$1" == "--log" ]; then
        shift
		errlog="$1"
        shift
    elif [ "$destdir" == "$default_destdir" ]; then
        destdir="$1"
        shift
    else
        echo "Warning: unexpected command line argument: $1"
        shift
    fi
done

DIR=`dirname $0`

srcfiles=("$trainfile" "$devfile" "$testfile")

if [ ${#srcfiles[@]} -eq 0 ]; then
	echo "error: no source files found"
	exit 1
fi

echo "Will prepare training data directory: $destdir"

mkdir -p $destdir
if [ $? -ne 0 ]; then
	echo "error, aborting"
	exit 1
fi

error=0

rm -f "$errlog" 2> /dev/null

if [ $platinum -eq 0 ]; then
	for input in "${srcfiles[@]}"; do
		output="$destdir/`basename $input`"
		echo -n "Preprocessing $input to $output ... "
		echo "Preprocessing $input to $output ... " >> "$errlog"
		$DIR/preprocess.py "$input" > "$output" 2>> "$errlog"
		if [ $? -eq 0 ]; then
			echo "ok"
		else
			error=1
			echo "error, check $errlog for error messages"
		fi
	done
else
	# sentences to be removed from train+dev set for platinum trainset
	platinum_rm_snt="910 1025 1622 1838 1888 3023 4213 5067 5329 5330 5448 5671 5831 6427 7107 7136 7525 7626 7664 8131 8154 8457 8577 9094 9180 9786 10067 10078 10161 11131 11515 11598 11932 11933 12099 12201 12717 12849 13600 13738 13963 14240 14398 14491 14631 14745 15043 15423 15639"

	# dev + train => train
	output="$destdir/`basename $trainfile`"
	echo -n "Preprocessing $trainfile + $devfile - non-platinum to $output ... "
	echo "Preprocessing $trainfile + $devfile - non-platinum to $output ... " >> "$errlog"
	$DIR/remove_sentences.py "$platinum_rm_snt" "$trainfile" 2>> "$errlog" > "$output.full"
	if [ $? -eq 0 ]; then
		$DIR/preprocess.py "$output.full" > "$output" 2>> "$errlog"
		if [ $? -eq 0 ]; then
			echo "ok"
			rm -rf "$output.full"
		else
			error=1
			echo "error, check $errlog for error messages"
		fi
	else
		error=1
		echo "error, check $errlog for error messages"
	fi

	input="$testfile"
	output="$destdir/`basename $input`"
	echo -n "Preprocessing $input to $output ... "
	echo "Preprocessing $input to $output ... " >> "$errlog"
	$DIR/preprocess.py "$input" > "$output" 2>> "$errlog"
	if [ $? -eq 0 ]; then
		echo "ok"
	else
		error=1
		echo "error, check $errlog for error messages"
	fi
fi

# remove error log if executed cleanly
if [ $error -eq 0 ]; then
	rm -f "$errlog" 2> /dev/null
fi
