#!/bin/sh

image=didzis/camrrest
port=5000

function usage {
	echo "CAMR REST API runner (dockerized version)"
    echo
	echo "usage: $0 [--image NAME] [-p PORT] [--detach] [--name NAME] [--] [options for rest.py (see below)]"
	echo
	echo "--image NAME           specify docker image (default: $image)"
	echo "--pull                 pull docker image from registry"
	echo "-p PORT, --port PORT   specify port on host system (default: $port)"
	echo "--name NAME            specify docker container name"
	echo "-d, --detach           run container in background"
	echo '-r, --reuse            reuse container if already exists (will first try `docker start NAME`)'
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
	elif [ $pull -eq 1 ]; then
		echo
		echo "Pulling from registry"
		docker pull $image
	fi
}

docker version > /dev/null
if [ $? -ne 0 ]; then
	echo "Docker not installed or engine not running."
	exit 1
fi

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
reuse=0
pull=0

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
		name="$1"
		name_arg="--name $1"
        shift
	elif [ $container_args_only -ne 1 ] && ([ "$1" = "--detach" ] || [ "$1" = "-d" ]); then
		detach_rm="-d"
        shift
	elif [ $container_args_only -ne 1 ] && ([ "$1" = "--reuse" ] || [ "$1" = "-r" ]); then
		reuse=1
        shift
	elif [ $container_args_only -ne 1 ] && [ "$1" = "--pull" ]; then
		pull=1
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

if [ $reuse -eq 1 ] && [ "$name" != "" ]; then
	if [ "`docker ps -aq --format '{{.Names}}' | grep "^$name$"`" != "" ]; then
		docker start $name
		if [ $? -eq 0 ]; then
			exit 0
		else
			exit 1
		fi
	else
		echo "Container $name does not exist, will create."
		echo
	fi
fi

if [ $reuse -eq 1 ] && [ "$name" != "" ] && [ "$detach_rm" == "--rm" ]; then
	# don't remove container if planned to be reused
	detach_rm=
fi

echo Will execute: docker run $detach_rm $name_arg -p $port:5000 $docker_tty $image --rest "${args[@]}"
check_image

echo
echo REST API will be available at host IP port $port
sleep 1
echo

id=`docker run $detach_rm $name_arg -p $port:5000 $docker_tty $image --rest "${args[@]}"`

if [ "$name" != "" ]; then
	id="$name"
fi

if [ "$detach_rm" == "-d" ]; then
	echo
	echo "Running in detached mode, to see output log, execute:"
	echo "$ docker logs -f $id"
	echo
fi
