import os
import re
import sys
import time
import requests
import subprocess
import shutil
import tempfile
from bs4 import BeautifulSoup
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QPoint, QTranslator, QLocale
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QPushButton,
                             QVBoxLayout, QHBoxLayout, QFrame, QWidget, QMessageBox)

APP_NAME = "Zen Browser"
INSTALL_DIR = os.path.expanduser("~/.local/share/AppImage")
INSTALL_PATH = os.path.join(INSTALL_DIR, "zen-x86_64.AppImage")
DESKTOP_DIR = os.path.expanduser("~/.local/share/applications")
DESKTOP_PATH = os.path.join(DESKTOP_DIR, "zen-browser.desktop")
ICON_DIR = os.path.expanduser("~/.local/share/icons")
ICON_PATH = os.path.join(ICON_DIR, "zen-browser.png")
SCRIPT_DIR = os.path.expanduser("~/.local/share/zenbrowserstart")
SCRIPT_PATH = os.path.join(SCRIPT_DIR, "zen-browser-start")
GITHUB_RELEASES_URL = "https://github.com/zen-browser/desktop/releases"

def get_resource_path(relative_path):
    """Obtiene la ruta absoluta a un recurso, funciona para desarrollo y para PyInstaller"""
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def load_translator(app):
    """Carga las traducciones según el idioma del sistema"""
    locale = QLocale.system().name()
    
    # Si el idioma es español, no cargamos traducción (usamos los textos originales)
    if locale.startswith('es'):
        return
        
    translator = QTranslator()
    translations = {
        'en': 'zn_en.qm',
        'pt': 'zn_pt.qm'
    }
    
    # Buscar la traducción más adecuada
    for lang, qm_file in translations.items():
        if locale.startswith(lang):
            trans_path = get_resource_path(os.path.join('resources', qm_file))
            if translator.load(trans_path):
                app.installTranslator(translator)
                break

class UninstallDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Desinstalar Zen Browser"))
        self.setWindowIcon(QIcon(self.load_icon()))
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        self.label = QLabel(self.tr("¿Estás seguro que deseas desinstalar Zen Browser?"))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        
        button_layout = QHBoxLayout()
        self.cancel_btn = QPushButton(self.tr("Cancelar"))
        self.uninstall_btn = QPushButton(self.tr("Desinstalar"))
        self.uninstall_btn.setStyleSheet("background-color: #e81123; color: white;")
        
        # Eliminar contorno de foco
        self.cancel_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.uninstall_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.cancel_btn.clicked.connect(self.reject)
        self.uninstall_btn.clicked.connect(self.uninstall)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.uninstall_btn)
        
        layout.addWidget(self.label)
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_icon(self):
        try:
            icon_path = get_resource_path(os.path.join('resources', 'logo.png'))
            if os.path.exists(icon_path):
                return icon_path
        except:
            pass
        return ""
    
    def uninstall(self):
        try:
            # Eliminar AppImage
            if os.path.exists(INSTALL_PATH):
                os.remove(INSTALL_PATH)
            
            # Eliminar archivo .desktop
            if os.path.exists(DESKTOP_PATH):
                os.remove(DESKTOP_PATH)
            
            # Eliminar icono
            if os.path.exists(ICON_PATH):
                os.remove(ICON_PATH)
            
            # Eliminar script wrapper
            if os.path.exists(SCRIPT_PATH):
                os.remove(SCRIPT_PATH)
            
            # Eliminar directorio si está vacío
            try:
                os.rmdir(SCRIPT_DIR)
            except OSError:
                pass  # El directorio no está vacío o no existe
            
            QMessageBox.information(self, self.tr("Desinstalación completada"), 
                                  self.tr("Zen Browser ha sido desinstalado correctamente."))
            self.accept()
            QApplication.quit()
            
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr("No se pudo completar la desinstalación: {0}").format(str(e)))

class InstallerWorker(QThread):
    update_signal = Signal(str)
    version_signal = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, args=None):
        super().__init__()
        self.is_installed = False
        self.latest_version = ""
        self.current_version = ""
        self.args = args or []
        self.temp_dir = None

    def run(self):
        try:
            self.create_directories()
            self.is_installed = os.path.exists(INSTALL_PATH) and os.access(INSTALL_PATH, os.X_OK)
            
            if self.is_installed:
                self.check_update()
            else:
                self.install()

        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            # Limpieza final de directorios temporales
            self.cleanup_all_temp_dirs()

    def create_directories(self):
        try:
            os.makedirs(INSTALL_DIR, mode=0o755, exist_ok=True)
            os.makedirs(DESKTOP_DIR, mode=0o755, exist_ok=True)
            os.makedirs(ICON_DIR, mode=0o755, exist_ok=True)
            os.makedirs(SCRIPT_DIR, mode=0o755, exist_ok=True)
            
            # Copiar el script actual a SCRIPT_DIR si no está ya allí
            current_script = os.path.abspath(sys.argv[0])
            if not os.path.samefile(current_script, SCRIPT_PATH):
                shutil.copy2(current_script, SCRIPT_PATH)
                os.chmod(SCRIPT_PATH, 0o755)
                
        except Exception as e:
            raise Exception(self.tr("Error al crear directorios: {0}").format(str(e)))

    def check_update(self):
        self.update_signal.emit(self.tr("Verificando actualizaciones..."))
        try:
            self.current_version = self.get_installed_version()
            self.latest_version, download_url = self.get_latest_version()

            if self.current_version != self.latest_version:
                self.version_signal.emit(self.tr("Nueva versión: {0}").format(self.latest_version))
                self.update_signal.emit(self.tr("Actualizando de v{0}...").format(self.current_version))
                self.download_and_install(download_url)
            else:
                self.update_signal.emit(self.tr("Ya tienes la última versión (v{0})").format(self.current_version))
                self.launch_app(self.args)
        except Exception as e:
            raise Exception(self.tr("Error al verificar actualizaciones: {0}").format(str(e)))

    def install(self):
        try:
            version, download_url = self.get_latest_version()
            self.version_signal.emit(self.tr("Nueva versión: {0}").format(version))
            self.update_signal.emit(self.tr("Descargando Zen Browser..."))
            self.download_and_install(download_url)
        except Exception as e:
            raise Exception(self.tr("Error durante la instalación: {0}").format(str(e)))

    def get_installed_version(self):
        # Crear un directorio temporal específico para esta operación
        with tempfile.TemporaryDirectory(prefix="zen_installer_") as temp_base:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_base)
                
                if not os.access(INSTALL_PATH, os.X_OK):
                    os.chmod(INSTALL_PATH, 0o755)
                
                # Extraer el AppImage en el directorio temporal
                result = subprocess.run(
                    [INSTALL_PATH, "--appimage-extract"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                ini_path = os.path.join("squashfs-root", "application.ini")
                if not os.path.exists(ini_path):
                    raise Exception(self.tr("No se encontró application.ini"))
                
                with open(ini_path, "r") as f:
                    content = f.read()
                    match = re.search(r"Version=([^\n]+)", content)
                    if not match:
                        raise Exception(self.tr("No se encontró la versión"))
                    version = match.group(1)
                
                return version
                
            except subprocess.CalledProcessError as e:
                raise Exception(self.tr("Error al extraer AppImage: {0}").format(e.stderr))
            except Exception as e:
                raise Exception(self.tr("Error al obtener versión instalada: {0}").format(str(e)))
            finally:
                os.chdir(original_cwd)

    def cleanup_all_temp_dirs(self):
        """Limpia todos los directorios temporales conocidos"""
        temp_dirs_to_clean = [
            "squashfs-root",
            "AppDir",
            os.path.expanduser("~/AppDir"),
            os.path.join(SCRIPT_DIR, "AppDir")
        ]
        
        # También buscar en el directorio actual
        current_dir = os.getcwd()
        for item in os.listdir(current_dir):
            if item in ["squashfs-root", "AppDir"]:
                temp_dirs_to_clean.append(os.path.join(current_dir, item))
        
        for temp_dir in temp_dirs_to_clean:
            self.clean_temp_directory(temp_dir)

    def clean_temp_directory(self, temp_dir):
        """Limpia un directorio temporal de forma segura"""
        try:
            if os.path.exists(temp_dir):
                print(f"Limpiando directorio temporal: {temp_dir}")
                # Esperar un poco para asegurar que el proceso haya terminado
                time.sleep(0.5)
                
                # Usar shutil.rmtree para eliminar recursivamente
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        shutil.rmtree(temp_dir)
                        print(f"Directorio eliminado: {temp_dir}")
                        break  # Si tuvo éxito, salir del loop
                    except (OSError, PermissionError) as e:
                        if attempt < max_retries - 1:
                            time.sleep(1)  # Esperar 1 segundo antes de reintentar
                        else:
                            print(f"Advertencia: No se pudo eliminar {temp_dir}: {e}")
        except Exception as e:
            print(f"Advertencia: Error al limpiar {temp_dir}: {e}")

    def get_latest_version(self):
        try:
            response = requests.get(GITHUB_RELEASES_URL, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.endswith("zen-x86_64.AppImage"):
                    match = re.search(r"/download/([^/]+)/zen-x86_64\.AppImage", href)
                    if match:
                        return match.group(1), f"https://github.com{href}"
            raise Exception(self.tr("No se encontró el AppImage en los releases"))
        except Exception as e:
            raise Exception(self.tr("Error al obtener última versión: {0}").format(str(e)))

    def download_and_install(self, url):
        try:
            temp_path = INSTALL_PATH + ".download"
            self.update_signal.emit(self.tr("Descargando actualización... 0%"))
            
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                
                with open(temp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress = int(downloaded / total_size * 100)
                            self.update_signal.emit(self.tr("Descargando actualización... {0}%").format(progress))
            
            if os.path.getsize(temp_path) == 0:
                raise Exception(self.tr("Archivo descargado vacío"))
            
            if os.path.exists(INSTALL_PATH):
                os.remove(INSTALL_PATH)
            os.rename(temp_path, INSTALL_PATH)
            os.chmod(INSTALL_PATH, 0o755)
            
            self.update_signal.emit(self.tr("Instalando..."))
            self.process_appimage()
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise Exception(self.tr("Error en descarga: {0}").format(str(e)))

    def process_appimage(self):
        # Crear un directorio temporal específico para esta operación
        with tempfile.TemporaryDirectory(prefix="zen_appimage_") as temp_base:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_base)
                
                # Extraer el AppImage en el directorio temporal
                subprocess.run([INSTALL_PATH, "--appimage-extract"], check=True)
                
                desktop_src = None
                icon_src = None
                
                for root, dirs, files in os.walk("squashfs-root"):
                    for file in files:
                        if file.lower() == "zen.desktop":
                            desktop_src = os.path.join(root, file)
                        elif file.lower() == "zen.png":
                            icon_src = os.path.join(root, file)
                
                if not desktop_src:
                    raise Exception(self.tr("No se encontró zen.desktop en el AppImage"))
                if not icon_src:
                    raise Exception(self.tr("No se encontró zen.png en el AppImage"))
                
                # Copiar archivos a sus ubicaciones finales
                shutil.copy2(desktop_src, DESKTOP_PATH)
                shutil.copy2(icon_src, ICON_PATH)
                
                # Leer y modificar el archivo .desktop
                with open(DESKTOP_PATH, "r") as f:
                    content = f.read()
                
                # Reemplazar todas las ocurrencias del ejecutable
                content = re.sub(r'Exec\s*=\s*.*zen', f'Exec={SCRIPT_PATH}', content)
                content = re.sub(r'Exec\s*=\s*".*zen"', f'Exec={SCRIPT_PATH}', content)
                content = content.replace("Icon=zen", "Icon=zen-browser")
                
                # Añadir acción de desinstalación
                if "[Desktop Action uninstallzenbrowser]" not in content:
                    content += "\n\n[Desktop Action uninstallzenbrowser]\n"
                    content += f"Name={self.tr('Uninstall Zen Browser')}\n"
                    content += f"Exec={SCRIPT_PATH} --uninstallzenbrowser\n"
                
                # Escribir el archivo .desktop modificado
                with open(DESKTOP_PATH, "w") as f:
                    f.write(content)
                
                self.update_signal.emit(self.tr("¡Instalación completada!"))
                self.launch_app(self.args)
                
            except Exception as e:
                raise Exception(self.tr("Error al procesar AppImage: {0}").format(str(e)))
            finally:
                os.chdir(original_cwd)
                # Limpieza adicional por si acaso
                self.cleanup_all_temp_dirs()

    def launch_app(self, args=None):
        try:
            self.update_signal.emit(self.tr("Iniciando Zen Browser..."))
            cmd = [INSTALL_PATH]
            if args:
                cmd.extend(args)
            
            # Debug: Mostrar comando que se ejecutará
            print(f"Ejecutando: {' '.join(cmd)}")
            
            # Usar Popen con stdin/stdout/stderr redirigidos para evitar problemas
            subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            self.finished.emit(True, self.tr("Aplicación iniciada"))
        except Exception as e:
            raise Exception(self.tr("Error al iniciar: {0}").format(str(e)))

class ZenInstaller(QDialog):
    def __init__(self, args=None):
        super().__init__()
        self.drag_pos = QPoint()
        self.args = args or []
        
        # Verificar si se solicitó desinstalación
        if "--uninstallzenbrowser" in self.args:
            self.show_uninstall_dialog()
            return
            
        self.setup_ui()
        self.check_installation()

    def setup_ui(self):
        self.setWindowTitle(self.tr("Zen Browser"))  
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(400, 400)
        
        self.setWindowIcon(QIcon(self.load_embedded_icon()))
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setObjectName("TitleBar")
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(0, 0, 5, 0)
        title_layout.setSpacing(0)
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setObjectName("CloseButton")
        close_btn.clicked.connect(self.close)
        
        # Eliminar contorno de foco
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.setContentsMargins(30, 20, 30, 30)
        content_layout.setSpacing(15)
        
        self.logo = QLabel()
        self.load_logo()
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        
        self.version_label = QLabel()
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setWordWrap(True)
        self.version_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        self.version_label.hide()
        
        content_layout.addWidget(self.logo)
        content_layout.addWidget(self.status_label)
        content_layout.addWidget(self.version_label)
        
        main_layout.addWidget(self.title_bar)
        main_layout.addWidget(content_widget)
        self.setLayout(main_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                color: #ffffff;
                border: none;
            }
            QFrame#TitleBar {
                background-color: #121212;
                border: none;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton#CloseButton {
                background-color: transparent;
                color: #ffffff;
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 15px;
                outline: none;
            }
            QPushButton#CloseButton:hover {
                background-color: #e81123;
            }
            QPushButton#CloseButton:pressed {
                background-color: #f1707a;
            }
            /* Eliminar el contorno de foco para todos los botones */
            QPushButton:focus {
                outline: none;
                border: none;
            }
        """)

    def show_uninstall_dialog(self):
        dialog = UninstallDialog()
        dialog.exec()
        sys.exit(0)

    def load_embedded_icon(self):
        try:
            icon_path = get_resource_path(os.path.join('resources', 'logo.png'))
            if os.path.exists(icon_path):
                return icon_path
        except:
            pass
        return ""

    def load_logo(self):
        try:
            icon_path = self.load_embedded_icon()
            if icon_path and os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    self.logo.setPixmap(pixmap.scaled(
                        220, 220, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    ))
                    return
        except Exception as e:
            print(f"Error al cargar logo: {e}")

        self.logo.setText("ZEN")
        self.logo.setStyleSheet("""
            font-size: 72px;
            font-weight: bold;
            color: #555555;
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.title_bar.geometry().contains(event.position().toPoint()):
                self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_pos'):
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()

    def check_installation(self):
        self.worker = InstallerWorker(self.args)
        self.worker.update_signal.connect(self.update_status)
        self.worker.version_signal.connect(self.show_version)
        self.worker.finished.connect(self.operation_finished)
        self.worker.start()

    def update_status(self, message):
        self.status_label.setText(message)
        if not message.startswith((self.tr("Actualizando"), self.tr("Descargando"), self.tr("Iniciando"))):
            self.version_label.hide()

    def show_version(self, version_text):
        self.version_label.setText(version_text)
        self.version_label.show()

    def operation_finished(self, success, message):
        if not success:
            self.status_label.setText(self.tr("Error: {0}").format(message))
            self.version_label.hide()
        else:
            # Cerrar la ventana después de un breve retraso
            QTimer.singleShot(1000, self.close)

def create_resource_module():
    resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
    os.makedirs(resources_dir, exist_ok=True)
    init_file = os.path.join(resources_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write("# Resources package\n")

if __name__ == "__main__":
    create_resource_module()
    
    app = QApplication(sys.argv)
    
    # Cargar traducciones
    load_translator(app)
    
    # Obtener argumentos de línea de comandos (omitiendo el nombre del script)
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    
    # Verificar si se está ejecutando desde otra ubicación y copiarse si es necesario
    current_script = os.path.abspath(sys.argv[0])
    if not current_script.startswith(os.path.expanduser("~/.local/share/zenbrowserstart")):
        os.makedirs(SCRIPT_DIR, exist_ok=True)
        shutil.copy2(current_script, SCRIPT_PATH)
        os.chmod(SCRIPT_PATH, 0o755)
    
    installer = ZenInstaller(args)
    installer.show()
    sys.exit(app.exec())