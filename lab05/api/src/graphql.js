const { buildSchema, graphql } = require("graphql");

const schemaSDL = /* GraphQL */ `
  type Address {
    street: String!
    city: String!
    zip: String!
  }

  type Preferences {
    theme: String!
    language: String!
    marketingOptIn: Boolean!
  }

  type Stats {
    postCount: Int!
    commentCount: Int!
  }

  type Comment {
    id: Int!
    postId: Int!
    authorName: String!
    body: String!
    createdAt: String!
  }

  type Post {
    id: Int!
    userId: Int!
    title: String!
    body: String!
    tags: [String!]!
    createdAt: String!
    comments: [Comment!]!
  }

  type User {
    id: Int!
    name: String!
    username: String!
    email: String!
    age: Int!
    phone: String!
    address: Address!
    profileBio: String!
    preferences: Preferences!
    createdAt: String!
    posts: [Post!]!
    stats: Stats!
  }

  type UserSummary {
    id: Int!
    name: String!
    username: String!
    createdAt: String!
    posts: [PostSummary!]!
  }

  type PostSummary {
    id: Int!
    title: String!
    createdAt: String!
  }

  type Query {
    user(id: Int!): User
    userSummary(id: Int!): UserSummary
    users(limit: Int = 20): [User!]!
  }
`;

function createGraphqlExecutor({ dataset }) {
  const schema = buildSchema(schemaSDL);

  const rootValue = {
    user: ({ id }) => dataset.buildUserFull(id),
    userSummary: ({ id }) => dataset.buildUserSummary(id),
    users: ({ limit }) => dataset.listUsers(limit)
  };

  async function execute({ query, variables, operationName }) {
    return graphql({
      schema,
      source: query,
      rootValue,
      variableValues: variables,
      operationName
    });
  }

  return { execute };
}

module.exports = { createGraphqlExecutor };
