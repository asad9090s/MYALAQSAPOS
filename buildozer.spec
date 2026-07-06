[app]

# Application metadata
title = POS Mobile
package.name = pos_mobile
package.domain = com.pos

# Source code location
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json

# Version
version = 1.0.0

# Application requirements
# Kivy is required, sqlite3 is built into Python, no extra perms needed
requirements = python3,kivy==2.3.0,sqlite3

# Orientation
orientation = portrait

# List of services (none for now)
services =

# Android permissions
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Android API
android.api = 33

# Android min API
android.minapi = 24

# Android NDK
android.ndk = 25b

# Android SDK path (set this if you have it, otherwise buildozer will download)
# android.sdk_path = /home/user/.buildozer/android/platform/android-sdk

# Python for Android
p4a.source_dir = /home/user/.buildozer/python-for-android
p4a.branch = master

# Build options
fullscreen = 0
android.presplash_color = #1e293b
android.icon = assets/icon.png
android.presplash_filename = assets/presplash.png

# Build type - release ke saath sign karna padega Play Store ke liye
# debug default - testing ke liye
# release - production ke liye (keystore chahiye)
mode = debug

# Architecture (modern phones)
android.archs = arm64-v8a, armeabi-v7a

# Allow backup
android.allow_backup = 1

# Logcat filter (for debugging)
logcat_filters = *:S python:V

# Copy libs
android.add_src =

# JNIus (Java bridge - optional, needed for camera etc)
# requirements += pyjnius

# Custom Java files
# android.add_src = src

# Native libraries
# android.add_libs = libs/*.so

# Bypass certificate check (only for dev)
# no-compile-pyo = 1

[buildozer]
log_level = 2
warn_on_root = 1
