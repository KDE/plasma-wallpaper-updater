from subprocess import check_output, run
from os.path import exists, join
import os
from shutil import copy
from json import load, dump
from PIL import Image, ImageFilter


class KDiag:

    def get_dir(text):
        KDiag.popup(text)
        return check_output(['kdialog', '--getexistingdirectory','.']).decode().strip()

    def get_png(text):
        KDiag.popup(text)
        return check_output(['kdialog', '--getopenfilename', '.', 'image/png']).decode().strip()

    def error(text):
        run(['kdialog', '--error', text])
        exit()

    def ask(text, default):
        return check_output(['kdialog', '--inputbox', text, default]).decode().strip()

    def popup(text): run(['kdialog', '--msgbox', text])

class Strings:

    cmake = 'install(DIRECTORY {dir} DESTINATION ${{KDE_INSTALL_WALLPAPERDIR}})\n'

    meta = '[Desktop Entry]\nName={name}\n\nX-KDE-PluginInfo-Name=Next\nX-KDE-PluginInfo-Author={author}\nX-KDE-PluginInfo-Email={email}\nX-KDE-PluginInfo-License=CC-BY-SA-4.0'

# Step 0: The only third party library and warnings

try:
    import git
except ModuleNotFoundError:
    KDiag.error("Could not find gitpython. Please run 'python3 -m pip install gitpython'.")
KDiag.popup('Hey! This will remove any local uncommited change to current branch of '
            'breeze, plasma workspace and plasma workspace wallpapers. '
            'Ctrl+C the script instead of pressing OK to avoid this.')

# Step 1: Getting The Repositories

plasma_w, breeze, plasma_w_w = None, None, None
if exists('.magic.config'):
    config = load(open('.magic.config'))
    plasma_w = config.get('plasma-w', None)
    breeze = config.get('breeze', None)
    plasma_w_w = config.get('plasma-w-w', None)
breeze = breeze or KDiag.get_dir('Please select Breeze repository.')
plasma_w = plasma_w or KDiag.get_dir('Please select Plasma Workspace repository.')
plasma_w_w = plasma_w_w or KDiag.get_dir('Please select P-W Wallpaper repository.')
dump({'plasma-w': plasma_w, 'breeze': breeze, 'plasma-w-w': plasma_w_w},
     open('.magic.config', 'w'))

# Step 2.1: Setting Up Git

branch = KDiag.ask('Insert branch name', 'work/new_wallpaper')
for repo in (git.Repo(breeze), git.Repo(plasma_w), git.Repo(plasma_w_w)):
    repo.git.checkout('.')
    repo.git.clean('-fd')
    repo.git.checkout('master')
    try: repo.git.branch('-D', branch)
    except: pass
    repo.git.checkout('-b', branch)

# Step 2: Moving The Old Wallpaper to P-W-W

next_folder = join(breeze, 'wallpapers', 'Next')
metadata = join(next_folder, 'metadata.json')
if exists(next_folder) and not exists(join(next_folder, '.new')):
    old_name = next(l.strip().replace('"Name": ', '').replace('"', '') for l in
                    open(metadata).readlines() if l.strip().startswith('"Name":'))
    cmake_pww = join(plasma_w_w, 'CMakeLists.txt')
    open(cmake_pww, 'a').write(Strings.cmake.format(dir=old_name))
    target_old = join(plasma_w_w, old_name)
    os.rename(next_folder, target_old)
    sizes = join(target_old, 'contents', 'images')
    for filename in os.listdir(sizes):
        if filename in ('5120x2880.png', '1080x1920.png'): continue
        os.remove(join(sizes, filename))
else: KDiag.popup('Old Next folder was already moved. Skipping moving it.')

# Step 3: Creating New Wallpaper Folder

sizes = join(next_folder, 'contents', 'images')
sizes_dark = join(next_folder, 'contents', 'images_dark')
if not exists(next_folder):
    os.mkdir(next_folder)
    open(join(next_folder, '.new'), 'w').write('Creating folder...')
    open(metadata, 'w').write(Strings.meta.format(
        name=KDiag.ask("New Wallpaper Name:", "Sexy Chimps"),
        author=KDiag.ask("New Wallpaper Author:", "Mr. Drunk Elk"),
        email=KDiag.ask("Author Email:", "drunk@elk.com")))
    os.mkdir(content := join(next_folder, 'contents'))
    os.mkdir(sizes)
    os.mkdir(sizes_dark)
    copy(KDiag.get_png('Select Light New PNG Wallpaper Image'),
         join(sizes, 'base_size.png'))
    copy(KDiag.get_png('Select Light Vertical Wallpaper Image: '
        'either same as before for auto crop, or manually 9:16 crop.'),
         join(sizes, 'vertical_base_size.png'))
    copy(KDiag.get_png('Select DARK New PNG Wallpaper Image'),
         join(sizes_dark, 'base_size.png'))
    copy(KDiag.get_png('Select DARK Vertical Wallpaper Image: '
        'either same as before for auto crop, or manually 9:16 crop.'),
         join(sizes_dark, 'vertical_base_size.png'))
    KDiag.popup("I'll now do many image editing stuff. Press OK and take a coffee!")
    try:
        run(['python3', join(breeze, 'wallpapers', 'generate_wallpaper_sizes.py')], cwd=breeze)
    except:
        pass
    Image.open(join(sizes, '440x247.png')).save(join(content, 'screenshot.png'), format='png')
else: KDiag.popup('Old Next folder already made. Skipping creating it.')

# Step 4: Generating Previews

wallpaper = Image.open(join(sizes, '1920x1080.png')).convert('RGBA')
lnfs = {'light': join(plasma_w, 'lookandfeel', 'org.kde.breeze'),
        'dark': join(plasma_w, 'lookandfeel', 'org.kde.breezedark'),
        'twilight': join(plasma_w, 'lookandfeel', 'org.kde.breezetwilight')}
for mod in ('light', 'dark', 'twilight'):
    img = Image.alpha_composite(wallpaper, Image.open(f"assets/{mod}.png"))
    img.convert('RGB').save(join(lnfs[mod], 'contents', 'previews', 'fullscreenpreview.jpg'))
    img.resize((600, 337)).save(join(lnfs[mod], 'contents', 'previews', 'preview.png'), format='png')
blurred = Image.alpha_composite(wallpaper.filter(ImageFilter.GaussianBlur(20)),
                                Image.open("assets/login.png"))
blurred.resize((600, 337)).save(join(lnfs['light'], 'contents', 'previews', 'lockscreen.png'), format='png')
blurred.save(join(plasma_w, 'lookandfeel', 'sddm-theme', 'preview.png'), format='png')

# Step 4.1: Committing All Changes

os.remove(join(next_folder, '.new'))
repos = ['plasma workspace wallpapers', 'plasma workspace', 'breeze']
for repo in (git.Repo(breeze), git.Repo(plasma_w), git.Repo(plasma_w_w)):
    repo.git.add('-A')
    repo.git.commit('-m',
        KDiag.ask(f'Commit for {repos.pop()}', 'Moved old wallpaper, added new one, updated previews'))

KDiag.popup("All done. You can now git push or create MRs with the commits.")
