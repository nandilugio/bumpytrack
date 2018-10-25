#!/usr/bin/env bash

BIN_DIR=`dirname $(readlink -f $0)`

$BIN_DIR/clean.sh
$BIN_DIR/build.sh
$BIN_DIR/publish.sh
