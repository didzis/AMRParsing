#!/bin/bash

DIR=`dirname $0`

$DIR/prepare_golds.sh
$DIR/prepare_traindir.sh $@

