#!/bin/bash

# first argument: basedir
if [ "$1" != "" ]; then
	cd "$1"
fi

if [ "`which pip2`" = "" ]; then
	curl -s https://bootstrap.pypa.io/get-pip.py | sudo python
	[ $? -ne 0 ] && exit 1
fi
sudo pip2 install --upgrade pip
#[ $? -ne 0 ] && exit 1

# install homebrew if not installed (to /usr/local/homebrew, not /usr/local directly !!!)
if [ "`which brew`" = "" ]; then

	# check if current user is in admin group
	isadmin=0
	if [ "`id | grep '(admin)'`" != "" ]; then
		isadmin=1
	fi

	sudo mkdir -p /usr/local 2> /dev/null
	if [ $? -eq 0 ] && [ $isadmin -eq 1 ]; then
		# current user must be in admin group
		# change group of /usr/local to admin
		sudo chgrp admin /usr/local
		sudo chmod g+ws /usr/local
	fi

	# prepare bin directory
	sudo mkdir -p /usr/local/bin 2> /dev/null
	if [ $? -eq 0 ] && [ $isadmin -eq 1 ]; then
		sudo chmod g+ws /usr/local/bin
	else
		# check if current user has the /usr/local/bin group
		bingrp=`stat -f %Sg /usr/local/bin`
		if [ "`id | grep "($bingrp)"`" = "" ]; then
			# if not allow full access to /usr/local/bin
			sudo chmod a+rwx /usr/local/bin
		fi
	fi

	mkdir -p /usr/local/homebrew
	if [ $? -ne 0 ]; then
		sudo mkdir -p /usr/local/homebrew
		if [ $isadmin -eq 1 ]; then
			sudo chgrp admin /usr/local/homebrew
			sudo chmod g+ws /usr/local/homebrew
		fi
	fi

	brewgrp=`stat -f %Sg /usr/local/homebrew`
	if [ "`id | grep "($bingrp)"`" = "" ]; then
		# if not allow full access to /usr/local/homebrew
		sudo chmod a+rwx /usr/local/homebrew
	fi

	git clone https://github.com/Homebrew/homebrew.git /usr/local/homebrew

	sudo chmod -R g+w /usr/local/homebrew

	ln -s /usr/local/homebrew/bin/brew bin/brew

	sudo rm -rf /Library/Caches/Homebrew
	sudo rm -rf ~/Library/Logs/Homebrew
fi

brew update
brew tap homebrew/boneyard
brew install libiomp
brew install swig

git clone https://github.com/BLLIP/bllip-parser.git
cd bllip-parser
FOPENMP=-liomp5 make
#FOPENMP=-fopenmp=libiomp5 make

python setup.py build
sudo python setup.py install
