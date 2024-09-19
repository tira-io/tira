module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.(ts|tsx)?$': 'ts-jest',
    "^.+\\.(js|jsx)$": "babel-jest",
  },
  "coverageReporters": ["json-summary", "text", "lcov"],
  "collectCoverageFrom" : ["src/**/*.ts", "src/**/*.js", "src/**/*.vue", ],
};
