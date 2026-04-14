"""
MessageMesh - Raspberry Pi Image Slideshow with FTP Sync

Version: 1.2.0

Description:
This Python script enables a Raspberry Pi to display a synchronized image slideshow
by periodically checking an FTP server for new images.

Changelog:
- Version 1.0.0: Initial release with basic functionality.
- Version 1.1.0: Improved image scaling, cleanup functionality, and deployment instructions.
- Version 1.1.1: Updated deployment instructions for FileZilla Server on Windows.
- Version 1.2.0: Added configurable slideshow duration, customization options, and optimizations.

Author: Robert Frantz
Date: 02/06/2024
"""

import ftplib
import os
import pygame
from pygame.locals import *
import time

# FTP server details
ftp_server = "your_ftp_server_ip"
ftp_user = "ftpuser"
ftp_password = "ftpuser_password"
ftp_directory = "/home/ftpuser"


# Local directory to store downloaded images
local_directory = "/path/to/local/images"

# Duration each image is displayed (in seconds)
display_duration = 5

# Sleep interval between each check for new files (in seconds)
check_interval = 300  # 5 minutes

def download_images():
    ftp = ftplib.FTP(ftp_server, ftp_user, ftp_password)
    ftp.cwd(ftp_directory)

    if not os.path.exists(local_directory):
        os.makedirs(local_directory)

    # Get the list of current local files
    local_files = set(os.listdir(local_directory))

    # Get the list of files on the FTP server
    ftp_files = set(ftp.nlst())

    # Calculate the files to be removed from the local directory
    files_to_remove = local_files - ftp_files

    # Remove old files from the local directory
    for file_to_remove in files_to_remove:
        os.remove(os.path.join(local_directory, file_to_remove))

    # Download new files from the FTP server
    for filename in ftp_files:
        local_file_path = os.path.join(local_directory, filename)
        with open(local_file_path, 'wb') as local_file:
            ftp.retrbinary('RETR ' + filename, local_file.write)

    ftp.quit()

def display_slideshow():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    image_files = [f for f in os.listdir(local_directory) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    images = [pygame.image.load(os.path.join(local_directory, image)) for image in image_files]

    start_time = time.time()
    index = 0

    while True:
        for event in pygame.event.get():
            if event.type == KEYDOWN or event.type == QUIT:
                pygame.quit()
                return

        screen.blit(images[index], (0, 0))
        pygame.display.flip()

        if time.time() - start_time > display_duration:
            index = (index + 1) % len(images)
            start_time = time.time()

        pygame.time.delay(100)

def main():
    while True:
        download_images()
        display_slideshow()
        time.sleep(check_interval)

if __name__ == "__main__":
    main()