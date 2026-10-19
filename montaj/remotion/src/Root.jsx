import React from 'react';
import {Composition} from 'remotion';
import {Montaj} from './Montaj';

export const RemotionRoot = () => (
  <>
    <Composition
      id="Montaj"
      component={Montaj}
      durationInFrames={1703}
      fps={25}
      width={1080}
      height={1920}
    />
  </>
);
