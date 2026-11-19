import { chromium } from "playwright";
import assert from "node:assert/strict";
import {mkdir} from "node:fs/promises";
import {fileURLToPath} from "node:url";

const output = fileURLToPath(new URL("../../output/regional/", import.meta.url));
await mkdir(output,{recursive:true});
const browser = await chromium.launch({headless:true, channel:process.env.ALIBI_BROWSER_CHANNEL || "chrome"});
try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];
  page.on("pageerror",e=>errors.push(e.message));
  await page.goto("http://127.0.0.1:5173");
  await page.getByText("Local service connected").waitFor();
  const cases=await (await page.request.get("http://127.0.0.1:5173/api/investigations")).json();
  const demo=cases.find(c=>c.name.startsWith("SYNTHETIC / D realistic incident"));
  assert.ok(demo,"Run scripts/seed_scenario_d.py first");
  const select=page.getByLabel("Active investigation",{exact:true});
  await select.selectOption(demo.id);
  await page.getByRole("button",{name:/5 investigative leads/}).waitFor();
  await page.getByLabel("Search timeline",{exact:true}).fill("no-such-demo-record");
  await page.getByRole("button",{name:/Investigation Brief/}).click();
  const brief=page.locator(".brief-content");
  await brief.getByText(/3 sources · 3 files · 39 normalized events · 1 parsing gap · 5 investigative leads/).waitFor();
  await brief.getByText(/05:00:00Z — 2026-11-19 05:09:00Z/).waitFor();
  await brief.getByText("Integrity: Not checked",{exact:true}).waitFor();
  await brief.getByRole("button",{name:"Check integrity"}).click();
  await brief.getByText(/^Verified at /).waitFor();
  await brief.locator("summary").click();
  await brief.getByText(/supplied ±2 s/).waitFor();
  for(const width of [1440,768,390]) {
    await page.setViewportSize({width,height:950});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),"Brief overflow at "+width);
    await brief.getByRole("button",{name:/auth.log line 8$/}).first().click();
    const comparison=page.getByRole("region",{name:"Clock comparison"});
    const content=await comparison.innerText();
    for(const value of ["Nov 19 05:02:35","+90 s","±2 s","05:04:05Z","05:04:03Z","05:04:07Z","90 seconds slow","line 8"]) assert.ok(content.includes(value),value);
    await page.getByText("Original SHA-256 verified",{exact:true}).waitFor();
    assert.ok(await comparison.evaluate(el=>el.scrollWidth<=el.clientWidth+1));
    await page.getByRole("button",{name:"Close dialog",exact:true}).click();
  }
  // Failure-display branch only: inject a failed verification response without changing vault bytes.
  await page.route("**/verify",route=>route.fulfill({json:[{filename:"auth.log",status:"mismatch",evidence_id:"test-only"}]}));
  await brief.getByRole("button",{name:"Check integrity"}).click();
  await brief.getByText(/Integrity check failed: auth.log/).waitFor();
  await page.unroute("**/verify");
  await page.getByRole("button",{name:"Verify & export",exact:true}).click();
  const waiting=page.waitForEvent("download");
  await page.getByRole("button",{name:"Export Complete Case",exact:true}).click();
  await (await waiting).saveAs(output+"/ALIBI_Scenario_D.zip");
  // Empty and all-gap views exercise the UI independently of any operator's stored cases.
  const prefix="**/investigations/"+demo.id;
  for(const gapCount of [0,2]) {
    await page.route(prefix+"/evidence",route=>route.fulfill({json:gapCount ? [{id:"gap",source:"Test",filename:"empty.log",parsed_records:0,total_records:2,gap_records:2,offset_seconds:0,uncertainty_seconds:0}]:[]}));
    await page.route(prefix+"/findings",route=>route.fulfill({json:[]}));
    await page.route(prefix+"/timeline?**",route=>route.fulfill({json:{total:0,items:[]}}));
    await page.reload();await select.selectOption(demo.id);
    await page.getByRole("button",{name:/Investigation Brief/}).click();
    await brief.getByText("No normalized observations.",{exact:true}).waitFor();
    await brief.getByText("No investigative leads.",{exact:true}).waitFor();
    await brief.getByText(new RegExp("0 normalized events · "+gapCount+" parsing gaps")).waitFor();
    await page.unroute(prefix+"/evidence");await page.unroute(prefix+"/findings");await page.unroute(prefix+"/timeline?**");
  }
  assert.deepEqual(errors,[]);
  console.log("PASS: D live counts, unfiltered bounds, lead record, corrected interval, fresh verification, package download, 1440/768/390; isolated UI edge cases passed.");
} finally {await browser.close();}
