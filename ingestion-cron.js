/**
 * AutoHire AI - 24-Hour Automated Ingestion Cron Worker Pipeline
 * Features:
 * 1. High-Volume Multi-Source Extraction (Jobs, Internships, Hackathons)
 * 2. Deterministic SHA-256 Deduplication (organization + title + type)
 * 3. Strict Schema Normalization
 * 4. 24-Hour TTL Purge (Expired Hackathons & 30-Day Old Jobs)
 * 5. Vector RAG Embedding & Indexing
 */

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const jobAggregator = require("./job-aggregator");
const ragEngine = require("./rag-engine");

// Helper: Generate SHA-256 Hash ID
function generateSHA256Id(organization, title, type) {
  const rawKey = `${(organization || "").trim().toLowerCase()}_${(title || "").trim().toLowerCase()}_${(type || "").trim().toLowerCase()}`;
  return crypto.createHash("sha256").update(rawKey).digest("hex").slice(0, 24);
}

// 1. Schema Normalization Function
function normalizeOpportunitySchema(item) {
  const org = (item.organization || item.company || item.company_name || item.organizer || "Tech Organization").toString().trim();
  const cleanTitle = (item.title || item.role || "Opportunity").toString().replace(/<\/?[^>]+(>|$)/g, "").trim();
  const rawType = (item.type || item.job_type || "").toString().toLowerCase();

  let type = "job";
  if (rawType.includes("intern") || cleanTitle.toLowerCase().includes("intern")) {
    type = "internship";
  } else if (rawType.includes("hackathon") || cleanTitle.toLowerCase().includes("hackathon") || cleanTitle.toLowerCase().includes("contest")) {
    type = "hackathon";
  }

  let category = "Engineering";
  const titleLower = cleanTitle.toLowerCase();
  if (titleLower.includes("teacher") || titleLower.includes("instructor") || titleLower.includes("professor") || titleLower.includes("curriculum") || titleLower.includes("educator")) {
    category = "Teaching";
  } else if (titleLower.includes("design") || titleLower.includes("ui") || titleLower.includes("ux") || titleLower.includes("art") || titleLower.includes("creative") || titleLower.includes("animator")) {
    category = "Arts & Design";
  } else if (titleLower.includes("medical") || titleLower.includes("health") || titleLower.includes("doctor") || titleLower.includes("clinical") || titleLower.includes("pharma")) {
    category = "Medical";
  } else if (type === "hackathon") {
    category = "Hackathons";
  } else if (type === "internship") {
    category = "Internships";
  }

  const id = item.id && item.id.length === 24 ? item.id : generateSHA256Id(org, cleanTitle, type);
  const location = (item.location || item.display_location || "Remote").toString().trim();

  // Skills Extraction
  let skills = item.skills_required || item.skills || [];
  if (!Array.isArray(skills) || skills.length === 0) {
    skills = ["Python", "JavaScript", "React", "Node.js", "SQL", "Git", "REST APIs", "AWS"];
  }

  const postedDate = item.deadline_or_posted || item.postedAt || new Date().toISOString();
  const mode = location.toLowerCase().includes("remote") || location.toLowerCase().includes("online") ? "Online" : "In-Person";

  return {
    id: id,
    type: type,
    title: cleanTitle,
    organization: org,
    location: location,
    category: category,
    description: item.description ? item.description.replace(/<\/?[^>]+(>|$)/g, "").slice(0, 300) : `Exciting ${cleanTitle} opportunity at ${org}.`,
    skills_required: skills,
    apply_url: item.apply_url || item.sourceUrl || item.apply_link || `https://www.google.com/search?q=${encodeURIComponent(org + " " + cleanTitle)}`,
    direct_apply_supported: item.direct_apply_supported !== undefined ? item.direct_apply_supported : true,
    deadline_or_posted: postedDate,
    metadata: {
      prize_pool: item.metadata?.prize_pool || (type === "hackathon" ? "$10,000 Total Prizes" : "N/A"),
      stipend_or_salary: item.metadata?.stipend_or_salary || item.salary || (type === "internship" ? "₹20,000 - ₹35,000 / mo" : "₹12,00,000 - ₹24,00,000 / yr"),
      mode: mode
    },
    synced_at: new Date().toISOString()
  };
}

// 2. TTL Retention & Purge Policy
function purgeExpiredRecords(items) {
  const nowMs = Date.now();
  const thirtyDaysMs = 30 * 86400 * 1000;

  return items.filter(item => {
    // Purge expired hackathons
    if (item.type === "hackathon" && item.deadline_or_posted) {
      const deadlineMs = new Date(item.deadline_or_posted).getTime();
      if (!isNaN(deadlineMs) && deadlineMs < nowMs - 86400000) {
        console.log(`[Cron Purge] Purging expired hackathon: ${item.title}`);
        return false;
      }
    }

    // Purge jobs/internships older than 30 days
    if ((item.type === "job" || item.type === "internship") && item.synced_at) {
      const syncedMs = new Date(item.synced_at).getTime();
      if (!isNaN(syncedMs) && nowMs - syncedMs > thirtyDaysMs) {
        console.log(`[Cron Purge] Purging stale 30-day listing: ${item.title}`);
        return false;
      }
    }

    return true;
  });
}

// 3. Main 24-Hour Ingestion Runner
async function run24HourIngestionCron() {
  console.log(`[Cron Worker] Initiating 24-Hour Multi-Source Ingestion at ${new Date().toISOString()}...`);

  try {
    // A. Fetch multi-source listings
    const rawListings = await jobAggregator.fetchMultiSourceJobs();
    console.log(`[Cron Worker] Extracted ${rawListings.length} raw entries from multi-source APIs.`);

    // B. Normalize Schema & Deduplicate via SHA-256
    const deduplicatedMap = new Map();
    for (const raw of rawListings) {
      const normalized = normalizeOpportunitySchema(raw);
      if (!deduplicatedMap.has(normalized.id)) {
        deduplicatedMap.set(normalized.id, normalized);
      }
    }

    let normalizedItems = Array.from(deduplicatedMap.values());
    console.log(`[Cron Worker] Deduplicated down to ${normalizedItems.length} unique items via SHA-256.`);

    // C. Apply TTL Retention Policy
    normalizedItems = purgeExpiredRecords(normalizedItems);

    // D. Upsert into Vector RAG Store
    console.log(`[Cron Worker] Generating Vector Embeddings & Indexing into Vector RAG Store...`);
    if (ragEngine && typeof ragEngine.indexOpportunities === "function") {
      await ragEngine.indexOpportunities(normalizedItems);
    }

    // E. Cache locally to JSON file
    const cachePath = path.join(__dirname, "aggregated_opportunities.json");
    fs.writeFileSync(cachePath, JSON.stringify(normalizedItems, null, 2));

    console.log(`[Cron Worker] 24-Hour Ingestion Cron complete! ${normalizedItems.length} active opportunities indexed.`);
    return {
      success: true,
      total: normalizedItems.length,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    console.error("[Cron Worker Error] Failed 24-hour ingestion pipeline:", error);
    return { success: false, error: error.message };
  }
}

// Allow CLI direct execution
if (require.main === module) {
  run24HourIngestionCron();
}

module.exports = {
  run24HourIngestionCron,
  normalizeOpportunitySchema,
  purgeExpiredRecords,
  generateSHA256Id
};
