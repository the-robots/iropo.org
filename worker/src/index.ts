/**
 * Contact form backend for iropo.org.
 *
 * The site is static: GitHub Pages serves it through Cloudflare. This Worker runs only on
 * iropo.org/api/*. It checks the contact form POST and emails it to the project through
 * Cloudflare Email Routing. It stores nothing and never logs message contents; the sender's IP
 * address is used only as the rate limit key. The destination address is the CONTACT_TO secret,
 * so it never appears in the repository or on the site.
 *
 * It answers in whichever shape the sender can use: JSON for the page script, and for browsers
 * without JavaScript a 303 redirect to /contact/sent/ or a small error page.
 */
import { CONTACT_LIMITS, CONTACT_TOPICS } from "../../src/lib/contact.ts";

interface EmailAddress {
  email: string;
  name?: string;
}

/** The part of the send_email binding this Worker uses. */
interface SendEmail {
  send(message: {
    from: EmailAddress;
    to: string;
    replyTo: EmailAddress;
    subject: string;
    text: string;
  }): Promise<{ messageId: string }>;
}

/** The part of the rate limiting binding this Worker uses. */
interface RateLimit {
  limit(options: { key: string }): Promise<{ success: boolean }>;
}

export interface Env {
  EMAIL: SendEmail;
  LIMITER: RateLimit;
  /** Secret: where messages go. It must be a verified Email Routing destination address. */
  CONTACT_TO: string;
  /** Sender address on the Email Routing domain. */
  CONTACT_FROM: string;
  /** Comma-separated origins allowed to post the form. */
  ALLOWED_ORIGINS: string;
}

type Field = "name" | "email" | "topic" | "message";
type Fields = Record<Field, string>;
type FieldErrors = Partial<Record<Field, string>>;

const SENT_PAGE = "/contact/sent/";
const MAX_BODY_BYTES = 32 * 1024;
const MAX_LINKS = 3;
// Bots fill in every field, including one hidden from people, and submit faster than anyone types.
const HONEYPOT_FIELD = "website";
const MIN_FILL_MS = 3000;
const EMAIL_PATTERN = /^[^\s@<>()[\]",;:]+@[^\s@<>()[\]",;:]+\.[^\s@<>()[\]",;:]{2,}$/;
const NO_STORE = { "cache-control": "no-store", "x-content-type-options": "nosniff" };

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const { pathname } = new URL(request.url);
    if (pathname !== "/api/contact") return plain("Not found", 404);
    if (request.method !== "POST") return plain("Method not allowed", 405, { allow: "POST" });
    return handleContact(request, env);
  },
};

async function handleContact(request: Request, env: Env): Promise<Response> {
  const json = (request.headers.get("accept") ?? "").includes("application/json");
  const origins = env.ALLOWED_ORIGINS.split(",").map((origin) => origin.trim());
  if (!origins.includes(request.headers.get("origin") ?? "")) {
    return failure(json, 403, "This form can only be sent from iropo.org.");
  }
  if (Number(request.headers.get("content-length") ?? 0) > MAX_BODY_BYTES) {
    return failure(json, 413, "That message is too long.");
  }

  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return failure(json, 400, "The form could not be read.");
  }

  // Accept bot submissions quietly so they get no signal, but never deliver them.
  if (text(form.get(HONEYPOT_FIELD)) || filledTooFast(form.get("started"))) {
    return success(json);
  }

  const { fields, errors } = validate(form);
  if (Object.keys(errors).length > 0) {
    return failure(json, 422, "Please check the form and try again.", errors);
  }

  const { success: allowed } = await env.LIMITER.limit({
    key: request.headers.get("cf-connecting-ip") ?? "unknown",
  });
  if (!allowed) return failure(json, 429, "Too many messages. Please wait a minute and try again.");

  try {
    await env.EMAIL.send({
      from: { email: env.CONTACT_FROM, name: "IROPO contact form" },
      to: env.CONTACT_TO,
      replyTo: { email: fields.email, name: fields.name },
      subject: `IROPO contact: ${fields.topic} from ${fields.name}`.slice(0, 200),
      text: emailBody(fields),
    });
  } catch (error) {
    // Log only the error code, never the message or the sender's details.
    console.error("contact form: send failed", (error as { code?: string }).code ?? "unknown");
    return failure(json, 502, "Your message could not be sent. Please try again later.");
  }
  return success(json);
}

function validate(form: FormData): { fields: Fields; errors: FieldErrors } {
  const fields: Fields = {
    name: singleLine(form.get("name")),
    email: singleLine(form.get("email")),
    topic: singleLine(form.get("topic")),
    message: multiLine(form.get("message")),
  };
  const errors: FieldErrors = {};
  if (!fields.name) errors.name = "Enter your name.";
  else if (fields.name.length > CONTACT_LIMITS.name) {
    errors.name = `Keep your name to ${CONTACT_LIMITS.name} characters or fewer.`;
  }
  if (fields.email.length > CONTACT_LIMITS.email || !EMAIL_PATTERN.test(fields.email)) {
    errors.email = "Enter a valid email address.";
  }
  if (!(CONTACT_TOPICS as readonly string[]).includes(fields.topic)) errors.topic = "Choose a topic.";
  if (fields.message.length < CONTACT_LIMITS.messageMin) {
    errors.message = `Write a message of at least ${CONTACT_LIMITS.messageMin} characters.`;
  } else if (fields.message.length > CONTACT_LIMITS.message) {
    errors.message = `Keep your message to ${CONTACT_LIMITS.message} characters or fewer.`;
  } else if (countLinks(fields.message) > MAX_LINKS) {
    errors.message = `Include no more than ${MAX_LINKS} links.`;
  }
  return { fields, errors };
}

function text(value: FormDataEntryValue | null): string {
  return typeof value === "string" ? value : "";
}

/** Strips control characters, including CR and LF, so nothing can reach the mail headers. */
function singleLine(value: FormDataEntryValue | null): string {
  return text(value)
    .replace(/[\u0000-\u001f\u007f]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function multiLine(value: FormDataEntryValue | null): string {
  return text(value)
    .replace(/\r\n?/g, "\n")
    .replace(/[\u0000-\u0008\u000b-\u001f\u007f]/g, "")
    .trim();
}

function countLinks(message: string): number {
  return message.match(/https?:\/\/|www\./gi)?.length ?? 0;
}

/** The page script stamps the form when it loads. Without JavaScript the field is empty. */
function filledTooFast(value: FormDataEntryValue | null): boolean {
  const started = Number(text(value));
  return started > 0 && Date.now() - started < MIN_FILL_MS;
}

function emailBody(fields: Fields): string {
  return [
    fields.message,
    "",
    "--",
    `From: ${fields.name} <${fields.email}>`,
    `Topic: ${fields.topic}`,
    "Sent with the contact form on iropo.org. Reply to this email to answer.",
  ].join("\n");
}

function plain(body: string, status: number, headers: Record<string, string> = {}): Response {
  return new Response(body, {
    status,
    headers: { ...NO_STORE, "content-type": "text/plain; charset=utf-8", ...headers },
  });
}

function success(json: boolean): Response {
  if (json) return Response.json({ ok: true }, { headers: NO_STORE });
  return new Response(null, { status: 303, headers: { ...NO_STORE, location: SENT_PAGE } });
}

function failure(json: boolean, status: number, message: string, errors: FieldErrors = {}): Response {
  if (json) return Response.json({ ok: false, error: message, errors }, { status, headers: NO_STORE });
  const details = Object.values(errors);
  return new Response(errorPage(details.length > 0 ? details : [message]), {
    status,
    headers: { ...NO_STORE, "content-type": "text/html; charset=utf-8" },
  });
}

function errorPage(messages: string[]): string {
  const items = messages.map((message) => `<li>${escapeHtml(message)}</li>`).join("");
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex">
<title>Message not sent · IROPO</title>
<style>body{font:1rem/1.6 system-ui,sans-serif;max-width:40rem;margin:4rem auto;padding:0 1.25rem}</style>
</head>
<body>
<h1>Your message was not sent</h1>
<ul>${items}</ul>
<p>Use your browser's Back button to return to the form. What you typed should still be there.</p>
<p><a href="/contact/">Back to the contact page</a></p>
</body>
</html>
`;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`);
}
