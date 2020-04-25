import argparse
import datetime
import os
import requests
import shutil
import subprocess
import sys
import zipfile

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
ICONPACK_OTHER = 'iconpack_others.zip'
APPNAMES_OTHER = 'appnames_other.json'
APPNAMES_GALAG_NAME = 'appnames_quest_en_US.json'

def main():
    parser = argparse.ArgumentParser(description='Quest Asset Generator')
    parser.add_argument('-a', '--access-token', required=True, help='GitHub acess token')
    parser.add_argument('-dr', '--download-release', action='store_true', help='Download latest asset release from github')
    parser.add_argument('-da', '--download-assets', action='store_true',help='Download assets from Oculus')
    parser.add_argument('-c', '--compare', action='store_true', help='Compare assets')
    parser.add_argument('-r', '--release', action='store_true', help='Draft a github release')
    args = parser.parse_args()

    # If nothing is specified, perform all actions
    if (not args.download_release and not args.download_assets and not args.compare and not args.release):
        args.download_release = True
        args.download_assets = True
        args.compare = True
        args.release = True

    # Instantiate github client
    g = Github(args.access_token)
    repo = g.get_user().get_repo('QuestAppLauncher_Assets')

    # Set up temp dir
    folder_path_temp = os.path.abspath(TEMP_DIR);
    if (not os.path.isdir(folder_path_temp)):
       os.mkdir(folder_path_temp)

    # Download latest assets
    if (args.download_assets):
        download_latest_assets()

    # Download latest release
    if (args.download_release):
        download_release_assets(repo)

    if (args.compare):
        compare()

    if (args.release):
        create_release(repo)

def get_release_download_path():
    return os.path.join(os.path.abspath(TEMP_DIR), LATEST_RELASE_DIR)

def get_galag_download_path():
    return os.path.abspath(os.path.join(os.path.abspath(TEMP_DIR), QALAG_OUTPUT_DIR))

# Download latest Github release
def download_release_assets(repo):
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

# Download latest assets
def download_latest_assets():
    galag_exe_full_path = os.path.abspath(QALAG_EXE_PATH)
    galag_output_dir = get_galag_download_path()

    if (os.path.isdir(galag_output_dir)):
        shutil.rmtree(galag_output_dir)
    os.mkdir(galag_output_dir)

    # Launch exe, temporarily changing cwd to land results in proper place
    cur_dir = os.path.abspath('.')
    os.chdir(galag_output_dir)
    launch_executable([], galag_exe_full_path)
    os.chdir(cur_dir)

    # Rename file
    os.rename(os.path.join(galag_output_dir, APPNAMES_GALAG_NAME), os.path.join(galag_output_dir, APPNAMES_QUEST))

# Compare
def compare():
    iconpack_quest_release_ext_path = os.path.join(get_release_download_path(), QUEST_DIR)
    iconpack_quest_generated_ext_path = os.path.join(get_galag_download_path(), QUEST_DIR)
    launch_executable(['-t', iconpack_quest_release_ext_path, iconpack_quest_generated_ext_path], bin_path=WINDIFF_EXE_PATH)

    appnames_quest_release_path = os.path.join(get_release_download_path(), APPNAMES_QUEST)
    appnames_quest_generated_path = os.path.join(get_galag_download_path(), APPNAMES_QUEST)
    launch_executable([appnames_quest_release_path, appnames_quest_generated_path], bin_path=WINDIFF_EXE_PATH)

# Create release
def create_release(repo):
    tag = 'v' + datetime.date.today().strftime('%m.%d.%Y')
    name = tag + ': Update quest assets'
    print(str.format('Creating release: tag: %s, name: %s' % (tag, name)))
    release = repo.create_git_release(tag=tag, name=name, message='Updating quest assets', draft=True)

    # Upload the assets, refreshing quest from generated path
    release.upload_asset(os.path.join(get_release_download_path(), APPNAMES_OTHER))
    release.upload_asset(os.path.join(get_release_download_path(), ICONPACK_OTHER))
    release.upload_asset(os.path.join(get_galag_download_path(), APPNAMES_QUEST))
    release.upload_asset(os.path.join(get_galag_download_path(), ICONPACK_QUEST))

# Launch executable and return output
def launch_executable(args, bin_path):
    try:
        output = subprocess.check_output([bin_path] + args, stderr=subprocess.STDOUT)
        return output.decode(sys.stdout.encoding)
    except subprocess.CalledProcessError as e:
        raise Exception(str.format(str(e) + ". Output: '%s'" % (e.output.decode(sys.stdout.encoding).rstrip()))) from e
    except Exception as e:
        raise type(e)(str.format(str(e) + " when calling '%s'" % (bin_path)))

main()