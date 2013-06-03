
# Coding
## Requirements
You should use Python =< 2.6 methods only. If not make it clear in the documentation what Python version you need.

## Coding style
The code should conform to pep8. I'm ignoring "E501 line too long".
`apt-get install pep8`
`pep8 yourcode.py`

# GIT

For an introduction to git see: http://gitimmersion.com/

## Setup

```
# only push the current branch (not all)
git config --global push.default current
# adapt your user settings
git config --global user.name "Your Name"
git config --global user.email you@example.com
```

## Getting the Source
`git clone git://github.com/mknx/smarthome.git`

## Update the Code
`git pull`

## Git branches
There are three special branches:
   * `master`: this is the default branch and it contains the current developement. Please only commit to master if you have tested your code.
   * `stable`: this branch contains official released code. Do not commit to this branch!
   * `gh-pages`: is the branch for the website. I recommend tracking it in a sepearte directory `git clone -b gh-pages git@github.com:mknx/smarthome.git sh-pages`

The rest of the branches are temporary developement branches.

### Creating you own branch
Create your own branch to start developing. e.g. 'mybranch'
<pre>
# clone mybranch from master
git branch mybranch master
# switch to mybranch
git checkout mybranch
</pre>

If you want to push your branch to github: `git push origin mybranch`

## Usefull commands
### List Release-Changes
`git log --pretty=format:"%s" VERSIONTAG..HEAD`

### Undo
`git reset --hard XXXIDXXX`
`git push origin master --force`
