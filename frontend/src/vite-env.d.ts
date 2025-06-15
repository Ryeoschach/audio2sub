// This file is used to declare module types for assets if you import them directly in TypeScript
// e.g., import logo from './logo.svg';

declare module '*.svg' {
    import React = require('react');
    export const ReactComponent: React.FC<React.SVGProps<SVGSVGElement>>;
    const src: string;
    export default src;
  }
  
declare module '*.png';
declare module '*.jpg';
declare module '*.jpeg';
declare module '*.gif';
