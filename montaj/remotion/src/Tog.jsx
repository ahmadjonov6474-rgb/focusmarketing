import React from 'react';
import {RANG} from './tokens';

// Karta pastidagi tog' siluetlari — referensdagi bezak
export const Tog = () => (
  <svg
    viewBox="0 0 1080 300"
    preserveAspectRatio="none"
    style={{position: 'absolute', left: 0, right: 0, bottom: 0, width: '100%', height: 300}}
  >
    <path
      d="M0,300 L0,210 L150,110 L260,215 L390,120 L520,230 L650,130 L790,225 L920,125 L1080,235 L1080,300 Z"
      fill={RANG.tog1}
    />
    <path
      d="M0,300 L0,255 L120,195 L250,265 L380,205 L520,275 L660,210 L800,268 L940,200 L1080,262 L1080,300 Z"
      fill={RANG.tog2}
    />
  </svg>
);
