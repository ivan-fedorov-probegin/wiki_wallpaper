import datetime
import imghdr
import json
import os
import re
import subprocess
import sys
import urllib
import urlparse

from PIL import Image, ImageDraw, ImageFont


def insert_text(image_path, text):
    img = Image.open(image_path)
    w, h = img.size

    img_txt = Image.new("RGB", (w, h/6),'black')
    draw = ImageDraw.Draw(img_txt)
    font = ImageFont.truetype("fonts/arial.ttf", 60)
    text = text.replace('\n', ' ').replace('\r', '')

    line = ""
    lines = []
    width_of_line = 0
    number_of_lines = 0
    # break string into multi-lines that fit base_width
    for token in text.split():
        token = token + ' '
        token_width = font.getsize(token)[0]
        if width_of_line + token_width < w:
            line += token
            width_of_line += token_width
        else:
            lines.append(line)
            number_of_lines += 1
            width_of_line = 0
            line = ""
            line += token
            width_of_line += token_width
    if line:
        lines.append(line)
        number_of_lines += 1

    y_text = 0  # h
    # render each sentence
    for line in lines:
        width, height = font.getsize(line)
        draw.text(((w - width) / 2, y_text), line, font=font,
                  fill=(255,255,255))
        y_text += height


    img.save(image_path)

    new_im = Image.new('RGB', (w, h + h/6))

    y_offset = 0
    for im in [img, img_txt]:
        new_im.paste(im, (0, y_offset))
        y_offset += im.size[1]

    new_im.save(image_path)


TAG_RE = re.compile(r'<[^>]+>')


def remove_tags(text):
    return TAG_RE.sub(' ', text)


def get_desktop_environment():
    if sys.platform in ["win32", "cygwin"]:
        return "windows"
    elif sys.platform == "darwin":
        return "mac"
    else:  # Most likely either a POSIX system or something not much common
        desktop_session = os.environ.get("DESKTOP_SESSION")
        if desktop_session is not None:  # easier to match if we doesn't have
            #   to deal with caracter cases
            desktop_session = desktop_session.lower()
            if desktop_session in ["gnome", "unity", "cinnamon", "mate",
                                   "xfce4", "lxde", "fluxbox",
                                   "blackbox", "openbox", "icewm", "jwm",
                                   "afterstep", "trinity", "kde"]:
                return desktop_session
            elif "xfce" in desktop_session or desktop_session.startswith(
                    "xubuntu"):
                return "xfce4"
            elif desktop_session.startswith("ubuntu"):
                return "unity"
            elif desktop_session.startswith("lubuntu"):
                return "lxde"
            elif desktop_session.startswith("kubuntu"):
                return "kde"
            elif desktop_session.startswith("razor"):  # e.g. razorkwin
                return "razor-qt"
            elif desktop_session.startswith("wmaker"):  # e.g. wmaker-common
                return "windowmaker"
        if os.environ.get('KDE_FULL_SESSION') == 'true':
            return "kde"
        elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
            if not "deprecated" in os.environ.get('GNOME_DESKTOP_SESSION_ID'):
                return "gnome2"
        # From http://ubuntuforums.org/showthread.php?t=652320
        elif is_running("xfce-mcs-manage"):
            return "xfce4"
        elif is_running("ksmserver"):
            return "kde"
    return "unknown"


def is_running(process):
    try:  # Linux/Unix
        s = subprocess.Popen(["ps", "axw"], stdout=subprocess.PIPE)
    except:  # Windows
        s = subprocess.Popen(["tasklist", "/v"], stdout=subprocess.PIPE)
    for x in s.stdout:
        if re.search(process, x):
            return True
    return False


def set_wallpaper(file_loc):
    desktop_env = get_desktop_environment()
    if desktop_env in ["gnome", "unity", "cinnamon"]:
        uri = "'file://%s'" % file_loc

        args = ["gsettings", "set", "org.gnome.desktop.background",
                "picture-options", "scaled"]
        subprocess.Popen(args)
        args = ["gsettings", "set", "org.gnome.desktop.background",
                "picture-uri", uri]
        subprocess.Popen(args)


def download_image(url):
    url = url.encode('utf8')
    a = urlparse.urlparse(url)
    name = 'images/' + os.path.basename(a.path)

    urllib.urlretrieve(url, name)
    return os.path.abspath( name)


def get_POTD(indent=0):
    today = datetime.datetime.today()
    parameter = (today + datetime.timedelta(days=indent)).strftime("%Y-%m-%d")

    page_url = u"https://en.wikipedia.org/w/api.php?action=parse&prop=images" \
               u"|text&format=json&page=Template:POTD/{0}".format(
        parameter)
    print page_url

    page = urllib.urlopen(page_url).read()
    data = json.loads(page)

    image_parameter = data['parse']['images'][0]
    text = data['parse']['text']['*']
    text = remove_tags(text)
    image_url = u"https://en.wikipedia.org/wiki/Special:Filepath/{0}".format(
        image_parameter)

    return download_image(image_url), text

#
# fullpath, text = get_POTD()
#
# if imghdr.what(fullpath).lower() in ['png', 'jpg', 'jpeg', 'gif']:
#     insert_text(fullpath, text)
# set_wallpaper(fullpath)

# presentation
for i in range(0, 10):

    fullpath, text = get_POTD(i)

    if imghdr.what(fullpath).lower() in ['png', 'jpg', 'jpeg', 'gif']:
        insert_text(fullpath, text)
    set_wallpaper(fullpath)
