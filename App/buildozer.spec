[app]

# (str) Title of your application
title = Clima App

# (str) Package name
package.name = clima_App

# (str) Package domain (needed for android/ios packaging)
package.domain = com.metis

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,ttf

# (list) List of inclusions using pattern matching
source.include_patterns = img/*.png,fonts/*.ttf

# (list) Source files to exclude (let empty to not exclude anything)
# source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, venv

# (str) Application versioning
version = 0.1

# (list) Application requirements
requirements = python3,kivy,websockets

# (str) Icon of the application
icon.filename = %(source.dir)s/logo.png

# (list) Supported orientations
orientation = portrait

# Android specific settings
fullscreen = 0

# (list) Permissions
android.permissions = android.permission.INTERNET

# (list) Android architecture to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) Enables Android auto backup feature
android.allow_backup = True

# (str) Android entry point (for PyQt5, no need to modify this unless you use a custom entry point)
android.entrypoint = org.kivy.android.PythonActivity

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
