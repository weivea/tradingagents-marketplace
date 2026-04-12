import { Config } from "@remotion/cli/config";

// Use PNG for intermediate frames — lossless 8-bit preserves gradient
// precision. JPEG introduces compression artifacts that worsen banding.
Config.setVideoImageFormat("png");
Config.setOverwriteOutput(true);
