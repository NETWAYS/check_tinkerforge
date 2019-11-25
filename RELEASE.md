# Release Tasks

## Milestone

Ensure that all issues/PRs for the milestone are closed: https://github.com/NETWAYS/check_tinkerforge/milestones

## Version

Specify the version:

```
VERSION=1.2.0
```

Update the version in the plugin:

```
sed -i "s/__version__ = .*/__version__ = '$VERSION'/g" check_tinkerforge.py
```

## Commit, Tag, Push

```
git commit -v -a -m "Release version $VERSION"
```

```
git tag -s -m "Version $VERSION" v$VERSION
```

```
git push origin master

git push --tags
```

## GitHub Release

Close the milestone: https://github.com/NETWAYS/check_tinkerforge/milestones

Create a new release from the pushed tag: https://github.com/NETWAYS/check_tinkerforge/releases
Link the closed milestone.

