# Changelog

## ScriptLauncher 1.1.0 (2023-01-18)

- Default values for filenames makes them optional
- File upload progress indicated by a spinner and green check
- Parameter type, if not of the special types supported it  is used as HTML input type
    - For example: color, date, time, local-datetime...
- Documentation: Setup and usage in README, CHANGES
- Upgrade notes
    - All scripts that rely on the former working dir should
      declare `workingdir: LEGACY`.
      This can be done on particular scripts, at category level
      or as configuration with `dbconfig.scriptlauncher.legacyWorkingDir=True`.
    - If you define it widely you can remove legacy behaviour with `workingdir: .`.
    - Consider adding `type` attribute to all parameters of the
      new supported types: `date`, `time`, `localDateTime`, `color`...


