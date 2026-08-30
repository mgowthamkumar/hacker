/**
 * AutoHire On-the-Fly PDF Study Pack Generator Engine
 * Generates custom branded study packs based on RAG vector search matches.
 */

const ragEngine = require("./rag-engine.js");

function generateStudyPackData(topicOrGap, candidateName = "Candidate") {
  const matches = ragEngine.similaritySearch(topicOrGap, 3, "StudyGuide");
  const primaryMatch = (matches.length > 0 && matches[0].document) ? matches[0].document : null;

  const topicTitle = (primaryMatch && primaryMatch.metadata.title) ? primaryMatch.metadata.title : (topicOrGap || "Custom Skill Accelerator");
  const category = (primaryMatch && primaryMatch.category) ? primaryMatch.category : "General Engineering";
  const theoryText = (primaryMatch && primaryMatch.metadata.theory) ? primaryMatch.metadata.theory : "Comprehensive theoretical framework and core concepts for mastering this skill area.";
  const questions = (primaryMatch && primaryMatch.metadata.questions) ? primaryMatch.metadata.questions : {
    easy: "Q1. Define key terms and fundamentals for " + topicTitle + ".",
    medium: "Q2. Solve an intermediate practical challenge involving " + topicTitle + " design.",
    hard: "Q3. Architect an end-to-end production solution applying " + topicTitle + " principles."
  };

  return {
    success: true,
    candidateName,
    topicTitle,
    category,
    generatedAt: new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }),
    rationale: `RAG Vector Match analysis identified "${topicTitle}" as a critical skill gap to maximize your interview success rate and career readiness.`,
    progression: [
      { level: "🟢 Easy (Fundamentals)", question: questions.easy, focus: "Core Concepts & Basic Implementation" },
      { level: "🟡 Medium (Application)", question: questions.medium, focus: "Problem Solving & System Architecture" },
      { level: "🔴 Hard (Production Scale)", question: questions.hard, focus: "Optimization, Edge Cases & Performance" }
    ],
    theory: theoryText
  };
}

// Generate Printable HTML Document for Server-Side PDF / Client Window Download
function generateStudyPackHtml(data) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AutoHire RAG Study Pack - ${data.topicTitle}</title>
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px; }
    .header { border-bottom: 2px solid #38bdf8; padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }
    .logo { font-size: 24px; font-weight: 800; color: #38bdf8; text-decoration: none; }
    .title-box { background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 24px; margin-bottom: 24px; }
    .category-badge { display: inline-block; background: #a855f7; color: #fff; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 10px; }
    h1 { margin: 0 0 10px 0; color: #f8fafc; font-size: 26px; }
    p { line-height: 1.6; color: #94a3b8; }
    .section-title { font-size: 20px; color: #38bdf8; margin-top: 30px; margin-bottom: 16px; border-left: 4px solid #38bdf8; padding-left: 12px; }
    .progression-card { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 18px; margin-bottom: 14px; }
    .level-header { font-weight: 700; font-size: 16px; margin-bottom: 6px; }
    .q-text { color: #e2e8f0; font-weight: 600; margin-bottom: 4px; }
    .footer { text-align: center; margin-top: 50px; font-size: 12px; color: #64748b; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 20px; }
    @media print { body { background: #fff; color: #000; } .title-box, .progression-card { border-color: #ccc; background: #f9f9f9; } h1, .section-title, .logo { color: #000; } }
  </style>
</head>
<body>
  <div class="header">
    <div class="logo">✨ AutoHire RAG Study Pack</div>
    <div>Date: ${data.generatedAt}</div>
  </div>

  <div class="title-box">
    <span class="category-badge">${data.category}</span>
    <h1>${data.topicTitle}</h1>
    <p><strong>Candidate:</strong> ${data.candidateName}</p>
    <p><strong>RAG Recommendation Rationale:</strong> ${data.rationale}</p>
  </div>

  <div class="section-title">📖 Core Theoretical Fundamentals</div>
  <div class="progression-card">
    <p style="color: #cbd5e1; margin: 0;">${data.theory}</p>
  </div>

  <div class="section-title">🚀 Difficulty Progression Roadmap (Practice Challenges)</div>
  ${data.progression.map(p => `
    <div class="progression-card">
      <div class="level-header">${p.level}</div>
      <div class="q-text">${p.question}</div>
      <div style="font-size: 13px; color: #94a3b8;">Focus Area: ${p.focus}</div>
    </div>
  `).join('')}

  <div class="footer">
    AutoHire AI RAG Grounded Career Engine &copy; 2026. All rights reserved.
  </div>
</body>
</html>`;
}

module.exports = {
  generateStudyPackData,
  generateStudyPackHtml
};
