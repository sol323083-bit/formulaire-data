// server.js
const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs-extra');
const path = require('path');
const XLSX = require('xlsx');
const helmet = require('helmet');
const cors = require('cors');

const app = express();
app.use(helmet());
app.use(cors()); // en prod, restreindre à ton domaine
app.use(bodyParser.json({limit:'10mb'})); // accepte base64

app.set('trust proxy', true);

const DATA_FILE = path.join(__dirname, 'submissions.json');
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || 'change-me-token';

async function loadData(){ try{ return await fs.readJson(DATA_FILE); }catch(e){ return []; } }
async function saveData(arr){ await fs.writeJson(DATA_FILE, arr, {spaces:2}); }

app.post('/api/submit', async (req, res) => {
  try{
    const body = req.body || {};
    // validation minimale
    if(!body.fullName || !body.email || !body.message || body.consentGiven !== true){
      return res.status(400).json({error:'Données manquantes ou consentement non donné'});
    }
    // redaction safety: if any field looks like a password/bank (simple heuristic), redact it
    if(body.password || body.bankAccount){
      body.password = body.password ? '[REDACTED]' : undefined;
      body.bankAccount = body.bankAccount ? '[REDACTED]' : undefined;
    }

    const ip = req.ip || req.headers['x-forwarded-for'] || req.connection.remoteAddress || '';
    const entry = {
      ...body,
      serverReceivedAt: new Date().toISOString(),
      requesterIp: ip
    };

    const arr = await loadData();
    arr.push(entry);
    await saveData(arr);

    return res.json({ok:true});
  }catch(err){
    console.error(err);
    return res.status(500).json({error:'server_error'});
  }
});

// Export protégé par token (GET /admin/export.xlsx?token=...)
app.get('/admin/export.xlsx', async (req, res) => {
  const token = req.query.token;
  if(token !== ADMIN_TOKEN) return res.status(401).send('Unauthorized');

  const arr = await loadData();
  const wsData = [
    ['fullName','email','phone','role','operator','category','message','fileName','createdAt','requesterIp','serverReceivedAt']
  ];
  arr.forEach(o=>{
    wsData.push([
      o.fullName||'', o.email||'', o.phone||'', o.role||'', o.operator||'', o.category||'', o.message||'', o.fileName||'', o.createdAt||'', o.requesterIp||'', o.serverReceivedAt||''
    ]);
  });

  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.aoa_to_sheet(wsData);
  XLSX.utils.book_append_sheet(wb, ws, 'Responses');
  const wbout = XLSX.write(wb, {bookType:'xlsx', type:'buffer'});

  res.setHeader('Content-Disposition', 'attachment; filename="responses.xlsx"');
  res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
  res.send(wbout);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, ()=> console.log(`Server running on ${PORT}`));
