# Script Launcher

A simple web app to launch scripts on a server.

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
python scriptlauncher.py myscripts.yaml
```

Passing the tests

```bash
python scriptlauncher.py scripts.yaml
# To pass the tests (requires server up)
echo myerpuser:myerppassword > test.cfg
./test.sh
```

## Diclaimer on security

This application is not intended to be used by untrusted users.
It executes command line scripts with user provided parameters.
Special care must be taken on how scripts are defined as it might
create script injection oportunities.

## Adding scripts

You can run ScriptLauncher providing a yaml configuration file (or many) as command line parameter.

A configuration file contains a set of categories
each one including a set of scripts.

```yaml
myfirstcategory:
  description: My First Category
  scripts:
    myfirstscript:
      title: My first script
      description: >
        An extended description for the script
        for the user to understand how to use it
      script: savebirthday {name} {birthday} {favouriteColor}
      parameters:
        name:
          description: Your name
        birthday:
          description: Your birthday date
          type: date
        favouriteColor:
          description: Your favourite colour
          type: color
          default: '#ffff00'
```

Keys for categories and scripts will be used as identifiers in url's
that can be used to access scripts directly.

## Multiple configuration files

If several configuration files are provided,
they are merged at category level.
If the same category is defined in a later configuration file,
scripts on the same category for the previous configuration are discarded.

## Using parameters

Parameters can be expanded into the command line,
by using [Python format minilanguage](https://docs.python.org/3/library/string.html#formatspec).

The format string is passed an array with all the user
provided values and some extra provide ones:

- title: The entry title
- today: The current date
- OKKO: An empty string or 'ERROR' if the command failed (only available after execution)

## Working directory

For every configuration file,
the default working directory to execute scripts from
is the containing directory of each configuration file.
Working directory is inherited from file to category to scripts.
You can override it by adding a `workingdir` attribute
at script or category level.
Relative paths refer to the inherited `workingdir`.

### Legacy working dir

**This functionality is provided as migration tool, is deprecated and will be dropped eventually.**

In previous versions, scripts were run in the same working dir than the scriptlauncher API is run.
For compatibility with old configurations, you can define `workingdir: LEGACY` in categories or scripts.
Also `configdb.scriptlauncher.legacyWorkingDir=True` does that in general.
This will set the API working directory as working directory for the scripts.

Legacy mode is inherited but the standard behaviour is
recovered when `workingdir` is set different to `LEGACY`.

Relative paths refer to the path as in standard behaviour,
not the LEGACY path.
So, conveniently `.` just recovers the standard behaviour
and can be used for progressive migration.

## Parameter types

By default, script parameters are plain text fields.
This can be changed by using the `type` attribute:

- `enum`: Will be shown as a select box.
	- You can specify `options` as a dictionary where keys are the displayed texts and values are the sent value.
- `date`, `time`, `color` or any other supported [HTML input type](https://www.w3schools.com/html/html_form_input_types.asp)
   will be applied to the HTML `input` and it will use browser input control for that type.
- `FILE`: A file uploaded by the user
	- The parameter will be substituted on the command line by the server location of the uploaded file.
	- If you want to make a file to be optional by defaulting to a server path. A useful choice is `/dev/null`.
- `FILEDOWN`:
	- This parameter is not editable by the user
	- It will expand in the command line to a temporary file name you can use as output for your command
	- The file will be downloaded after executing the script.
	- An `extension` can be specified for the browser to identify the file type
	- Also a `filename` the browser will propose as save name
		- The filename can contain format specifiers to use parameters

For any type but `FILEDOWN`, you can specify a `default` property.
This value will be taken if none is specified.

## Automatically send mails

Script attibute `send` can be used to automatically
send the output of the script by mail.
The output will be html formated including ANSI colors.

Sendmail configuration has to be added to configdb.py
(see [emili](https://github.com/Som-Energia/emili) documentation).

The `send` attribute has the following structure:

```yaml
  myscript:
    ...
    send:
        subject: "This is the subject"
        to:
        - recipient1@somewhere.com
        - recipient2@somewhere.com
```

Both `subject` and `to` strings may contain format directives
that will be filed with any parameter and those extra ones:

- title: The entry title
- today: The current date
- OKKO: An empty string or 'ERROR' if the command failed.


## dbconfig Configuration

- `scriptlauncher.prefix`: will substitute `SOME_SRC` string in commandline
- `scriptlauncher.legacyWorkingDir`: Enables the legacy working dir mode (Default: False)
- `scriptlauncher.ignoreauth`: Disables auth for testing purposes (Default: False)
- `scriptlauncher.download_folder`: Disables auth for testing purposes (Default: `/tmp`)











