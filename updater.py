from subprocess import check_output, run, CalledProcessError
from os.path import exists, join
import os
from shutil import copy, copytree
from json import load, dump
from PIL import Image, ImageFilter


class KDiag:

    def get_dir(text):
        KDiag.popup(text)
        return check_output(['kdialog', '--getexistingdirectory','.']).decode().strip()

    def get_png(text):
        KDiag.popup(text)
        try:
            return check_output(['kdialog', '--getopenfilename', '.', 'image/png']).decode().strip()
        except CalledProcessError:
            return None

    def error(text):
        run(['kdialog', '--error', text])
        exit()

    def ask(text, default):
        return check_output(['kdialog', '--inputbox', text, default]).decode().strip()

    def popup(text): run(['kdialog', '--msgbox', text])

class Strings:

    cmake = 'install(DIRECTORY {dir} DESTINATION ${{KDE_INSTALL_WALLPAPERDIR}})\n'

    def metadata(name, author, email):
        return """{
    "KPlugin": {
        "Authors": [
            {
                "Email": \"""" + email + """\",
                "Name": \"""" + author + """\"
            }
        ],
        "Id": "Next",
        "License": "CC-BY-SA-4.0",
        "Name": \"""" + name + """\"
    }
}
"""

# Step 0: The only third party library and warnings

try:
    import git
except ModuleNotFoundError:
    KDiag.error("Could not find gitpython. Please run 'python3 -m pip install gitpython'.")
KDiag.popup('Hey! This will remove any local uncommited change to current branch of '
            'breeze, plasma workspace and plasma workspace wallpapers. '
            'Ctrl+C the script instead of pressing OK to avoid this.')

# Step 1: Getting The Repositories

plasma_w, plasma_d, breeze, plasma_w_w = None, None, None, None
if exists('.magic.config'):
    config = load(open('.magic.config'))
    plasma_w = config.get('plasma-w', None)
    plasma_d = config.get('plasma-d', None)
    breeze = config.get('breeze', None)
    plasma_w_w = config.get('plasma-w-w', None)
breeze = breeze or KDiag.get_dir('Please select Breeze repository.')
plasma_w = plasma_w or KDiag.get_dir('Please select Plasma Workspace repository.')
plasma_d = plasma_d or KDiag.get_dir('Please select Plasma Desktop repository.')
plasma_w_w = plasma_w_w or KDiag.get_dir('Please select P-W Wallpaper repository.')
dump({'plasma-w': plasma_w, 'plasma-d': plasma_d, 'breeze': breeze, 'plasma-w-w': plasma_w_w},
     open('.magic.config', 'w'))

# Step 2.1: Setting Up Git

branch = KDiag.ask('Insert branch name', 'work/new_wallpaper')
for repo in (git.Repo(breeze), git.Repo(plasma_w), git.Repo(plasma_d), git.Repo(plasma_w_w)):
    repo.git.checkout('.')
    repo.git.clean('-fd')
    repo.git.checkout('master')
    try: repo.git.branch('-D', branch)
    except: pass
    repo.git.checkout('-b', branch)

# Step 2: Copying The Old Wallpaper to P-W-W

next_folder = join(breeze, 'wallpapers', 'Next')
metadata = join(next_folder, 'metadata.json')
old_name = load(open(metadata))['KPlugin']['Name']
target_old = join(plasma_w_w, old_name)
cmake_pww = join(plasma_w_w, 'CMakeLists.txt')
open(cmake_pww, 'a').write(Strings.cmake.format(dir=old_name))
copytree(next_folder, target_old)

# Step 3: Creating New Wallpaper Folder

sizes = join(next_folder, 'contents', 'images')
sizes_dark = join(next_folder, 'contents', 'images_dark')
open(join(next_folder, '.new'), 'w').write('Creating folder...')
open(metadata, 'w').write(Strings.metadata(
    KDiag.ask("New Wallpaper Name:", "Sexy Chimps"),
    KDiag.ask("New Wallpaper Author:", "Mr. Drunk Elk"),
    KDiag.ask("Author Email:", "drunk@elk.com")))

copy(KDiag.get_png('Select Light New PNG Wallpaper Image'),
        join(sizes, '5120x2880.png'))
copy(KDiag.get_png('Select Light Vertical Wallpaper Image: '
    'either same as before for auto crop, or manually 9:16 crop.'),
    join(sizes, '1440x2960.png'))
light_ultrawide = KDiag.get_png('Select Light Ultrawide Wallpaper Image: '
    'it has to be 7680x2160; just close the window if there\'s none')
if light_ultrawide:
    copy(light_ultrawide, join(sizes, '7680x2160.png'))

copy(KDiag.get_png('Select DARK New PNG Wallpaper Image'),
        join(sizes_dark, '5120x2880.png'))
copy(KDiag.get_png('Select DARK Vertical Wallpaper Image: '
    'either same as before for auto crop, or manually 9:16 crop.'),
    join(sizes_dark, '1440x2960.png'))
if light_ultrawide:
    dark_ultrawide = KDiag.get_png('Select Dark Ultrawide Wallpaper Image: '
        'it has to be 7680x2160; just close the window if there\'s none')
    if dark_ultrawide:
        copy(dark_ultrawide, join(sizes_dark, '7680x2160.png'))

# Step 4: Generating Previews

wallpaper = Image.open(join(sizes, '5120x2880.png')).resize((1920, 1080), Image.LANCZOS).convert('RGBA')
dark_wallpaper = Image.open(join(sizes_dark, '5120x2880.png')).resize((1920, 1080), Image.LANCZOS).convert('RGBA')
lnfs = {'light': join(plasma_w, 'lookandfeel', 'org.kde.breeze'),
        'dark': join(plasma_w, 'lookandfeel', 'org.kde.breezedark'),
        'twilight': join(plasma_w, 'lookandfeel', 'org.kde.breezetwilight')}
for mod in ('light', 'dark', 'twilight'):
    which_wallpaper = wallpaper if mod == 'light' else dark_wallpaper
    img = Image.alpha_composite(which_wallpaper, Image.open(f"assets/{mod}.png"))
    img.convert('RGB').save(join(lnfs[mod], 'contents', 'previews', 'fullscreenpreview.jpg'))
    img.resize((600, 337)).save(join(lnfs[mod], 'contents', 'previews', 'preview.png'), format='png', optimize=True)
blurred = Image.alpha_composite(which_wallpaper.filter(ImageFilter.GaussianBlur(20)),
                                Image.open("assets/login.png"))
blurred.resize((600, 337)).save(join(lnfs['light'], 'contents', 'previews', 'lockscreen.png'), format='png', optimize=True)
blurred.save(join(plasma_d, 'sddm-theme', 'preview.png'), format='png', optimize=True)

# Step 4.1: Committing All Changes

os.remove(join(next_folder, '.new'))
repos = ['plasma workspace wallpapers', 'plasma workspace', 'plasma-desktop', 'breeze']
for repo in (git.Repo(breeze), git.Repo(plasma_w), git.Repo(plasma_d), git.Repo(plasma_w_w)):
    repo.git.add('-A')
    repo.git.commit('-m',
        KDiag.ask(f'Commit for {repos.pop()}', 'Move old wallpaper, add new one, update previews'))

KDiag.popup("All done. You can now git push or create MRs with the commits.")
