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

### Create your project in Google Cloud Platform

1. [Create a new GCP project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).
1. [Install `gcloud` CLI](https://cloud.google.com/sdk/docs/install).

### Setup Miyoka

1. Install [Python 3.11.3](https://www.python.org/downloads/windows/).
1. Install [Poetry](https://python-poetry.org/docs/#installing-with-pipx), which is a package manager for python projects.
1. [Download Miyoka](https://github.com/fgcreplaymiyoka/fgc-replay-miyoka/releases).
1. Install dependencies of Miyoka:
    1. [Open a **Command Prompt**](https://www.wikihow.com/Open-the-Command-Prompt-in-Windows#:~:text=Open%20the%20%22Start%22%20menu%20and,%22%20and%20press%20%22Enter%22.) in your windows.
    1. [Change the current directory](https://www.geeksforgeeks.org/change-directories-in-command-prompt/) to the downloaded Miyoka project. e.g.
        ```shell
        cd fgc-replay-miyoka
        ```
    1. Install dependencies via poetry:
        ```shell
        poetry install --with win
        ```
1. Right-click on the `miyoka/setup.ps1` file and select "Run with PowerShell".
    Alternatively, you can open Windows Powershell and execute the following command:
    ```
    powershell.exe -executionpolicy bypass -file .\setup.ps1
    ```
    This command creates a `config.yaml` file in your Miyoka folder, which
    contains all of the information for your Miyoka server.
    Do **NOT** share it with someone else since it contains secrets.
1. Update the config file `config.yaml` based on your personal information.
   Most of the fields are pre-filled by `setup.ps1` script,
   and you need to complete the rest of the `<required>` fields manually. e.g. `player_name`

### Setup OBS

1. [Download OBS](https://obsproject.com/download).
1. [Enable websocket server](https://fms-manual.readthedocs.io/en/latest/audience-display/obs-integration/obs-websockets.html).
    - Change secret to "secret"
1. [Change recording resolution](https://obsproject.com/kb/standard-recording-output-guide) to 1280 x 720
1. Change OBS Recording FPS setting from 60. Settings > Video > Integer FPS Value > 60 > Apply
1. Set OUTPUT > Recording > Recording Format to "MPEG-4 (.mp4)"
1. Run OBS Studio as Administrator ([ref](https://www.google.com/search?q=obs+studio+run+as+administrator&rlz=1C1LLPF_enJP1059JP1059&oq=OBS+Studio+admini&gs_lcrp=EgZjaHJvbWUqCAgBEAAYFhgeMgYIABBFGDkyCAgBEAAYFhgeMgoIAhAAGAgYDRgeMgoIAxAAGAgYDRgeMg0IBBAAGIYDGIAEGIoFMg0IBRAAGIYDGIAEGIoFMg0IBhAAGIYDGIAEGIoFMg0IBxAAGIYDGIAEGIoFMg0ICBAAGIYDGIAEGIoFMgoICRAAGIAEGKIE0gEIMzc5MWowajeoAgCwAgA&sourceid=chrome&ie=UTF-8)). This could reduce the frame dropping rate.

<details>
<summary>Explanation:</summary>
Miyoka uses OBS to record replays on the game screen. OBS is quite performant that can reduce the frame dropping rate (approx. 1-5% loss).
Since fighting games are usually processing p1/p2 frames at 60 FPS, the recording FPS must be equal to or greater than that.
</details>

## Continue

- [Getting started for Street Fighter 6](getting_started/sf6.md)

## Delete Miyoka server

You can delete your Miyoka server by the following steps:

- Delete your GCP project. Follow https://cloud.google.com/resource-manager/docs/creating-managing-projects#shutting_down_projects.
  This cascadingly delete all of your resources (e.g. replays in storages).
