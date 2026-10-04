/**
 * Progressive enhancement for the contact form. Without JavaScript the form posts normally and
 * the Worker answers with a redirect to /contact/sent/ or an error page. With it, the message is
 * sent in the background and the result is announced in place.
 *
 * Markup contract:
 *   <form data-contact-form action="/api/contact"> … <input name="started" type="hidden">
 *     <button type="submit"> <p data-contact-status role="status">
 */
interface Result {
  ok?: boolean;
  error?: string;
  errors?: Record<string, string>;
}

const FALLBACK = "Sorry, your message could not be sent. Please try again later.";

const form = document.querySelector<HTMLFormElement>("form[data-contact-form]");
const statusLine = form?.querySelector<HTMLElement>("[data-contact-status]");
const button = form?.querySelector<HTMLButtonElement>('button[type="submit"]');
const started = form?.querySelector<HTMLInputElement>('input[name="started"]');

if (form && statusLine && button && started) {
  // Lets the Worker drop submissions made faster than a person could type.
  const stamp = () => (started.value = String(Date.now()));
  const show = (message: string, state: "pending" | "success" | "error") => {
    statusLine.textContent = message;
    statusLine.dataset.state = state;
  };
  stamp();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    button.disabled = true;
    show("Sending…", "pending");
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" },
      });
      const result: Result = await response.json().catch(() => ({}));
      if (response.ok && result.ok) {
        form.reset();
        stamp();
        show("Thank you. Your message was sent.", "success");
      } else {
        const details = Object.values(result.errors ?? {});
        show(details.length > 0 ? details.join(" ") : (result.error ?? FALLBACK), "error");
      }
    } catch {
      show("Sorry, your message could not be sent. Check your connection and try again.", "error");
    } finally {
      button.disabled = false;
    }
  });
}
