#!/bin/bash

cd `dirname $0`/..
basedir=`pwd`

echo "Setup Stanford CoreNLP ..."
cd "$basedir/stanfordnlp"
wget http://nlp.stanford.edu/software/stanford-corenlp-full-2013-06-20.zip
unzip stanford-corenlp-full-2013-06-20.zip
ln -s stanford-corenlp-full-2013-06-20 stanford-corenlp
#wget http://nlp.stanford.edu/software/stanford-parser-full-2014-01-04.zip 
#unzip stanford-parser-full-2014-01-04.zip

echo "Setup JAMR ..."
cd "$basedir"
git clone https://github.com/jflanigan/jamr.git
cd "$basedir/jamr"
patch -p1 < $basedir/scripts/jamr_align.patch
./setup

echo "Setup Charniak Parser ..."
if [ "`uname`" = "Darwin" ]; then
	`dirname $0`/install-bllip-parser-osx.sh "$basedir"
else
	pip2 install --user bllipparser
fi

echo "Setup SMATCH 2.0.2 ..."
cd "$basedir/scripts"
wget http://alt.qcri.org/semeval2016/task8/data/uploads/smatch-v2.0.2.tar.gz
tar xvf smatch-v2.0.2.tar.gz --strip-components=1 "*/amr.py" "*/smatch.py"
{ echo '#!/usr/bin/env python'; cat smatch.py; } > ../smatch.py
chmod +x ../smatch.py
rm smatch.py
mv amr.py ..

echo "Install python modules for REST API"
pip2 install --user --upgrade flask flask-cors pyyaml

echo "Download Swagger Editor"
cd "$basedir/static"
wget https://github.com/swagger-api/swagger-editor/releases/download/v2.9.9/swagger-editor.zip
unzip swagger-editor.zip
mv dist swagger-editor
rm swagger-editor.zip
cp "$basedir/swagger.yaml" "swagger-editor/spec-files/default.yaml"
cp "$basedir/swagger.yaml" "swagger/swagger.yaml"
