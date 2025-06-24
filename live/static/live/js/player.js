/**
 * Initializes an HLS.js video player for the given video element ID and HLS source URL.
 *
 * This function checks if HLS.js is supported in the browser. If it is, it uses HLS.js to
 * attach the stream to the video element and attempts to autoplay once the manifest is parsed.
 * If HLS.js is not supported but the browser natively supports HLS (e.g., Safari), it sets the
 * `src` of the video element directly and plays on metadata load. Otherwise, it logs an error.
 *
 * @param {string} id - The ID of the HTML video element to attach the stream to.
 * @param {string} src - The URL of the HLS stream (e.g., `.m3u8` file).
 */
const initializeHLSPlayer = (id, src) => {
  const video = document.getElementById(id);
  if (!video) return;

  if (Hls.isSupported()) {
    const hls = new Hls({ lowLatencyMode: true });
    hls.loadSource(src);
    hls.attachMedia(video);
    hls.startLevel = -1;
    hls.on(Hls.Events.MANIFEST_PARSED, function () {
      video.play().catch((err) => {
        console.warn("Autoplay failed:", err);
      });
    });
  } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
    video.src = src;
    video.addEventListener("loadedmetadata", function () {
      video.play().catch((err) => {
        console.warn("Autoplay failed:", err);
      });
    });
  } else {
    console.error("This browser does not support HLS playback.");
  }
};
