# Getting started for Street Fighter 6

## Before you continue

- Make sure that you've finished [the setup](../getting_started.md#setup).

## Record replays

Replay Uploader is the program to upload your replays from a fighting game to your cloud storage.

1. Launch Street Fighter 6.
1. Right-click on the `miyoka/upload-replay.ps1` file and select "Run with PowerShell".
    Alternatively, you can open Windows Powershell and execute the following command:
    ```
    powershell.exe -executionpolicy bypass -file .\upload-replay.ps1
    ```

NOTE:

- During the recording, you should **NOT** move your mouse or type keyboard. Otheriwse, the recording will stop.
- The recording could take a few hours to finish. Run it when you don't have a plan to use your computer e.g. run it while you sleep.

## View replays

Replay Viewer is the program to view your replays in your cloud storage.

1. Right-click on the `miyoka/deploy.ps1` file and select "Run with PowerShell".
    Alternatively, you can open Windows Powershell and execute the following command:
    ```
    powershell.exe -executionpolicy bypass -file .\deploy.ps1
    ```

This command will deploy [the replay-viewer Docker image](https://hub.docker.com/r/fgcreplaymiyoka/replay-viewer/tags)
to your cloud server.

After the deployment succeeds, get URL to your replay-viewer.

1. Visit [Google Cloud Platform](https://cloud.google.com/).
1. Navigate to **Your GCP project > Cloud Run > miyoka-viewer**. The URL is displayed at the top.

You can create a bookmark to the URL in your mobile phone so that it's easy to access.

Aside from the initial deployment, you should re-deploy when:

- You changed `config.yml` file.
- You want to use the latest replay-viewer Docker image.
