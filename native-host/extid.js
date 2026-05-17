#!/usr/bin/env node
'use strict';
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const scriptDir = __dirname;
const manifestPath = path.join(scriptDir, '..', 'manifest.json');
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));

const keyB64 = manifest.key || '';
let h;
if (keyB64) {
    h = crypto.createHash('sha256').update(Buffer.from(keyB64, 'base64')).digest();
} else {
    h = crypto.createHash('sha256').update(path.join(scriptDir, '..').toLowerCase()).digest();
}

const chars = [];
for (let i = 0; i < 16; i++) {
    chars.push(String.fromCharCode(97 + (h[i] >> 4)));
    chars.push(String.fromCharCode(97 + (h[i] & 0x0f)));
}
console.log(chars.splice(0, 32).join(''));
