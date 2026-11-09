/* Native-frame calculations, independent of drawing and playback. */
(function(root){
 'use strict';
 function decode(buffer,frames){
   if(buffer.byteLength!==frames*33)throw Error('Unexpected native-frame file length');
   const view=new DataView(buffer),xy=new Float64Array(frames*4);
   for(let i=0;i<xy.length;i++)xy[i]=view.getFloat64(i*8,true);
   return {xy,flags:new Uint8Array(buffer,frames*32,frames)};
 }
 function area(track,s,radius,dwell,excludeFill=false){
   const near=[],eligible=[];let end=0,episodes=0,entries=0,occupied=0,unknownOnsets=0;
   const minimum=Math.max(1,Math.ceil(dwell*s.fps));
   for(let i=0;i<s.frames;i++){
     const f=track.flags[i];eligible[i]=!!(f&1)&&!!(f&8)&&(!excludeFill||!(f&2));
     const x=(track.xy[4*i+2]-s.pool_px[0])/s.pool_px[2],y=(track.xy[4*i+3]-s.pool_px[1])/s.pool_px[2];
     near[i]=eligible[i]&&Math.hypot(x-s.p1_normalized[0],y-s.p1_normalized[1])*86<=radius;
   }
   for(let a=0;a<s.frames;a++)if(near[a]){
     end=a+1;while(end<s.frames&&near[end])end++;
     if(end-a>=minimum){episodes++;occupied+=end-a;if(a>0&&eligible[a-1]&&!near[a-1])entries++;else unknownOnsets++;}
     a=end-1;
   }
   return {episodes,entries,occupied_frames:occupied,seconds:occupied/s.fps,unknownOnsets};
 }
 root.PortalMath={decode,area};
 if(typeof module!=='undefined')module.exports=root.PortalMath;
})(typeof globalThis!=='undefined'?globalThis:this);
