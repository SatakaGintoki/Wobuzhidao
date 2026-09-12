import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {requireQ3Delivery, requiredChecks} from './gate.mjs';
const valid = {result_version:'q3-closeout-v1', delivery_gate:{
  checks:Object.fromEntries(requiredChecks.map(name=>[name,true])), meets_delivery_gate:true,
}};
requireQ3Delivery(valid);
for (const name of requiredChecks) {
  const bad = structuredClone(valid);
  bad.delivery_gate.checks[name] = false;
  assert.throws(()=>requireQ3Delivery(bad));
  delete bad.delivery_gate.checks[name];
  assert.throws(()=>requireQ3Delivery(bad));
}
for (const bad of [{}, {...valid,delivery_gate:{checks:{},meets_delivery_gate:true}},
    {...valid,delivery_gate:{...valid.delivery_gate,meets_delivery_gate:false}}]) {
  assert.throws(()=>requireQ3Delivery(bad));
}
const result = {pass:true, required_checks:requiredChecks, failed_and_missing_checks_blocked:30,
  malformed_gates_blocked:3, valid_gate_passes:true};
await fs.writeFile(new URL('../../results/diagnostics/q3_closeout/js_gate_test.json',import.meta.url), JSON.stringify(result,null,2));
console.log(JSON.stringify(result));
