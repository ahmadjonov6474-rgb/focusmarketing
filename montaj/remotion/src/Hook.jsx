import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

// Tepadagi hook sarlavha — so'zlar birin-ketin chiqadi (referensda ham shunday)
export const Hook = ({matn, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sozlar = matn.split(' ');
  const chiq = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{opacity: chiq}}>
      <div
        style={{
          position: 'absolute', left: 72, top: 36, right: 80,
          fontSize: 66, fontWeight: 900, fontStyle: 'italic',
          textTransform: 'uppercase', lineHeight: 1.12, color: '#fff',
          textShadow: '0 6px 26px rgba(0,0,0,.8), 0 2px 6px rgba(0,0,0,.9)',
        }}
      >
        {sozlar.map((s, i) => {
          const p = spring({frame: frame - i * 4, fps, config: {damping: 12, stiffness: 170}});
          return (
            <span
              key={i}
              style={{
                display: 'inline-block', marginRight: '.28em',
                opacity: Math.min(1, p * 1.6),
                transform: `translateY(${interpolate(p, [0, 1], [34, 0])}px) scale(${interpolate(p, [0, 1], [0.86, 1])})`,
              }}
            >
              {s}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
