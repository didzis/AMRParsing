#!/bin/bash

image=didzis/camrwrapper

function usage {
	echo "CAMR wrapper parser runner (dockerized version)"
    echo
	echo "usage: $0 [--amrfmt|--amr] [--image NAME] [--preserve] [--preserve-all] <input> [output]"
    echo
	echo "--amrfmt       expect input file to be in AMR format"
	# echo "--image NAME   specify docker image (default: $image)"
	echo "--preserve     preserve pre-processed file and parsed AMR (before post-processing)"
	echo "--preserve-all preserve all intermediate files"
	echo
	echo "output defaults to <input>.final"
	echo
	echo "notes:"
	echo "* input file directory must be writable"
	echo "* requires up to 18GB of RAM"
	echo "* requires at least 2GB of disk space"
	echo
}

for arg in $@; do
    if [ "$arg" == "--help" ] || [ "$arg" == "-h" ]; then
        usage
        exit 0
    fi
done

while [ $# -gt 0 ]; do
	if [ "$1" == "--" ]; then
		shift
		# break
    elif [ "$1" == "--image" ]; then
		shift
		image="$1"
        shift
    elif [ "$1" == "--amrfmt" ] || [ "$1" == "--amr" ]; then
		amrfmt="--amrfmt"
        shift
    elif [ "$1" == "--plain" ]; then
		amrfmt=
        shift
    elif [ "$1" == "--preserve" ] && [ "$preserve" == "" ]; then
		preserve="$1"
        shift
    elif [ "$1" == "--preserve-all" ]; then
		preserve="$1"
        shift
    elif [ "$input" == "" ] && [ -f "$1" ]; then
		input="$1"
        shift
    elif [ "$input" != "" ] && [ "$output" == "" ]; then
		output="$1"
        shift
	else
		echo "unknown argument: $1"
		exit 1
	fi
done

if [ "$input" == "" ]; then
	echo "error: input file not specified"
	exit 1
fi

if [ ! -f "$input" ]; then
	echo "error: invalid input file: $input"
	exit 1
fi


# http://stackoverflow.com/questions/3572030/bash-script-absolute-path-with-osx
# http://stackoverflow.com/questions/6270440/simple-logical-operators-in-bash
absdirname () { { [ -f "$1" ] && echo $(cd `dirname "$1"` && echo "$PWD") ; } || { [ -d "$1" ] && echo $(cd "$1" && echo "$PWD") ; } ; }

# inputdir=`dirname "$input"`
inputdir=`absdirname "$input"`
input=`basename "$input"`

if [ "$output" == "" ]; then
	output="$input.final"
else
	# outputdir=`dirname "$output"`
	outputdir=`absdirname "$output"`
	if [ ! -d "$outputdir" ]; then
		mkdir -p "$outputdir"
		if [ $? -ne 0 ] || [ ! -d "$outputdir" ]; then
			echo "error: output directory could not be created"
			exit 1
		fi
	fi
	if [ "$outputdir" != "$inputdir" ]; then
		cp_output="$output"
		output="$input.final"
	else
		output=`basename "$output"`
	fi
fi

if [ "$amrfmt" != "" ]; then
	fmt=" (AMR)"
fi
echo "Input$fmt: $inputdir/$input"
if [ "$cp_output" == "" ]; then
	echo "Output: $inputdir/$output"
else
	echo "Output: $cp_output"
fi

docker run -it -v $inputdir:/data $image $amrfmt $preserve --input "$input" --output "$output"

if [ $? -eq 0 ]; then
	if [ "$cp_output" == "" ]; then
		echo "Output written to $inputdir/$output"
	else
		cp "$inputdir/$output" "$cp_output"
		if [ $? -eq 0 ]; then
			echo "Output written to $cp_output"
			rm -f "$inputdir/$output"
		else
			echo "Unable to write to $cp_output"
			echo "Result file is available at $inputdir/$output"
		fi
	fi
fi
