export const mockValidationData = {
  status: "complete", // "idle", "in_progress", "complete", "error"
  level: {
    status: "complete",
    data: {
      level: "Beginner",
      type: "README",
    },
  },
  structure: {
    status: "complete",
    valid: false,
    score: 75,
    issues: [
      "Missing required 'license' file in root directory",
      "Directory structure doesn't follow the standard template pattern",
    ],
    recommendations: [
      "Add a LICENSE file to the root directory with appropriate open source license",
      "Reorganize files following the pattern: Area/Specialism/Product/Asset/files/",
    ],
  },
  template: {
    status: "complete",
    valid: true,
    score: 90,
    issues: [],
    recommendations: [
      "Consider adding a 'Contributing' section to the README",
      "Add more detailed installation instructions",
    ],
  },
  security: {
    status: "complete",
    hasSecurity: false,
    criticalIssues: ["Exposed API keys found in route.js file"],
    highIssues: ["Insecure authentication method used in the API route"],
    mediumIssues: [
      "No input validation for user-provided URLs",
      "Missing Content Security Policy headers",
    ],
    lowIssues: [
      "Dependencies might be outdated - consider running 'npm audit'",
      "Consider implementing rate limiting on API endpoints",
    ],
  },
  quality: {
    status: "complete",
    qualityScore: 7,
    issues: [
      "Code contains TODO comments that should be addressed",
      "Some components lack proper TypeScript typing",
    ],
    recommendations: [
      "Add more comprehensive JSDoc documentation to utility functions",
      "Implement unit tests for critical components",
      "Consider adding error boundaries around major UI sections",
    ],
  },
  overallResult: "fail", // "pass", "fail", "pending"
};
