# This should be reimplemented in python https://github.com/sign-language-processing/signwriting/issues/1
import os
import subprocess
import tempfile

from PIL import Image

TMPDIR = os.getenv('TMPDIR', '/tmp')
REPO_URL = 'https://github.com/sutton-signwriting/font-db.git'
REPO_DIR = os.path.join(TMPDIR, 'font-db')


def clone_repo_if_needed():
    if not os.path.exists(REPO_DIR):
        print(f"Cloning repository into {REPO_DIR}...")
        subprocess.run(["git", "clone", REPO_URL, REPO_DIR], check=True)

    # check if node_modules exists
    if not os.path.exists(os.path.join(REPO_DIR, 'node_modules')):
        print("Installing dependencies...")
        subprocess.run(["npm", "install"], cwd=REPO_DIR, check=True)


def signwriting_to_image(fsw: str):
    clone_repo_if_needed()

    # pylint: disable=consider-using-with
    temp_output = tempfile.NamedTemporaryFile(suffix='.png').name
    cmd = f'node {REPO_DIR}/fsw/fsw-sign-png "{fsw}" {temp_output}'
    subprocess.run(cmd, shell=True, check=True)

    return Image.open(temp_output)  # this is RGBA
