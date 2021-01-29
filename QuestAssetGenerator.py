import argparse
import datetime
import os
import requests
import shutil
import subprocess
import sys
import zipfile
import json
import re
import time
import urllib.request

from github import Github  # pip install PyGithub

# Temporary directory for scratch space
TEMP_DIR = '__temp__'
LATEST_RELASE_DIR = 'latest_release'
QALAG_OUTPUT_DIR = 'qalag'

QALAG_EXE_PATH = 'bin\\qalag.exe'
WINDIFF_EXE_PATH = 'bin\\windiff.exe'

QUEST_DIR = 'quest'
ICONPACK_QUEST = 'iconpack_quest.zip'
APPNAMES_QUEST = 'appnames_quest.json'
APPNAMES_QUEST_GENREFIED = 'appnames_quest_genrefied.json'
ICONPACK_OTHER = 'iconpack_others.zip'
APPNAMES_OTHER = 'appnames_other.json'
APPNAMES_GALAG_NAME = 'appnames_quest_en_US.json'


VRDB_APPS = "vrdb.json"
VRDB_CACHETIME = 12  # time in hours to refresh the cachefile


# Change the region
# VRDB_URL = "https://vrdb.app/quest/index_us.json"
VRDB_URL = "https://vrdb.app/quest/index_eu.json"
# VRDB_URL = "https://vrdb.app/quest/index_au.json"
# VRDB_URL = "https://vrdb.app/quest/index_ca.json"
# VRDB_URL = "https://vrdb.app/quest/index_gb.json"


def main():
    parser = argparse.ArgumentParser(description='Quest Asset Generator - Genrefied')
    parser.add_argument('-a', '--access-token', required=True, help='GitHub access token')
    parser.add_argument('-dr', '--download-release', action='store_true', help='Download latest asset release from github')
    parser.add_argument('-da', '--download-assets', action='store_true', help='Download assets from Oculus')
    parser.add_argument('-g', '--genrefy', action='store_true', help='Genrefy appnames_quest.json file')
    parser.add_argument('-c', '--compare', action='store_true', help='Compare assets')
    parser.add_argument('-r', '--release', action='store_true', help='Draft a github release')
    args = parser.parse_args()

    # If nothing is specified, perform all actions
    if (not args.download_release and not args.download_assets and not args.compare and not args.genrefy and not args.release):
        print("perform all actions")
        args.download_release = True
        args.download_assets = True
        args.genrefy = True
        args.compare = True
        args.release = True

    # Instantiate github client
    g = Github(args.access_token)
    repo = g.get_user().get_repo('QuestAppLauncher_Assets')
    print(f"Loaded repo {repo.full_name}")

    # Set up temp dir
    folder_path_temp = os.path.abspath(TEMP_DIR)
    print(f"folder_path_temp => {folder_path_temp}")
    if (not os.path.isdir(folder_path_temp)):
        print("Create tmp folder")
        os.mkdir(folder_path_temp)

    # Download latest assets
    if (args.download_assets):
        download_latest_assets()

    # Download latest release
    if (args.download_release):
        download_release_assets(repo)

    if (args.genrefy):
        populate_genre()

    if (args.compare):
        compare()

    if (args.release):
        create_release(repo)


def get_release_download_path():
    return os.path.join(os.path.abspath(TEMP_DIR), LATEST_RELASE_DIR)


def get_vrdb_file():
    return os.path.join(os.path.abspath(TEMP_DIR), VRDB_APPS)


def get_galag_download_path():
    return os.path.abspath(os.path.join(os.path.abspath(TEMP_DIR), QALAG_OUTPUT_DIR))


# Download latest Github release
def download_release_assets(repo):


    print("=== START download_release_assets ===")

    # check if there is a release
    if(repo.get_releases().totalCount == 0):
        print("WARN: No release found!")
    else:
        release = repo.get_latest_release()
        print("Downloading release: '%s'" % (release.title))

        download_release_path = get_release_download_path();
        if (os.path.isdir(download_release_path)):
            shutil.rmtree(download_release_path)
        os.mkdir(download_release_path)

        assets = release.get_assets()
        for asset in assets:
            print("\tAsset: %s [%s]" % (asset.name, asset.url))

            r = requests.get(asset.url, allow_redirects=True, headers={'Accept': 'application/octet-stream'})
            file_path = os.path.join(download_release_path, asset.name)
            open(file_path, 'wb').write(r.content)

        # Extract quest icons
        iconpack_quest_release_zip = os.path.join(download_release_path, ICONPACK_QUEST)
        iconpack_quest_release_ext_path = os.path.join(download_release_path, QUEST_DIR)
        with zipfile.ZipFile(iconpack_quest_release_zip) as zip:
            zip.extractall(iconpack_quest_release_ext_path)


    print("=== END download_release_assets ===")


# Download latest assets
def download_latest_assets():


    print("=== START download_latest_assets ===")
    galag_exe_full_path = os.path.abspath(QALAG_EXE_PATH)
    galag_output_dir = get_galag_download_path()

    print(f"galag_exe_full_path => {galag_exe_full_path}")
    print(f"galag_output_dir => {galag_output_dir}")
    if (os.path.isdir(galag_output_dir)):
        # print(f"delete output dir")
        shutil.rmtree(galag_output_dir)

    # print(f"create output dir")
    os.mkdir(galag_output_dir)

    # Launch exe, temporarily changing cwd to land results in proper place
    cur_dir = os.path.abspath('.')
    os.chdir(galag_output_dir)
    print(f"Launch QALAG_EXE")
    launch_executable([], galag_exe_full_path)
    print(f"Done QALAG_EXE")
    os.chdir(cur_dir)

    # Rename file
    os.rename(os.path.join(galag_output_dir, APPNAMES_GALAG_NAME), os.path.join(galag_output_dir, APPNAMES_QUEST))
    print("=== END download_latest_assets ===")


# Compare
def compare():


    print("=== START compare ===")
    if(os.path.isfile(os.path.join(get_release_download_path(), QUEST_DIR))):
        print(f"compare {QUEST_DIR}")
        iconpack_quest_release_ext_path = os.path.join(get_release_download_path(), QUEST_DIR)
        iconpack_quest_generated_ext_path = os.path.join(get_galag_download_path(), QUEST_DIR)
        launch_executable(['-t', iconpack_quest_release_ext_path, iconpack_quest_generated_ext_path], bin_path=WINDIFF_EXE_PATH)
    else:
        print(f"skip {QUEST_DIR}")


    if (os.path.isfile(os.path.join(get_release_download_path(), APPNAMES_QUEST))):
        print(f"compare {APPNAMES_QUEST}")
        appnames_quest_release_path = os.path.join(get_release_download_path(), APPNAMES_QUEST)
        appnames_quest_generated_path = os.path.join(get_galag_download_path(), APPNAMES_QUEST)
        launch_executable([appnames_quest_release_path, appnames_quest_generated_path], bin_path=WINDIFF_EXE_PATH)
    else:
        print(f"skip {APPNAMES_QUEST}")

    print("=== END compare ===")

# Create release
def create_release(repo):


    print("=== START create_release ===")

    tag = 'v' + datetime.date.today().strftime('%Y.%m.%d')
    name = tag + ': Update Quest assets'
    print(str.format('Creating release: tag: %s, name: %s' % (tag, name)))
    release = repo.create_git_release(tag=tag, name=name, message='Updating Quest assets', draft=False)

    # Upload the assets, refreshing quest from generated path
    # if(os.path.isfile(os.path.join(get_release_download_path(), APPNAMES_OTHER))):
    #     print(f"upload {APPNAMES_OTHER}")
    #     release.upload_asset(os.path.join(get_release_download_path(), APPNAMES_OTHER))
    #
    # if (os.path.isfile(os.path.join(get_release_download_path(), ICONPACK_OTHER))):
    #     print(f"upload {ICONPACK_OTHER}")
    #     release.upload_asset(os.path.join(get_release_download_path(), ICONPACK_OTHER))


    if (os.path.isfile(os.path.join(get_galag_download_path(), APPNAMES_QUEST_GENREFIED))):
        print(f"upload {APPNAMES_QUEST_GENREFIED}")
        release.upload_asset(os.path.join(get_galag_download_path(), APPNAMES_QUEST_GENREFIED))

    print(f"upload {APPNAMES_QUEST}")
    release.upload_asset(os.path.join(get_galag_download_path(), APPNAMES_QUEST))

    print(f"upload {ICONPACK_QUEST}")
    release.upload_asset(os.path.join(get_galag_download_path(), ICONPACK_QUEST))


    print("=== END create_release ===")


def populate_genre():
    # load cached or live game lists
    app_file_age_in_hours = False
    if os.path.isfile(get_vrdb_file()):
        if os.path.getsize(get_vrdb_file()) != 0:
            app_file_age_in_hours = round(((int(time.time() - os.path.getmtime(get_vrdb_file()))) / 60 / 60), 2)
            print(f"Cached app file {get_vrdb_file()} is {app_file_age_in_hours}h old")

    if app_file_age_in_hours is False or app_file_age_in_hours >= VRDB_CACHETIME:
        print(f"Load applist from {VRDB_URL}")
        vrdb_data = load_json(VRDB_URL)
    else:
        print(f"Load applist from cached {get_vrdb_file()}")
        vrdb_data = load_json(get_vrdb_file())


    appname_quest_data = load_json(os.path.join(get_galag_download_path(), APPNAMES_QUEST))
    appname_quest_data_with_genres = parse_genres(appname_quest_data,vrdb_data)

    with open(os.path.join(get_galag_download_path(), APPNAMES_QUEST_GENREFIED), 'w', encoding='utf8') as outfile:
        json.dump(appname_quest_data_with_genres, outfile, indent=4, ensure_ascii=False)


def load_json(path_or_url):
    data = []
    if path_or_url.find("http") == 0:
        response = urllib.request.urlopen(path_or_url)
        response = response.read()
        if not response or len(response) == 0:
            print(f'Loading from {VRDB_URL} FAILED: response error')
            exit(1)
        data = json.loads(response)

        if not data:
            print(f'Loading from {VRDB_URL} FAILED: (json) data empty')
            exit(1)
        # else:
        #     print(f'Loading from {VRDB_URL} SUCCESS')

        # cache loaded app data
        with open(get_vrdb_file(), 'w', encoding='utf8') as outfile:
            json.dump(data, outfile, indent=4, ensure_ascii=False)
    else:
        with open(path_or_url, encoding='utf8') as json_file:
            data = json.load(json_file)
    return data


def parse_genres(app_names,vrdb_data):
    # print(app_names)
    for app_name, app_data in app_names.items():
        # print(app_name + " => " + json.dumps(app_data))
        # print("App title => " + app_data["name"])
        if not app_data["name"]:
            print(f"ERROR {app_name} has no app title | app_data => {app_data}")
            continue

        genres = get_genres_from_app_list_by_app_name(app_data["name"],vrdb_data)
        if genres:
            genres = genres.replace("360 Experience (non-game)", "360 Experience")
            genres = [genres.strip() for genres in genres.split(',')]
            # print(genres)
            if len(genres) >= 1:
                app_names[app_name]["category"] = genres[0]
                if len(genres) >= 2:
                    app_names[app_name]["category2"] = genres[1]
        # elif not genres:
        #     print(f"ERROR app `{app_name}` has no genre")

    # print(app_names)
    return app_names


def get_genres_from_app_list_by_app_name(app_name,vrdb_data):
    genres = ""
    found = False
    for idx, vrdb_entry in enumerate(vrdb_data["data"]):
        appListName = vrdb_entry[1] # get link with name from json
        appListName = re.sub('<[^<]+?>', '', appListName) # remove html tags
        prepared_app_name = app_name.lower().replace(" - demo", "").replace(" - vr comic", "").replace(" - vr","")

        # fix for a hidden special char, dont remove it, i know it looks duplicated!
        prepared_app_name = prepared_app_name.replace(" – demo","")

        if prepared_app_name.endswith(' vr'):
            prepared_app_name = prepared_app_name[:-3]
        if prepared_app_name in appListName.lower():
            found = True
            # print(f"Found app `{app_name}` in applist {idx}|´{appListName}´")
            genres = vrdb_entry[11]
            # print(f"Genres => {genres}")
            break

    if not found:
        print(f"ERROR app `{app_name}` NOT in applist")
        print(f"prepared_app_name => `{prepared_app_name}`")
    elif not genres:
        print(f"ERROR app `{app_name}` has no genre")

    return genres


# Launch executable and return output
def launch_executable(args, bin_path):


    print("=== START launch_executable ===")
    print(f"bin_path => {bin_path}")
    print(f"args => {args}")
    try:
        print("running...")
        output = subprocess.check_output([bin_path] + args, stderr=subprocess.STDOUT)
        print("=== RETURN launch_executable ===")
        return output.decode(sys.stdout.encoding)
    except subprocess.CalledProcessError as e:
        raise Exception(str.format(str(e) + ". Output: '%s'" % (e.output.decode(sys.stdout.encoding).rstrip()))) from e
    except Exception as e:
        raise type(e)(str.format(str(e) + " when calling '%s'" % (bin_path)))


main()
