const express = require("express");
const cors = require("cors");
const { createDataset } = require("./data");
const { createGraphqlExecutor } = require("./graphql");

const PORT = parseInt(process.env.PORT || "4000", 10);
const DATASET_SEED = parseInt(process.env.DATASET_SEED || "123", 10);
const USER_COUNT = parseInt(process.env.USER_COUNT || "500", 10);
const POSTS_PER_USER = parseInt(process.env.POSTS_PER_USER || "10", 10);
const COMMENTS_PER_POST = parseInt(process.env.COMMENTS_PER_POST || "5", 10);

const dataset = createDataset({
  seed: DATASET_SEED,
  userCount: USER_COUNT,
  postsPerUser: POSTS_PER_USER,
  commentsPerPost: COMMENTS_PER_POST
});

const gql = createGraphqlExecutor({ dataset });

const app = express();
app.use(cors());
app.use(express.json({ limit: "2mb" }));

app.get("/health", (req, res) => {
  res.json({ ok: true, dataset: dataset.config });
});

app.get("/rest/user/:id", (req, res) => {
  const id = parseInt(req.params.id, 10);
  const user = dataset.buildUserFull(id);
  if (!user) return res.status(404).json({ error: "User not found" });
  return res.json(user);
});

app.post("/graphql", async (req, res) => {
  const { query, variables, operationName } = req.body || {};
  if (!query || typeof query !== "string") {
    return res.status(400).json({ errors: [{ message: "Missing 'query'" }] });
  }

  try {
    const result = await gql.execute({ query, variables, operationName });
    // GraphQL spec: 200 even when errors present; but we keep 200 for comparability.
    return res.status(200).json(result);
  } catch (err) {
    return res.status(500).json({ errors: [{ message: String(err?.message || err) }] });
  }
});

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Lab05 API listening on http://localhost:${PORT}`);
});
