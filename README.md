# zen-browser-installer
This is a program written in Python that allows you to manage the Zen Browser AppImage through a graphical interface and with Linux desktop integration. (Supports Gnome, KDE Plasma, etc.)

https://github.com/user-attachments/assets/cacddfe3-50ce-4eee-bdc4-ec14c0a44f69

You can use the Python3 zen-browser-start command after cloning the repository into the cloned folder, or you can use the pre-compiled binary at https://github.com/krafairus/zen-browser-installer/releases.

Using pyinstaller, you can create a binary containing the program and its necessary resources.

## Steps to compile a portable installer:

# Generate .ts files
pylupdate5 zen-browser-start -ts resources/zn_en.ts resources/zn_pt.ts

# Edit translations with Qt Linguist (do it manually)
linguist resources/zn_en.ts resources/zn_pt.ts

# To compile all:
release resources/zn_*.ts

# Compile the program into a binary using pyinstaller (pip install pyinstaller)
pyinstaller --onefile --windowed --add-data "resources/logo.png:resources" --add-data "resources/zn_en.qm:resources" --add-data "resources/zn_pt.qm:resources" --icon=resources/logo.png zen-browser-start
