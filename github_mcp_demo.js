// GitHub MCP Server Demo
// This script demonstrates the capabilities of the GitHub API
// that would be available through the MCP server

import { Octokit } from 'octokit';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Load GitHub token from .env.github file
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const envFile = path.join(__dirname, '.env.github');
const envContent = fs.readFileSync(envFile, 'utf8');
const tokenMatch = envContent.match(/GITHUB_PERSONAL_ACCESS_TOKEN=(.+)/);
const GITHUB_TOKEN = tokenMatch ? tokenMatch[1].trim() : '';

if (!GITHUB_TOKEN) {
  console.error('Error: GitHub Personal Access Token not found in .env.github file');
  process.exit(1);
}

console.log('Using GitHub token:', GITHUB_TOKEN.substring(0, 4) + '...' + GITHUB_TOKEN.substring(GITHUB_TOKEN.length - 4));

const octokit = new Octokit({
  auth: GITHUB_TOKEN,
});

// Example 1: Search for repositories
async function searchRepositories() {
  try {
    console.log('Searching for popular machine learning repositories...');
    const { data } = await octokit.rest.search.repos({
      q: 'topic:machine-learning language:python stars:>1000',
      per_page: 5,
    });
    
    console.log(`Found ${data.total_count} repositories. Here are the top 5:`);
    data.items.forEach((repo, index) => {
      console.log(`${index + 1}. ${repo.full_name} - ⭐ ${repo.stargazers_count}`);
      console.log(`   Description: ${repo.description}`);
      console.log(`   URL: ${repo.html_url}`);
      console.log('---');
    });
  } catch (error) {
    console.error('Error searching repositories:', error.message);
  }
}

// Example 2: Get file contents
async function getFileContents(owner, repo, path, branch) {
  try {
    console.log(`Getting contents of ${path} from ${owner}/${repo}...`);
    const params = {
      owner,
      repo,
      path,
    };
    
    if (branch) {
      params.ref = branch;
    }
    
    const { data } = await octokit.rest.repos.getContent(params);
    
    if (!Array.isArray(data) && data.type === 'file' && data.content) {
      const content = Buffer.from(data.content, 'base64').toString('utf-8');
      console.log('File content:');
      console.log('---');
      console.log(content.slice(0, 500) + (content.length > 500 ? '...' : ''));
      console.log('---');
    } else if (Array.isArray(data)) {
      console.log('Directory contents:');
      data.forEach(item => {
        console.log(`- ${item.name} (${item.type})`);
      });
    }
  } catch (error) {
    console.error('Error getting file contents:', error.message);
  }
}

// Example 3: List issues
async function listIssues(owner, repo) {
  try {
    console.log(`Listing recent issues from ${owner}/${repo}...`);
    const { data } = await octokit.rest.issues.listForRepo({
      owner,
      repo,
      state: 'open',
      per_page: 5,
    });
    
    console.log(`Found ${data.length} issues:`);
    data.forEach((issue, index) => {
      console.log(`${index + 1}. #${issue.number}: ${issue.title}`);
      console.log(`   Created by: ${issue.user.login}`);
      console.log(`   Created at: ${new Date(issue.created_at).toLocaleDateString()}`);
      console.log(`   URL: ${issue.html_url}`);
      console.log('---');
    });
  } catch (error) {
    console.error('Error listing issues:', error.message);
  }
}

// Run the examples
async function runDemo() {
  console.log('=== GitHub MCP Server Demo ===');
  console.log('This demonstrates the capabilities that would be available through the GitHub MCP server');
  console.log('');
  
  // Search for repositories related to the user's repository
  console.log('Searching for repositories related to "Rakuimporter"...');
  try {
    const { data } = await octokit.rest.search.repos({
      q: 'Rakuimporter',
      per_page: 5,
    });
    
    console.log(`Found ${data.total_count} repositories related to "Rakuimporter":`);
    data.items.forEach((repo, index) => {
      console.log(`${index + 1}. ${repo.full_name} - ⭐ ${repo.stargazers_count}`);
      console.log(`   Description: ${repo.description || 'No description'}`);
      console.log(`   URL: ${repo.html_url}`);
      console.log('---');
    });
  } catch (error) {
    console.error('Error searching repositories:', error.message);
  }
  console.log('\n');
  
  // Get README from the user's repository
  await getFileContents('yikuochan', 'Rakuimporter', 'README.md', 'main');
  console.log('\n');
  
  // List issues from the user's repository
  await listIssues('yikuochan', 'Rakuimporter');
  
  console.log('\nDemo completed!');
}

runDemo().catch(console.error);
