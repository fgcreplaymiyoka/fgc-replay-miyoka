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

Replay Viewer is the program to upload your replays from a fighting game to your cloud storage.

1. Right-click on the `miyoka/deploy-replay-viewer.ps1` file and select "Run with PowerShell".
    Alternatively, you can open Windows Powershell and execute the following command:
    ```
    powershell.exe -executionpolicy bypass -file .\deploy-replay-viewer.ps1
    ```

This command will deploy [the replay-viewer Docker image](https://hub.docker.com/r/fgcreplaymiyoka/replay-viewer/tags)
to your cloud server.
