#!/bin/bash

cd `dirname $0`/..
basedir=`pwd`

echo "Setup Stanford CoreNLP ..."
cd "$basedir/stanfordnlp"
wget http://nlp.stanford.edu/software/stanford-corenlp-full-2013-06-20.zip
unzip stanford-corenlp-full-2013-06-20.zip
#wget http://nlp.stanford.edu/software/stanford-parser-full-2014-01-04.zip 
#unzip stanford-parser-full-2014-01-04.zip

echo "Setup JAMR ..."
cd "$basedir"
git clone https://github.com/jflanigan/jamr.git
cd "$basedir/jamr"
patch -p1 < $basedir/scripts/jamr_align.patch
./setup

echo "Setup Charniak Parser ..."
pip install --user bllipparser

echo "Setup SMATCH 2.0.2 ..."
cd "$basedir/scripts"
wget http://alt.qcri.org/semeval2016/task8/data/uploads/smatch-v2.0.2.tar.gz
tar xvf smatch-v2.0.2.tar.gz --strip-components=1 "*/amr.py" "*/smatch.py"
{ echo '#!/usr/bin/env python'; cat smatch.py; } > ../smatch.py
chmod +x ../smatch.py
rm smatch.py
mv amr.py ..
