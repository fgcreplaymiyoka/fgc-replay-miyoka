# Getting started for Street Fighter 6

## Before you continue

- Make sure that you've finished [the setup](../getting_started.md#setup).

## Record replays

Replay Recorder is the automation for recording replays in the game.

1. Launch Street Fighter 6.
1. Right-click on the `miyoka/record-replay.ps1` file and click **Run with PowerShell**.
    Alternatively, you can open Windows Powershell and execute the following command:
    ```shell
    powershell.exe -executionpolicy bypass -file .\record-replay.ps1
    ```

NOTE:

- During the recording, you should **NOT** move your mouse or type keyboard. Otheriwse, the recording will stop.
- The recording could take a few hours to finish. Run it when you don't have a plan to use your computer e.g. run it while you sleep.

### Save replays in your computer

You can record and save replays in your computer instead of uploading the videos to google cloud storage.
To do so, set `local_file_storage` to `replay_recorder.save_to` in `config.yaml`.

The recorded replays can be found in the `replays` folder in the miyoka directory.

## View replays

Replay Viewer is the program to view your replays in your cloud storage.

1. Right-click on the `miyoka/deploy.ps1` file and click **Run with PowerShell**.
    Alternatively, you can open Windows Powershell and execute the following command:
    ```shell
    powershell.exe -executionpolicy bypass -file .\deploy.ps1
    ```

After the deployment succeeds, get URL to your replay-viewer.

1. Visit [Google Cloud Platform](https://cloud.google.com/).
1. Navigate to **Your GCP project > Cloud Run > miyoka-viewer**. The URL is displayed at the top.

You can create a bookmark to the URL in your mobile phone so that it's easy to access.

In addition to the initial deployment, you should re-deploy when you changed `replay_viewer` setting in `config.yml` file.

## Troubleshooting

### Replay Viewer stopped working after I changed my player name in the game

If you have changed your player name in the game, you might encounter the following error:

```plaintext
Length of Replay dataset and Player dataset don't match. Please check that the game.players[].pattern in config.yaml is set correctly.
```

To resolve this error, register both your new name and old name to the `game.players[].pattern` in config.yaml. For example:

```yaml
game:
  players:
    - name: My Player name
      id: xxxxxxxx
      pattern: MyNewNmae|MyOldNmae
```