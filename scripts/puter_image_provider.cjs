#!/usr/bin/env node
"use strict";

const { init } = require("@heyputer/puter.js/src/init.cjs");

function fail(code, message) {
  process.stdout.write(JSON.stringify({ ok: false, code, message }) + "\n");
  process.exit(1);
}

async function main() {
  let input = "";
  for await (const chunk of process.stdin) input += chunk;
  let request;
  try {
    request = JSON.parse(input);
  } catch {
    fail("invalid_input", "Puter bridge received invalid JSON");
    return;
  }

  const token = process.env.PUTER_AUTH_TOKEN || "";
  if (!token.trim()) {
    fail("not_configured", "PUTER_AUTH_TOKEN is not configured");
    return;
  }

  if (request.test_mode === true) {
    fail("test_mode_forbidden", "Puter test_mode is forbidden at the production image boundary");
    return;
  }

  const prompt = typeof request.prompt === "string" ? request.prompt.trim() : "";
  if (!prompt) {
    fail("prompt_required", "Image generation prompt must not be empty");
    return;
  }

  const controller = new AbortController();
  const timeoutMs = Number(process.env.PUTER_IMAGE_TIMEOUT_MS || 120000);
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const puter = init(token.trim());
    const options = {};
    if (request.model) options.model = request.model;
    if (request.provider) options.provider = request.provider;
    if (request.test_mode === true) options.test_mode = true;
    if (request.puter_output_path) options.puter_output_path = request.puter_output_path;
    if (request.ratio && Number(request.ratio.w) > 0 && Number(request.ratio.h) > 0) {
      options.ratio = { w: Number(request.ratio.w), h: Number(request.ratio.h) };
    }

    const generation = puter.ai.txt2img(prompt, options);
    const image = await Promise.race([
      generation,
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("Puter image generation timed out")), timeoutMs)
      ),
    ]);
    const src = image && typeof image.src === "string" ? image.src : "";
    if (!src) fail("empty_image", "Puter returned no image source");

    let bytes;
    let mime = "";

    if (src.startsWith("data:")) {
      const match = src.match(/^data:([^;,]+)?(;base64)?,(.*)$/s);
      if (!match) fail("invalid_image", "Puter returned an invalid data URI");
      mime = match[1] || "";
      if (match[2]) {
        bytes = Buffer.from(match[3], "base64");
      } else {
        bytes = Buffer.from(decodeURIComponent(match[3]), "utf8");
      }
    } else {
      const response = await fetch(src, { signal: controller.signal });
      if (!response.ok) {
        fail("image_fetch_failed", "Puter image URL fetch failed with HTTP " + response.status);
      }
      mime = response.headers.get("content-type") || "";
      bytes = Buffer.from(await response.arrayBuffer());
    }

    if (!bytes || bytes.length === 0) {
      fail("empty_image", "Puter returned empty image bytes");
    }

    process.stdout.write(JSON.stringify({
      ok: true,
      mime_type: mime.split(";")[0].trim().toLowerCase(),
      bytes_base64: bytes.toString("base64"),
      source: src.startsWith("data:") ? "data_uri" : "hosted_url"
    }) + "\n");
  } catch (error) {
    const code = error && (error.errorCode || error.code) ? String(error.errorCode || error.code) : "upstream_failed";
    const message = error && error.message ? String(error.message) : String(error);
    fail(code, message);
  } finally {
    clearTimeout(timer);
  }
}

main().catch((error) => fail("upstream_failed", error.message || String(error)));
