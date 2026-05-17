#!/usr/bin/env node
'use strict';
const childProcess = require('child_process');

const hostBat = process.argv[2];
if (!hostBat) {
    console.log('FAIL: host.bat path required');
    process.exit(1);
}

const proc = childProcess.spawn(hostBat, [], {
    stdio: ['pipe', 'pipe', 'pipe'],
    shell: process.platform === 'win32',
    windowsHide: true,
});

const msg = JSON.stringify({ action: 'test' });
const lenBuf = Buffer.alloc(4);
lenBuf.writeUInt32LE(Buffer.byteLength(msg, 'utf-8'), 0);

proc.stdin.write(lenBuf);
proc.stdin.write(msg);
proc.stdin.end();

const chunks = [];
const errChunks = [];
proc.stdout.on('data', (c) => chunks.push(c));
proc.stderr.on('data', (c) => errChunks.push(c));

proc.on('error', (err) => {
    console.log('FAIL: ' + err.message);
    process.exit(1);
});

proc.on('close', () => {
    const stdout = Buffer.concat(chunks);
    const stderr = Buffer.concat(errChunks).toString();
    if (stdout.length >= 4) {
        const respLen = stdout.slice(0, 4).readUInt32LE(0);
        const resp = JSON.parse(stdout.slice(4, 4 + respLen).toString());
        if (resp.status === 'ok') {
            console.log('SUCCESS:' + resp.message);
            process.exit(0);
        } else {
            console.log('WARN:' + (resp.message || ''));
            process.exit(0);
        }
    } else {
        console.log('FAIL: Native host 无响应');
        if (stderr) console.log('STDERR:' + stderr);
        process.exit(1);
    }
});
