
# GIT

For an introduction see: http://gitimmersion.com/

## Setup

```
# only push the current branch (not all)
git config --global push.default current
# adapt your user settings
git config --global user.name "Your Name"
git config --global user.email you@example.com
```

## Getting the Source
git clone git://github.com/mknx/smarthome.git

## Update the Code
git pull

# Coding

## Python Version
You should use Python =< 2.6 methods only. If not make it clear in the documentation.
## pep8
Test the code style with pep8. I'm ignoring "E501 line too long".
`apt-get install pep8`
`pep8 yourcode.py`

# Release
## Changes
`git log --pretty=format:"%s" VERSIONTAG..HEAD`

# Homepage
```
git clone -b gh-pages git@github.com:mknx/smarthome.git sh-pages
```
