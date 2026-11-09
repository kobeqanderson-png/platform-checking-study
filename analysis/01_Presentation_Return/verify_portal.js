/* Cross-language numerical checks against independent NumPy computations. */
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.join(__dirname,'site/portal_data'),math=require('./site/portal_math.js');
const {sessions}=JSON.parse(fs.readFileSync(path.join(root,'sessions.json'))),cases=JSON.parse(fs.readFileSync(path.join(root,'verification_cases.json')));
let checked=0,frames=0;
for(const s of sessions){
 const b=fs.readFileSync(path.join(root,s.track));const t=math.decode(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),s.frames);frames+=s.frames;
 for(const c of cases.filter(c=>c.id===s.id)){
  const q=math.area(t,s,c.radius,c.dwell);for(const k of ['episodes','entries','occupied_frames'])assert.strictEqual(q[k],c[k],s.id+' '+k);checked++;
 }
}
// A gap cannot produce a known outside-to-inside transition; a single-frame
// entry remains a visit at zero dwell, while interpolation exclusion splits it.
const s={frames:6,fps:10,pool_px:[0,0,86],p1_normalized:[0,0]};
const xy=new Float64Array([0,0,30,0, 0,0,0,0, 0,0,NaN,NaN, 0,0,0,0, 0,0,0,0, 0,0,30,0]);
const flags=new Uint8Array([9,9,0,11,9,9]);
assert.deepStrictEqual(math.area({xy,flags},s,20,0),{episodes:2,entries:1,occupied_frames:3,seconds:.3,unknownOnsets:1});
assert.equal(math.area({xy,flags},s,20,.2).entries,0);
assert.equal(math.area({xy,flags},s,20,0,true).occupied_frames,2);
console.log(JSON.stringify({sessions:sessions.length,nativeFrames:frames,pythonJavaScriptCases:checked,gapAndDwellFixture:'passed'}));
