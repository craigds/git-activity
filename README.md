# git-activity

Run this tool in a git repository.

Given a list of file/directory names, this tool spits out the changes
to those files on the git repo, on _all branches_.

This is useful when you want to do a large bulk change, and be sure that there won't be many conflicts with other developers' feature branches.

In other words, this lets you make big changes without pissing off everyone on your team.

## Usage

```
usage: git-activity.py [-h] [--verbose] [--days DAYS] FILE [FILE ...]

Summarize git activity on other branches

positional arguments:
  FILE

optional arguments:
  -h, --help   show this help message and exit
  --verbose
  --days DAYS  How far back to look for activity
```

You need to run this from inside a git repository. The current branch needs to track a branch on the remote.

