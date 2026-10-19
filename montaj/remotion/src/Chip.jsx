import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {RANG, IKON} from './tokens';

// Video ustidagi chip. Referensda markazdan "pop" bo'lib chiqadi va
// ~6% ortiqcha kengayib orqaga qaytadi — Remotion spring shuni beradi.
export const Chip = ({katta, kichik, ikon = 'odam', durationInFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const kir = spring({frame, fps, config: {damping: 11, stiffness: 180, mass: 0.8}});
  const chiq = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.in(Easing.cubic),
  });

  const scale = interpolate(kir, [0, 1], [0.72, 1]) * interpolate(chiq, [0, 1], [0.93, 1]);
  const y = interpolate(kir, [0, 1], [46, 0]);

  // ichki elementlar birin-ketin (stagger)
  const st = (i) =>
    spring({frame: frame - 3 - i * 3, fps, config: {damping: 14, stiffness: 150}});

  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: 72,
          right: 72,
          top: 1230,
          minHeight: 210,
          borderRadius: 36,
          display: 'flex',
          alignItems: 'center',
          gap: 34,
          padding: '26px 38px',
          background: `linear-gradient(152deg, ${RANG.brendYorqin}, ${RANG.brend} 72%)`,
          border: '3px solid rgba(255,255,255,.85)',
          boxShadow: '0 20px 56px rgba(0,0,0,.55)',
          transform: `translateY(${y}px) scale(${scale})`,
          opacity: Math.min(1, kir * 1.8) * chiq,
        }}
      >
        <div
          style={{
            flex: '0 0 120px',
            height: 120,
            borderRadius: 999,
            background: 'rgba(255,255,255,.18)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transform: `scale(${interpolate(st(0), [0, 1], [0.5, 1])})`,
          }}
        >
          <svg viewBox="0 0 24 24" style={{width: 62, height: 62, fill: '#fff'}}>
            <path d={IKON[ikon] || IKON.odam} />
          </svg>
        </div>
        <div style={{flex: 1, minWidth: 0}}>
          <div
            style={{
              fontSize: 78,
              fontWeight: 900,
              fontStyle: 'italic',
              textTransform: 'uppercase',
              lineHeight: 1,
              color: '#fff',
              opacity: st(1),
              transform: `translateX(${interpolate(st(1), [0, 1], [22, 0])}px)`,
            }}
          >
            {katta}
          </div>
          {kichik ? (
            <div
              style={{
                fontSize: 39,
                fontWeight: 500,
                fontStyle: 'italic',
                color: 'rgba(255,255,255,.93)',
                marginTop: 10,
                opacity: st(2),
                transform: `translateX(${interpolate(st(2), [0, 1], [22, 0])}px)`,
              }}
            >
              {kichik}
            </div>
          ) : null}
        </div>
      </div>
    </AbsoluteFill>
  );
};
