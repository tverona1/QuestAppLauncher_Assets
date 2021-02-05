import argparse
import datetime
import os
import requests
import mimetypes
import shutil
import subprocess
import sys
import zipfile
import json
import re
import time
import unicodedata
import concurrent.futures
import demjson

from urllib.request import Request, urlopen
from PIL import Image
from github import Github  # pip install PyGithub

# Temporary directory for scratch space
TEMP_DIR = '__temp__'
LATEST_RELASE_DIR = 'latest_release'
QALAG_OUTPUT_DIR = 'qalag'

QALAG_EXE_PATH = 'bin\\qalag.exe'
WINDIFF_EXE_PATH = 'bin\\windiff.exe'

APPNAMES_qalag_NAME = 'appnames_quest_en_US.json'

QUEST_DIR = 'quest'
ICONPACK_QUEST = 'iconpack_quest.zip'
APPNAMES_QUEST = 'appnames_quest.json'

APPNAMES_QUEST_GENREFIED = 'appnames_quest_genrefied.json'

ICONPACK_OTHER = 'iconpack_others.zip'
APPNAMES_OTHER = 'appnames_other.json'

SIDEQUEST_DIR = 'sidequest'
APPNAMES_SIDEQUEST = 'appnames_o_sidequest.json'  # o before q(-uest) to prio quest store names and banners
ICONPACK_SIDEQUEST = 'iconpack_o_sidequest.zip'  # o before q(uest) to prio quest store names and banners


VRDB_CACHETIME = 24  # time in hours to refresh the cachefile
SIDEQUEST_CACHETIME = 24  # time in hours to refresh the cachefile

IMGFETCHER_WORKERS = 10

# Change the region
# VRDB_URL_QUEST = "https://vrdb.app/quest/index_us.json"
VRDB_URL_QUEST = "https://vrdb.app/quest/index_eu.json"
VRDB_URL_APPLAB = "https://vrdb.app/quest/lab/index_eu.json"

VRDB_QUEST_CACHE = "vrdb_quest.json"
VRDB_APPLAB_CACHE = "vrdb_applab.json"


CATEGORY_WEIGHTS = {
        "Shooter": 9000,
        "FPS": 5000,
        "Music": 8000,
        "Fitness": 7000,
        "Combat": 6000,
        "Horror": 5750,
        "Escape": 5500,
        "Puzzle": 5350,
        "Adventure": 3000,
        "Multiplayer": 100,
        "Early Access": 95,
        "Streaming": 80,
        "All Games & Apps": 0,
    }

CATEGORY_MAPPING = {
    "FPS": "Shooter",
    "Relaxation/Meditation": "Relaxation",
    "Meditation": "Relaxation",
    "Climbing": "Exploration",
    "Art/Creativity": "Creativity",
    "Sports": "Fitness",
}



def main():
    parser = argparse.ArgumentParser(description='Quest Asset Generator - Genrefied')
    parser.add_argument('-a', '--access-token', help='GitHub access token')
    parser.add_argument('-dr', '--download-release', action='store_true',
                        help='Download latest asset release from github')
    parser.add_argument('-da', '--download-assets', action='store_true', help='Download assets from Oculus')
    parser.add_argument('-ds', '--download-sidequest', action='store_true', help='Download assets from Sidequest')
    parser.add_argument('-g', '--genrefy', action='store_true', help='Genrefy appnames_quest.json file')
    parser.add_argument('-c', '--compare', action='store_true', help='Compare assets')
    parser.add_argument('-r', '--release', action='store_true', help='Draft a github release')
    args = parser.parse_args()

    # use access_token file if no acces token in arguments
    if (not args.access_token or args.access_token == ""):
        if os.path.isfile(os.path.join("access_token")):
            print("use access_token file")
            with open(os.path.join("access_token")) as f:
                first_line = f.readline()
            args.access_token = first_line
            if not args.access_token or args.access_token == "":
                print("ERROR: access_token file is empty")
                exit(1)
        else:
            print("ERROR: add your github access token as argument or crete a access_token file")
            exit(1)

    # If nothing is specified, perform all actions
    # if (
    #         not args.download_release and not args.download_assets and not args.compare and not args.genrefy and not args.release and not args.download_sidequest):
    #     print("perform all actions")
    #     args.download_release = True
    #     args.download_assets = True
    #     args.download_sidequest = True
    #     args.genrefy = True
    #     # args.compare = True
    #     args.release = True

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

    if (args.genrefy):
        populate_genre()

    if (args.download_sidequest):
        get_sidequet_categories()

    # Download latest release
    if (args.download_release):
        download_release_assets(repo)


    if (args.compare):
        compare()

    if (args.release):
        create_release(repo)


def get_release_download_path():
    return os.path.join(os.path.abspath(TEMP_DIR), LATEST_RELASE_DIR)


def get_cache_file(cachefile):
    return os.path.join(os.path.abspath(TEMP_DIR), cachefile)


def get_qalag_download_path():
    return os.path.abspath(os.path.join(os.path.abspath(TEMP_DIR), QALAG_OUTPUT_DIR))


def get_override_path(OVERRIDE):
    return os.path.abspath(os.path.join(os.path.abspath("overrides"), OVERRIDE))



APPNAMES_SIDEQUEST_DATA = {}
def get_sidequet_categories():
    print("=== START get_sidequet_categories ===")
    mainjs_url = "https://sidequestvr.com/main.js"  # this has the categorie in it


    # if (os.path.isdir(get_cache_file(SIDEQUEST_DIR))):
    #     shutil.rmtree(get_cache_file(SIDEQUEST_DIR))

    if (not os.path.isdir(get_cache_file(SIDEQUEST_DIR))):
        os.mkdir(get_cache_file(SIDEQUEST_DIR))

    headers = {
        "Origin": "https://sidequestvr.com",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "QuestAppLauncher Assets"
    }

    categories = {}
    req = Request(mainjs_url)
    if (headers):
        for key, value in headers.items():
            # print(key, '->', value)
            req.add_header(key, value)
    response = urlopen(req)
    response = response.read().decode('utf-8')



    if not response or len(response) == 0:
        print(f'Loading from {mainjs_url} FAILED: response error')
        exit(1)

    # print(response)

    #this.sidequestItems=[{...}]
    match = re.search(r"this.sidequestItems=(\[.*?\])", response, re.MULTILINE | re.DOTALL)
    if match:
        js_cats = match.group(1)
        print(match.group(1))
        js_cats=js_cats.replace("!0", "\"!0\"")
        categories = demjson.decode(js_cats)



    if len(categories) > 0:

        processes = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            for idx, category in enumerate(categories):
                # print(f"{idx} => {category}")
                print(f"Doing {idx} => {category['name']}...")

                # if not "tag" in category:
                #     continue

                processes.append(executor.submit(get_sidequest_caegory_Data, category, idx))

                # print(res)
                # concurrent.futures.wait(res)
                # APPNAMES_SIDEQUEST_DATA = APPNAMES_SIDEQUEST_DATA + appnames_sidequest_data_sub

            concurrent.futures.wait(processes, timeout=None, return_when=concurrent.futures.ALL_COMPLETED)

            for _ in concurrent.futures.as_completed(processes):
                result = _.result()
                # print('Result: ', result)
                categories[result["idx"]]["count"] = result["count"]
                weight = CATEGORY_WEIGHTS.get(categories[result["idx"]]["name"], result["count"])
                categories[result["idx"]]["weight"] = weight
                categories[result["idx"]]["data"] = result["data"]


        # Order categories by weight
        categories = sorted(categories, key=lambda k: k['weight'], reverse=True)
        # print(categories)
        # exit(0)

        for idx, category in enumerate(categories):
            download_sidequest_assets(category,idx)


        # print(APPNAMES_SIDEQUEST_DATA)

        # cache loaded app data
        print(f"write {APPNAMES_SIDEQUEST}")
        with open(get_cache_file(APPNAMES_SIDEQUEST), 'w', encoding='utf8') as outfile:
            json.dump(APPNAMES_SIDEQUEST_DATA, outfile, indent=4, ensure_ascii=False) # , sort_keys=True

        # Extract quest icons
        print(f"zip images {ICONPACK_SIDEQUEST}")
        zipf = zipfile.ZipFile(os.path.join(TEMP_DIR, ICONPACK_SIDEQUEST), 'w', zipfile.ZIP_DEFLATED)
        zipdir(os.path.join(TEMP_DIR, SIDEQUEST_DIR), zipf)
        zipf.close()

    print("=== END get_sidequet_categories ===")



def get_sidequest_caegory_Data(category,cidx):
    print("=== START get_sidequest_caegory_Data ===")

    result = {
        "idx": cidx,
        "count": 0,
    }
    # curl "https://api.sidequestvr.com/search-apps
    # ?search=&page=0&order=rating&direction=desc&app_categories_id=1&tag=null&users_id=null&limit=51&device_filter=all&license_filter=all"
    # -H "Accept: application/json" -H "Accept-Language: de,en;q=0.7,en-US;q=0.3"
    # -H "Content-Type: application/json"
    # -H "Origin: https://sidequestvr.com"
    headers = {
        "Origin": "https://sidequestvr.com",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "QuestAppLauncher Assets"
    }

    limit = 100
    page = 0
    results = True
    tag = "null"
    if 'tag' in category:
        tag = category['tag']
    elif category["name"] != 'All Games & Apps':
        tag = category["name"].replace(" ", "").lower()
    else:
        print(category)
        # exit(1)

    sidequest_data = []

    while results:
        # sidequest_url = f"https://api.sidequestvr.com/search-apps?search=&page={page}&order=rating&direction=desc&app_categories_id=1&tag={tag}&limit={limit}&device_filter=quest&license_filter=all"
        sidequest_url = f"https://api.sidequestvr.com/search-apps?search=&page={page}&tag={tag}&limit={limit}&device_filter=quest"
        data = []

        req = Request(sidequest_url)
        if (headers):
            for key, value in headers.items():
                # print(key, '->', value)
                req.add_header(key, value)
        response = urlopen(req)
        response = response.read()

        if not response or len(response) == 0:
            print(f'Loading from {sidequest_url} FAILED: response error')
            exit(1)

        data = json.loads(response)

        if not data:
            print(f'Loading from {sidequest_url} FAILED: (json) data empty')
            exit(1)
        # else:
        #     print(f'Loading from {VRDB_URL_QUEST} SUCCESS')

        print(f"Tag {tag} ({category['name']}) | page => {page}, results => {len(data['data'])}")

        if (len(data["data"]) > 0):

            # print(sidequest_data)
            # print(data["data"])

            if not sidequest_data:
                sidequest_data = data
            else:
                sidequest_data["data"] += data["data"]

            page = page + 1
        else:
            results = False

    print(f"Tag {tag} ({category['name']}) | TOTAL RESULTS => {len(sidequest_data['data'])}")

    result["count"] = len(sidequest_data['data'])
    result["data"] = sidequest_data["data"]
    # print(sidequest_data)

    print("=== END get_sidequest_caegory_Data ===")

    return result

def download_sidequest_assets(category,cidx):
    print("=== START download_sidequest_assets ===")




    if category["count"] > 0:
        processes = [];
        with concurrent.futures.ThreadPoolExecutor(max_workers=IMGFETCHER_WORKERS) as executor:
            for idx, sidequest_entry in enumerate(category["data"]):
                # print(f"{idx} => {sidequest_entry}")
                print(f"Doing {cidx} | {idx} => {category['name']} | {sidequest_entry['name']} | {sidequest_entry['packagename']}...")

                catname = "SideQuest"
                if category['name'] not in {"All Games & Apps", "Staff Picks", "App Lab"}:
                    catname = category['name']


                catname = CATEGORY_MAPPING.get(catname,catname)

                if sidequest_entry["packagename"] in APPNAMES_SIDEQUEST_DATA:
                    if APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]]["category"] == "" or \
                            APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]]["category"] == "SideQuest":
                        APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]]["category"] = catname

                    else:
                        if APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]]["category2"] == "" or \
                                APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]]["category2"] == "SideQuest":
                            APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]]["category2"] = catname

                else:
                    APPNAMES_SIDEQUEST_DATA[sidequest_entry["packagename"]] = {
                        "name": sidequest_entry["name"],
                        "category": catname,
                        "category2": "",
                    }


                processes.append(executor.submit(fetch_sidequest_images, sidequest_entry, idx))

            concurrent.futures.wait(processes, timeout=None, return_when=concurrent.futures.ALL_COMPLETED)

    # return APPNAMES_SIDEQUEST_DATA

    print("=== END download_sidequest_assets ===")

    return True


def fetch_sidequest_images(sidequest_entry, idx, force_banner=False):
    file_path = os.path.join(get_cache_file(SIDEQUEST_DIR),slugify(sidequest_entry["packagename"])) + ".jpg"

    img_file_age_in_hours = get_file_age_in_hours(file_path)


    if img_file_age_in_hours is not False:
        # print(f"Cached img file {file_path} is {img_file_age_in_hours} h old")
        if img_file_age_in_hours <= SIDEQUEST_CACHETIME:
            return True


    override_path = os.path.join(get_override_path(SIDEQUEST_DIR), sidequest_entry["packagename"]) + ".jpg"

    if os.path.exists(override_path):
        print(f"use override image for {sidequest_entry['packagename']}")
        file_path_new = os.path.join(get_cache_file(SIDEQUEST_DIR), slugify(sidequest_entry["packagename"])) + ".jpg"
        optimize_image(override_path, file_path_new)
        # change_aspect_ratio(override_path,file_path_new)

    else:
        image_url = sidequest_entry["image_url"]
        if not image_url or image_url == "" or force_banner:
            print(f"{idx} => No image, use banner")
            image_url = sidequest_entry["app_banner"]

        if not image_url or image_url == "" or image_url == "n/a":
            print(f"{idx} => NO IMAGE FOR {sidequest_entry['name']}")
        else:
            print(f"{idx} => load image for {sidequest_entry['name']} | {sidequest_entry['packagename']} => {image_url}")

            r = requests.get(image_url+"?size=705", allow_redirects=True, headers={'Accept': '*/*'})

            # print(r.headers)
            # print(r.content)
            # print(r.reason)
            # print(r.text)
            # r.close()
            # exit(1)

            if r.status_code != 200:
                print(r.headers)
                print(r.content)
                print(r.reason)
                print(r.text)
                r.close()
                exit(1)

            content_type = r.headers['content-type']
            # print(f"content_type => {content_type}")
            extension = mimetypes.guess_extension(content_type)
            # print(f"extension => {extension}")

            if not extension:
                print(f"{idx} => EXTENSION ERROR: {extension}")
                extension = os.path.splitext(image_url)[len(os.path.splitext(image_url)) - 1]
                print(f"{idx} => NEW TRY: {extension}")

            file_path = os.path.join(get_cache_file(SIDEQUEST_DIR), slugify(sidequest_entry["packagename"])) + extension

            # print("write")
            open(file_path, 'wb').write(r.content)
            # print("written")

            r.close()

            if extension != ".jpg":
                # print(f"{idx} => Convert {extension} to JPG => {slugify(sidequest_entry['packagename']) + extension}")
                try:
                    file_path_new = os.path.join(get_cache_file(SIDEQUEST_DIR),
                                                 slugify(sidequest_entry["packagename"])) + ".jpg"
                    Image.open(file_path).convert('RGB').save(file_path_new)
                    os.remove(file_path)
                    file_path = file_path_new
                    extension = ".jpg"


                except Exception as e:
                    print(f"{idx} => Convert error: {e}")

            if extension == ".jpg":
                optimize_image(file_path)
                # change_aspect_ratio(file_path)

            # image = Image.open(file_path)
            # width = image.size[0]
            # height = image.size[1]

            # if (width == height and not force_banner):
            #     print("image is 1:1, try banner url")
            #     fetch_sidequest_images(sidequest_entry, idx, True)


    return True


def optimize_image(file_path, file_path_new=""):
    if not file_path_new or file_path_new == "":
        file_path_new = file_path

    # print(f"Optimize: {file_path}")
    try:
        # optimize images
        img = Image.open(file_path)
        # I downsize the image with an ANTIALIAS filter (gives the highest quality)
        img.thumbnail((720, 405), Image.ANTIALIAS)
        img.save(file_path_new, optimize=True, quality=90)


    except Exception as e:
        print(f"Optimize error: {e}")



def change_aspect_ratio(file_path, file_path_new=""):
    if not file_path_new or file_path_new == "":
        file_path_new = file_path

    ideal_width = 720
    ideal_height = 405

    image = Image.open(file_path)
    width = image.size[0]
    height = image.size[1]

    aspect = width / float(height)

    ideal_aspect = ideal_width / float(ideal_height)

    if aspect > ideal_aspect:
        # Then crop the left and right edges:
        new_width = int(ideal_aspect * height)
        offset = (width - new_width) / 2
        resize = (offset, 0, width - offset, height)
    else:
        # ... crop the top and bottom:
        new_height = int(width / ideal_aspect)
        offset = (height - new_height) / 2
        resize = (0, offset, width, height - offset)

    thumb = image.crop(resize).resize((ideal_width, ideal_height), Image.ANTIALIAS)
    thumb.save(file_path_new)


# Download latest Github release
def download_release_assets(repo):
    print("=== START download_release_assets ===")

    # check if there is a release
    if (repo.get_releases().totalCount == 0):
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
            r.close()

            file_path = os.path.join(download_release_path, asset.name)
            open(file_path, 'wb').write(r.content)

        # Extract quest icons
        iconpack_quest_release_zip = os.path.join(download_release_path, ICONPACK_QUEST)
        iconpack_quest_release_ext_path = os.path.join(download_release_path, QUEST_DIR)
        with zipfile.ZipFile(iconpack_quest_release_zip) as zip:
            zip.extractall(iconpack_quest_release_ext_path)

    print("=== END download_release_assets ===")


# Download latest assets
def download_latest_assets(genrefy=False):
    print("=== START download_latest_assets ===")
    qalag_exe_full_path = os.path.abspath(QALAG_EXE_PATH)
    qalag_output_dir = get_qalag_download_path()

    print(f"qalag_exe_full_path => {qalag_exe_full_path}")
    print(f"qalag_output_dir => {qalag_output_dir}")
    if (os.path.isdir(qalag_output_dir)):
        # print(f"delete output dir")
        shutil.rmtree(qalag_output_dir)

    # print(f"create output dir")
    os.mkdir(qalag_output_dir)

    # Launch exe, temporarily changing cwd to land results in proper place
    cur_dir = os.path.abspath('.')
    os.chdir(qalag_output_dir)
    print(f"Launch QALAG_EXE")
    launch_executable([], qalag_exe_full_path)
    print(f"Done QALAG_EXE")
    os.chdir(cur_dir)

    # Rename file
    os.rename(os.path.join(qalag_output_dir, APPNAMES_qalag_NAME), os.path.join(qalag_output_dir, APPNAMES_QUEST))
    print("=== END download_latest_assets ===")

    if genrefy:
        populate_genre()


# Compare
def compare():
    print("=== START compare ===")
    if (os.path.isfile(os.path.join(get_release_download_path(), QUEST_DIR))):
        print(f"compare {QUEST_DIR}")
        iconpack_quest_release_ext_path = os.path.join(get_release_download_path(), QUEST_DIR)
        iconpack_quest_generated_ext_path = os.path.join(get_qalag_download_path(), QUEST_DIR)
        launch_executable(['-t', iconpack_quest_release_ext_path, iconpack_quest_generated_ext_path],
                          bin_path=WINDIFF_EXE_PATH)
    else:
        print(f"skip {QUEST_DIR}")

    if (os.path.isfile(os.path.join(get_release_download_path(), APPNAMES_QUEST))):
        print(f"compare {APPNAMES_QUEST}")
        appnames_quest_release_path = os.path.join(get_release_download_path(), APPNAMES_QUEST)
        appnames_quest_generated_path = os.path.join(get_qalag_download_path(), APPNAMES_QUEST)
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

    if (os.path.isfile(os.path.join(get_qalag_download_path(), APPNAMES_QUEST_GENREFIED))):
        print(f"upload {APPNAMES_QUEST_GENREFIED}")
        release.upload_asset(os.path.join(get_qalag_download_path(), APPNAMES_QUEST_GENREFIED))

    if (os.path.isfile(get_cache_file(APPNAMES_SIDEQUEST))):
        print(f"upload {APPNAMES_SIDEQUEST}")
        release.upload_asset(get_cache_file(APPNAMES_SIDEQUEST))

    if (os.path.isfile(get_cache_file(ICONPACK_SIDEQUEST))):
        print(f"upload {ICONPACK_SIDEQUEST}")
        release.upload_asset(get_cache_file(ICONPACK_SIDEQUEST))

    print(f"upload {APPNAMES_QUEST}")
    release.upload_asset(os.path.join(get_qalag_download_path(), APPNAMES_QUEST))

    print(f"upload {ICONPACK_QUEST}")
    release.upload_asset(os.path.join(get_qalag_download_path(), ICONPACK_QUEST))

    print("=== END create_release ===")

def get_file_age_in_hours(file_path):
    app_file_age_in_hours = False
    if os.path.isfile(file_path):
        if os.path.getsize(file_path) != 0:
            app_file_age_in_hours = round(((int(time.time() - os.path.getmtime(file_path))) / 60 / 60), 2)
            # print(f"Cached file {file_path} is {app_file_age_in_hours}h old")
    return app_file_age_in_hours

def populate_genre():
    # load cached or live game lists
    app_file_age_in_hours = get_file_age_in_hours(get_cache_file(VRDB_QUEST_CACHE))
    print(f"Cached app file {get_cache_file(VRDB_QUEST_CACHE)} is {app_file_age_in_hours}h old")

    if app_file_age_in_hours is False or app_file_age_in_hours >= VRDB_CACHETIME:
        print(f"Load applist from {VRDB_URL_QUEST}")
        quest_vrdb_data = load_json(VRDB_URL_QUEST, VRDB_QUEST_CACHE)
        applab_vrdb_data = load_json(VRDB_URL_APPLAB, VRDB_APPLAB_CACHE)


    else:
        print(f"Load applist from cached {get_cache_file(VRDB_QUEST_CACHE)}")
        quest_vrdb_data = load_json(get_cache_file(VRDB_QUEST_CACHE))
        print(f"Load applist from cached {get_cache_file(VRDB_APPLAB_CACHE)}")
        applab_vrdb_data = load_json(get_cache_file(VRDB_APPLAB_CACHE))

    vrdb_data = quest_vrdb_data["data"] + applab_vrdb_data["data"]

    appname_quest_data = load_json(os.path.join(get_qalag_download_path(), APPNAMES_QUEST))
    appname_quest_data_with_genres = parse_genres(appname_quest_data, vrdb_data)

    with open(os.path.join(get_qalag_download_path(), APPNAMES_QUEST_GENREFIED), 'w', encoding='utf8') as outfile:
        json.dump(appname_quest_data_with_genres, outfile, indent=4, ensure_ascii=False)


def load_json(path_or_url, cachefile="", headers={}):
    data = []
    if path_or_url.find("http") == 0:  # begins with http

        req = Request(path_or_url)
        if (headers):
            for key, value in headers.items():
                # print(key, '->', value)
                req.add_header(key, value)
        response = urlopen(req)
        response = response.read()
        if not response or len(response) == 0:
            print(f'Loading from {path_or_url} FAILED: response error')
            exit(1)
        data = json.loads(response)

        if not data:
            print(f'Loading from {path_or_url} FAILED: (json) data empty')
            exit(1)
        # else:
        #     print(f'Loading from {VRDB_URL_QUEST} SUCCESS')

        # cache loaded app data
        with open(get_cache_file(cachefile), 'w', encoding='utf8') as outfile:
            json.dump(data, outfile, indent=4, ensure_ascii=False)
    else:
        with open(path_or_url, encoding='utf8') as json_file:
            data = json.load(json_file)
    return data


def parse_genres(app_names, vrdb_data):
    # print(app_names)
    for app_name, app_data in app_names.items():
        # print(app_name + " => " + json.dumps(app_data))
        # print("App title => " + app_data["name"])
        if not app_data["name"]:
            print(f"ERROR {app_name} has no app title | app_data => {app_data}")
            continue

        genres = get_genres_from_app_list_by_app_name(app_data["name"], vrdb_data)
        if genres:
            genres = genres.replace("360 Experience (non-game)", "360 Experience")
            genres = [genres.strip() for genres in genres.split(',')]
            # print(genres)
            if len(genres) >= 1:

                genres[0] = CATEGORY_MAPPING.get( genres[0], genres[0])
                app_names[app_name]["category"] = genres[0]
                if len(genres) >= 2:
                    genres[1] = CATEGORY_MAPPING.get( genres[1], genres[1])
                    app_names[app_name]["category2"] = genres[1]
        # elif not genres:
        #     print(f"ERROR app `{app_name}` has no genre")

    # print(app_names)
    return app_names


def get_genres_from_app_list_by_app_name(app_name, vrdb_data):
    genres = ""
    found = False
    for idx, vrdb_entry in enumerate(vrdb_data):
        appListName = vrdb_entry[1]  # get link with name from json
        appListName = re.sub('<[^<]+?>', '', appListName)  # remove html tags
        prepared_app_name = app_name.lower().replace(" - demo", "").replace(" - vr comic", "").replace(" - vr", "")

        # fix for a hidden special char, dont remove it, i know it looks duplicated!
        prepared_app_name = prepared_app_name.replace(" – demo", "")

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


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s\.-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(file), os.path.join(path, '..', '..')))


main()
