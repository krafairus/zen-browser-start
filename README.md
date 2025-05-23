# Zen Browser Start (Zen Browser Installer AppImage)
This is a program written in Python that allows you to manage the Zen Browser AppImage through a graphical interface and with Linux desktop integration. (Supports Gnome, KDE Plasma, etc.)

https://github.com/user-attachments/assets/cacddfe3-50ce-4eee-bdc4-ec14c0a44f69

You can use the "python3 zen-browser-start" command after cloning the repository into the cloned folder, or you can use the pre-compiled binary at https://github.com/krafairus/zen-browser-installer/releases.

WARNING!
This program is not affiliated with the [Zen Team](https://zen-browser.app/about/), nor do we own the logos or trademarks used for this program. All rights belong to their respective owners. It works, but it has a problem loading translations. Since I'm the creator, I speak Spanish, so I didn't see a problem leaving it like that. However, I'll fix it when I have time, as it seems to be a simple problem.

Also, to uninstall the browser, simply right-click "Uninstall Zen Browser" in the desktop environment applications menu on any distro. In environments like DDE, this doesn't seem to be implemented, but you can use the command mentioned below.

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

## Uninstall all
Open your terminal and enter:
.local/share/zenbrowserstart/zen-browser-start --uninstallzenbrowser
for your user folder

or from, replacing "user" with the name of your user folder
/home/user/.local/share/zenbrowserstart/zen-browser-start --uninstallzenbrowser

# UI uninstall:
![imagen](https://github.com/user-attachments/assets/b97bf332-c2af-4273-afd2-2989a7d3548c)

Thanks to the support of the Deepin Spanish community and the Deepines team: https://github.com/deepin-espanol
