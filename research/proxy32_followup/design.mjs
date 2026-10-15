import {ARM_DEFINITIONS,CONFIG,TIMING_ORDER} from './p7-frozen/design.mjs';
export {CONFIG,TIMING_ORDER};
export const PHASE='P7b';
export const PARENT_ARCHIVE_SHA256='e09b48282f81034a724db19dfb29f4b6bd7eacdde92b3f963e90f66ae746b32d';
export const NEW_ARM=Object.freeze({id:'dev-proxy32-r120',n:32,rate:120,role:'proxy'});
export const SHARED_ARM=ARM_DEFINITIONS.find(a=>a.role==='shared');
export const REFERENCE_ID='dev-ref256-r480';
export const INHERITED_IDS=[REFERENCE_ID,SHARED_ARM.id];
export const SOURCE_FILES=['PROTOCOL.md','design.mjs','run.mjs','test.mjs','baseline-pins.json','audit_b.py',...['design.mjs','wrapper.mjs','metrics.mjs','run.mjs','test.mjs','p6-core.mjs','PROTOCOL.md','audit.py'].map(f=>'p7-frozen/'+f)];
