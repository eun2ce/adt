# adt

Automatic deployment and testing of Kubernetes services

## code format

### pycharm

Preference > Tools > File Watchers > "+" > custom

```yaml
name: black
file type: python
Scope: Project Files
Program: {your black path}
Arguments: $FilePath$
Output paths to refresh: $FilePath$
Working Directory: $ProjectFileDir$
```
#### optional
* auto-save edited files to trigger the watcher : false
* Trigger the watcher on external changes: true