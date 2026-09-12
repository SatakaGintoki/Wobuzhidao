import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
import {requireQ3Delivery} from './gate.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'../..');
const original=path.join(root,'results/archive/q3-pre-closeout-20260911/results/result3.xlsx');
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(original));
if(process.argv.includes('--preview-only')){
  console.log((await wb.inspect({kind:'workbook,sheet,table',maxChars:1200,tableMaxRows:3,tableMaxCols:4})).ndjson);
  const view=await wb.render({sheetName:'水分浓度',range:'A1:H10',scale:1.3,format:'png'});
  await fs.writeFile(path.join(here,'before.png'),new Uint8Array(await view.arrayBuffer()));
} else {
  const v=JSON.parse(await fs.readFile(path.join(root,'results/diagnostics/q3_closeout/pre_export.json'),'utf8'));
  requireQ3Delivery(v);
  const data=JSON.parse(await fs.readFile(path.join(root,'results/diagnostics/q3_closeout/excel_payload.json'),'utf8'));
  const sheet=wb.worksheets.getItem(data.sheet);
  const matrix=[data.headers,...data.rows],nr=matrix.length,nc=matrix[0].length;
  sheet.getUsedRange().clear({applyTo:'contents'});
  sheet.getRangeByIndexes(0,0,nr,nc).values=matrix;
  sheet.getRangeByIndexes(1,1,nr-1,nc-1).setNumberFormat('0.0000');
  sheet.getRangeByIndexes(1,0,nr-1,1).setNumberFormat('0');
  sheet.getRangeByIndexes(nr-1,0,1,1).setNumberFormat('0.00');
  sheet.getRangeByIndexes(0,0,nr,1).format.columnWidth=30;
  sheet.getRangeByIndexes(0,1,nr,nc-1).format.columnWidth=11;
  wb.recalculate();
  console.log((await wb.inspect({kind:'table',range:'水分浓度!A1:F4',include:'values,formulas',tableMaxRows:4,tableMaxCols:6,maxChars:1200})).ndjson);
  console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!',options:{useRegex:true,maxResults:10},maxChars:1000})).ndjson);
  const preview=await wb.render({sheetName:data.sheet,range:'A1:H10',scale:1.3,format:'png'});
  await fs.writeFile(path.join(here,'after.png'),new Uint8Array(await preview.arrayBuffer()));
  const tail=await wb.render({sheetName:data.sheet,range:`A${nr-6}:V${nr}`,scale:1,format:'png'});
  await fs.writeFile(path.join(here,'tail.png'),new Uint8Array(await tail.arrayBuffer()));
  const output=await SpreadsheetFile.exportXlsx(wb);await output.save(data.path);
  console.log(JSON.stringify({path:data.path,rows:nr,cols:nc}));
}
