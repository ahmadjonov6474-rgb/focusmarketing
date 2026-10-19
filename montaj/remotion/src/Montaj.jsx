import React from 'react';
import {AbsoluteFill, Audio, OffthreadVideo, Sequence, staticFile, useVideoConfig} from 'remotion';
import senariy from './senariy.json';
import {Chip} from './Chip';
import {Karta} from './Karta';
import {Hook} from './Hook';
import {Subtitr} from './Subtitr';

export const Montaj = () => {
  const {fps} = useVideoConfig();
  const kadr = (s) => Math.round(s * fps);

  return (
    <AbsoluteFill style={{backgroundColor: '#000', fontFamily: 'Inter, sans-serif'}}>
      {/* Baza: kesilgan va kadrlangan montaj (42 klip, o'rtacha 1.62 s) */}
      <OffthreadVideo src={staticFile('cut_tez.mp4')} />

      {/* Effektlar treki — sintez qilingan (whoosh/pop/impact/tick) */}
      <Audio src={staticFile('sfx.wav')} volume={0.5} />

      {/* So'zma-so'z subtitr butun davomiylikda */}
      <Subtitr />

      {/* Grafika elementlari — har biri o'z oynasida */}
      {senariy.map((e, i) => {
        const from = kadr(e.start);
        const dur = kadr(e.end) - from;
        return (
          <Sequence key={i} from={from} durationInFrames={dur}>
            {e.tur === 'chip' ? (
              <Chip katta={e.katta} kichik={e.kichik} ikon={e.ikon} durationInFrames={dur} />
            ) : e.tur === 'karta' ? (
              <Karta
                ust={e.ust}
                band={e.band}
                chiplar={e.chiplar}
                quote={e.quote}
                durationInFrames={dur}
              />
            ) : (
              <Hook matn={e.matn} durationInFrames={dur} />
            )}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
