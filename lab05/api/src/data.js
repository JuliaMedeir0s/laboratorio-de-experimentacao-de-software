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

function intBetween(rng, minInclusive, maxInclusive) {
  return Math.floor(rng() * (maxInclusive - minInclusive + 1)) + minInclusive;
}

function pick(rng, arr) {
  return arr[intBetween(rng, 0, arr.length - 1)];
}

function makeString(rng, length, alphabet) {
  let s = "";
  for (let i = 0; i < length; i++) s += alphabet[intBetween(rng, 0, alphabet.length - 1)];
  return s;
}

function isoDateDaysAgo(rng, maxDaysAgo) {
  const now = Date.now();
  const daysAgoMs = intBetween(rng, 0, maxDaysAgo) * 24 * 60 * 60 * 1000;
  return new Date(now - daysAgoMs).toISOString();
}

function createDataset({
  seed = 123,
  userCount = 500,
  postsPerUser = 10,
  commentsPerPost = 5
} = {}) {
  const rng = mulberry32(seed);
  const firstNames = ["Ana", "Bruno", "Carla", "Diego", "Ester", "Felipe", "Gi", "Heitor", "Iris", "Joao", "Kai", "Lia", "Marta", "Nina", "Otavio", "Paula", "Rafa", "Sara", "Tomas", "Vivi"];
  const lastNames = ["Silva", "Souza", "Oliveira", "Pereira", "Lima", "Costa", "Ferreira", "Rodrigues", "Almeida", "Santos", "Gomes", "Barbosa"];
  const cities = ["Belo Horizonte", "São Paulo", "Rio de Janeiro", "Curitiba", "Recife", "Salvador", "Brasília", "Fortaleza"];
  const tagsPool = ["graphql", "rest", "api", "web", "lab", "experiment", "performance", "json", "node", "express", "schema", "endpoint"];
  const alphabet = "abcdefghijklmnopqrstuvwxyz";

  const users = [];
  const posts = [];
  const comments = [];

  let postId = 1;
  let commentId = 1;

  for (let userId = 1; userId <= userCount; userId++) {
    const first = pick(rng, firstNames);
    const last = pick(rng, lastNames);
    const username = (first[0] + last + userId).toLowerCase();

    users.push({
      id: userId,
      name: `${first} ${last}`,
      username,
      email: `${username}@example.com`,
      age: intBetween(rng, 18, 60),
      phone: `+55 31 9${intBetween(rng, 1000, 9999)}-${intBetween(rng, 1000, 9999)}`,
      address: {
        street: `${intBetween(rng, 1, 9999)} Rua ${pick(rng, lastNames)}`,
        city: pick(rng, cities),
        zip: `${intBetween(rng, 10000, 99999)}-${intBetween(rng, 100, 999)}`
      },
      profileBio: makeString(rng, intBetween(rng, 80, 160), alphabet + "     "),
      preferences: {
        theme: pick(rng, ["light", "dark"]),
        language: pick(rng, ["pt-BR", "en-US"]),
        marketingOptIn: rng() > 0.5
      },
      createdAt: isoDateDaysAgo(rng, 365)
    });

    for (let p = 0; p < postsPerUser; p++) {
      const tagCount = intBetween(rng, 2, 5);
      const tags = new Set();
      while (tags.size < tagCount) tags.add(pick(rng, tagsPool));

      const thisPostId = postId++;
      posts.push({
        id: thisPostId,
        userId,
        title: `Post ${thisPostId} - ${makeString(rng, intBetween(rng, 10, 20), alphabet)}`,
        body: makeString(rng, intBetween(rng, 400, 900), alphabet + "     " + alphabet.toUpperCase()),
        tags: Array.from(tags),
        createdAt: isoDateDaysAgo(rng, 180)
      });

      for (let c = 0; c < commentsPerPost; c++) {
        comments.push({
          id: commentId++,
          postId: thisPostId,
          authorName: `${pick(rng, firstNames)} ${pick(rng, lastNames)}`,
          body: makeString(rng, intBetween(rng, 60, 160), alphabet + "     "),
          createdAt: isoDateDaysAgo(rng, 90)
        });
      }
    }
  }

  const usersById = new Map(users.map((u) => [u.id, u]));
  const postsByUserId = new Map();
  for (const p of posts) {
    if (!postsByUserId.has(p.userId)) postsByUserId.set(p.userId, []);
    postsByUserId.get(p.userId).push(p);
  }

  const commentsByPostId = new Map();
  for (const c of comments) {
    if (!commentsByPostId.has(c.postId)) commentsByPostId.set(c.postId, []);
    commentsByPostId.get(c.postId).push(c);
  }

  function buildUserFull(userId) {
    const u = usersById.get(userId);
    if (!u) return null;

    const userPosts = postsByUserId.get(userId) || [];
    const fullPosts = userPosts.map((p) => ({
      ...p,
      comments: (commentsByPostId.get(p.id) || []).map((c) => ({ ...c }))
    }));

    return {
      ...u,
      posts: fullPosts,
      stats: {
        postCount: fullPosts.length,
        commentCount: fullPosts.reduce((acc, p) => acc + p.comments.length, 0)
      }
    };
  }

  function buildUserSummary(userId) {
    const u = usersById.get(userId);
    if (!u) return null;
    const userPosts = postsByUserId.get(userId) || [];

    return {
      id: u.id,
      name: u.name,
      username: u.username,
      createdAt: u.createdAt,
      posts: userPosts.slice(0, 5).map((p) => ({ id: p.id, title: p.title, createdAt: p.createdAt }))
    };
  }

  function listUsers(limit = 20) {
    return users.slice(0, limit).map((u) => ({ ...u }));
  }

  return {
    config: { seed, userCount, postsPerUser, commentsPerPost },
    buildUserFull,
    buildUserSummary,
    listUsers
  };
}

module.exports = { createDataset };
