# QuestAppLauncher_Assets
Assets (icon pack, app names) for QuestAppLauncher

Including utility to auto-update the assets


---

This modded repo adds genres as custom categorie from vrdb.

Add the repo url in your config.json as described on [QuestAppLauncher Readme](https://github.com/tverona1/QuestAppLauncher#configjson-configuration-file)

![grafik](https://user-images.githubusercontent.com/14855001/106215011-514c9f80-61d0-11eb-8e0b-c31d22dd4fd7.png)

---
Example config.json
Be sure to add teh new repo AFTER tverona1 repo
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
Generator usage:
Add args to run specific tasks 
or run all tasks and do a release
```
QuestAssetGenerator.py -a ACCESS_TOKEN -da -dr -c -g

-a ACCESS_TOKEN | *required* Peronal Github accesstoken for releasing
-g  | Add genres to appnames_quest.json
-da | Download Assets from Oculus Store
-dr | Download latest release from github for comparing
-c  | Compare latest release with new release
-r  | Create a Github release
```

---

`python -m venv venv`

`.\venv\Scripts\pip.exe install requests`
`.\venv\Scripts\pip.exe install PyGithub`

`.\venv\Scripts\pip.exe freeze > requirements.txt`

