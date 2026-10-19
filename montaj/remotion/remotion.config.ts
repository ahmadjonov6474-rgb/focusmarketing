import {Config} from '@remotion/cli/config';

// Konteynerda Chromium allaqachon bor; Remotion o'zinikini yuklab olmasin
// (remotion.media domeni tarmoq siyosatida yopiq).
Config.setBrowserExecutable('/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell');
Config.setVideoImageFormat('jpeg');
Config.setConcurrency(4);
Config.setChromiumOpenGlRenderer('swangle');
