import { chromium } from "playwright";
import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";

const root = path.resolve("../..");
const output = path.join(root, "output/browser");
await mkdir(output, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  channel: process.env.ALIBI_BROWSER_CHANNEL || "chrome",
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
const failures = [];
page.on("pageerror", (error) => failures.push(error.message));
page.on("console", (message) => {
  if (message.type() === "error") failures.push(message.text());
});
try {
  await page.goto("http://127.0.0.1:5173");
  await page.getByText("Local service connected").waitFor();
  await page
    .getByRole("button", { name: "New investigation", exact: true })
    .click();
  await page
    .getByLabel("Investigation name", { exact: true })
    .fill("SYNTHETIC / Browser validation");
  await page
    .getByLabel("Description", { exact: true })
    .fill("Automated UI smoke test with synthetic scenario A.");
  await page
    .getByRole("button", { name: "Create investigation", exact: true })
    .click();
  await page
    .getByText(
      "Investigation created. Import your first evidence file to begin.",
    )
    .waitFor();
  for (const [filename, source, offset] of [
    ["web.log", "Web gateway", "0"],
    ["auth.log", "Linux host A", "73"],
  ]) {
    await page
      .getByRole("button", { name: "Import evidence", exact: true })
      .click();
    await page
      .getByLabel("Evidence files", { exact: true })
      .setInputFiles(
        path.join(root, "datasets/A_conflicting_clocks", filename),
      );
    await page.getByLabel("Source label", { exact: true }).fill(source);
    await page
      .getByLabel("Year for yearless syslog", { exact: true })
      .fill("2026");
    await page
      .getByLabel("Clock correction (seconds)", { exact: true })
      .fill(offset);
    await page
      .getByLabel("Basis for correction", { exact: true })
      .fill("Known synthetic clock offset");
    await page
      .getByRole("button", { name: "Preserve & import", exact: true })
      .click();
    await page.getByRole("dialog").waitFor({ state: "hidden" });
  }
  await page.getByRole("button", { name: "Timeline", exact: true }).click();
  await page.getByText("1–6 of 6 events", { exact: false }).waitFor();
  assert.equal(await page.locator("tbody tr").count(), 6);
  await page.screenshot({
    path: path.join(output, "timeline-desktop.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Inspect web.log line 1", exact: true })
    .click();
  await page.getByText("Original SHA-256 verified", { exact: true }).waitFor();
  await page.screenshot({
    path: path.join(output, "event-detail.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Close dialog", exact: true }).click();
  await page.getByLabel("Search timeline", { exact: true }).fill("R7");
  await page.getByText("1–2 of 2 events", { exact: false }).waitFor();
  assert.equal(await page.locator("tbody tr").count(), 2);
  await page
    .getByRole("button", { name: "Clear filters", exact: true })
    .click();
  await page
    .getByLabel("Event type filter", { exact: true })
    .selectOption("auth");
  await page.getByText("1–3 of 3 events", { exact: false }).waitFor();
  await page
    .getByRole("button", { name: "Clear filters", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Evidence vault", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Correct clock", exact: true })
    .nth(1)
    .click();
  await page.getByLabel("Uncertainty ± seconds", { exact: true }).fill("2");
  await page
    .getByLabel("Supporting evidence / reason", { exact: true })
    .fill("Synthetic clock measurement with two-second uncertainty");
  await page
    .getByRole("button", {
      name: "Apply correction & record assumption",
      exact: true,
    })
    .click();
  await page.getByRole("dialog").waitFor({ state: "hidden" });
  await page
    .getByRole("button", { name: "Verify & export", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Verify all files", exact: true })
    .click();
  await page.locator(".verify-result").first().waitFor();
  assert.equal(await page.locator(".verify-result .good").count(), 2);
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: /PDF report/ }).click();
  const download = await downloadPromise;
  await download.saveAs(path.join(output, "browser-report.pdf"));
  assert.ok(
    (await readFile(path.join(output, "browser-report.pdf")))
      .subarray(0, 4)
      .equals(Buffer.from("%PDF")),
  );
  await page.getByRole("button", { name: "Timeline", exact: true }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: path.join(output, "timeline-mobile.png"),
    fullPage: true,
  });
  assert.ok(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
    "Page should not overflow viewport",
  );
  // Separate same-event fixture: required scenario A has associations only.
  await page.setViewportSize({ width: 1440, height: 1050 });
  const fixtureResponse = await page.request.post(
    "http://127.0.0.1:5173/api/investigations",
    {
      data: {
        name: "SYNTHETIC / Same-event calibration",
        description:
          "Repeated recordings of identical synthetic events on two clocks.",
      },
    },
  );
  assert.ok(fixtureResponse.ok());
  const fixtureCase = (await fixtureResponse.json()).id;
  const fixtureIds = [];
  for (const [source, times] of [
    ["Reference", ["04:44:07", "04:45:07", "04:46:07"]],
    ["Target", ["04:42:54", "04:43:54", "04:44:54"]],
  ]) {
    const content = times
      .map(
        (t, i) =>
          `2026-10-28T${t}Z ${source} service: same fixture event event_id=E${i}\n`,
      )
      .join("");
    const result = await page.request.post(
      `http://127.0.0.1:5173/api/investigations/${fixtureCase}/evidence`,
      {
        multipart: {
          file: {
            name: source + ".log",
            mimeType: "text/plain",
            buffer: Buffer.from(content),
          },
          options: JSON.stringify({ source }),
        },
      },
    );
    assert.ok(result.ok());
    fixtureIds.push((await result.json()).id);
  }
  await page.reload();
  await page
    .getByLabel("Active investigation", { exact: true })
    .selectOption(fixtureCase);
  await page
    .getByRole("button", { name: "Evidence vault", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Correct clock", exact: true })
    .nth(1)
    .click();
  await page
    .getByLabel("Reference evidence", { exact: true })
    .selectOption(fixtureIds[0]);
  await page
    .getByLabel("Same-event anchor basis", { exact: true })
    .fill(
      "The synthetic fixture records identical events with stable clocks and no systematic latency.",
    );
  await page
    .getByRole("button", { name: "Preview supported correction", exact: true })
    .click();
  await page.getByText(/Proposed correction: \+73s/).waitFor();
  await page.screenshot({
    path: path.join(output, "anchor-preview.png"),
    fullPage: true,
  });
  await page
    .getByLabel("Anchor approval reason", { exact: true })
    .fill(
      "Reviewed all three synthetic same-event anchors and the reference clock.",
    );
  await page
    .getByRole("button", { name: "Approve & apply correction", exact: true })
    .click();
  await page
    .getByText(
      "Reviewed anchor correction applied and recorded in the audit trail.",
      { exact: true },
    )
    .waitFor();
  assert.deepEqual(failures, [], "No browser console or JavaScript errors");
  console.log(
    "PASS: create, upload both formats, timeline, search, filter, provenance, clock correction, verify, PDF download, mobile layout, anchor preview and approval; zero browser errors.",
  );
} catch (error) {
  await page.screenshot({
    path: path.join(output, "failure.png"),
    fullPage: true,
  });
  console.error(await page.locator("body").innerText());
  throw error;
} finally {
  await browser.close();
}
