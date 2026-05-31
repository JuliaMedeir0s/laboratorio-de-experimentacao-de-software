/*
  Executes the controlled experiment:
  - Starts the local REST+GraphQL server
  - Performs warm-up (discarded)
  - Performs randomized trials and writes CSV

  Usage:
    node bench/run_experiment.js --trials 200 --warmup 20 --out data/results.csv
*/

const fs = require("fs");
const path = require("path");
const os = require("os");
const { spawn } = require("child_process");

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = true;
    } else {
      args[key] = next;
      i++;
    }
  }
  return args;
}

function shuffleInPlace(rng, arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

function mulberry32(seed) {
  let a = seed >>> 0;
  return function next() {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

async function sleep(ms) {
  await new Promise((r) => setTimeout(r, ms));
}

async function waitForHealth({ baseUrl, timeoutMs = 15000 }) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(`${baseUrl}/health`);
      if (res.ok) return;
    } catch {
      // ignore
    }
    await sleep(100);
  }
  throw new Error(`Server did not become healthy within ${timeoutMs}ms`);
}

function byteLengthFromArrayBuffer(ab) {
  return Buffer.from(ab).length;
}

function hrtimeMs(startNs) {
  const diffNs = process.hrtime.bigint() - startNs;
  return Number(diffNs) / 1e6;
}

const GQL_FULL_QUERY = `
query FullUser($id: Int!) {
  user(id: $id) {
    id
    name
    username
    email
    age
    phone
    createdAt
    profileBio
    address { street city zip }
    preferences { theme language marketingOptIn }
    stats { postCount commentCount }
    posts {
      id
      userId
      title
      body
      tags
      createdAt
      comments { id postId authorName body createdAt }
    }
  }
}
`;

const GQL_SMALL_QUERY = `
query SmallUser($id: Int!) {
  userSummary(id: $id) {
    id
    name
    username
    createdAt
    posts { id title createdAt }
  }
}
`;

async function requestRestFull({ baseUrl, userId }) {
  return fetch(`${baseUrl}/rest/user/${userId}`);
}

async function requestGql({ baseUrl, query, variables }) {
  return fetch(`${baseUrl}/graphql`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ query, variables })
  });
}

async function runOneMeasurement({ treatment, baseUrl, userId }) {
  const startNs = process.hrtime.bigint();
  let res;
  try {
    if (treatment === "REST_FULL") {
      res = await requestRestFull({ baseUrl, userId });
    } else if (treatment === "GQL_FULL") {
      res = await requestGql({ baseUrl, query: GQL_FULL_QUERY, variables: { id: userId } });
    } else if (treatment === "GQL_SMALL") {
      res = await requestGql({ baseUrl, query: GQL_SMALL_QUERY, variables: { id: userId } });
    } else {
      throw new Error(`Unknown treatment: ${treatment}`);
    }

    const ab = await res.arrayBuffer();
    const latencyMs = hrtimeMs(startNs);
    const sizeBytes = byteLengthFromArrayBuffer(ab);

    return {
      ok: res.ok,
      status: res.status,
      latencyMs,
      sizeBytes
    };
  } catch (err) {
    const latencyMs = hrtimeMs(startNs);
    return {
      ok: false,
      status: 0,
      latencyMs,
      sizeBytes: 0,
      error: String(err?.message || err)
    };
  }
}

function toCsvValue(v) {
  if (v === null || v === undefined) return "";
  const s = String(v);
  if (s.includes(",") || s.includes("\n") || s.includes('"')) {
    return '"' + s.replaceAll('"', '""') + '"';
  }
  return s;
}

async function main() {
  const args = parseArgs(process.argv);

  const trials = parseInt(args.trials || "200", 10);
  const warmup = parseInt(args.warmup || "20", 10);
  const outPath = args.out || "data/results.csv";
  const userId = parseInt(args.userId || "42", 10);
  const port = parseInt(args.port || "4000", 10);
  const seed = parseInt(args.seed || "12345", 10);

  const baseUrl = `http://localhost:${port}`;

  const resultsAbs = path.resolve(process.cwd(), outPath);
  fs.mkdirSync(path.dirname(resultsAbs), { recursive: true });

  const runInfoPath = path.resolve(process.cwd(), args.runInfo || "data/run_info.json");
  fs.mkdirSync(path.dirname(runInfoPath), { recursive: true });

  const serverScript = path.resolve(__dirname, "../api/src/server.js");
  const serverCwd = path.resolve(__dirname, "../api");

  const serverEnv = {
    ...process.env,
    PORT: String(port),
    DATASET_SEED: args.datasetSeed || "123",
    USER_COUNT: args.userCount || "500",
    POSTS_PER_USER: args.postsPerUser || "10",
    COMMENTS_PER_POST: args.commentsPerPost || "5"
  };

  const server = spawn("node", [serverScript], {
    cwd: serverCwd,
    env: serverEnv,
    stdio: ["ignore", "pipe", "pipe"]
  });

  server.stdout.on("data", (d) => process.stdout.write(d));
  server.stderr.on("data", (d) => process.stderr.write(d));

  try {
    await waitForHealth({ baseUrl });

    const treatments = ["REST_FULL", "GQL_FULL", "GQL_SMALL"];

    // Warm-up
    for (const t of treatments) {
      for (let i = 0; i < warmup; i++) {
        await runOneMeasurement({ treatment: t, baseUrl, userId });
      }
    }

    // Prepare randomized schedule
    const schedule = [];
    for (let i = 1; i <= trials; i++) {
      for (const t of treatments) {
        schedule.push({ trial: i, treatment: t });
      }
    }

    const rng = mulberry32(seed);
    shuffleInPlace(rng, schedule);

    const header = [
      "ts",
      "trial",
      "treatment",
      "userId",
      "latency_ms",
      "size_bytes",
      "ok",
      "status",
      "error"
    ].join(",");

    fs.writeFileSync(resultsAbs, header + "\n", "utf8");

    for (let idx = 0; idx < schedule.length; idx++) {
      const item = schedule[idx];
      const r = await runOneMeasurement({ treatment: item.treatment, baseUrl, userId });
      const row = [
        new Date().toISOString(),
        item.trial,
        item.treatment,
        userId,
        r.latencyMs.toFixed(3),
        r.sizeBytes,
        r.ok ? 1 : 0,
        r.status,
        r.error || ""
      ]
        .map(toCsvValue)
        .join(",");
      fs.appendFileSync(resultsAbs, row + "\n", "utf8");

      if ((idx + 1) % 50 === 0) {
        process.stdout.write(`Progress: ${idx + 1}/${schedule.length}\n`);
      }
    }

    const runInfo = {
      startedAt: new Date().toISOString(),
      platform: {
        os: os.platform(),
        release: os.release(),
        arch: os.arch(),
        cpus: os.cpus()?.length,
        totalmem: os.totalmem(),
        node: process.version
      },
      experiment: {
        trials,
        warmup,
        treatments,
        userId,
        baseUrl,
        randomSeed: seed,
        dataset: {
          seed: serverEnv.DATASET_SEED,
          userCount: serverEnv.USER_COUNT,
          postsPerUser: serverEnv.POSTS_PER_USER,
          commentsPerPost: serverEnv.COMMENTS_PER_POST
        }
      },
      outputs: {
        csv: path.relative(process.cwd(), resultsAbs)
      }
    };

    fs.writeFileSync(runInfoPath, JSON.stringify(runInfo, null, 2) + "\n", "utf8");
    process.stdout.write(`\nWrote ${path.relative(process.cwd(), resultsAbs)}\n`);
    process.stdout.write(`Wrote ${path.relative(process.cwd(), runInfoPath)}\n`);
  } finally {
    server.kill("SIGTERM");
  }
}

main().catch((err) => {
  // eslint-disable-next-line no-console
  console.error(err);
  process.exitCode = 1;
});
