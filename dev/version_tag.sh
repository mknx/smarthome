#!/bin/sh
#

usage() {
    echo "usage: version_tag.sh <version-id>"
}

if [ $# -ne 1 ]; then
    usage
    exit 1
fi
if ! sed -i 's/^VERSION =.*$/VERSION = '$1'/g' bin/smarthome.py; then
    echo "Could not replace VERSION variable." >&2
    exit 2
fi
JS = example/visu/js/smarthome
if ! sed -i "s/^var shVersion = .*/var shVersion = $1;/g" $JS.js; then
    echo "Could not replace shVersion variable." >&2
    exit 2
fi
cat $JS.js | grep -v 'console.log' > $JS.tmp.js
java -jar ./dev/yuicompressor-*.jar $JS.tmp.js -o $JS.min.js --charset utf-8
rm -f $JS.tmp.js
echo "$1" > VERSION

#git add VERSION
#git commit -m "set version to $1" VERSION

