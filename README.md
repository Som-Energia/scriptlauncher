# scriptlauncher

Flask app to launch scripts in a server

## Development Setup

```bash
# First time setup
mkvirtualenv scriptlauncher
# Next time you will need to get into the virtualenv
workon scriptlauncher
# Install dependencies
sudo apt install python-dev libyaml-dev
pip install -r requirements.txt
# Configure configdb
# - The usual configdb.erppeek configuration plus (used for user validation)
# - configdb.scriptlauncher.prefix to use as working path
# Launch the server
python scriptlauncher.py scriptlauncher.yaml
# To pass the tests (requires server up)
echo myerpuser:myerppassword > test.cfg
./test.sh
```











