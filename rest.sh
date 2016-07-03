#!/bin/sh

image=didzis/camrrest
port=5000

function usage {
	echo "CAMR REST API runner (dockerized version)"
    echo
	echo "usage: $0 [--image NAME] [-p PORT] [--detach] [--name NAME] [--] [options for rest.py (see below)]"
	echo
	echo "--image NAME           specify docker image (default: $image)"
	echo "-p PORT, --port PORT   specify port on host system (default: $port)"
	echo "--name NAME            specify docker container name"
	echo "-d, --detach           run container in background"
	echo
	echo "notes:"
	echo "* requires up to 22GB of RAM"
	echo "* requires at least 2GB of disk space (for docker image)"
    echo
}

function check_image {
	if [ "$(docker images -q $image 2> /dev/null)" = "" ]; then
		read -p "Docker image $image not found, pull from registry (at least 2GB of disk space required) [Y/n] ? " -n 1 -r
		echo    # (optional) move to a new line
		if [[ $REPLY =~ ^[Nn]$ ]]; then
			exit 1
		fi
	fi
}

if [ -t 0 ]; then
	docker_tty=-it
else
	docker_tty=
fi

for arg in $@; do
    if [ "$arg" = "--help" ] || [ "$arg" = "-h" ]; then
		usage
		check_image
		docker run --rm $docker_tty $image --rest --help
        exit $?
    fi
done

detach_rm="--rm"

args=()
container_args_only=0
while [ $# -gt 0 ]; do
	if [ "$1" = "--" ]; then
		container_args_only=1
		shift
		# break
    elif [ $container_args_only -ne 1 ] && [ "$1" = "--image" ]; then
		shift
		image="$1"
        shift
    elif [ $container_args_only -ne 1 ] && [ "$1" = "--name" ]; then
		shift
		name="--name $1"
        shift
	elif [ $container_args_only -ne 1 ] && ([ "$1" = "--detach" ] || [ "$1" = "-d" ]); then
		detach_rm="-d"
        shift
	elif [ $container_args_only -ne 1 ] && ([ "$1" = "--port" ] || [ "$1" = "-p" ]); then
		shift
		port="$1"
        shift
	else
		args=("${args[@]}" "$1")
		shift
	fi
done

echo Executing: docker run --rm -p $port:5000 $docker_tty $image --rest "${args[@]}"
check_image

echo
echo REST API will be available at host IP port $port
sleep 1
echo

docker run $detach_rm $name -p $port:5000 $docker_tty $image --rest "${args[@]}"
