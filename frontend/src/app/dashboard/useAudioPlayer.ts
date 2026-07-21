import { useCallback, useEffect, useRef, useState } from "react";

interface AudioPlayerState {
  isLoading: boolean;
  isPlaying: boolean;
  isPaused: boolean;
  isEnded: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  playbackRate: number;
  isMuted: boolean;
  error: string | null;
}

const initialState: AudioPlayerState = {
  isLoading: false,
  isPlaying: false,
  isPaused: false,
  isEnded: false,
  currentTime: 0,
  duration: 0,
  volume: 1,
  playbackRate: 1,
  isMuted: false,
  error: null,
};

export function useAudioPlayer(src?: string | null) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [state, setState] = useState<AudioPlayerState>(initialState);
  const [source, setSource] = useState<string | null>(src || null);

  const updateState = useCallback((patch: Partial<AudioPlayerState>) => {
    setState((prev) => ({ ...prev, ...patch }));
  }, []);

  useEffect(() => {
    if (!audioRef.current) {
      const audio = new Audio();
      audio.preload = "none";
      audioRef.current = audio;
    }

    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadedMetadata = () => {
      console.info("Audio metadata loaded", { src: audio.currentSrc || source });
      updateState({
        duration: Number.isFinite(audio.duration) ? audio.duration : 0,
        isLoading: false,
        error: null,
      });
    };

    const handleCanPlay = () => {
      console.info("Audio ready for playback", { src: audio.currentSrc || source });
      updateState({ isLoading: false, error: null });
    };

    const handleTimeUpdate = () => {
      updateState({ currentTime: audio.currentTime });
    };

    const handlePlay = () => {
      console.info("Playback started");
      updateState({ isPlaying: true, isPaused: false, isEnded: false, error: null });
    };

    const handlePause = () => {
      console.info("Playback paused");
      updateState({ isPlaying: false, isPaused: true, isEnded: false });
    };

    const handleEnded = () => {
      console.info("Playback completed");
      updateState({ isPlaying: false, isPaused: false, isEnded: true, currentTime: audio.duration || 0 });
    };

    const handleError = () => {
      console.warn("Playback failed", { src: audio.currentSrc || source });
      updateState({
        isLoading: false,
        isPlaying: false,
        isPaused: false,
        error: "Unable to load recording.",
      });
    };

    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("canplay", handleCanPlay);
    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("error", handleError);

    return () => {
      audio.pause();
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("canplay", handleCanPlay);
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("error", handleError);
      audio.src = "";
    };
  }, [source, updateState]);

  useEffect(() => {
    if (src !== source) {
      setSource(src || null);
      updateState({
        isLoading: false,
        isPlaying: false,
        isPaused: false,
        isEnded: false,
        currentTime: 0,
        duration: 0,
        error: null,
      });
    }
  }, [src, source, updateState]);

  const loadRecording = useCallback(async (autoPlay = false) => {
    const audio = audioRef.current;
    if (!audio || !source) {
      updateState({ error: "No recording available." });
      return;
    }

    console.info("Loading recording...", { src: source });
    updateState({ isLoading: true, error: null, isEnded: false });

    audio.src = source;
    audio.load();

    const waitForReady = () => new Promise<void>((resolve, reject) => {
      const onReady = () => {
        audio.removeEventListener("canplay", onReady);
        audio.removeEventListener("error", onError);
        resolve();
      };
      const onError = () => {
        audio.removeEventListener("canplay", onReady);
        audio.removeEventListener("error", onError);
        reject(new Error("Unable to load recording."));
      };

      if (audio.readyState >= 2) {
        resolve();
        return;
      }
      audio.addEventListener("canplay", onReady, { once: true });
      audio.addEventListener("error", onError, { once: true });
    });

    try {
      await waitForReady();
      console.info("Recording URL resolved.");
      if (autoPlay) {
        await audio.play();
        console.info("Playback started");
      }
      updateState({ isLoading: false, error: null });
    } catch (error) {
      console.warn("Playback failed", { src: source, error });
      updateState({ isLoading: false, error: "Unable to load recording." });
    }
  }, [source, updateState]);

  const playRecording = useCallback(async () => {
    const audio = audioRef.current;
    if (!audio || !source) {
      updateState({ error: "No recording available." });
      return;
    }

    if (audio.paused && !audio.ended) {
      try {
        await audio.play();
        updateState({ isPlaying: true, isPaused: false, isEnded: false, error: null });
      } catch (error) {
        console.warn("Playback failed", { src: source, error });
        updateState({ isLoading: false, error: "Unable to load recording." });
      }
      return;
    }

    if (audio.src && audio.currentSrc === source) {
      if (audio.ended) {
        audio.currentTime = 0;
      }
      await loadRecording(true);
      return;
    }

    await loadRecording(true);
  }, [loadRecording, source, updateState]);

  const pausePlayback = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.pause();
    updateState({ isPlaying: false, isPaused: true });
  }, [updateState]);

  const replay = useCallback(() => {
    const audio = audioRef.current;
    if (!audio || !source) return;
    audio.currentTime = 0;
    updateState({ currentTime: 0, isEnded: false, isPlaying: false, isPaused: false });
    void loadRecording(true);
  }, [loadRecording, source, updateState]);

  const seekTo = useCallback((value: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = value;
    updateState({ currentTime: value });
  }, [updateState]);

  const setPlaybackRate = useCallback((rate: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.playbackRate = rate;
    updateState({ playbackRate: rate });
  }, [updateState]);

  const setVolume = useCallback((value: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.volume = value;
    audio.muted = false;
    updateState({ volume: value, isMuted: false });
  }, [updateState]);

  const toggleMute = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.muted = !audio.muted;
    updateState({ isMuted: audio.muted, volume: audio.muted ? 0 : audio.volume });
  }, [updateState]);

  return {
    audioRef,
    ...state,
    loadRecording,
    playRecording,
    pausePlayback,
    replay,
    seekTo,
    setPlaybackRate,
    setVolume,
    toggleMute,
    togglePlayback: state.isPlaying ? pausePlayback : playRecording,
  };
}
