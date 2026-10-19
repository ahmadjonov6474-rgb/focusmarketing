import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {RANG} from './tokens';
import {Tog} from './Tog';

// To'liq ekran karta. Referensdan o'lchangan o'tish:
// 2 kadr kadr qorayadi -> oq chaqnash -> karta 0.2 s da normal holatga tushadi.
export const Karta = ({ust, band, chiplar = [], quote, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const dip = interpolate(frame, [-2, 0, 1], [0.42, 0.42, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const flash = interpolate(frame, [0, 6], [0.88, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.in(Easing.cubic),
  });
  const fonS = interpolate(frame, [0, 22], [1.12, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const st = (i) => spring({frame: frame - 3 - i * 4, fps, config: {damping: 13, stiffness: 160}});
  const bandW = interpolate(st(1), [0, 1], [0, 100]);

  const chiq = interpolate(frame, [durationInFrames - 7, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: chiq}}>
      <AbsoluteFill style={{transform: `scale(${fonS})`}}>
        <AbsoluteFill
          style={{
            background: `radial-gradient(ellipse 72% 46% at 50% 32%, ${RANG.brendYorqin} 0%, ${RANG.brend} 46%, ${RANG.brendToq} 100%)`,
          }}
        />
        <AbsoluteFill
          style={{
            backgroundImage:
              'repeating-linear-gradient(0deg, rgba(255,255,255,.05) 0 1px, transparent 1px 135px),' +
              'repeating-linear-gradient(90deg, rgba(255,255,255,.05) 0 1px, transparent 1px 135px)',
          }}
        />
        <Tog />

        {ust ? (
          <div
            style={{
              position: 'absolute', left: 0, right: 0, top: 500, textAlign: 'center',
              fontSize: 51, fontWeight: 500, fontStyle: 'italic', color: '#fff',
              textShadow: '0 3px 14px rgba(0,0,0,.45)',
              opacity: st(0),
              transform: `translateY(${interpolate(st(0), [0, 1], [26, 0])}px)`,
            }}
          >
            {ust}
          </div>
        ) : null}

        {band ? (
          <div
            style={{
              position: 'absolute', left: 0, top: 1110, height: 138, width: '100%',
              background: '#fff', display: 'flex', alignItems: 'center',
              justifyContent: 'center', boxShadow: '0 14px 44px rgba(0,0,0,.42)',
              clipPath: `inset(0 ${100 - bandW}% 0 0)`,
            }}
          >
            <span
              style={{
                color: RANG.brend, fontSize: 78, fontWeight: 900, fontStyle: 'italic',
                textTransform: 'uppercase', whiteSpace: 'nowrap', padding: '0 46px',
                transform: `translateX(${interpolate(st(1), [0, 1], [-30, 0])}px)`,
              }}
            >
              {band}
            </span>
          </div>
        ) : null}

        {chiplar.length ? (
          <div
            style={{
              position: 'absolute', left: 0, right: 0, top: 1290, display: 'flex',
              flexDirection: 'column', alignItems: 'center', gap: 18,
            }}
          >
            {chiplar.map((c, i) => {
              const p = st(2 + i * 0.6);
              return (
                <div
                  key={i}
                  style={{
                    background: 'rgba(0,0,0,.26)', border: '2px solid rgba(255,255,255,.3)',
                    borderRadius: 999, padding: '12px 30px', fontSize: 34,
                    fontWeight: 500, fontStyle: 'italic', color: '#fff',
                    opacity: p,
                    transform: `translateY(${interpolate(p, [0, 1], [24, 0])}px)`,
                  }}
                >
                  {c}
                </div>
              );
            })}
          </div>
        ) : null}

        {quote ? (
          <div
            style={{
              position: 'absolute', left: 60, right: 60, top: 1530, textAlign: 'center',
              fontSize: 84, fontWeight: 900, fontStyle: 'italic', lineHeight: 1.08,
              color: '#fff', textShadow: '0 5px 20px rgba(0,0,0,.5)',
              opacity: st(4),
              transform: `translateY(${interpolate(st(4), [0, 1], [34, 0])}px) scale(${interpolate(st(4), [0, 1], [0.94, 1])})`,
            }}
          >
            {quote}
          </div>
        ) : null}
      </AbsoluteFill>

      {dip > 0.002 ? <AbsoluteFill style={{background: '#000', opacity: dip}} /> : null}
      {flash > 0.002 ? <AbsoluteFill style={{background: '#fff', opacity: flash}} /> : null}
    </AbsoluteFill>
  );
};
