#!/bin/bash
# a simple script to create a bunch of bare git repos in the
# format of a pensieve collection

cd pensieve
rm -rf *
for name in "$@"; do
    mkdir $name
    (cd $name && git init --bare repo.git)
done
