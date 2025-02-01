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

  console.log("MyComponent init");
  // console.log("theme", theme)
  const playerRef = React.useRef<Player | null>(null);
  const playPauseButtonRef = useRef<HTMLButtonElement | null>(null);
  const videoJsOptions = {
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
  const [speed, setSpeed] = useState(1)

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

    // Start from the 1st second
    player.currentTime(1);

    // You can handle player events here, for example:
    player.on('waiting', () => {
      videojs.log('player is waiting');
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
  };

  // useEffect(() => {
  //   Streamlit.setComponentValue(numClicks)
  // }, [numClicks])

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
    const player = playerRef.current;
    if (player) {
      player.playbackRate(rate);
    }
    // setSpeed(rate);
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
      <VideoJS options={videoJsOptions} onReady={handlePlayerReady} />
      <button style={style} ref={playPauseButtonRef} onClick={onClicked}>Play</button>
      <button style={style} onClick={() => movePosition(-0.016)}>-1 frame</button>
      <button style={style} onClick={() => movePosition(0.016)}>+1 frame</button>
      <button style={style} onClick={() => movePosition(-1)}>-1 sec</button>
      <button style={style} onClick={() => movePosition(1)}>+1 sec</button>
      <button style={style} onClick={() => movePosition(5)}>+5 sec</button>
      <button style={style} onClick={() => changeSpeed(0.25)}>0.25X</button>
      <button style={style} onClick={() => changeSpeed(0.5)}>0.5X</button>
      <button style={style} onClick={() => changeSpeed(1)}>1X</button>
      <button style={style} onClick={() => changeSpeed(1.5)}>1.5X</button>
      <button style={style} onClick={() => changeSpeed(2)}>2X</button>
      <DropdownButton id="dropdown-basic-button" title={`${speed}X`} size="sm">
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
