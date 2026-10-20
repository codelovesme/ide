// The person's half of IDE sign-in, in a real Chromium, for tools/mike-login-e2e.py:
// open exactly the URL the IDE asked the desktop browser to open, sign in
// on the ordinary account card, press Connect. Nothing is injected: the
// page's own handoff posts the session to the IDE's loopback callback.
//
//   PLAYWRIGHT=<path to playwright/index.mjs> node browser-login.mjs '{"url","email","password","action"}'
//   action: "connect" (default) or "leave" (sign in, then close without connecting)
//
// Prints one JSON object: { ok, ...observations }.
const { chromium } = await import(process.env.PLAYWRIGHT);
const args = JSON.parse(process.argv[2] ?? "{}");
const browser = await chromium.launch();
const result = { ok: false };
try {
  const page = await browser.newPage();
  await page.goto(args.url);
  result.clean_url = !page.url().includes("state=");
  await page.locator("#mike-connect h1", { hasText: "Connect IDE" }).waitFor({ timeout: 20_000 });
  await page.locator("#mike-connect-action", { hasText: "Sign in" }).click();
  await page.locator("#guest-panel label:text-is('Email') + input").fill(args.email);
  await page.locator("#guest-panel label:text-is('Password') + input").fill(args.password);
  await page.locator("#guest-panel .card button", { hasText: "Sign in" }).click();
  await page.locator("#mike-connect-action", { hasText: "Connect this desktop" }).waitFor({ timeout: 30_000 });
  if (args.action === "leave") {
    result.ok = true;
  } else {
    await page.locator("#mike-connect-action").click();
    await page.waitForURL(/127\.0\.0\.1:\d+\/callback$/, { timeout: 15_000 });
    result.answer = (await page.locator("body").innerText()).slice(0, 200);
    result.token_in_url = page.url().includes("token");
    result.ok = result.answer.includes("You are signed in");
  }
} catch (error) {
  result.error = String(error).slice(0, 500);
} finally {
  await browser.close();
}
console.log(JSON.stringify(result));
