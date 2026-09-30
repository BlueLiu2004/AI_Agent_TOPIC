import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {Video} from './Video';
const Root=()=>React.createElement(Composition,{id:'OnboardBot',component:Video,width:1920,height:1080,fps:30,durationInFrames:5760});
registerRoot(Root);
