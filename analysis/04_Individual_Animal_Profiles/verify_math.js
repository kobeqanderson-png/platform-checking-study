const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const data=fs.readFileSync(path.join(__dirname,'exports/profile_data.json'),'utf8');
const source=fs.readFileSync(path.join(__dirname,'profiles.js'),'utf8').split("for(const id of ['sort'")[0];
const context={document:{getElementById:id=>id==='profileData'?{textContent:data}:id==='replay'?{getAttribute:()=> 'explorer.html'}:{value:'test'},querySelector:()=>({getAttribute:()=> 'profile_exports/profile_data.json'})}};
vm.createContext(context);vm.runInContext(source,context);
const expected=JSON.parse(fs.readFileSync(path.join(__dirname,'expected_correlations.json'),'utf8'));
for(const r of expected){const result=vm.runInContext(`corr(S.filter(s=>s.cond===${JSON.stringify(r.cond)}),${JSON.stringify(r.x)},${JSON.stringify(r.y)})`,context);assert.equal(result.n,r.n);assert(Math.abs(result.r-r.rho)<1e-12)}
assert.equal(vm.runInContext('JSON.stringify(ranks([2,2,4,1]))',context),'[2.5,2.5,4,1]');
assert.equal(vm.runInContext('position(S.find(s=>s.id==="kac_d8_2"),"swim_speed")',context),null);
console.log('Browser correlation math matches six independent SciPy calculations; ties and undefined values checked.');
const csv=vm.runInContext('profileCsv(S)',context);assert.equal(csv.split('\r\n').length,92);assert(!csv.split('\r\n')[0].includes('return_timeline'));fs.writeFileSync(path.join(__dirname,'browser_export_check.csv'),csv);
