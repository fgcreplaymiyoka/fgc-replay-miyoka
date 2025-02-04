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

/**
 * This is a React-based component template. The passed props are coming from the 
 * Streamlit library. Your custom args can be accessed via the `args` props.
 */
function MyComponent({ args, disabled, theme }: ComponentProps): ReactElement {
  const { video_url } = args

  console.log("MyComponent function calling");
  // console.log("theme", theme)
  const playerRef = React.useRef<Player | null>(null);
  const playPauseButtonRef = useRef<HTMLButtonElement | null>(null);
  const speedDropdownButtonRef = useRef<HTMLDivElement | null>(null);
  const initialVideoJsOptions = {
    autoplay: 'muted',
    controls: true,
    responsive: true,
    fluid: true,
    playsinline: true,
    sources: [{
      src: video_url,
      type: 'video/mp4'
    }]
  };

  // const [isFocused, setIsFocused] = useState(false)
  // const [numClicks, setNumClicks] = useState(0)
  const [videoJsOptions, setVideoJsOptions] = useState(initialVideoJsOptions);
  const [playbackRate, setPlaybackRate] = useState(1)

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
      playPauseButtonRef.current!.innerHTML = "pause";
    });

    player.on('pause', function () {
      videojs.log('player is paused');
      playPauseButtonRef.current!.innerHTML = "play";
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

  // useEffect(() => {
  //   Streamlit.setComponentValue(numClicks)
  // }, [numClicks])

  useEffect(() => {
    setVideoJsOptions({
      ...videoJsOptions,
      sources: [{
        src: video_url,
        type: 'video/mp4'
      }]
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
  const onClicked = useCallback((): void => {
    // setNumClicks((prevNumClicks) => prevNumClicks + 1)
    if (playerRef.current?.paused()) {
      playerRef.current?.play();
    } else {
      playerRef.current?.pause();
    }
  }, [])

  const movePosition = useCallback((seconds: number): void => {
    const player = playerRef.current;
    if (player) {
      var currentTime = player?.currentTime() ?? 0
      player.currentTime(currentTime + seconds);
    }
  }, []);

  const setComponentValue = useCallback((action: string): void => {
    Streamlit.setComponentValue(action)
  }, []);

  const changeSpeed = useCallback((rate: number): void => {
    console.log("changeSpeed", rate)
    const player = playerRef.current;
    if (player) {
      player.playbackRate(rate);
    }
  }, []);

  // /** Focus handler for our "Click Me!" button. */
  // const onFocus = useCallback((): void => {
  //   setIsFocused(true)
  // }, [])

  // /** Blur handler for our "Click Me!" button. */
  // const onBlur = useCallback((): void => {
  //   setIsFocused(false)
  // }, [])

  // Show a button and some text.
  // When the button is clicked, we'll increment our "numClicks" state
  // variable, and send its new value back to Streamlit, where it'll
  // be available to the Python program.
  // return (
  //   <span>
  //     Hello, {video_url}! &nbsp;
  //     <button
  //       style={style}
  //       onClick={onClicked}
  //       disabled={disabled}
  //       onFocus={onFocus}
  //       onBlur={onBlur}
  //     >
  //       Click Me!
  //     </button>
  //   </span>
  // )
  // return (
  //   <span>
  //     Hello, {video_url}! &nbsp;
  //   </span>
  // )
  return (
    <>
      <VideoJS options={videoJsOptions} onReady={handlePlayerReady} onUpdate={handlePlayerUpdate} />
      <button style={style} ref={playPauseButtonRef} onClick={onClicked}>Play</button>
      <button style={style} onClick={() => movePosition(-0.016)}>-1f</button>
      <button style={style} onClick={() => movePosition(0.016)}>+1f</button>
      <button style={style} onClick={() => movePosition(-0.16)}>-10f</button>
      <button style={style} onClick={() => movePosition(0.16)}>+10f</button>
      <button style={style} onClick={() => movePosition(-1)}>-1s</button>
      <button style={style} onClick={() => movePosition(1)}>+1s</button>
      <DropdownButton ref={speedDropdownButtonRef} title={`${playbackRate}X`} size="sm">
        <Dropdown.Item onClick={() => changeSpeed(0.25)} href="#/action-1">0.25X</Dropdown.Item>
        <Dropdown.Item onClick={() => changeSpeed(0.5)} href="#/action-2">0.5X</Dropdown.Item>
        <Dropdown.Item onClick={() => changeSpeed(1)} href="#/action-3">1X</Dropdown.Item>
        <Dropdown.Item onClick={() => changeSpeed(1.5)} href="#/action-3">1.5X</Dropdown.Item>
        <Dropdown.Item onClick={() => changeSpeed(2)} href="#/action-3">2X</Dropdown.Item>
      </DropdownButton>
    </>
  );
}

// "withStreamlitConnection" is a wrapper function. It bootstraps the
// connection between your component and the Streamlit app, and handles
// passing arguments from Python -> Component.
//
// You don't need to edit withStreamlitConnection (but you're welcome to!).
export default withStreamlitConnection(MyComponent)
