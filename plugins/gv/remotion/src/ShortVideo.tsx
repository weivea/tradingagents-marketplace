// src/ShortVideo.tsx
import React from "react";
import { Audio, Sequence, useVideoConfig } from "remotion";
import type { VideoProps } from "./types";
import { generateVariant } from "./theme/variants";
import { calcSectionTimings } from "./utils/audio-sync";
import { Subtitle } from "./components/Subtitle";

import { TitleScene } from "./scenes/TitleScene";
import { DisclaimerScene } from "./scenes/DisclaimerScene";
import { RatingScene } from "./scenes/RatingScene";
import { PointScene } from "./scenes/PointScene";
import { ComparisonScene } from "./scenes/ComparisonScene";
import { DataHighlightScene } from "./scenes/DataHighlightScene";
import { CatalystScene } from "./scenes/CatalystScene";
import { QuoteScene } from "./scenes/QuoteScene";
import { ConclusionScene } from "./scenes/ConclusionScene";
import { FollowScene } from "./scenes/FollowScene";

const CIRCLED = "❶❷❸❹❺❻❼❽❾❿";

export const ShortVideo: React.FC<VideoProps> = ({
  sections,
  timestamps,
  audioPath,
  totalDuration,
  seed,
}) => {
  const { fps } = useVideoConfig();
  const variant = generateVariant(seed);
  const timings = calcSectionTimings(sections, totalDuration, fps);

  // Extract ticker and date from title section
  let ticker = "STOCK";
  let date = "";
  for (const s of sections) {
    if (s.type === "title") {
      const parts = s.headline.split(/\s+/);
      for (const p of parts) {
        if (/^[A-Z]+$/.test(p)) {
          ticker = p;
          break;
        }
      }
    }
    const m = s.body?.match(/(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})/);
    if (m) date = m[1];
  }

  // Track point index for alternating enter direction
  let pointCounter = 0;

  return (
    <>
      {audioPath && <Audio src={audioPath} />}

      {sections.map((section, i) => {
        const timing = timings[i];
        if (!timing) return null;

        const progressPct = Math.round(((i + 1) / sections.length) * 100);
        const progressIcon = CIRCLED[Math.min(i, CIRCLED.length - 1)];

        const commonProps = {
          variant,
          progressPct,
          progressIcon,
          ticker,
          date,
        };

        let sceneElement: React.ReactNode;

        switch (section.type) {
          case "title":
            sceneElement = (
              <TitleScene
                section={section}
                variant={variant}
                ticker={ticker}
                date={date}
              />
            );
            break;
          case "disclaimer":
            sceneElement = (
              <DisclaimerScene section={section} {...commonProps} />
            );
            break;
          case "rating":
            sceneElement = <RatingScene section={section} {...commonProps} />;
            break;
          case "point":
            pointCounter++;
            sceneElement = (
              <PointScene
                section={section}
                {...commonProps}
                enterDirection={pointCounter % 2 === 1 ? "left" : "right"}
              />
            );
            break;
          case "comparison":
            sceneElement = (
              <ComparisonScene section={section} {...commonProps} />
            );
            break;
          case "data-highlight":
            sceneElement = (
              <DataHighlightScene section={section} {...commonProps} />
            );
            break;
          case "catalyst":
            sceneElement = (
              <CatalystScene section={section} {...commonProps} />
            );
            break;
          case "quote":
            sceneElement = <QuoteScene section={section} {...commonProps} />;
            break;
          case "conclusion":
            sceneElement = (
              <ConclusionScene section={section} {...commonProps} />
            );
            break;
          case "follow":
            sceneElement = (
              <FollowScene
                section={section}
                variant={variant}
                ticker={ticker}
                date={date}
              />
            );
            break;
          default:
            sceneElement = <PointScene section={section} {...commonProps} />;
        }

        return (
          <Sequence
            key={i}
            from={timing.startFrame}
            durationInFrames={timing.durationFrames}
          >
            {sceneElement}
          </Sequence>
        );
      })}

      {/* Subtitle overlay */}
      {timestamps.length > 0 && (
        <Sequence from={0} durationInFrames={Math.ceil(totalDuration * fps)}>
          <Subtitle timestamps={timestamps} globalStartFrame={0} />
        </Sequence>
      )}
    </>
  );
};
