import React from "react";
import { staticFile } from "remotion";

// Plain CSS @font-face via a <style> tag -- more reliable under render load
// than the JS FontFace()/delayRender() pattern, which timed out
// intermittently once OffthreadVideo-heavy frames were in the mix
// (isolated frame-extraction contexts couldn't reliably clear the
// delayRender handles). staticFile() resolves the right runtime URL;
// css-loader would otherwise treat url() in a plain .css file as a
// webpack module import and fail to resolve it.
export const Fonts: React.FC = () => (
  <style>{`
    @font-face {
      font-family: 'Jersey 20';
      src: url('${staticFile("fonts/Jersey20.woff2")}') format('woff2');
      font-weight: 400;
    }
    @font-face {
      font-family: 'Jersey 25';
      src: url('${staticFile("fonts/Jersey25.woff2")}') format('woff2');
      font-weight: 400;
    }
    @font-face {
      font-family: 'Noto Sans';
      src: url('${staticFile("fonts/NotoSans.woff2")}') format('woff2');
      font-weight: 100 900;
    }
  `}</style>
);
