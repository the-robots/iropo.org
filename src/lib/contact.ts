/** Contact form options shared by the contact page and the contact form Worker in worker/. */

export const CONTACT_TOPICS = [
  "General question",
  "Partnership or sponsorship",
  "Press or media",
  "Legal or privacy",
  "Something else",
] as const;

export const CONTACT_LIMITS = {
  name: 100,
  email: 200,
  messageMin: 10,
  message: 5000,
} as const;
