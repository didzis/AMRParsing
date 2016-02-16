#!/bin/bash

echo "Setup Stanford CoreNLP ..."
cd `dirname $0`/../stanfordnlp
wget http://nlp.stanford.edu/software/stanford-corenlp-full-2013-06-20.zip
unzip stanford-corenlp-full-2013-06-20.zip
#wget http://nlp.stanford.edu/software/stanford-parser-full-2014-01-04.zip 
#unzip stanford-parser-full-2014-01-04.zip

echo "Setup JAMR ..."
cd ..
git clone https://github.com/jflanigan/jamr.git
cd jamr
patch -p1 < ../scripts/jamr_align.patch
./setup

echo "Setup Charniak Parser ..."
pip install --user bllipparser
