# Getting started

## Before you start

### Supported fighting games

Here is the list of fighting games that confirmed working in Miyoka:

- Street Fighter 6

Community contributions are welcome to support more fighting games.

### Confirm that you can watch replays in the fighting game

- You have a desktop or laptop that runs Windows 11.
- You have installed Steam.
- You have purchased the fighting game on Steam.
- You can launch the game and access your replays in the game UI.

## Setup

Tutorial video:

[![Tutorial](https://img.youtube.com/vi/DYYpQVEDRVA/0.jpg)](https://www.youtube.com/watch?v=DYYpQVEDRVA)

### Create your project in Google Cloud Platform

NOTE:
If you want to [save replays in your computer instead of cloud storage](./getting_started/sf6.md#save-replays-in-your-computer), skip this step.

1. [Create a new GCP project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#console).
1. [Install `gcloud` CLI](https://cloud.google.com/sdk/docs/install). Follow the instruction to login to the GCP from `gcloud`.

### Setup Miyoka

1. Install [Python 3.11.3](https://www.python.org/downloads/windows/).
    - Recommended: [Windows installer (64-bit)](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe)
1. Install [Poetry](https://python-poetry.org/docs/#installing-with-pipx).
    - Recommended: [With the official installer](https://python-poetry.org/docs/#installing-with-the-official-installer). Follow the instruction to add PATH configuration in your terminal.
1. [Download Miyoka](https://github.com/fgcreplaymiyoka/fgc-replay-miyoka/releases).
    1. Click **Source code (zip)** of the latest version.
    1. Right-click the downloaded file and select **Extract All**.
1. Install dependencies of Miyoka:
    1. Open a **Windows Powershell** in your windows.
        1. Click the Start or Search icon, and then type "powershell" in the search box.
        1. Click "Open" or "Run as Administrator" to open PowerShell either normally or with administrative privileges.
    1. Change the current directory to the downloaded Miyoka project. e.g.
        ```shell
        cd c:\Users\name\Downloads\fgc-replay-miyoka-x.x.x\fgc-replay-miyoka-x.x.x
        ```
        Tips: To copy the path, you can drag-and-drop the folder from the File explorer to the Powershell terminal.
    1. Install dependencies via poetry:
        ```shell
        poetry install --with win
        ```
1. Right-click on the `miyoka/setup.ps1` file and click **Run with PowerShell**.
    Alternatively, you can open Windows Powershell and execute the following command:
    ```shell
    powershell.exe -executionpolicy bypass -file .\setup.ps1
    ```
    This command creates a `config.yaml` file in your Miyoka folder, which
    contains all of the information for your Miyoka server.
    Do **NOT** share it with someone else since it contains secrets.
1. Replace `<required>` values by your information in `config.yaml`.

### Setup OBS

1. [Download OBS](https://obsproject.com/download).
1. Create a new Game Capture source.
    1. Click **Sources > + (Add Source)** button.
    1. Select **Game Capture** and click **OK**.
    1. Select **Mode > Capture Specific Window**.
    1. Select **Window > [<game-title>.exe]** and click **OK**.
1. [Enable websocket server](https://fms-manual.readthedocs.io/en/latest/audience-display/obs-integration/obs-websockets.html):
    1. Click **Tools > WebSocket Server Settings**.
    1. Check **Enable WebSocket server**.
    1. Change the **Server Password** to `secret`.
    1. Click **Apply** button.
1. [Change recording resolution](https://obsproject.com/kb/standard-recording-output-guide) to 640x360 or 1280x720:
    1. Click **Controls > Settings**.
    1. Select **Video** menu.
    1. Ensure **Base (Canvas) Resolution** is 1280x720.
    1. Ensure **Output (Scaled) Resolution** is 640x360 or 1280x720. If you mainly watch replays without Wi-fi, it's recommended to set a lower resolution for faster streaming.
    1. Ensure **Common FPS Values** is selected, which records the replays 60 FPS.
    1. Click **Apply**.
1. Output settings:
    1. Click **Controls > Settings**.
    1. Select **Output** menu.
    1. Ensure **Recording format** is **MPEG-4 (.mp4)**.
    1. Ensure **Video Encoder** is **Hardware (NVENC, H.264)** or **Software (x264)** (If your graphic card doesn't support hardware acceleration).
    1. Click **Apply**.

## Continue

- [Getting started for Street Fighter 6](getting_started/sf6.md)

## Delete Miyoka server

You can delete your Miyoka server by the following steps:

- Delete your GCP project. Follow https://cloud.google.com/resource-manager/docs/creating-managing-projects#shutting_down_projects.
  This cascadingly delete all of your resources (e.g. replays in storages).
