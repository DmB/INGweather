#!/bin/sh

VER="0.1"
NAME="ingweather"
FNAME=$NAME-$VER

echo "creating" $FNAME
tar czf $FNAME.tar.gz data/ $NAME.py
mkdir $FNAME
cd $FNAME
dh_make -s --dpatch -e dmitriy.blinov@gmail.com -c GPL -f ../$FNAME.tar.gz;
cp ../$NAME.py .
cp -r ../data . 
touch changelog #FIXME
cp -f ../4deb/* ./debian/
dpkg-buildpackage -us -uc -rfakeroot
