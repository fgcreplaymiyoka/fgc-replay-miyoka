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

### Setup GCP

#### Create your project in Google Cloud Platform

1. [Create a new GCP project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).
1. [Install `gcloud` CLI](https://cloud.google.com/sdk/docs/install).

Tips:

- You can find your project in GCP console. See [this](https://cloud.google.com/resource-manager/docs/creating-managing-projects#identifying_projects) for more info.
- See [GCP doc](gcp.md) for more details.

### Setup Miyoka

1. [Download Miyoka](https://github.com/miyoka/miyoka/releases).
1. Open "Windows Powershell". Execute the following command:
    ```
    powershell.exe -executionpolicy bypass -file .\setup.ps1
    ```
1. Right-click on the `miyoka/setup.ps1` file and select "Run with PowerShell".

<details>
<summary>Explanation:</summary>

TODO: In the script:

Update `config.yaml` file. This contains all of the information for your Miyoka server. Do **NOT** share it with someone else since it contains secrets.

Install python dependencies:
```
cd fgc-replay-miyoka
poetry install --with win
```

Create the configuration file

Run the following command to create `config.yaml` file.

```
make create-config
```

And, update the `<required>` fields in the `config.yaml` file.

This contains all of the information for your Miyoka server. Do **NOT** share it with someone else since it contains secrets.

(To be removed) Install dependencies:

- [Python 3.11.3](https://www.python.org/downloads/windows/)
- [poetry](https://python-poetry.org/docs/#installing-with-pipx)
- GNU make https://gnuwin32.sourceforge.net/packages/make.htm (To be deprecated)

Login to Google Cloud Platform:

Launch a command prompt and run the following commands (Replace `<your-gcp-project-name>`):

```shell
gcloud auth application-default login
gcloud auth application-default set-quota-project <your-gcp-project-name>
gcloud config set project <your-gcp-project-name>
```

Deploy Replay Viewer to Cloud Run:
</details>

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
