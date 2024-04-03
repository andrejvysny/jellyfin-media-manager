from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QLabel, QFileDialog, QGroupBox, QSplitter)
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
import os
import sys
import subprocess
import requests
from bs4 import BeautifulSoup
import re
import string
import shutil
from unidecode import unidecode

def sanitize_folder_name(name):
    """
    Sanitizes a string to make it suitable for use as a folder name.
    This function removes problematic characters and can be extended
    to replace spaces with underscores or any other specific requirements.
    """
    # Transliterate non-ASCII characters to their ASCII equivalents
    name = unidecode(name)
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '')
    name = name.replace('  ', ' ')
    name = name.replace('\n', ' ')
    name = name.replace('\t', '')
    name = name.strip()
    return name

def getNameFromWeb(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:

        soup = BeautifulSoup(response.text, 'html.parser')
        h2_content = soup.find('h2').text if soup.find('h2') else "ERR"
        if h2_content == "ERR":
            exit()
        name = sanitize_folder_name(h2_content)
        match = re.search(r'movie/(\d+)-', url)
        movie_id = match.group(1) if match else 'NOID'
        if movie_id == 'NOID':
            exit()
        folderName= f"{name} [tmdbid-{movie_id}]"
        return folderName
    else:
        print(f"Failed to retrieve the webpage, status code: {response.status_code}")


class MainWindow(QMainWindow):
    TMDB_URL="https://www.themoviedb.org?language=en-US"
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Web and Form Application')
        self.selectedFilePath = ""

        self.resize(1920, 1080)  # Set the window size to 800x600 pixels

        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        layout = QVBoxLayout(self.mainWidget)

        self.webView = QWebEngineView()
        self.webView.setUrl(QUrl(self.TMDB_URL))
        self.webView.setMinimumHeight(400)

        self.formWidget = QWidget()
        formLayout = QHBoxLayout(self.formWidget)

        # File selection section
        self.fileButton = QPushButton("Choose File")
        self.fileButton.clicked.connect(self.choose_file)
        self.fileNameLabel = QLabel("No file selected")
        self.fileNameLabel.setWordWrap(True)
        fileLayout = QVBoxLayout()
        fileLayout.addWidget(self.fileButton)
        fileLayout.addWidget(self.fileNameLabel)

        # Play button
        self.playButton = QPushButton("Play")
        self.playButton.setStyleSheet("background-color : green")
        self.playButton.clicked.connect(self.play_file)

        # Checkboxes section
        checkboxLayout = QVBoxLayout()
        self.audioGroup = self.createCheckboxGroup("Audio", ["EN", "SK", "CZ"], checkboxLayout)
        self.subtitleGroup = self.createCheckboxGroup("Subtitles", ["ENtit", "SKtit", "CZtit"], checkboxLayout)

        # Submit button
        self.submitButton = QPushButton("Submit")
        self.submitButton.setStyleSheet("background-color : orange")
        self.submitButton.clicked.connect(self.submit_form)

        # Assembling form layout
        formLayout.addLayout(fileLayout)
        formLayout.addWidget(self.playButton)
        formLayout.addLayout(checkboxLayout)
        formLayout.addWidget(self.submitButton)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.webView)
        splitter.addWidget(self.formWidget)

        layout.addWidget(splitter)

    def createCheckboxGroup(self, title, options, layout):
        group = QGroupBox(title)
        groupLayout = QVBoxLayout()
        for option in options:
            checkBox = QCheckBox(option)
            groupLayout.addWidget(checkBox)
            setattr(self, f"checkBox{option}", checkBox)
        group.setLayout(groupLayout)
        layout.addWidget(group)
        return group

    def choose_file(self):
        # Define the initial directory relative to the current working directory
        initialDir = os.path.join(os.getcwd(), "inputs")
        
        # Check if the directory exists, and create it if it doesn't
        if not os.path.exists(initialDir):
            os.makedirs(initialDir)

        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select File", initialDir, "All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            self.selectedFilePath = fileName
            self.fileNameLabel.setText(os.path.basename(fileName))

    def submit_form(self):
        audioSelections = [checkBox.text() for checkBox in self.audioGroup.findChildren(QCheckBox) if checkBox.isChecked()]
        subtitleSelections = [checkBox.text() for checkBox in self.subtitleGroup.findChildren(QCheckBox) if checkBox.isChecked()]
        print("Selected Audio Options:", audioSelections)
        print("Selected Subtitle Options:", subtitleSelections)
        print("Selected File Path:", self.selectedFilePath)


            # Get current URL from the web view
        currentUrl = self.webView.url().toString()

        folderName=getNameFromWeb(currentUrl)

        # Define the target directory and new filename
        targetDir = os.path.join(os.getcwd(),"movies", folderName)

        originalFileName = os.path.basename(self.selectedFilePath)
        fileNameWithoutExtension, fileExtension = os.path.splitext(originalFileName)
        selectedOptions = ' '.join(audioSelections + subtitleSelections)
        newFileName = f"{folderName} - {selectedOptions}{fileExtension}"
        targetFilePath = os.path.join(targetDir, newFileName)

        if not os.path.exists(targetDir):
            os.makedirs(targetDir)

        # Define the target path for the file
        targetFilePath = os.path.join(targetDir, newFileName)

        # Move and rename the file
        shutil.move(self.selectedFilePath, targetFilePath)

        print(f"File moved and renamed to: {targetFilePath}")

        self.reset_form()

    def reset_form(self):
        self.webView.setUrl(QUrl(self.TMDB_URL))
        self.fileNameLabel.setText("No file selected")
        self.selectedFilePath = ""
        for checkBox in self.audioGroup.findChildren(QCheckBox) + self.subtitleGroup.findChildren(QCheckBox):
            checkBox.setChecked(False)
        #self.choose_file()

    def play_file(self):
        if self.selectedFilePath:
            try:
                subprocess.Popen(["vlc", self.selectedFilePath])
            except FileNotFoundError:
                try:
                    subprocess.Popen(["C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe", self.selectedFilePath.replace('/', '\\')])
                except FileNotFoundError:
                    try:
                        subprocess.Popen(["C:\\Program Files\\VideoLAN\\VLC\\vlc.exe", self.selectedFilePath.replace('/', '\\')])
                    except FileNotFoundError:
                        print(self.selectedFilePath)
                        print("VLC is not installed or the path is incorrect")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
