#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { Worker } = require("worker_threads");

function findCopilotTokenizer() {
  const local = process.env.LOCALAPPDATA;
  if (!local) return null;
  const roots = [
    path.join(local, "Programs", "Microsoft VS Code"),
    path.join(local, "Programs", "Microsoft VS Code Insiders"),
  ];
  for (const root of roots) {
    if (!fs.existsSync(root)) continue;
    const versions = fs.readdirSync(root, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name)
      .sort()
      .reverse();
    for (const version of versions) {
      const dist = path.join(root, version, "resources", "app", "extensions", "copilot", "dist");
      const worker = path.join(dist, "tikTokenizerWorker.js");
      const encoder = path.join(dist, "o200k_base.tiktoken");
      if (fs.existsSync(worker) && fs.existsSync(encoder)) return { worker, encoder };
    }
  }
  return null;
}

function call(worker, fn, args, id) {
  return new Promise((resolve, reject) => {
    const onMessage = (message) => {
      if (message.id !== id) return;
      worker.off("message", onMessage);
      if (message.err) reject(new Error(String(message.err.message || message.err)));
      else resolve(message.res);
    };
    worker.on("message", onMessage);
    worker.postMessage({ id, fn, args });
  });
}

async function main() {
  if (process.argv.length !== 3) throw new Error("usage: count_openai_tokens.js <utf8-text-file>");
  const located = findCopilotTokenizer();
  if (!located) throw new Error("o200k_base tokenizer assets were not found");
  const input = path.resolve(process.argv[2]);
  const text = fs.readFileSync(input, "utf8");
  const worker = new Worker(located.worker);
  try {
    const tokenizerId = await call(worker, "init", [located.encoder, "o200k_base", true], 1);
    const ids = await call(worker, "encode", [tokenizerId, text, undefined], 2);
    process.stdout.write(JSON.stringify({
      ok: true,
      tokenizer: "o200k_base",
      quality: "exact",
      tokens: ids.length,
    }));
  } finally {
    await worker.terminate();
  }
}

main().catch((error) => {
  process.stderr.write(String(error.stack || error) + "\n");
  process.exitCode = 2;
});
