"""
MessageMesh - Raspberry Pi Image Slideshow with FTP Sync

Version: 1.3.0

Description:
This Python script enables a Raspberry Pi to display a synchronized image slideshow
by periodically checking an FTP server for new images.

Changelog:
- Version 1.0.0: Initial release with basic functionality.
- Version 1.1.0: Improved image scaling, cleanup functionality, and deployment instructions.
- Version 1.1.1: Updated deployment instructions for FileZilla Server on Windows.
- Version 1.2.0: Added configurable slideshow duration, customization options, and optimizations.
- Version 1.3.0: Improved sync reliability, safer upload handling, and repo organization.

Author: Robert Frantz
Date: 02/06/2024
"""

import ftplib
import os
import time

import pygame
from pygame.locals import K_ESCAPE, KEYDOWN, QUIT

# FTP server details
FTP_SERVER = "your_ftp_server_ip"
FTP_USER = "ftpuser"
FTP_PASSWORD = "ftpuser_password"
FTP_DIRECTORY = "/home/ftpuser"
FTP_TIMEOUT = 30

# Local directory to store downloaded images
LOCAL_DIRECTORY = "/path/to/local/images"

# Duration each image is displayed (in seconds)
DISPLAY_DURATION = 5

# Sleep interval between each check for new files (in seconds)
CHECK_INTERVAL = 300  # 5 minutes

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif")
IGNORED_UPLOAD_SUFFIXES = (".tmp", ".part", ".uploading")


def ensure_local_directory():
    os.makedirs(LOCAL_DIRECTORY, exist_ok=True)


def is_image_file(filename):
    return filename.lower().endswith(IMAGE_EXTENSIONS)


def is_ready_image_file(filename):
    normalized_name = filename.lower()
    return is_image_file(normalized_name) and not normalized_name.endswith(
        IGNORED_UPLOAD_SUFFIXES
    )


def get_local_image_files():
    return {
        entry
        for entry in os.listdir(LOCAL_DIRECTORY)
        if os.path.isfile(os.path.join(LOCAL_DIRECTORY, entry))
        and is_ready_image_file(entry)
    }


def get_ftp_image_files(ftp):
    return {
        entry
        for entry in ftp.nlst()
        if entry not in (".", "..") and is_ready_image_file(entry)
    }


def download_images():
    ensure_local_directory()

    with ftplib.FTP(FTP_SERVER, FTP_USER, FTP_PASSWORD, timeout=FTP_TIMEOUT) as ftp:
        ftp.cwd(FTP_DIRECTORY)

        local_files = get_local_image_files()
        ftp_files = get_ftp_image_files(ftp)

        files_to_remove = local_files - ftp_files
        for file_to_remove in files_to_remove:
            os.remove(os.path.join(LOCAL_DIRECTORY, file_to_remove))

        for filename in ftp_files:
            local_file_path = os.path.join(LOCAL_DIRECTORY, filename)
            temp_file_path = local_file_path + ".tmp"

            with open(temp_file_path, "wb") as local_file:
                ftp.retrbinary(f"RETR {filename}", local_file.write)

            os.replace(temp_file_path, local_file_path)


def load_scaled_image(filename, screen_size):
    image_path = os.path.join(LOCAL_DIRECTORY, filename)
    image = pygame.image.load(image_path).convert()
    return pygame.transform.smoothscale(image, screen_size)


def display_message(screen, font, message):
    screen.fill((0, 0, 0))
    text_surface = font.render(message, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=screen.get_rect().center)
    screen.blit(text_surface, text_rect)
    pygame.display.flip()


def handle_events():
    for event in pygame.event.get():
        if event.type == QUIT:
            return False
        if event.type == KEYDOWN and event.key == K_ESCAPE:
            return False
    return True


def display_slideshow(screen, font):
    sync_deadline = time.monotonic() + CHECK_INTERVAL
    image_files = sorted(get_local_image_files())
    image_index = 0
    last_switch_time = 0
    current_image = None

    while time.monotonic() < sync_deadline:
        if not handle_events():
            return False

        image_files = sorted(get_local_image_files())
        if not image_files:
            display_message(screen, font, "No images available")
            pygame.time.delay(250)
            continue

        if current_image is None or time.monotonic() - last_switch_time >= DISPLAY_DURATION:
            filename = image_files[image_index % len(image_files)]
            current_image = load_scaled_image(filename, screen.get_size())
            image_index = (image_index + 1) % len(image_files)
            last_switch_time = time.monotonic()

        screen.blit(current_image, (0, 0))
        pygame.display.flip()
        pygame.time.delay(100)

    return True


def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("MessageMesh")
    font = pygame.font.Font(None, 48)

    try:
        while True:
            try:
                download_images()
            except (OSError, ftplib.all_errors) as error:
                print(f"Image sync failed: {error}")

            if not display_slideshow(screen, font):
                break
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
