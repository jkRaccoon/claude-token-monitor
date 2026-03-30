"""py2app 빌드 설정. 실행: python3 setup.py py2app"""

from setuptools import setup

APP = ["claude_monitor.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "LSUIElement": True,  # Dock에 표시하지 않음 (메뉴바 전용)
        "CFBundleName": "Claude Monitor",
        "CFBundleDisplayName": "Claude Monitor",
        "CFBundleIdentifier": "com.local.claude-monitor",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
    },
    "packages": ["requests", "keyring", "rumps"],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
    name="Claude Monitor",
)
