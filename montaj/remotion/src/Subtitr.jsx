import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {RANG} from './tokens';
import cues from './soz.json';

// So'zma-so'z subtitr: har guruh kichikdan kattaga "pop" bo'lib chiqadi.
export const Subtitr = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  const faol = cues.filter((c) => t >= c.start && t < c.end);
  if (!faol.length) return null;

  return (
    <AbsoluteFill>
      {faol.map((c, i) => {
        const p = spring({
          frame: frame - Math.round(c.start * fps),
          fps,
          config: {damping: 13, stiffness: 220, mass: 0.6},
        });
        return (
          <div
            key={i}
            style={{
              position: 'absolute', left: 110, right: 60, top: 980,
              fontSize: 62, fontWeight: 700, letterSpacing: '.02em',
              textTransform: 'uppercase', color: RANG.ikkilamchi,
              textShadow: '0 4px 18px rgba(0,0,0,.85), 0 2px 4px rgba(0,0,0,.9)',
              opacity: Math.min(1, p * 2),
              transform: `scale(${interpolate(p, [0, 1], [0.86, 1])})`,
              transformOrigin: 'left center',
            }}
          >
            {c.text}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
