import {
  Streamlit,
  withStreamlitConnection,
  ComponentProps,
} from "streamlit-component-lib"
import React, { useCallback, useEffect, useMemo, useRef, useState, ReactElement } from "react"
import VideoJS from "./VideoJS"
import videojs from 'video.js';
import Player from 'video.js/dist/types/player';
import Dropdown from 'react-bootstrap/Dropdown';
import DropdownButton from 'react-bootstrap/DropdownButton';
import Button from 'react-bootstrap/Button';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';

/**
 * This is a React-based component template. The passed props are coming from the 
 * Streamlit library. Your custom args can be accessed via the `args` props.
 */
function VideoComponent({ args, disabled, theme }: ComponentProps): ReactElement {
  const { video_url, metadata } = args

  console.log("VideoComponent function calling: ", video_url, metadata);
  const playerRef = React.useRef<Player | null>(null);
  const playPauseButtonRef = useRef<HTMLButtonElement | null>(null);
  const playbackRateDropdownButtonRef = useRef<HTMLDivElement | null>(null);
  const initialVideoJsOptions = {
    autoplay: 'muted',
    controls: true,
    responsive: true,
    fluid: true,
    playsinline: true,
    sources: [{
      src: video_url,
      type: video_url.endsWith('.m3u8') ? 'application/x-mpegURL' : 'video/mp4'
    }]
  };

  const [videoJsOptions, setVideoJsOptions] = useState(initialVideoJsOptions);
  const [playbackRate, setPlaybackRate] = useState(1)
  // https://dirask-react.medium.com/react-mouse-button-press-and-hold-example-9f749300f71a
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const style: React.CSSProperties = useMemo(() => {
    if (!theme) return {}

    // Use the theme object to style our button border. Alternatively, the
    // theme style is defined in CSS vars.
    // const borderStyling = `1px solid ${isFocused ? theme.primaryColor : "gray"}`
    console.log("theme", theme)
    const borderStyling = `1px solid ${theme.secondaryBackgroundColor}`
    return {
      border: borderStyling,
      outline: borderStyling,
      color: theme.textColor,
      font: theme.font,
      borderRadius: "5px",
      backgroundColor: theme.backgroundColor,
    }
  }, [theme])

  const handlePlayerReady = (player: Player) => {
    playerRef.current = player;

    // You can handle player events here, for example:
    // https://gist.github.com/alexrqs/a6db03bade4dc405a61c63294a64f97a
    player.on('waiting', () => {
      videojs.log('player is waiting');
    });

    player.on('ratechange', function () {
      videojs.log('player rate is changed');
      setPlaybackRate(player.playbackRate() ?? 1);
    });

    player.on('dispose', () => {
      videojs.log('player will dispose');
    });

    player.on('play', function () {
      videojs.log('player is played');
      playPauseButtonRef.current!.innerHTML = "⏸️";
    });

    player.on('pause', function () {
      videojs.log('player is paused');
      playPauseButtonRef.current!.innerHTML = "▶️";
    });

    player.on('ended', function () {
      videojs.log('player is ended');
    });

    player.on('error', function () {
      videojs.log('player is error');
    });

    player.on('loadeddata', function () {
      videojs.log('player is loadeddata');
    });

    player.on('loadstart', function () {
      videojs.log('player is loadstart');
      player.currentTime(1);
    });

    player.on('stalled', function () {
      videojs.log('player is stalled');
    });

    player.on('firstplay', function () {
      videojs.log('player is firstplay');
    });

    player.on('playerreset', function () {
      videojs.log('player is playerreset');
    });
  };

  const handlePlayerUpdate = (player: Player) => {
    playerRef.current = player;
  };

  useEffect(() => {
    setVideoJsOptions({
      ...videoJsOptions,
      sources: [
        {
          src: video_url,
          type: video_url.endsWith('.m3u8') ? 'application/x-mpegURL' : 'video/mp4'
        }
      ]
    });
  }, [video_url]);

  // setFrameHeight should be called on first render and evertime the size might change (e.g. due to a DOM update).
  // Adding the style and theme here since they might effect the visual size of the component.
  useEffect(() => {
    Streamlit.setFrameHeight()
  }, [style, theme])

  useEffect(() => {
    console.log("theme changed", theme)
  }, [theme])

  /** Click handler for our "Click Me!" button. */
  const playPause = useCallback((): void => {
    if (playerRef.current?.paused()) {
      playerRef.current?.play();
    } else {
      playerRef.current?.pause();
    }
  }, [])

  const movePosition = useCallback((direction: string, moveUnit: string): void => {
    const player = playerRef.current;
    if (player) {
      var currentTime = player?.currentTime() ?? 0
      var moveValue = 1

      switch (moveUnit) {
        case "frame":
          moveValue = 0.016
          break;
        case "second":
          moveValue = 1
          break;
      }

      if (direction === "forward") {
        player.currentTime(currentTime + moveValue);
      } else {
        player.currentTime(currentTime - moveValue);
      }
    }
  }, []);

  // const setComponentValue = useCallback((action: string): void => {
  //   Streamlit.setComponentValue(action)
  // }, []);

  const changePlaybackRate = useCallback((rate: number): void => {
    console.log("changePlaybackRate", rate)
    const player = playerRef.current;
    if (player) {
      player.playbackRate(rate);
    }
  }, []);

  const stopMoving = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const containerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '1px', // Adjust the gap between elements as needed
  };

  const replayInfoStyle: React.CSSProperties = {
    fontSize: '50%',
  };

  const replayInfoStyleSmall: React.CSSProperties = {
    fontSize: '80%',
  };

  return (
    <>
      <Container style={replayInfoStyle} fluid="sm">
        <Row>
          <Col>
            <Row>{metadata["player_1"]["player_name"]} | {metadata["player_1"]["character"].toUpperCase()} ({metadata["player_1"]["mode"]}) </Row>
            <Row>{metadata["player_1"]["result"].toUpperCase()} ({metadata["player_1"]["rounds"]})</Row>
            <Row>{metadata["player_1"]["rank"].toUpperCase()} ({metadata["player_1"]["point"]})</Row>
          </Col>
          <Col>
          <Row><div className="text-center">Round: {metadata["round"]} / {metadata["total_round_count"]}</div></Row>
            <Row style={replayInfoStyleSmall}><div className="text-center">Replay ID: {metadata["replay_id"]}</div></Row>
            <Row style={replayInfoStyleSmall}><div className="text-center">Play date: {metadata["played_at"]}</div></Row>
          </Col>
          <Col >
            <Row><div className="text-right">{metadata["player_2"]["player_name"]} | {metadata["player_2"]["character"].toUpperCase()} ({metadata["player_2"]["mode"]})</div></Row>
            <Row><div className="text-right">{metadata["player_2"]["result"].toUpperCase()} ({metadata["player_2"]["rounds"]})</div></Row>
            <Row><div className="text-right">{metadata["player_2"]["rank"].toUpperCase()} ({metadata["player_2"]["point"]})</div></Row>
          </Col>
        </Row>
      </Container>
      <VideoJS options={videoJsOptions} onReady={handlePlayerReady} onUpdate={handlePlayerUpdate} />
      <div style={containerStyle}>
        <Button style={style} ref={playPauseButtonRef} onClick={playPause} variant="light">▶️</Button>
        <Button style={style} onClick={() => movePosition('backward', 'frame')} variant="light">-1f</Button>
        <Button style={style} onClick={() => movePosition('forward', 'frame')} variant="light">+1f</Button>
        <Button style={style} onClick={() => movePosition('backward', 'second')} variant="light">-1s</Button>
        <Button style={style} onClick={() => movePosition('forward', 'second')} variant="light">+1s</Button>
        <DropdownButton style={style} variant="light" ref={playbackRateDropdownButtonRef} title={`Speed: ${playbackRate}x`} size="sm">
          <Dropdown.Item onClick={() => changePlaybackRate(0.25)}>0.25X</Dropdown.Item>
          <Dropdown.Item onClick={() => changePlaybackRate(0.5)}>0.5X</Dropdown.Item>
          <Dropdown.Item onClick={() => changePlaybackRate(1)}>1X</Dropdown.Item>
          <Dropdown.Item onClick={() => changePlaybackRate(1.5)}>1.5X</Dropdown.Item>
          <Dropdown.Item onClick={() => changePlaybackRate(2)}>2X</Dropdown.Item>
        </DropdownButton>
      </div>
    </>
  );
}

// "withStreamlitConnection" is a wrapper function. It bootstraps the
// connection between your component and the Streamlit app, and handles
// passing arguments from Python -> Component.
//
// You don't need to edit withStreamlitConnection (but you're welcome to!).
export default withStreamlitConnection(VideoComponent)
