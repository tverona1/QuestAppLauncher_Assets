[![GitHub release](https://img.shields.io/github/release/reloxx13/QuestAppLauncher_Assets.svg)](https://GitHub.com/reloxx13/QuestAppLauncher_Assets/releases/) 
[![GitHub contributors](https://img.shields.io/github/contributors/reloxx13/QuestAppLauncher_Assets.svg)](https://GitHub.com/reloxx13/QuestAppLauncher_Assets/graphs/contributors/)
[![GitHub stars](https://img.shields.io/github/stars/reloxx13/QuestAppLauncher_Assets.svg)](https://github.com/reloxx13/QuestAppLauncher_Assets/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/reloxx13/QuestAppLauncher_Assets.svg)](https://github.com/reloxx13/QuestAppLauncher_Assets/network)
[![GitHub watchers](https://badgen.net/github/watchers/reloxx13/QuestAppLauncher_Assets)](https://badgen.net/github/watchers/reloxx13/QuestAppLauncher_Assets)
[![Github all releases](https://img.shields.io/github/downloads/reloxx13/QuestAppLauncher_Assets/total.svg?label=gh%20downloads)](https://GitHub.com/reloxx13/QuestAppLauncher_Assets/releases/) 
[![HitCount](http://hits.dwyl.io/reloxx13/QuestAppLauncher_Assets.svg)](http://hits.dwyl.io/reloxx13/QuestAppLauncher_Assets)

[comment]: <> ([![GitHub license]&#40;https://img.shields.io/github/license/reloxx13/QuestAppLauncher_Assets.svg&#41;]&#40;https://github.com/reloxx13/QuestAppLauncher_Assets/blob/master/LICENSE&#41;)

# QuestAppLauncher Assets by reloxx13
Assets (icon pack, app names, genres) for [QuestAppLauncher](https://github.com/tverona1/QuestAppLauncher)

Including utility to auto-update the assets

---
## Info and how-to

This modded repo adds genres as custom categories, parsed from [vrdb.app](https://vrdb.app/).

SideQuest App banners are also added.

Add the repo url in your config.json `downloadRepos` section as described in [QuestAppLauncher Readme](https://github.com/tverona1/QuestAppLauncher#configjson-configuration-file)

![grafik](https://user-images.githubusercontent.com/14855001/106268646-ad90dd00-622b-11eb-9af9-ecf60f79e992.png)

---
## Example config.json

Be sure to add the new repo AFTER tverona1 repo in `downloadRepos` section.

```
{
  "gridSize": {
    "rows": 3,
    "cols": 3
  },
  "sortMode": "mostRecent",
  "show2D": true,
  "autoCategory": "top",
  "customCategory": "right",
  "autoUpdate": true,
  "background": "",
  "downloadRepos": [
    {
      "repoUri": "tverona1/QuestAppLauncher_Assets/releases/latest",
      "type": "github"
    },
    {
      "repoUri": "reloxx13/QuestAppLauncher_Assets/releases/latest",
      "type": "github"
    }
  ]
}
```

---
### Generator usage:
Windows only   
Add args to run specific tasks    
or run all tasks and do a release   
```
QuestAssetGenerator.py -a ACCESS_TOKEN -da -dr -c -g

-a ACCESS_TOKEN | Peronal Github accesstoken for releasing
-g  | Add genres to appnames_quest.json
-da | Download Assets from Oculus Store
-ds | Download Assets from SideQuest Store
-dr | Download latest release from github for comparing
-c  | Compare latest release with new release
-r  | Create a Github release
```

If there is no ACCESS_TOKEN in arguments, the script tries to use a `access_token` file.

---

#### Dev

`python -m venv venv`

`.\venv\Scripts\pip.exe install requests`
`.\venv\Scripts\pip.exe install PyGithub`

`.\venv\Scripts\pip.exe freeze > requirements.txt`

