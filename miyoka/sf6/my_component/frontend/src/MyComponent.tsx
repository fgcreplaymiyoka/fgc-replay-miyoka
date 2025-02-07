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
  const playbackRateDropdownButtonRef = useRef<HTMLDivElement | null>(null);
  const moveUnitDropdownButtonRef = useRef<HTMLDivElement | null>(null);
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
  const [moveUnit, setMoveUnit] = useState('second')
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

  const movePosition = useCallback((direction: string): void => {
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
  }, [moveUnit]);

  const setComponentValue = useCallback((action: string): void => {
    Streamlit.setComponentValue(action)
  }, []);

  const changePlaybackRate = useCallback((rate: number): void => {
    console.log("changePlaybackRate", rate)
    const player = playerRef.current;
    if (player) {
      player.playbackRate(rate);
    }
  }, []);

  const changeMoveUnit = useCallback((unit: string): void => {
    console.log("changeMoveUnit", unit)
    setMoveUnit(unit);
  }, []);

  const startMoving = (direction: string) => {
    if (intervalRef.current) return;
    intervalRef.current = setInterval(() => {
      movePosition(direction);
    }, 100); // Adjust the interval time as needed
  };

  const stopMoving = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

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
      <button style={style} onMouseDown={() => startMoving("backward")} onTouchStart={() => startMoving("backward")} onMouseUp={stopMoving} onMouseLeave={stopMoving} onTouchEnd={stopMoving}>⬅️</button>
      <button style={style} onMouseDown={() => startMoving("forward")} onTouchStart={() => startMoving("forward")} onMouseUp={stopMoving} onMouseLeave={stopMoving} onTouchEnd={stopMoving}>➡️</button>
      <DropdownButton ref={moveUnitDropdownButtonRef} title={`Unit: ${moveUnit}`} size="sm">
        <Dropdown.Item onClick={() => changeMoveUnit('frame')}>frame</Dropdown.Item>
        <Dropdown.Item onClick={() => changeMoveUnit('second')}>second</Dropdown.Item>
      </DropdownButton>
      <DropdownButton ref={playbackRateDropdownButtonRef} title={`Speed: ${playbackRate}x`} size="sm">
        <Dropdown.Item onClick={() => changePlaybackRate(0.25)}>0.25X</Dropdown.Item>
        <Dropdown.Item onClick={() => changePlaybackRate(0.5)}>0.5X</Dropdown.Item>
        <Dropdown.Item onClick={() => changePlaybackRate(1)}>1X</Dropdown.Item>
        <Dropdown.Item onClick={() => changePlaybackRate(1.5)}>1.5X</Dropdown.Item>
        <Dropdown.Item onClick={() => changePlaybackRate(2)}>2X</Dropdown.Item>
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
