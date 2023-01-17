#! /bin/bash
function b2b {
	name="$1"
	"${@:2}" > b2b/"$name"-result &&
		diff -q b2b/"$name"-result b2b/"$name"-expected 2> /dev/null &&
		echo -e '\033[32mOK\033[34;1m '"$name"'\033[0m' ||
		echo -e '\033[31mKO\033[34;1m '"$name"'\033[0m Run:' diff b2b/"$name"-result b2b/"$name"-expected
}

auth=$(cat test.cfg)
b2b index \
	curl -s localhost:5000 -u $auth
b2b runner \
	curl -s localhost:5000/runner/test_parameter -u $auth
b2b run \
	curl -s localhost:5000/run/test_parameter -u $auth
b2b workingdirOverride \
	curl -s localhost:5000/run/workingdirOverride -u $auth
b2b workingdirLegacy \
	curl -s localhost:5000/run/workingdirLegacy -u $auth
