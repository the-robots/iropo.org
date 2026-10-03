// Run with: node --test "worker/test/*.test.mjs" (Node 23.6+ strips the Worker's TypeScript types).
import assert from "node:assert/strict";
import { test } from "node:test";
import worker from "../src/index.ts";

const VALID = {
  name: "Ada Lovelace",
  email: "ada@example.com",
  topic: "Press or media",
  message: "I am writing a story about animal cruelty data and would like to talk.",
};

function makeEnv({ limited = false, sendError = null } = {}) {
  const sent = [];
  return {
    sent,
    EMAIL: {
      async send(message) {
        if (sendError) throw sendError;
        sent.push(message);
        return { messageId: "test" };
      },
    },
    LIMITER: {
      async limit() {
        return { success: !limited };
      },
    },
    CONTACT_TO: "inbox@example.com",
    CONTACT_FROM: "form@iropo.org",
    ALLOWED_ORIGINS: "https://iropo.org,https://www.iropo.org",
  };
}

function post(fields, { json = true, origin = "https://iropo.org", headers = {} } = {}) {
  const all = { ...headers };
  if (origin) all.origin = origin;
  if (json) all.accept = "application/json";
  return new Request("https://iropo.org/api/contact", {
    method: "POST",
    headers: all,
    body: new URLSearchParams(fields),
  });
}

test("sends a valid message as JSON", async () => {
  const env = makeEnv();
  const response = await worker.fetch(post(VALID), env);
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { ok: true });
  assert.equal(env.sent.length, 1);
  const [message] = env.sent;
  assert.equal(message.to, "inbox@example.com");
  assert.deepEqual(message.from, { email: "form@iropo.org", name: "IROPO contact form" });
  assert.deepEqual(message.replyTo, { email: "ada@example.com", name: "Ada Lovelace" });
  assert.equal(message.subject, "IROPO contact: Press or media from Ada Lovelace");
  assert.match(message.text, /^I am writing a story/);
  assert.match(message.text, /From: Ada Lovelace <ada@example.com>/);
});

test("redirects browsers without JavaScript to the sent page", async () => {
  const env = makeEnv();
  const response = await worker.fetch(post(VALID, { json: false }), env);
  assert.equal(response.status, 303);
  assert.equal(response.headers.get("location"), "/contact/sent/");
  assert.equal(env.sent.length, 1);
});

test("accepts multipart form data from the page script", async () => {
  const env = makeEnv();
  const body = new FormData();
  for (const [key, value] of Object.entries(VALID)) body.append(key, value);
  const request = new Request("https://iropo.org/api/contact", {
    method: "POST",
    headers: { origin: "https://iropo.org", accept: "application/json" },
    body,
  });
  const response = await worker.fetch(request, env);
  assert.equal(response.status, 200);
  assert.equal(env.sent.length, 1);
});

test("rejects posts from other origins or with no origin", async () => {
  for (const origin of ["https://evil.example", null]) {
    const env = makeEnv();
    const response = await worker.fetch(post(VALID, { origin }), env);
    assert.equal(response.status, 403);
    assert.equal(env.sent.length, 0);
  }
});

test("reports every invalid field", async () => {
  const env = makeEnv();
  const response = await worker.fetch(
    post({ name: " ", email: "not-an-email", topic: "Spam", message: "Hi" }),
    env,
  );
  assert.equal(response.status, 422);
  const result = await response.json();
  assert.equal(result.ok, false);
  assert.deepEqual(Object.keys(result.errors).sort(), ["email", "message", "name", "topic"]);
  assert.equal(env.sent.length, 0);
});

test("shows an error page to browsers without JavaScript", async () => {
  const env = makeEnv();
  const response = await worker.fetch(post({ ...VALID, email: "<b>bad" }, { json: false }), env);
  assert.equal(response.status, 422);
  assert.match(response.headers.get("content-type"), /^text\/html/);
  const html = await response.text();
  assert.match(html, /Enter a valid email address\./);
  assert.doesNotMatch(html, /<b>bad/);
});

test("limits links in the message", async () => {
  const env = makeEnv();
  const message = "See https://a.example https://b.example https://c.example www.d.example";
  const response = await worker.fetch(post({ ...VALID, message }), env);
  assert.equal(response.status, 422);
  assert.ok((await response.json()).errors.message);
});

test("keeps line breaks out of the mail headers", async () => {
  const env = makeEnv();
  const response = await worker.fetch(post({ ...VALID, name: "Ada\r\nBcc: victim@example.com" }), env);
  assert.equal(response.status, 200);
  const [message] = env.sent;
  assert.equal(message.replyTo.name, "Ada Bcc: victim@example.com");
  assert.doesNotMatch(message.subject, /[\r\n]/);
});

test("quietly drops the honeypot and instant submissions", async () => {
  for (const extra of [{ website: "https://spam.example" }, { started: String(Date.now()) }]) {
    const env = makeEnv();
    const response = await worker.fetch(post({ ...VALID, ...extra }), env);
    assert.equal(response.status, 200);
    assert.equal(env.sent.length, 0);
  }
});

test("sends when the form was open long enough", async () => {
  const env = makeEnv();
  const response = await worker.fetch(post({ ...VALID, started: String(Date.now() - 10_000) }), env);
  assert.equal(response.status, 200);
  assert.equal(env.sent.length, 1);
});

test("rate limits senders", async () => {
  const env = makeEnv({ limited: true });
  const response = await worker.fetch(post(VALID), env);
  assert.equal(response.status, 429);
  assert.equal(env.sent.length, 0);
});

test("reports delivery failures without leaking details", async () => {
  const sendError = Object.assign(new Error("boom"), { code: "E_DELIVERY_FAILED" });
  const env = makeEnv({ sendError });
  const originalError = console.error;
  const logged = [];
  console.error = (...args) => logged.push(args.join(" "));
  try {
    const response = await worker.fetch(post(VALID), env);
    assert.equal(response.status, 502);
    assert.equal((await response.json()).ok, false);
  } finally {
    console.error = originalError;
  }
  assert.deepEqual(logged, ["contact form: send failed E_DELIVERY_FAILED"]);
});

test("rejects oversized bodies", async () => {
  const env = makeEnv();
  const response = await worker.fetch(post(VALID, { headers: { "content-length": "999999" } }), env);
  assert.equal(response.status, 413);
});

test("only answers POST /api/contact", async () => {
  const env = makeEnv();
  const get = await worker.fetch(new Request("https://iropo.org/api/contact"), env);
  assert.equal(get.status, 405);
  assert.equal(get.headers.get("allow"), "POST");
  const other = await worker.fetch(new Request("https://iropo.org/api/other", { method: "POST" }), env);
  assert.equal(other.status, 404);
});
