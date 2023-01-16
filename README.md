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
python scriptlauncher.py scriptlauncher.yaml
# To pass the tests
echo myerpuser:myerppassword > test.cfg
./test.sh
```











