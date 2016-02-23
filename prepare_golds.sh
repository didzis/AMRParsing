#!/bin/bash

destdir=golds
srcname="LDC2015E86_DEFT_Phase_2_AMR_Annotation_R1"
tgz_file="$srcname.tgz"
rpath="data/amrs/split"

if [ -d "data/$srcname/$rpath" ]; then
	srcdir="data/$srcname"
elif [ -d "$srcname/$rpath" ]; then
	srcdir="$srcname"
fi

splits=(training dev test)
corpuses=(proxy bolt dfa mt09sdl xinhua wb cctv guidelines consensus)

function usage {
    echo "Extract training, dev and test splits from $srcname data"
    echo
    echo "usage: $0 [--srcdir <src dir>] [--tgz <src.tgz>] [--train|--training] [--dev] [--test] [dest dir] [--] [corpus #1] [corpus #2] ..."
    echo
	echo "--srcdir DIR  path to $srcname (default: [data/]$srcname)"
	echo "--tgz FILE    path to $tgz_file file (will be extracted in current directory)"
	echo
	echo "Select splits:"
	echo "--train       prepare training split"
	echo "--dev         prepare development split"
	echo "--test        prepare test split"
	echo
	echo "Default destination directory: $destdir"
	echo
	echo "If no source directory found, will search for tgz archive"
	echo
	# echo "List of splits: ${splits[@]}"
	echo "List of corpuses: ${corpuses[@]}"
	echo
	echo "By default if no splits or corpuses selected, all will be used"
    echo
}

for arg in $@; do
    if [ "$arg" == "--help" ] || [ "$arg" == "-h" ]; then
        usage
        exit 0
    fi
done

function extract_tgz {
	echo -n "Extracting $1 to `dirname $1` ... "
	tar -xf $1 -C `dirname $1`
	if [ $? -ne 0 ]; then
		echo "error: extracting source data from $1"
		exit 1
	fi
	if [ ! -d "`dirname $1`/$srcname" ]; then
		echo "error: directory `dirname $1`/$srcname not found after extracting archive $1"
		exit 1
	fi
	echo "ok"
	srcdir="`dirname $1`/$srcname"
}

selected_splits=()
selected_corpuses=()
default_destdir=1

while [ $# -gt 0 ]; do
	if [ "$1" == "--" ]; then
		shift
		break
    elif [ "$1" == "--srcdir" ]; then
        shift
		if [ -d "$1" ]; then
			srcdir="$1"
		else
			echo "error: invalid source directory: $1"
		fi
        shift
    elif [ "$1" == "--tgz" ]; then
        shift
		if [ -f "$1" ]; then
			extract_tgz $1
		else
			echo "error: invalid source data archive: $1"
		fi
        shift
	elif [ "$1" == "--training" ] || [ "$1" == "--train" ]; then
		selected_splits=(${selected_splits[@]} training)
		shift
	elif [ "$1" == "--dev" ]; then
		selected_splits=(${selected_splits[@]} dev)
		shift
	elif [ "$1" == "--test" ]; then
		selected_splits=(${selected_splits[@]} test)
		shift
	elif [ $default_destdir -eq 1 ]; then
		destdir="$1"
		default_destdir=0
		shift
	else
		found=0
		for corpus in ${corpuses[@]}; do
			if [ "$corpus" == "$1" ]; then
				selected_corpuses=(${selected_corpuses[@]} $1)
				found=1
			fi
		done
		if [ $found -eq 0 ]; then
			echo "error: corpus $1 not found"
			exit 1
		fi
		shift
	fi
done

if [ ${#selected_splits[@]} -gt 0 ]; then
	splits=(${selected_splits[@]})
fi

if [ ${#selected_corpuses} -gt 0 ] || [ $# -gt 0 ]; then
	for arg in $@; do
		for corpus in ${corpuses[@]}; do
			if [ "$corpus" == "$arg" ]; then
				selected_corpuses=(${selected_corpuses[@]} $arg)
			fi
		done
	done
	corpuses=(${selected_corpuses[@]})
	# corpuses=(${selected_corpuses[@]} $@)
fi

if [ "$srcdir" == "" ]; then
	if [ -f "data/$tgz_file" ]; then
		extract_tgz "data/$tgz_file"
	elif [ -f "$tgz_file" ]; then
		extract_tgz "$tgz_file"
	else
		echo "error: no source data found."
		exit 1
	fi
fi

if [ -d "$srcdir/$rpath" ]; then
	srcdir="$srcdir/$rpath"
else
	echo "Error: invalid source data directory: $srcdir"
	exit 1
fi

if [ "$destdir" == "" ]; then
	echo "error: output directory not specified"
	echo
	usage 1
	exit 1
fi

echo "Selected splits: ${splits[@]}"
echo "Selected corpuses: ${corpuses[@]}"


mkdir -p "$destdir"

echo "Will write splits to $destdir"
for split in ${splits[@]}; do
	dstsplit=$split
	if [ "$dstsplit" == "training" ]; then
		dstsplit=train
	fi
	rm -f "$destdir/$dstsplit" 2>/dev/null
	if [ ${#corpuses[@]} -ne 0 ]; then
		echo "Writing $destdir/$dstsplit"
	fi
	for corpus in ${corpuses[@]}; do
		if [ -f "$srcdir/$split/deft-p2-amr-r1-amrs-$split-$corpus.txt" ]; then
			echo "* $split-$corpus"
			cat "$srcdir/$split/deft-p2-amr-r1-amrs-$split-$corpus.txt" >> "$destdir/$dstsplit"
		fi
	done
done
