#! /bin/bash
auth=$(cat test.cfg)
curl localhost:5000 -u $auth >  b2b/index-result.html && diff b2b/index-expected.html b2b/index-result.html 2> /dev/null  && echo OK || echo KO
curl localhost:5000/runner/test -u $auth >  b2b/runner-result.html && diff b2b/runner-expected.html b2b/runner-result.html 2> /dev/null  && echo OK || echo KO
curl localhost:5000/run/test -u $auth >  b2b/run-result.html && diff b2b/run-expected.html b2b/run-result.html 2> /dev/null  && echo OK || echo KO
