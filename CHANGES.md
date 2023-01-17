# Changelog

## unreleased

- Optional filenames
- New file upload progress indicators
- Parameter type, if not supported, used as input type
    - For example: color, date, time, local-datetime...
- Setup and usage documentation
- Upgrade notes
    - All scripts that rely on the former working dir should
      declare `workingdir: LEGACY`.
      This can be added at category level for short.
    - Consider adding `type` attribute to all parameters of the
      new supported types: `date`, `time`, `localDateTime`, `color`...
      



