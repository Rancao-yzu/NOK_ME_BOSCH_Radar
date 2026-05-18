import os
import subprocess
import sys
import shutil

# only can be used in windows paltform

IS_WIN = sys.platform == "win32"

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(PROJECT_DIR, "src", "main_ui.py")
OUT_DIR = os.path.join(PROJECT_DIR, "dist")
NAME = "NOK数据合并工具"

COMMON_EXCLUDES = [
    "asyncio",
    "concurrent",
    "ctypes",
    "dbm",
    "distutils",
    "email",
    "ensurepip",
    "html",
    "http",
    "idlelib",
    "json",
    "lib2to3",
    "logging",
    "lzma",
    "multiprocessing",
    "pdb",
    "pickle",
    "pkgutil",
    "plistlib",
    "profile",
    "pstats",
    "py_compile",
    "pyclbr",
    "pydoc",
    "queue",
    "socket",
    "socketserver",
    "sqlite3",
    "ssl",
    "tarfile",
    "test",
    "turtle",
    "turtledemo",
    "unittest",
    "uuid",
    "venv",
    "wsgiref",
    "xml",
    "xmlrpc",
]

LINUX_EXCLUDES = [
    "curses",
]

WIN_EXCLUDES = [
    "msilib",
]

def get_excludes():
    excludes = list(COMMON_EXCLUDES)
    if IS_WIN:
        excludes.extend(WIN_EXCLUDES)
    else:
        excludes.extend(LINUX_EXCLUDES)
    return excludes


def check_pyinstaller():
    if shutil.which("pyinstaller"):
        return True
    print("未找到 PyInstaller，正在安装...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    return True


def clean():
    for folder in ["build", "dist", "__pycache__"]:
        path = os.path.join(PROJECT_DIR, folder)
        if os.path.isdir(path):
            shutil.rmtree(path)
    spec = os.path.join(PROJECT_DIR, f"{NAME}.spec")
    if os.path.isfile(spec):
        os.remove(spec)


def build():
    clean()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--clean",
        "--noconfirm",
        f"--name={NAME}",
        f"--distpath={OUT_DIR}",
        "--add-data", f"{os.path.join(PROJECT_DIR, 'src', 'data_processor.py')}{os.pathsep}.",
    ]

    excludes = get_excludes()
    for mod in excludes:
        cmd.extend(["--exclude-module", mod])

    cmd.append(MAIN_SCRIPT)

    print(f"\n开始打包: {NAME}")
    print(f"当前平台: {'Windows' if IS_WIN else 'Linux'}")
    print(f"入口文件: {MAIN_SCRIPT}")
    print(f"输出目录: {OUT_DIR}")
    print(f"已排除 {len(excludes)} 个不必要的模块\n")

    subprocess.check_call(cmd)

    spec_file = os.path.join(PROJECT_DIR, f"{NAME}.spec")
    if os.path.isfile(spec_file):
        os.remove(spec_file)

    out_name = NAME + (".exe" if IS_WIN else "")
    print(f"\n打包完成！输出文件: {os.path.join(OUT_DIR, out_name)}")


if __name__ == "__main__":
    check_pyinstaller()
    build()