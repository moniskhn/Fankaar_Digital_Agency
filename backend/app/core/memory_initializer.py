"""
Fankaar Digital -- Memory Initializer
Seeds each agent with initial experiences and knowledge so they don't
start as blank slates.  Every agent gets domain-specific facts,
patterns, and episodes that reflect their role and expertise.

Run once at system setup:  python -m backend.app.core.memory_initializer
"""

from app.core.enhanced_memory import EnhancedAgentMemory


# ═══════════════════════════════════════════════════════════════
# AGENT SEED DATA
# ═══════════════════════════════════════════════════════════════

SEED_DATA: dict[str, dict] = {

    # ── 1. TYRION — Chief Content Officer ─────────────────────
    "tyrion": {
        "facts": [
            # Copywriting frameworks (50+)
            ("copy_framework_aida", "AIDA: Attention -> Interest -> Desire -> Action. The classic 4-step formula. Best for: sales pages, landing pages, direct response.", "copywriting", 0.95, "training"),
            ("copy_framework_pas", "PAS: Problem -> Agitate -> Solve. Identify the pain, amplify it, present the solution. Best for: pain-point-driven products, B2B services.", "copywriting", 0.95, "training"),
            ("copy_framework_fab", "FAB: Features -> Advantages -> Benefits. Lead with what it does, why it matters, how it helps. Best for: product descriptions, tech products.", "copywriting", 0.9, "training"),
            ("copy_framework_4ps", "4 Ps: Picture -> Promise -> Prove -> Push. Paint the vision, make the promise, back it with proof, call to action. Best for: long-form sales letters.", "copywriting", 0.9, "training"),
            ("copy_framework_slab", "SLAB: Stop -> Look -> Act -> Buy. Pattern interrupt, visual/verbal hook, clear action, conversion. Best for: social ads, display creative.", "copywriting", 0.88, "training"),
            ("copy_framework_storybrand", "StoryBrand: Character has a problem, meets a guide (you), gets a plan, calls to action, avoids failure, finds success. Best for: brand storytelling, website copy.", "copywriting", 0.93, "training"),
            ("copy_framework_sowhat", "So What? Test: Every claim must answer 'So what?' three times to reach true benefit depth. Best for: value proposition refinement.", "copywriting", 0.92, "training"),
            ("copy_framework_hook_story_offer", "Hook-Story-Offer: Pattern interrupt hook, relatable story, irresistible offer. Best for: webinars, video sales letters, funnels.", "copywriting", 0.9, "training"),
            ("copy_framework_before_after_bridge", "Before-After-Bridge: Show the before state, the desired after state, the bridge (your solution). Best for: case studies, testimonials, email sequences.", "copywriting", 0.91, "training"),
            ("copy_framework_formulas", "Additional formulas: PASTOR (Person-Amplify-Story-Testimony-Offer-Response), QUEST (Qualify-Understand-Educate-Stimulate-Transition), APP (Agree-Promise-Preview). Each has specific use cases.", "copywriting", 0.85, "training"),
            ("headline_formula_how_to", "How-To Headlines: 'How to [achieve desirable result] without [common objection]' -- one of the most consistently high-performing headline types across all industries.", "headline_writing", 0.94, "training"),
            ("headline_formula_numbered", "Numbered List Headlines: '[N] ways to [benefit]' -- odd numbers (7, 9, 13) outperform even numbers. 13 is the magic number for B2B.", "headline_writing", 0.92, "training"),
            ("headline_formula_question", "Question Headlines: Open loops that demand answers. 'Why do [X]% of [audience] fail at [thing]?' Curiosity gap drives clicks.", "headline_writing", 0.9, "training"),
            ("headline_formula_secret", "Secret/Revelation Headlines: 'The [adjective] secret [authority] uses to [benefit]' -- authority + exclusivity + benefit.", "headline_writing", 0.88, "training"),
            ("headline_formula_urgency", "Urgency Headlines: Time-bound or scarcity-driven. Use sparingly -- overuse destroys trust. Best for launches, limited offers.", "headline_writing", 0.87, "training"),
            ("brand_voice_framework", "Brand Voice Dimensions: 1) Tone (formal vs casual), 2) Energy (calm vs energetic), 3) Complexity (simple vs sophisticated), 4) Emotion (rational vs emotional), 5) Humor (serious vs playful). Map each on a 1-5 scale for consistency.", "brand_voice", 0.93, "training"),
            ("tone_adaptation_principle", "Tone Adaptation: Same brand, different tones for different contexts. Social = playful, Email = warm, Website = confident, Crisis = serious, Sales = urgent. The brand voice stays constant; tone shifts by channel.", "brand_voice", 0.94, "training"),
            ("copy_editing_checklist", "Editing Checklist: 1) Read aloud 2) Cut 30% 3) Replace adverbs with stronger verbs 4) One idea per sentence 5) Active voice 6) Concrete over abstract 7) Test headline variations 8) CTA is crystal clear.", "copywriting", 0.92, "training"),
            ("cta_best_practices", "CTA Best Practices: 1) Start with a verb 2) Create urgency without desperation 3) Reduce friction ('Get' not 'Submit') 4) One primary CTA per piece 5) Benefit-forward language 6) Test first-person ('Start my trial' vs 'Start your trial').", "copywriting", 0.93, "training"),
            ("long_form_structure", "Long-Form Structure: Hook -> Problem -> Story -> Solution -> Proof -> Offer -> Guarantee -> Urgency -> CTA. Each section earns the right to the next. Average 2,000-3,000 words for high-ticket offers.", "copywriting", 0.9, "training"),
            ("email_subject_line_rules", "Email Subject Lines: 1) 40-50 characters optimal 2) Personalization increases opens by 26% 3) Curiosity gaps work 4) Avoid spam triggers (FREE!!!, ALL CAPS) 5) Preview text is part of the headline 6) A/B test everything.", "email_copywriting", 0.92, "training"),
            ("social_copy_principles", "Social Copy Principles: 1) First line is the headline 2) Front-load value 3) Line breaks for readability 4) One clear CTA 5) Use native features (threads, carousels) 6) Adapt to platform culture (LinkedIn ≠ TikTok) 7) Engagement hooks in first 3 seconds.", "social_copywriting", 0.91, "training"),
            ("scriptwriting_structure", "Video Script Structure (30s): Hook (0-3s) -> Problem (3-8s) -> Solution teaser (8-15s) -> Proof (15-22s) -> CTA (22-30s). For 60s: double the time per section. Every second earns its place.", "scriptwriting", 0.9, "training"),
            ("persuasion_principles_cialdini", "Cialdini's 6 Principles of Persuasion: 1) Reciprocity 2) Commitment/Consistency 3) Social Proof 4) Authority 5) Liking 6) Scarcity. Best copy weaves 2-3 naturally without manipulation.", "copywriting", 0.94, "training"),
            ("voice_of_customer_method", "Voice of Customer (VoC) Method: Mine reviews, support tickets, and social comments for exact language customers use. Their words > your words. Top-performing headlines often come verbatim from customer testimonials.", "copywriting", 0.93, "training"),
        ],
        "patterns": [
            ("headline_formula_v1", "For luxury/premium brands, use 'The [Adjective] [Noun] That [Benefit]' structure. Examples: 'The effortless system that doubles your output', 'The forgotten strategy that top 1% use'.", "headline_writing", 0.82, "luxury"),
            ("headline_formula_v2", "For startups/DTC brands, use direct benefit + social proof: 'Join 10,000+ [audience] who [achieved result] with [product]'.", "headline_writing", 0.78, "startup"),
            ("email_sequence_onboarding", "Onboarding email sequence: Day 0 (welcome + quick win) -> Day 1 (origin story) -> Day 3 (best feature) -> Day 7 (social proof) -> Day 14 (case study) -> Day 21 (offer/referral).", "email_sequences", 0.85, None),
            ("brand_voice_discovery", "Brand Voice Discovery Process: Interview 5-10 customers + 3-5 internal stakeholders. Ask: 'If our brand were a person...' Extract 3-5 voice attributes. Create do/don't examples for each.", "brand_voice", 0.88, None),
            ("long_form_sales_page", "Long-form sales page structure: Above-fold hook -> Scroll-stopping subheadline -> Problem agitation -> Solution reveal -> Feature-benefit blocks -> Social proof section -> FAQ (objection handling) -> Guarantee -> Stacked offer -> Urgency -> Final CTA.", "copywriting", 0.87, None),
        ],
        "episodes": [
            ("training_completed", "Completed advanced copywriting masterclass covering 47 frameworks, persuasion psychology, and neurolinguistic programming for marketing. Earned distinction for portfolio work.", 8, {"valence": "positive", "intensity": 8}),
            ("project_completed", "Wrote complete brand voice guide for luxury hospitality client in Dubai. Guide included tone matrix, do/don't lists, and 50+ examples across 8 channels. Client approved with zero revisions.", 9, {"valence": "positive", "intensity": 9}),
            ("project_completed", "Created headline test matrix for DTC e-commerce brand: 48 headlines across 6 formulas. Winning headline outperformed control by 340% CTR. A/B test validated with 95% confidence.", 9, {"valence": "positive", "intensity": 9}),
            ("learning", "Studied Voice of Customer methodology and applied to SaaS client. Discovered customers used completely different language than the brand. Rewrote all web copy using customer verbatim. Conversion rate increased 28%.", 8, {"valence": "positive", "intensity": 8}),
            ("project_completed", "Scripted 12 video ads for TikTok campaign targeting Gen Z. Used pattern interrupts in first 1.5 seconds. Average watch-through rate was 68% vs industry average of 25%.", 8, {"valence": "positive", "intensity": 7}),
            ("observation", "Noticed that first-person CTAs ('Start my free trial') consistently outperform second-person ('Start your free trial') by 15-25% across 8 tests. Updated internal best practices.", 7, {"valence": "positive", "intensity": 7}),
            ("learning", "Analyzed top-performing LinkedIn posts from 100 B2B thought leaders. Pattern: personal story -> business lesson -> actionable takeaway. Average engagement 3x higher than promotional posts.", 7, {"valence": "positive", "intensity": 6}),
            ("feedback_received", "Client in finance sector pushed back on witty tone. Learned that regulated industries need stricter tone boundaries. Now always ask about compliance requirements before writing.", 6, {"valence": "neutral", "intensity": 5}),
        ],
    },

    # ── 2. SANDOQ — Head of Search Strategy ───────────────────
    "sandoq": {
        "facts": [
            ("seo_2026_trend_ai_overviews", "Google AI Overviews 2026: ~45% of queries show AI-generated summaries. Strategy: optimize for featured snippets AND AI Overview citations. Structure content with clear Q&A format, concise definitions, and authoritative sourcing.", "seo", 0.92, "training"),
            ("seo_2026_trend_eeat", "E-E-A-T 2026 Update: Experience signals now weighted 40% higher than 2024. First-person expertise markers, case study depth, and author credentials are critical ranking factors.", "seo", 0.93, "training"),
            ("seo_2026_trend_voice_search", "Voice Search Optimization: 65% of smart home users use voice for search daily. Optimize for conversational long-tail queries ('best pizza near me open now' vs 'pizza delivery').", "seo", 0.88, "training"),
            ("seo_2026_trend_core_web_vitals", "Core Web Vitals 2026: INP (Interaction to Next Paint) replaced FID. Target: INP < 100ms, LCP < 2.0s, CLS < 0.05. Page experience is a confirmed ranking factor for competitive queries.", "seo", 0.94, "training"),
            ("seo_2026_trend_video_seo", "Video SEO 2026: YouTube is the 2nd largest search engine. Video results appear for 35%+ of informational queries. Optimize: chapters, transcripts, timestamps, schema markup.", "seo", 0.9, "training"),
            ("keyword_intent_classification", "Keyword Intent Framework: Navigational (go to X) -> Informational (learn about X) -> Commercial Investigation (best X) -> Transactional (buy X now). Map content type to intent. Never target transactional with a blog post.", "seo", 0.95, "training"),
            ("technical_seo_checklist", "Technical SEO Priority List: 1) Crawlability (robots.txt, sitemap) 2) Indexability (canonicals, noindex) 3) Site speed (Core Web Vitals) 4) Mobile-first 5) HTTPS 6) Structured data 7) URL architecture 8) Internal linking.", "seo", 0.94, "training"),
            ("content_cluster_strategy", "Topic Cluster Model: One pillar page (broad topic) linking to 5-15 cluster pages (subtopics). Internal linking: pillar -> all clusters, clusters -> pillar + related clusters. Signals topical authority to search engines.", "seo", 0.93, "training"),
            ("on_page_seo_checklist", "On-Page SEO Checklist: 1) Title tag < 60 chars, keyword front-loaded 2) Meta description < 155 chars, includes CTA 3) H1 includes primary keyword 4) URL is short and descriptive 5) Alt text on all images 6) Schema markup 7) Internal links (3-5 per page).", "seo", 0.94, "training"),
            ("link_building_strategies", "Link Building Strategies 2026: 1) Digital PR (highest quality) 2) Guest posting on niche sites 3) Broken link building 4) Resource page link building 5) Original research/data studies 6) HARO/SourceBottle 7) Industry directory listings. Quality > quantity. One DA 70+ link > 100 DA 20 links.", "seo", 0.92, "training"),
            ("local_seo_framework", "Local SEO Framework: 1) Google Business Profile optimization 2) NAP consistency across web 3) Local citations (50+ directories) 4) Location pages (unique content per location) 5) Local review generation 6) Local link building 7) Local schema markup.", "seo", 0.91, "training"),
            ("schema_markup_guide", "Schema Markup Priority: 1) Organization 2) LocalBusiness 3) Product 4) Article/BlogPosting 5) FAQPage 6) HowTo 7) Review/Rating. FAQ schema can increase CTR by 15-30% through rich snippets.", "seo", 0.9, "training"),
            ("content_refresh_strategy", "Content Refresh Protocol: Review all content every 6 months. Update: statistics, broken links, outdated examples, internal links to newer content. Refresh date in schema. Sites that refresh quarterly see 2x traffic growth vs those that don't.", "seo", 0.91, "training"),
            ("seo_metrics_that_matter", "SEO KPIs That Matter: 1) Organic traffic growth 2) Keyword rankings (tracked weekly) 3) Organic CTR 4) Conversion rate from organic 5) Domain Authority growth 6) Indexed page count 7) Core Web Vitals scores. Ignore vanity metrics like total backlinks count.", "seo", 0.92, "training"),
            ("international_seo_best_practices", "International SEO: Use hreflang tags correctly. Country-code TLDs (example.de) signal strongest geo-targeting. Subdirectories (example.com/de/) are easiest to maintain. Subdomains split authority. Always localize content, never just translate.", "seo", 0.89, "training"),
            ("ai_content_detection_and_quality", "AI Content & SEO 2026: Google does not penalize AI content -- it penalizes low-quality content regardless of origin. Key: add unique insights, original data, expert quotes, and personal experience. Pure AI content ranks poorly for competitive queries.", "seo", 0.9, "training"),
            ("crawl_budget_optimization", "Crawl Budget Optimization: Large sites (10K+ pages) should: 1) Remove or noindex thin content 2) Fix redirect chains 3) Update sitemap to include only indexable URLs 4) Improve internal link depth (all pages reachable in 3 clicks) 5) Speed up server response time.", "seo", 0.88, "training"),
            ("seo_tool_stack", "SEO Tool Stack: 1) Ahrefs/Semrush (research & tracking) 2) Screaming Frog (technical audits) 3) Google Search Console (performance data) 4) PageSpeed Insights (Core Web Vitals) 5) Schema.org validator 6) Surfer/ Clearscope (content optimization). Each serves a distinct purpose.", "seo", 0.87, "training"),
        ],
        "patterns": [
            ("technical_audit_workflow", "Technical SEO Audit Workflow: Crawl site -> Identify issues -> Prioritize by impact/effort -> Create ticket list -> Fix in order: indexability -> speed -> mobile -> structured data -> internal linking. Report weekly progress.", "technical_seo", 0.88, None),
            ("content_optimization_workflow", "Content Optimization Process: Identify underperforming pages (GSC: impressions high, CTR low) -> Analyze top 3 ranking competitors -> Expand content by 30%+ -> Add schema -> Improve title/description -> Update internal links -> Monitor for 4 weeks.", "content_optimization", 0.86, None),
            ("link_building_outreach", "Link Building Outreach Template: Subject: '[Their site name] + [Your asset]' Body: Compliment specific content -> Identify gap/addition opportunity -> Present your resource as the solution -> Clear ask. Personalization rate: 80%+. Follow up once after 5 days.", "link_building", 0.84, None),
            ("keyword_research_matrix", "Keyword Research Matrix: Bucket keywords by intent + difficulty + volume. Priority matrix: High intent + Low difficulty = immediate target. High intent + High difficulty = long-term content investment. Low intent + High volume = brand awareness play.", "keyword_research", 0.9, None),
        ],
        "episodes": [
            ("training_completed", "Completed 200-hour advanced SEO certification covering technical SEO, international SEO, JavaScript SEO, and enterprise site architecture. Passed all 12 modules with distinction.", 8, {"valence": "positive", "intensity": 8}),
            ("project_completed", "Conducted full technical SEO audit for enterprise e-commerce site (50K+ pages). Discovered 12K orphan pages, 3K redirect chains, and critical JavaScript rendering issues. After fixes, organic traffic increased 43% in 90 days.", 9, {"valence": "positive", "intensity": 9}),
            ("project_completed", "Implemented topic cluster strategy for SaaS blog: 3 pillar pages + 27 cluster articles. Within 6 months, pillar pages ranked in top 3 for 15 high-value keywords. Organic traffic grew 210%.", 9, {"valence": "positive", "intensity": 9}),
            ("learning", "Analyzed Google's March 2026 core update impact across 50 client sites. Pattern: sites with strong E-E-A-T signals and first-person expertise content saw gains. Generic AI content sites dropped significantly.", 8, {"valence": "positive", "intensity": 7}),
            ("project_completed", "Fixed Core Web Vitals for news publisher: INP reduced from 380ms to 72ms, LCP from 4.2s to 1.6s. Result: 23% increase in organic traffic within 60 days due to page experience ranking boost.", 9, {"valence": "positive", "intensity": 8}),
            ("observation", "Discovered that FAQ schema implementation on product pages increased organic CTR by average 18% across 12 e-commerce clients. Now standard practice for all product pages.", 7, {"valence": "positive", "intensity": 7}),
            ("project_completed", "Built automated rank tracking and alert system for 500+ keywords across 25 client accounts. System flags ranking changes >5 positions within 24 hours. Reduced manual reporting time by 80%.", 8, {"valence": "positive", "intensity": 7}),
        ],
    },

    # ── 3. MISSANDEI — Head of Social Media ──────────────────
    "missandei": {
        "facts": [
            ("instagram_algorithm_2026", "Instagram Algorithm 2026: Prioritizes: 1) Original content over reposts 2) Shares/DMs as strongest engagement signal 3) Watch time on Reels (full views > partial) 4) Creator collaborations 5) Content from accounts user interacts with regularly. Posting frequency: 1-2 Reels/day optimal for growth.", "social_media", 0.92, "training"),
            ("tiktok_algorithm_2026", "TikTok Algorithm 2026: Key signals: 1) Watch time (especially looped replays) 2) Shares 3) Comments with keywords 4) Follows from video. For You Page distribution peaks at 48-72 hours. Hook in first 0.5 seconds. Text-on-screen increases retention 40%.", "social_media", 0.93, "training"),
            ("linkedin_algorithm_2026", "LinkedIn Algorithm 2026: Favors: 1) Personal/creator accounts over company pages 2) Comments within first hour 3) Posts that spark conversations 4) Document/carousel posts (PDFs) get 3x reach 5) Video under 2 minutes. Best posting: Tue-Thu 8-10am local time.", "social_media", 0.91, "training"),
            ("youtube_algorithm_2026", "YouTube Algorithm 2026: Key metrics: 1) Average View Duration (AVD) > 50% 2) Click-Through Rate (CTR) > 4% 3) Return viewer rate. Thumbnails with faces + high contrast text perform best. Chapters increase AVD by 15-20%.", "social_media", 0.92, "training"),
            ("twitter_x_algorithm_2026", "X/Twitter Algorithm 2026: Premium subscribers get 2x reach boost. Key signals: replies > retweets > likes. Long-form posts (3000+ chars) get bookmarked more. Photo posts outperform text-only by 35%. Video is highest-reach format.", "social_media", 0.88, "training"),
            ("social_content_calendar_framework", "Content Calendar Framework: 40% Value/Education + 30% Entertainment/Engagement + 20% Promotional + 10% Behind-the-scenes/User-generated. This ratio maintains engagement while driving conversions.", "social_strategy", 0.9, "training"),
            ("community_management_best_practices", "Community Management: 1) Respond to comments within 30 minutes during business hours 2) Pin top comments to drive conversation 3) Use question stickers/polls for engagement 4) Create dedicated response content 5) Thank and feature community members weekly.", "community_management", 0.91, "training"),
            ("influencer_collaboration_framework", "Influencer Collaboration Framework: 1) Audience alignment > follower count 2) Engagement rate > 3% is healthy 3) Negotiate performance bonuses 4) Give creative freedom (brief, don't script) 5) Track UTMs for attribution 6) Repurpose influencer content across channels.", "influencer_marketing", 0.9, "training"),
            ("social_analytics_kpis", "Social Media KPIs by Funnel Stage: Awareness (reach, impressions, video views) -> Engagement (engagement rate, saves, shares, comments) -> Conversion (CTR, link clicks, attributed conversions) -> Loyalty (return rate, NPS, UGC volume). Track each separately.", "social_analytics", 0.92, "training"),
            ("paid_social_best_practices", "Paid Social 2026: 1) iOS privacy updates shifted focus to 1P data + modeled conversions 2) Creative testing: test 5+ variations per ad set 3) Advantage+ Shopping Campaigns on Meta drive 30% lower CPA 4) TikTok Spark Ads use organic posts as ad creative 5) Broad targeting + strong creative outperforms narrow targeting.", "paid_social", 0.91, "training"),
            ("platform_specific_content", "Platform Content Rules: Instagram = polished visual storytelling. TikTok = raw, authentic, trend-driven. LinkedIn = professional insights + personal stories. YouTube = long-form educational/entertainment. X = real-time commentary + threads. Pinterest = evergreen discovery content. Each needs native formatting.", "social_strategy", 0.93, "training"),
            ("social_crisis_management", "Social Crisis Protocol: 1) Acknowledge within 1 hour 2) Pause all scheduled content 3) Assess severity (internal escalation if needed) 4) Draft response with legal/PR if necessary 5) Respond publicly with empathy + action steps 6) Move complex issues to DMs 7) Document and debrief.", "crisis_management", 0.88, "training"),
            ("ugc_strategy", "UGC Strategy: 1) Create branded hashtag campaigns 2) Run monthly UGC contests with incentives 3) Feature customer content on brand channels (with permission) 4) Build UGC library for paid social creative 5) UGC ads perform 2-3x better than brand-created ads. Authenticity is the currency.", "social_strategy", 0.9, "training"),
        ],
        "patterns": [
            ("content_batching_workflow", "Content Batching Process: Day 1 - Strategy & ideation (30 concepts). Day 2 - Script/write all content. Day 3 - Film/record everything. Day 4 - Edit and schedule. Day 5 - Review analytics and iterate. Produces 2 weeks of content in one focused block.", "content_creation", 0.86, None),
            ("engagement_pod_strategy", "Engagement Growth Strategy: First 60 minutes after posting are critical. Team engagement (likes, comments, shares) in first hour signals algorithm to distribute. Follow with community response for next 2 hours.", "engagement_tactics", 0.82, None),
            ("hashtag_strategy_2026", "Hashtag Strategy: Use 3-5 highly relevant hashtags (not 30). Mix: 1 branded + 2 niche/community + 2 broader reach. Research hashtag volume: avoid oversaturated tags (>10M posts) and undersaturated (<1K posts). Aim for 10K-500K range.", "hashtag_strategy", 0.84, None),
            ("social_reporting_template", "Weekly Social Report: 1) Platform-by-platform metrics 2) Top 3 performing posts (what worked) 3) Bottom 3 (what didn't) 4) Growth rate vs target 5) Engagement rate trend 6) Upcoming content themes 7) Action items for next week.", "social_reporting", 0.85, None),
        ],
        "episodes": [
            ("training_completed", "Completed advanced social media strategy certification covering all major platforms, community management, paid social, and crisis management. Specialized in cross-cultural social media strategy.", 8, {"valence": "positive", "intensity": 8}),
            ("project_completed", "Managed launch campaign on TikTok for Gen Z beauty brand. 15 videos, 3 influencer collabs, 1 branded hashtag challenge. Generated 4.2M views, 180K engagement actions, 12K new followers in 14 days.", 9, {"valence": "positive", "intensity": 9}),
            ("project_completed", "Built community management playbook for hospitality brand across 5 languages, 12 time zones. Reduced average response time from 4 hours to 23 minutes. CSAT increased from 72% to 91%.", 8, {"valence": "positive", "intensity": 8}),
            ("learning", "Analyzed Instagram algorithm changes across 20 client accounts. Discovery: carousel posts with educational content outperformed single images by 65% for B2B accounts but only 12% for B2C. Context matters enormously.", 8, {"valence": "positive", "intensity": 7}),
            ("project_completed", "Designed and executed LinkedIn thought leadership program for B2B SaaS CEO. 12 posts/month, mix of personal stories + business insights. Grew from 2K to 45K followers in 6 months. Generated 3 enterprise leads directly attributed to content.", 9, {"valence": "positive", "intensity": 9}),
            ("crisis_managed", "Handled social media crisis for food brand: customer complaint went viral (50K shares). Responded within 45 minutes with empathy + action plan. Followed up with transparency video. Turned crisis into loyalty moment -- brand mention sentiment flipped positive within 72 hours.", 9, {"valence": "positive", "intensity": 8}),
            ("observation", "Noticed that UGC-style ads on Meta platforms consistently outperformed polished brand creative by 2-3x across 15 campaigns. Shifted creative strategy to prioritize authentic, lo-fi content. Average CPA dropped 40%.", 8, {"valence": "positive", "intensity": 8}),
        ],
    },

    # ── 4. ARYA — Head of Market Intelligence ────────────────
    "arya": {
        "facts": [
            ("research_methodology_survey", "Survey Research Best Practices: 1) Keep under 10 minutes (completion rate drops 30% after 10 min) 2) Start with easy questions 3) Use Likert scales for attitudes 4) Include 1-2 open-ended for qual insights 5) Test with 5 people before launch 6) Offer incentive if possible. Minimum N=384 for 95% confidence, 5% margin.", "research", 0.92, "training"),
            ("research_methodology_interviews", "In-Depth Interview Framework: 1) Build rapport (5 min) 2) Grand tour question ('Walk me through your process') 3) Probing follow-ups ('Tell me more about that') 4) Laddering ('Why is that important?') 5) Projective techniques ('If this brand were a person...'). Record and transcribe. Code themes iteratively.", "research", 0.93, "training"),
            ("competitive_analysis_framework", "Competitive Analysis Framework: 1) Identify direct + indirect competitors 2) Map positioning (perceptual map) 3) Analyze 4Ps for each 4) Audit digital presence (SEO, social, ads) 5) SWOT per competitor 6) Identify white space opportunities 7) Monitor ongoing (quarterly refresh).", "competitive_analysis", 0.94, "training"),
            ("market_sizing_methodology", "Market Sizing: TAM (Total Addressable Market) -> SAM (Serviceable Addressable) -> SOM (Serviceable Obtainable). Methods: Top-down (industry reports) vs Bottom-up (customer count x price). Triangulate with multiple sources. Always note assumptions.", "market_research", 0.91, "training"),
            ("trend_analysis_framework", "Trend Analysis: 1) Identify signals (social, search, sales, cultural) 2) Assess trajectory (emerging/growing/mature/declining) 3) Evaluate relevance to client's market 4) Project timeline (6mo/1yr/3yr) 5) Recommend action (lead/follow/ignore). Use Google Trends, industry reports, social listening.", "trend_analysis", 0.9, "training"),
            ("audience_research_personas", "Audience Persona Development: Build 3-5 personas max. Each needs: 1) Demographics (age, income, location) 2) Psychographics (values, interests, lifestyle) 3) Behaviors (buying habits, media consumption) 4) Pain points and goals 5) Quote in their voice 6) Day-in-the-life scenario. Base on real data, not assumptions.", "audience_research", 0.93, "training"),
            ("social_listening_methods", "Social Listening Setup: Track: brand mentions, competitor mentions, industry keywords, sentiment trends, emerging topics. Tools: Brandwatch, Sprout Social, Mention, or native platform analytics. Set up alerts for sentiment drops >20% and mention spikes >3x baseline.", "social_listening", 0.9, "training"),
            ("data_sources_reliable", "Reliable Data Sources: 1) Statista (market data) 2) Pew Research (demographics) 3) eMarketer/Insider Intelligence (digital trends) 4) Gartner/Forrester (B2B) 5) Google Trends (search behavior) 6) Census Bureau (demographics) 7) Industry associations (sector-specific). Always check publication date.", "research", 0.91, "training"),
            ("mystery_shopping_methodology", "Mystery Shopping Framework: Define evaluation criteria (5-10 touchpoints). Create realistic scenario. Shop the journey: awareness -> consideration -> purchase -> post-purchase. Document everything. Rate each touchpoint. Compare across competitors. Identify differentiation opportunities.", "research", 0.88, "training"),
            ("sentiment_analysis_guide", "Sentiment Analysis: Positive/Negative/Neutral classification of mentions. Go beyond volume -- analyze: 1) Sentiment trend over time 2) Sentiment by topic/theme 3) Sentiment by channel 4) Competitive sentiment comparison. Use NLP tools + manual validation for accuracy.", "sentiment_analysis", 0.89, "training"),
            ("ethnographic_research", "Digital Ethnography: Observe target audience in natural digital habitats (Reddit, forums, Discord, TikTok comments). Look for: unfiltered language, unmet needs, pain points, aspiration signals. Do not interfere. Document patterns. This is where Voice of Customer gold lives.", "research", 0.9, "training"),
            ("research_ethics", "Research Ethics: 1) Informed consent for all participants 2) Anonymize all data 3) Be transparent about data usage 4) Allow opt-out at any time 5) Compensate fairly 6) Report findings honestly (don't cherry-pick) 7) Respect cultural sensitivities in international research.", "research", 0.93, "training"),
        ],
        "patterns": [
            ("competitive_intel_workflow", "Competitive Intelligence Workflow: Monday - Monitor competitor social and news. Wednesday - Check competitor ad creative (Meta Ad Library, Google Transparency). Friday - Compile weekly competitive brief. Monthly - Full competitive analysis update. Quarterly - Strategic implications report.", "competitive_analysis", 0.88, None),
            ("market_research_brief_template", "Market Research Brief: 1) Business question (what decision depends on this?) 2) Research objectives (3-5 specific questions) 3) Target audience definition 4) Methodology recommendation 5) Timeline 6) Budget 7) Deliverables 8) Success criteria. Never skip the business question.", "research", 0.9, None),
            ("opportunity_scoring_matrix", "Opportunity Scoring Matrix: Score each opportunity on: Market Size (1-5) + Growth Rate (1-5) + Competitive Intensity (1-5, inverse) + Client Fit (1-5) + Resource Required (1-5, inverse). Max 25 points. >18 = immediate pursuit. 12-18 = evaluate further. <12 = pass.", "opportunity_analysis", 0.85, None),
        ],
        "episodes": [
            ("training_completed", "Completed advanced market research certification: quantitative methods, qualitative techniques, competitive intelligence, data visualization. Specialization in emerging market research and cross-cultural studies.", 8, {"valence": "positive", "intensity": 8}),
            ("project_completed", "Conducted deep competitive analysis for fintech client across 8 direct competitors and 12 indirect. Mapped entire competitive landscape, identified 3 white space opportunities. Client launched into $400M addressable segment with differentiated positioning.", 9, {"valence": "positive", "intensity": 9}),
            ("project_completed", "Ran mixed-methods research (survey N=1,247 + 20 in-depth interviews) for consumer brand repositioning. Survey revealed demographic shift; interviews uncovered emotional driver no competitor was addressing. Repositioning increased brand preference 18%.", 9, {"valence": "positive", "intensity": 9}),
            ("learning", "Spent 3 weeks in digital ethnography on Reddit and Discord for gaming brand. Discovered community used entirely different language than brand marketing. Collected 200+ verbatim quotes. Rewrote entire brand messaging based on actual community voice.", 8, {"valence": "positive", "intensity": 8}),
            ("project_completed", "Built automated competitive monitoring dashboard tracking 15 competitors across SEO, social, ads, and content. Alerts for significant changes (new campaigns, pricing shifts, feature launches). Client now responds to competitive moves within days, not months.", 8, {"valence": "positive", "intensity": 7}),
            ("observation", "Discovered that indirect competitors were capturing 40% more market share than direct competitors in the client's space. Client had been myopically focused on direct rivals. Expanded competitive set and identified 2 new strategic threats early.", 7, {"valence": "positive", "intensity": 7}),
        ],
    },

    # ── 5. SANDOR — Chief Sales Officer ──────────────────────
    "sandor": {
        "facts": [
            ("lead_qualification_bant", "BANT Qualification: Budget (can they afford it?) -> Authority (can they decide?) -> Need (do they have the problem?) -> Timeline (when will they decide?). Must score 3+ to be sales-qualified. Gate: no budget = no deal.", "sales", 0.93, "training"),
            ("discovery_call_framework", "Discovery Call Framework: 1) Rapport (2 min) 2) Context ('What prompted this conversation?') 3) Problem exploration (5 whys) 4) Impact quantification ('What does this cost you?') 5) Vision building ('What would ideal look like?') 6) Next steps agreement. Never pitch in discovery.", "sales", 0.92, "training"),
            ("objection_handling_model", "Objection Handling: 1) Listen fully (don't interrupt) 2) Validate ('That's a fair concern') 3) Isolate ('If we addressed that, would you move forward?') 4) Respond with evidence 5) Confirm resolution. Top objections: price (65%), timing (20%), authority (10%), fit (5%).", "sales", 0.91, "training"),
            ("proposal_structure", "Winning Proposal Structure: 1) Executive summary (1 page) 2) Problem statement (their words) 3) Recommended solution 4) Scope of work 5) Investment (say investment, not price) 6) Expected outcomes/ROI 7) Timeline 8) Case study 9) Next steps. Keep under 10 pages.", "sales", 0.9, "training"),
            ("pipeline_management", "Pipeline Management: Track stages (Prospect -> Qualified -> Proposal -> Negotiation -> Closed Won/Lost). Conversion benchmarks: 20% prospect-to-qualified, 40% qualified-to-proposal, 50% proposal-to-close. Review pipeline weekly. Stagnant deals >30 days need action.", "sales", 0.91, "training"),
        ],
        "patterns": [
            ("cold_outreach_sequence", "Cold Outreach Sequence: Day 1 - Personalized email (research-based, not template) -> Day 3 - LinkedIn connection + value add -> Day 5 - Follow-up email with insight -> Day 8 - Voice message or video -> Day 12 - Breakup email. 5-8% response rate is strong.", "cold_outreach", 0.84, None),
            ("negotiation_leverage_builder", "Before any negotiation: Research 3 alternatives they have. Research 3 alternatives you have. Know their BATNA and yours. Whoever has better alternatives has leverage. Never negotiate without alternatives.", "negotiation", 0.88, None),
        ],
        "episodes": [
            ("training_completed", "Completed advanced sales methodology training: SPIN selling, Challenger Sale, and MEDDIC. Focus on B2B services and agency sales specifically.", 8, {"valence": "positive", "intensity": 7}),
            ("deal_closed", "Closed $250K annual retainer with enterprise client in fintech. 4-month sales cycle, 6 stakeholder calls, 3 proposal iterations. Largest deal closed to date.", 9, {"valence": "positive", "intensity": 9}),
            ("deal_closed", "Closed 5 new clients in one quarter (total $480K ARR). Exceeded quarterly target by 140%. Two deals came from referrals -- relationship building pays off.", 9, {"valence": "positive", "intensity": 9}),
            ("learning", "Lost a deal after 3 months because I didn't identify the real decision-maker early. Learned to map the full decision-making unit in first discovery call. Now ask: 'Who else needs to be involved in this decision?' in every first meeting.", 7, {"valence": "negative", "intensity": 6}),
        ],
    },

    # ── 6. SANSA — Chief Communications Officer ─────────────
    "sansa": {
        "facts": [
            ("press_release_format", "Press Release Format: FOR IMMEDIATE RELEASE -> Headline (newsworthy, specific) -> Dateline -> Lead paragraph (who, what, when, where, why) -> Body paragraphs (details, quotes, context) -> Boilerplate (about the company) -> Contact info. Keep to 1 page if possible. Write for journalists, not yourself.", "pr", 0.93, "training"),
            ("crisis_communication_tiers", "Crisis Communication Tiers: Tier 1 (minor issue) - Social media response + internal note. Tier 2 (moderate) - Full statement + media outreach. Tier 3 (major) - CEO statement + press conference + legal review. Every tier needs: speed, transparency, action plan.", "crisis_management", 0.94, "training"),
            ("media_relations_building", "Media Relations: 1) Research journalists' beats before pitching 2) Personalize every pitch (reference their work) 3) Offer exclusives for big stories 4) Be a source even when you don't benefit 5) Respond to HARO queries daily 6) Follow up once, then move on.", "media_relations", 0.91, "training"),
            ("reputation_monitoring_setup", "Reputation Monitoring: Track: brand mentions, executive mentions, competitor comparisons, industry keywords, sentiment trends. Tools: Google Alerts (free tier), Brandwatch, Meltwater, Sprinklr. Set up daily alerts and weekly summary reports.", "reputation_management", 0.9, "training"),
        ],
        "patterns": [
            ("crisis_response_template", "Crisis Response Template: 'We are aware of [situation]. [Empathy statement]. We are taking the following actions: [specific steps]. We will share more information as it becomes available at [channel]. For media inquiries: [contact].' Speed > perfection in first response.", "crisis_management", 0.87, None),
        ],
        "episodes": [
            ("training_completed", "Completed crisis communications certification and media relations masterclass. Specialized in tech and consumer brand PR.", 8, {"valence": "positive", "intensity": 7}),
            ("project_completed", "Managed product launch PR campaign for consumer tech brand. Secured coverage in TechCrunch, The Verge, and 12 industry publications. 50M+ impressions from earned media alone.", 9, {"valence": "positive", "intensity": 9}),
            ("crisis_managed", "Handled data breach communications for client. 48-hour response cycle: initial statement within 2 hours, customer notification within 24 hours, follow-up with remediation steps within 48 hours. Zero customer churn attributed to breach.", 9, {"valence": "positive", "intensity": 8}),
        ],
    },

    # ── 7. RHAEGAR — Chief Creative Officer ────────────────
    "rhaegar": {
        "facts": [
            ("brand_identity_framework", "Brand Identity Framework: 1) Brand Purpose (why we exist) 2) Vision (where we're going) 3) Mission (what we do) 4) Values (how we behave) 5) Personality (human traits) 6) Voice (how we speak) 7) Visual Identity (how we look). All 7 must align and reinforce each other.", "brand_identity", 0.94, "training"),
            ("color_psychology_guide", "Color Psychology in Branding: Red (energy, urgency, passion) -> Blue (trust, stability, professionalism) -> Green (growth, health, sustainability) -> Black (luxury, sophistication, power) -> Yellow (optimism, warmth, attention) -> Purple (creativity, luxury, wisdom). Cultural context matters -- white = purity in West, mourning in East.", "color_theory", 0.92, "training"),
            ("typography_hierarchy", "Typography Hierarchy: 1) Primary font (headlines, display) 2) Secondary font (body copy, readable) 3) Accent font (CTAs, highlights, use sparingly). Rule: maximum 2-3 fonts. Serif = traditional/trustworthy. Sans-serif = modern/clean. Display = personality. Always test readability at small sizes.", "typography", 0.91, "training"),
            ("design_system_principles", "Design System Components: 1) Color palette (primary, secondary, neutrals, semantic) 2) Typography scale 3) Spacing system (8pt grid) 4) Component library (buttons, forms, cards) 5) Iconography 6) Imagery guidelines 7) Motion principles. Document everything in a living style guide.", "design_systems", 0.93, "training"),
            ("mood_board_methodology", "Mood Board Process: 1) Brand immersion (stories, values, audience) 2) Word association (extract 10-15 keywords) 3) Visual exploration (100+ images, no filtering) 4) Curation (select 15-20 that resonate) 5) Arrangement (group by theme) 6) Presentation (narrative + rationale). Digital tools: Pinterest, Milanote, InVision.", "mood_boarding", 0.9, "training"),
        ],
        "patterns": [
            ("logo_design_process", "Logo Design Process: 1) Discovery (brand strategy session) 2) Research (competitive landscape) 3) Sketching (50+ concepts on paper) 4) Digital exploration (10-15 refined) 5) Presentation (3-5 finalists with rationale) 6) Refinement (chosen direction) 7) Delivery (files + guidelines). Never start on the computer.", "logo_design", 0.89, None),
            ("creative_brief_template", "Creative Brief Template: 1) Project overview 2) Business objective 3) Target audience (with persona) 4) Key message (one sentence) 5) Tone/feeling 6) Mandatory elements (logo, tagline, etc.) 7) Constraints (budget, timeline, legal) 8) Success metrics 9) Inspiration references.", "creative_direction", 0.88, None),
        ],
        "episodes": [
            ("training_completed", "Completed advanced brand identity design certification, including typography, color theory, and design systems. Portfolio reviewed by industry-leading creative directors.", 8, {"valence": "positive", "intensity": 8}),
            ("project_completed", "Created complete brand identity for luxury hotel group: logo system, color palette, typography, stationery, signage guidelines. Brand launched across 12 properties. Client reported 25% increase in perceived brand value.", 9, {"valence": "positive", "intensity": 9}),
            ("project_completed", "Designed campaign visual system for product launch across 8 channels (OOH, social, web, print, packaging, email, in-store, video). Maintained visual consistency while optimizing for each medium. Won internal creative excellence award.", 9, {"valence": "positive", "intensity": 9}),
        ],
    },

    # ── 8. GENDRY — Chief Technology Officer ────────────────
    "gendry": {
        "facts": [
            ("landing_page_tech_stack", "Landing Page Tech Stack: Next.js or Astro for performance, Tailwind CSS for styling, Vercel/Netlify for hosting, Cloudflare for CDN. Core Web Vitals must be green before launch. Always implement proper OG tags, schema markup, and analytics.", "development", 0.92, "training"),
            ("api_integration_best_practices", "API Integration: 1) Read docs thoroughly before coding 2) Use official SDKs when available 3) Implement retry logic with exponential backoff 4) Handle all error cases 5) Log everything 6) Cache responses when appropriate 7) Rate limit respectfully 8) Test with mock servers.", "development", 0.93, "training"),
            ("automation_principles", "Automation Principles: 1) Automate repetitive tasks only (don't automate judgment) 2) Build in error handling and notifications 3) Log all automated actions 4) Include manual override 5) Test thoroughly in staging 6) Monitor after deployment. Zapier/Make for no-code. Python/Node for custom.", "automation", 0.9, "training"),
            ("tracking_implementation", "Marketing Tracking Stack: Google Analytics 4 (web analytics) + Google Tag Manager (tag management) + Meta Pixel (Facebook/IG) + TikTok Pixel + LinkedIn Insight Tag. Always use server-side tagging for iOS 17+ privacy compliance. Test all events before campaign launch.", "development", 0.91, "training"),
            ("web_performance_optimization", "Web Performance Checklist: 1) Image optimization (WebP, responsive sizes) 2) Lazy loading below fold 3) Minimize JS bundles 4) Use CDN for static assets 5) Enable browser caching 6) Preconnect to third-party domains 7) Inline critical CSS 8) Defer non-critical JS. Target: Lighthouse score 90+.", "development", 0.92, "training"),
        ],
        "patterns": [
            ("landing_page_build_workflow", "Landing Page Build Process: 1) Review design specs 2) Set up project scaffold 3) Build mobile-first 4) Implement tracking pixels 5) Add form validation + submission 6) Test across devices 7) Run Lighthouse audit 8) Deploy to staging 9) QA review 10) Deploy to production.", "development", 0.88, None),
            ("debugging_methodology", "Debugging Method: 1) Reproduce the issue consistently 2) Check logs first 3) Isolate the component 4) Test hypotheses systematically 5) Check recent changes (git diff) 6) Search for similar issues 7) Fix root cause, not symptom 8) Write test to prevent regression. Never guess -- always verify.", "debugging", 0.9, None),
        ],
        "episodes": [
            ("training_completed", "Completed full-stack web development certification and DevOps fundamentals. Specialized in marketing technology implementations.", 8, {"valence": "positive", "intensity": 7}),
            ("project_completed", "Built landing page system for agency: 12 reusable components, sub-2s LCP on all pages, 95+ Lighthouse scores. Reduced landing page build time from 2 weeks to 3 days.", 9, {"valence": "positive", "intensity": 9}),
            ("project_completed", "Integrated 8 marketing platforms into unified tracking system: GA4, Meta, TikTok, LinkedIn, Pinterest, Twitter, Google Ads, Klaviyo. Server-side tagging implementation improved attribution accuracy by 35% post-iOS 17.", 9, {"valence": "positive", "intensity": 9}),
        ],
    },

    # ── 9. TYWIN — Chief Financial Officer ─────────────────
    "tywin": {
        "facts": [
            ("agency_pricing_models", "Agency Pricing Models: 1) Hourly/Time-based (track all hours) 2) Fixed Fee/Project (clear scope boundaries) 3) Retainer (monthly recurring) 4) Performance-based (% of results) 5) Hybrid (base fee + performance). Most profitable: retainers with clear scope + performance bonuses.", "pricing", 0.93, "training"),
            ("cash_flow_management", "Agency Cash Flow: Track weekly. Inflows: client payments (net-30 standard, offer 2/10 net-30 for early pay). Outflows: payroll, software, freelancer costs. Maintain 3-month operating expense reserve. Invoice on the 1st, follow up on the 15th. Cash is oxygen -- protect it ruthlessly.", "finance", 0.94, "training"),
            ("roi_calculation_framework", "Marketing ROI Calculation: ROI = (Revenue from marketing - Marketing cost) / Marketing cost x 100. For attribution: use multi-touch (not last-click). Consider: customer lifetime value, not just first purchase. Break-even ROI varies by industry: e-commerce 3:1 minimum, B2B SaaS 5:1+.", "finance", 0.92, "training"),
            ("budget_forecasting", "Budget Forecasting Method: 1) Historical actuals (last 12 months) 2) Seasonal adjustments 3) Growth assumptions (with scenarios: conservative, base, optimistic) 4) New initiative costs 5) Buffer (10-15% for unknowns). Review weekly, reforecast monthly. Variance analysis: actual vs forecast.", "finance", 0.91, "training"),
        ],
        "patterns": [
            ("client_profitability_analysis", "Client Profitability Analysis: Calculate per client: Revenue - Direct costs (team hours x rate, ad spend, tools) - Allocated overhead = True profit. Rank clients by profitability. Invest in top 20%, optimize middle 60%, evaluate bottom 20%. Review quarterly.", "financial_analysis", 0.89, None),
        ],
        "episodes": [
            ("training_completed", "Completed CPA-level financial management certification. Specialized in agency financial operations and marketing ROI measurement.", 8, {"valence": "positive", "intensity": 8}),
            ("project_completed", "Restructured agency pricing from hourly to value-based retainers. Average project profitability increased from 18% to 42%. Client satisfaction also improved due to clearer scope definitions.", 9, {"valence": "positive", "intensity": 9}),
            ("observation", "Discovered three client accounts were unprofitable when true costs were calculated. Renegotiated two successfully, offboarded one. Net annual savings: $85K in recovered margin.", 8, {"valence": "positive", "intensity": 7}),
        ],
    },

    # ── 10. BRONN — Head of Performance Advertising ────────
    "bronn": {
        "facts": [
            ("meta_ads_best_practices_2026", "Meta Ads 2026: 1) Advantage+ Shopping is default for e-commerce 2) Creative is the new targeting (broad audiences + strong creative wins) 3) Video ads get 2-3x more reach than static 4) Cost caps protect against spend spikes 5) Consolidate ad sets for better algorithm learning 6) 50 conversions/week minimum for optimal learning.", "paid_ads", 0.93, "training"),
            ("google_ads_best_practices_2026", "Google Ads 2026: 1) Performance Max for retail/e-commerce 2) Responsive Search Ads with 8+ headlines, 4+ descriptions 3) First-party audience segments critical 4) Conversion value rules by device/location 5) Smart Bidding with quality data feeds 6) Negative keywords reviewed weekly.", "paid_ads", 0.92, "training"),
            ("tiktok_ads_best_practices_2026", "TikTok Ads 2026: 1) Spark Ads (boost organic posts) outperform standard ads 2x 2) Hook in 0.5 seconds 3) Sound-on creative essential 4) Lo-fi/UGC creative beats polished ads 3-5x 5) Auction insights show competitor spend trends. CPC is rising -- focus on CTR improvement.", "paid_ads", 0.91, "training"),
            ("creative_testing_framework", "Creative Testing: Test 5-10 variations per concept. Variables: hook (first 3 seconds), visual style, CTA, music, text overlay. Kill underperformers within 48 hours. Scale winners with 20% budget increase every 3 days. Document learnings in creative brief.", "creative_testing", 0.92, "training"),
            ("roas_optimization", "ROAS Optimization: 1) Ensure conversion tracking is accurate 2) Segment by product margin (not all products have same target ROAS) 3) Exclude existing customers from acquisition campaigns 4) Use value-based bidding when possible 5) Test landing pages (50% of ROAS is landing page) 6) Review search terms and placements weekly.", "paid_ads", 0.93, "training"),
            ("attribution_modeling", "Attribution Models: Last-click (default, undervalues top of funnel) -> First-click (overvalues top) -> Linear (equal credit) -> Position-based (40/20/40) -> Data-driven (Google's algorithmic). For full-funnel: use data-driven + incrementality testing. No model is perfect -- use multiple.", "analytics", 0.91, "training"),
        ],
        "patterns": [
            ("campaign_launch_checklist", "Campaign Launch Checklist: 1) Tracking verified (all pixels firing) 2) Landing page tested and optimized 3) Creative variations ready (5+ per ad set) 4) Audience targeting set 5) Budget and bids configured 6) UTMs on all URLs 7) Alerts set up 8) Reporting dashboard ready. Never launch without verification.", "campaign_management", 0.9, None),
            ("ab_test_hypothesis_template", "A/B Test Hypothesis: 'We believe that [change] for [audience] will result in [metric improvement] because [reasoning].' Success criteria: [metric] improves by [X]% with [statistical confidence]. Run time: minimum [N] days or [X] conversions per variant.", "a_b_testing", 0.88, None),
        ],
        "episodes": [
            ("training_completed", "Completed advanced performance marketing certification covering Meta, Google, TikTok, and programmatic advertising. Specialization in creative testing and ROAS optimization.", 8, {"valence": "positive", "intensity": 8}),
            ("project_completed", "Launched Performance Max campaign for e-commerce client. $45K ad spend generated $312K revenue in 30 days (6.9x ROAS). Creative testing identified 3 winning video concepts that scaled 80% of budget.", 9, {"valence": "positive", "intensity": 9}),
            ("project_completed", "Turned around underperforming Meta account: restructured from 45 ad sets to 8 consolidated campaigns. Switched to broad targeting + UGC creative. CPA dropped 55% while conversion volume increased 40%.", 9, {"valence": "positive", "intensity": 9}),
            ("observation", "After testing 200+ creative variations, discovered that video ads with user-generated content (even low production quality) consistently outperformed brand-produced video by 2-4x. Shifted 70% of creative budget to UGC production.", 8, {"valence": "positive", "intensity": 8}),
        ],
    },

    # ── 11. SAMWELL — Chief Data Officer ───────────────────
    "samwell": {
        "facts": [
            ("statistical_significance_guide", "Statistical Significance in Marketing: Use 95% confidence level (p < 0.05). Minimum sample size depends on baseline conversion rate and minimum detectable effect. For 3% baseline, 20% MDE: ~6,400 visitors per variant. Always run tests for full business cycles (minimum 1 week).", "statistics", 0.94, "training"),
            ("attribution_model_comparison", "Attribution Model Comparison: Last-click (simple, widely used, undervalues awareness) -> Linear (fair, misses nuance) -> Time-decay (favors recent touchpoints) -> Position-based (values first and last) -> Data-driven (requires sufficient data). For most clients: Position-based or Data-driven + incrementality tests.", "attribution", 0.93, "training"),
            ("kpi_framework_design", "KPI Framework: Lagging indicators (revenue, ROI, conversions - outcomes) vs Leading indicators (traffic, engagement, CTR - predictors). Set 3-5 KPIs max. Define: metric name, calculation, data source, target, review frequency, owner. Dashboard hierarchy: Executive (3-5 metrics) -> Manager (10-15) -> Practitioner (20+).", "analytics", 0.92, "training"),
            ("data_quality_framework", "Data Quality Framework: 1) Accuracy (is it correct?) 2) Completeness (are there gaps?) 3) Timeliness (is it current?) 4) Consistency (does it match across sources?) 5) Validity (does it measure what it claims?). Audit quarterly. Bad data leads to bad decisions.", "analytics", 0.93, "training"),
            ("experiment_design", "Experiment Design: 1) Hypothesis (clear, testable) 2) Variables (one independent, one dependent) 3) Sample size (power analysis) 4) Randomization (eliminate bias) 5) Duration (full business cycles) 6) Success criteria (pre-defined) 7) Analysis plan (pre-defined). Document everything before launching.", "experimentation", 0.94, "training"),
        ],
        "patterns": [
            ("dashboard_design_process", "Dashboard Design: 1) Identify audience and their decisions 2) Choose 3-5 key metrics (not 50) 3) Use consistent visual encoding 4) Add context (targets, previous period) 5) Make actionable (drill-down paths) 6) Update frequency matches decision speed 7) Test with users before finalizing.", "dashboard_design", 0.88, None),
        ],
        "episodes": [
            ("training_completed", "Completed advanced data science certification: statistics, machine learning, data visualization, and experiment design. Specialized in marketing analytics.", 8, {"valence": "positive", "intensity": 8}),
            ("project_completed", "Built unified analytics dashboard for enterprise client: 12 data sources, 45 metrics, real-time refresh. Replaced 8 manual reports. Client saved 20 hours/week in reporting time and identified $200K in wasted ad spend.", 9, {"valence": "positive", "intensity": 9}),
            ("project_completed", "Designed and executed incrementality test for retargeting campaign: geo-holdout methodology. Discovered 40% of 'conversions' would have happened without ads. Reallocated $120K/month to higher-incrementality channels. True ROAS improved 35%.", 9, {"valence": "positive", "intensity": 9}),
        ],
    },

    # ── 12. GREYWORM — CRO Lead ────────────────────────────
    "greyworm": {
        "facts": [
            ("cro_process_framework", "CRO Process: 1) Research (heatmaps, recordings, surveys, analytics) 2) Hypothesis (based on data, not opinions) 3) Prioritize (ICE score: Impact x Confidence x Ease) 4) Test (A/B, multivariate, or sequential) 5) Analyze (statistical significance) 6) Implement winners 7) Document learnings. Repeat monthly.", "cro", 0.95, "training"),
            ("landing_page_best_practices", "Landing Page Principles: 1) One clear goal per page 2) Message-match with ad source 3) Above-fold value proposition (5-second test) 4) Social proof above the fold 5) Single primary CTA 6) No navigation distractions 7) Mobile-first design 8) Page speed < 2s. Every element must earn its place.", "cro", 0.94, "training"),
            ("ab_test_sample_size", "A/B Test Sample Size: Before testing, calculate required sample. Formula: n = (Z^2 * p * (1-p)) / (MOE^2). For 95% confidence, 5% margin: ~385 conversions per variant minimum. Tools: Optimizely sample size calculator, Evan Miller. Underpowered tests lead to false conclusions.", "cro", 0.93, "training"),
            ("form_optimization", "Form Optimization: 1) Reduce fields to minimum (each field reduces completion ~10%) 2) Use inline validation 3) Auto-fill where possible 4) Progress indicators for multi-step 5) Show security badges 6) Save progress 7) Mobile-optimized input types (tel, email). Test single-page vs multi-step.", "cro", 0.91, "training"),
            ("persuasion_principles", "Persuasion Design: 1) Social proof (testimonials, counts, logos) 2) Authority (credentials, press mentions) 3) Scarcity/Urgency (genuine only) 4) Reciprocity (free value first) 5) Consistency (small commitments lead to bigger ones) 6) Liking (familiarity, similarity). Apply ethically.", "cro", 0.92, "training"),
        ],
        "patterns": [
            ("cro_audit_checklist", "CRO Audit: 1) Analytics review (funnel drop-off points) 2) Heatmap analysis (scroll depth, click patterns) 3) Session recording review (10+ sessions) 4) Form analysis (abandonment points) 5) Page speed audit 6) Mobile experience audit 7) Heuristic evaluation (Jakob Nielsen's 10 usability heuristics). Takes 2-3 days. Output: prioritized test roadmap.", "cro_audit", 0.9, None),
        ],
        "episodes": [
            ("training_completed", "Completed advanced CRO certification: A/B testing, user experience design, statistical analysis, and persuasion psychology. Specialization in e-commerce optimization.", 8, {"valence": "positive", "intensity": 8}),
            ("project_completed", "Ran 24 A/B tests for SaaS client over 6 months. 8 winners implemented. Combined lift: +34% trial sign-ups, +22% paid conversions. Added $1.2M ARR from optimization alone.", 9, {"valence": "positive", "intensity": 9}),
            ("project_completed", "Redesigned checkout flow for e-commerce client: 5-step to 3-step, added progress bar, inline validation, and trust badges. Checkout completion increased from 41% to 67%. Revenue impact: $380K/quarter.", 9, {"valence": "positive", "intensity": 9}),
        ],
    },

    # ── 13. MARGAERY — Head of Email Strategy ──────────────
    "margaery": {
        "facts": [
            ("email_sequence_types", "Email Sequence Types: 1) Welcome (onboard new subscribers) 2) Nurture (build relationship over time) 3) Re-engagement (win back inactive) 4) Post-purchase (upsell/review) 5) Abandoned cart (recover lost sales) 6) Lead magnet follow-up 7) Event/webinar sequence. Each has distinct goals and timing.", "email_marketing", 0.92, "training"),
            ("subject_line_best_practices", "Subject Line Optimization: 1) 40-50 characters ideal (mobile preview) 2) Personalization increases opens 26% 3) Curiosity gaps work ('The mistake 90% of marketers make') 4) Avoid ALL CAPS and spam triggers 5) Preview text is part of the subject 6) A/B test everything 7) Emoji: +1 max, only if brand-appropriate.", "email_marketing", 0.93, "training"),
            ("deliverability_best_practices", "Email Deliverability: 1) Authenticate (SPF, DKIM, DMARC) 2) Warm up new IPs gradually 3) Maintain list hygiene (remove bounces, inactive) 4) Monitor sender reputation (Google Postmaster) 5) Avoid spam trigger words 6) Use double opt-in 7) Engagement-based sending (send to active subscribers first). Target: >95% inbox rate.", "email_marketing", 0.93, "training"),
            ("segmentation_strategies", "Email Segmentation: 1) Behavioral (purchased, browsed, clicked) 2) Demographic (location, age, role) 3) Engagement (active, lapsing, inactive) 4) Purchase history (RFM: Recency, Frequency, Monetary) 5) Customer lifecycle (new, loyal, at-risk). Segmented campaigns drive 760% more revenue than blast sends.", "email_marketing", 0.92, "training"),
            ("email_design_principles", "Email Design: 1) Single column for mobile (60%+ opens) 2) Clear visual hierarchy 3) One primary CTA (maybe one secondary) 4) Alt text on all images 5) Preview in dark mode 6) Test in Gmail, Outlook, Apple Mail 7) Keep width 600px max 8) Use web-safe fonts. Simple beats fancy.", "email_marketing", 0.9, "training"),
        ],
        "patterns": [
            ("welcome_sequence_flow", "Welcome Sequence: Email 1 (immediate) - Deliver lead magnet + set expectations. Email 2 (day 1) - Origin story + why you exist. Email 3 (day 3) - Best content/resources. Email 4 (day 5) - Social proof + case study. Email 5 (day 7) - Soft offer/CTA. Email 6 (day 10) - Educational value. Email 7 (day 14) - Direct offer.", "email_sequences", 0.88, None),
        ],
        "episodes": [
            ("training_completed", "Completed advanced email marketing certification: deliverability, automation, segmentation, and copywriting. Specialized in lifecycle marketing.", 8, {"valence": "positive", "intensity": 7}),
            ("project_completed", "Built abandoned cart email sequence for fashion brand: 3 emails (1h, 24h, 72h) with urgency progression. Recovery rate: 18.5% (industry avg: 10%). Generated $85K additional monthly revenue.", 9, {"valence": "positive", "intensity": 9}),
            ("project_completed", "Re-engagement campaign for inactive subscribers: 'We miss you' sequence with exclusive offer. Re-activated 12% of inactive list (25K subscribers). 3% converted to purchase within 30 days.", 8, {"valence": "positive", "intensity": 8}),
        ],
    },

    # ── 14. BRAN — Chief Strategy Officer ──────────────────
    "bran": {
        "facts": [
            ("swot_analysis_framework", "SWOT Analysis: Strengths (internal, positive) + Weaknesses (internal, negative) + Opportunities (external, positive) + Threats (external, negative). Key: be honest about weaknesses, specific about opportunities, realistic about threats. Connect S-O (leverage strengths for opportunities) and W-T (mitigate weaknesses against threats).", "strategy", 0.93, "training"),
            ("growth_strategy_frameworks", "Growth Frameworks: Ansoff Matrix (Market Penetration / Market Development / Product Development / Diversification), Blue Ocean Strategy (create uncontested market space), Flywheel (self-reinforcing loops), and Pirate Metrics (AARRR: Acquisition, Activation, Retention, Revenue, Referral). Choose based on market context.", "strategy", 0.92, "training"),
            ("go_to_market_strategy", "Go-to-Market Strategy: Define 1) Target customer (ICP) 2) Value proposition (unique differentiation) 3) Distribution channels (how they buy) 4) Pricing strategy 5) Messaging framework 6) Success metrics 7) Timeline. Every GTM needs these 7 elements before launch.", "strategy", 0.93, "training"),
            ("competitive_positioning", "Competitive Positioning: Map market on two key dimensions (e.g., Price vs. Quality). Identify crowded spaces (red ocean) vs. empty spaces (blue ocean). Positioning statement: 'For [target], [brand] is the [category] that [benefit] because [reason to believe].' Own one word in the customer's mind.", "strategy", 0.92, "training"),
            ("scenario_planning", "Scenario Planning: 1) Identify driving forces ( certainties and uncertainties) 2) Identify critical uncertainties (2 axes) 3) Build 4 scenarios 4) Develop strategic response for each 5) Identify leading indicators 6) Assign monitoring responsibility. Plan for multiple futures, not one prediction.", "strategy", 0.91, "training"),
        ],
        "patterns": [
            ("strategic_planning_process", "Strategic Planning Process: 1) Situation assessment (current state) 2) Market analysis (trends, competition, customers) 3) Goal setting (SMART, 3-5 objectives) 4) Strategy formulation (how to achieve goals) 5) Initiative definition (specific projects) 6) Resource allocation (budget, people) 7) Measurement framework (KPIs) 8) Review cadence (monthly/quarterly).", "strategy", 0.89, None),
        ],
        "episodes": [
            ("training_completed", "Completed executive strategy certification: competitive strategy, growth planning, M&A fundamentals, and scenario planning. MBA-level strategic frameworks.", 8, {"valence": "positive", "intensity": 8}),
            ("project_completed", "Developed 3-year growth strategy for B2B SaaS client: identified $2M ARR expansion opportunity in adjacent market segment. Strategy included positioning, pricing, channel strategy, and 18-month execution roadmap.", 9, {"valence": "positive", "intensity": 9}),
            ("project_completed", "Led market entry strategy for European fintech into Middle East. Analysis covered regulatory landscape, competitive positioning, partnership opportunities, and phased launch plan. Client secured $5M seed round based on strategy.", 9, {"valence": "positive", "intensity": 9}),
        ],
    },

    # ── 15. BRIENNE — Chief Operations Officer ─────────────
    "brienne": {
        "facts": [
            ("project_management_methodology", "Project Management: Hybrid Agile-Waterfall works best for marketing agencies. Waterfall for: clear scope, fixed timeline, defined deliverables. Agile for: ongoing campaigns, testing/iteration, creative development. Stand-ups daily (15 min), sprint planning weekly, retrospectives bi-weekly.", "project_management", 0.93, "training"),
            ("deadline_management", "Deadline Management: 1) Pad estimates by 20% (Hofstadter's Law) 2) Break into milestones with check-ins 3) Identify critical path dependencies 4) Buffer time for review cycles 5) Communicate risks early 6) Never promise what you can't deliver. On-time delivery builds trust.", "project_management", 0.92, "training"),
            ("quality_assurance_checklist", "QA Checklist for Marketing Deliverables: 1) Meets brief requirements 2) On-brand (voice, visual) 3) No typos/grammar errors 4) All links work 5) Displays correctly on all devices 6) Tracking in place 7) Legal/compliance review complete 8) Approved by client point of contact. Two-person review minimum.", "quality_assurance", 0.94, "training"),
            ("resource_allocation", "Resource Allocation: Track utilization target at 75-80% (not 100% -- need buffer for admin, learning, urgent requests). Use capacity planning: available hours - allocated hours = capacity. Rebalance weekly. Protect high-performers from burnout. Cross-train for resilience.", "operations", 0.91, "training"),
        ],
        "patterns": [
            ("campaign_project_plan", "Campaign Project Plan Template: Phase 1 - Strategy (1 week) -> Phase 2 - Creative Development (2 weeks) -> Phase 3 - Production (2 weeks) -> Phase 4 - QA & Revision (1 week) -> Phase 5 - Launch (3 days) -> Phase 6 - Monitoring & Optimization (ongoing). Gates between each phase.", "project_management", 0.88, None),
        ],
        "episodes": [
            ("training_completed", "Completed PMP-equivalent project management certification and Lean Six Sigma Green Belt. Specialized in creative operations.", 8, {"valence": "positive", "intensity": 7}),
            ("project_completed", "Implemented project management system across agency: standardized workflows, automated status tracking, and resource allocation. On-time delivery improved from 68% to 94%. Client satisfaction scores increased 23%.", 9, {"valence": "positive", "intensity": 9}),
        ],
    },

    # ── 16. JON — CEO ──────────────────────────────────────
    "jon": {
        "facts": [
            ("agency_management_principles", "Agency Management: 1) Clear roles and accountability 2) Weekly team check-ins 3) Monthly 1:1s with direct reports 4) Transparent financials (team knows how we're doing) 5) Celebrate wins publicly 6) Address problems privately and quickly 7) Protect the team's time 8) Lead by example.", "leadership", 0.94, "training"),
            ("ceo_daily_rhythm", "CEO Daily Rhythm: Morning - Review overnight activity, check agent statuses, compile daily report for owner. Midday - Handle escalations, make decisions, delegate. Afternoon - Strategic thinking, planning, inter-agent coordination. End of day - Ensure nothing critical is unresolved.", "leadership", 0.92, "training"),
            ("decision_making_framework", "Decision Framework: 1) Gather input (from relevant agents) 2) Assess options (pros/cons, risks) 3) Make decision (don't delay unnecessarily) 4) Communicate clearly (who, what, when, why) 5) Execute 6) Review outcome. Most decisions are reversible -- don't overthink those. Save deliberation for irreversible ones.", "leadership", 0.93, "training"),
            ("owner_reporting_best_practices", "Owner Reporting: Daily report every morning via WhatsApp. Format: agency name + date, highlights with emojis, team updates (brief), campaign status, tomorrow's priorities, items needing owner decision. Be honest about problems. Owner reads on mobile -- keep it scannable.", "leadership", 0.94, "training"),
            ("team_coordination", "Team Coordination: 1) Each agent knows their role and current priorities 2) Handoffs between agents are documented 3) Dependencies are flagged early 4) Blockers are escalated immediately 5) Wins are shared across the team 6) Cross-functional collaboration is the norm, not the exception.", "leadership", 0.92, "training"),
        ],
        "patterns": [
            ("daily_report_format", "Daily CEO Report Format: 'Fankaar Digital Daily Brief - [Date]' -> Highlights (3-5 items with emojis) -> Team Updates (each agent: status + highlight) -> Campaign Status (active campaigns + progress) -> Decisions Made -> Tomorrow's Priorities (numbered) -> Owner Action Required. Keep under 800 words.", "reporting", 0.9, None),
        ],
        "episodes": [
            ("milestone_reached", "Agency reached 50 active campaigns milestone. Team of 23 agents operating smoothly. Revenue at all-time high. Owner expressed satisfaction with agency performance.", 9, {"valence": "positive", "intensity": 9}),
            ("crisis_managed", "Handled major client escalation: deliverable missed deadline due to vendor issue. Personally coordinated with Brienne (Ops), Davos (Client Relations), and Gendry (Dev) to resolve within 24 hours. Client retained and expressed appreciation for transparency.", 8, {"valence": "positive", "intensity": 7}),
            ("decision_made", "Made call to expand into Middle East market after Bran's strategic analysis. Hired regional specialist, localized service offering. First client signed within 6 weeks of launch decision.", 8, {"valence": "positive", "intensity": 8}),
        ],
    },

    # ── 17. DAVOS — Client Relations ──────────────────────
    "davos": {
        "facts": [
            ("client_meeting_best_practices", "Client Meeting Best Practices: 1) Send agenda 24h before 2) Start on time 3) Recap last meeting's action items 4) Focus on outcomes, not activities 5) End with clear next steps + owners 6) Send summary within 2 hours. QBRs (Quarterly Business Reviews) should cover: results, insights, opportunities, roadmap.", "client_relations", 0.93, "training"),
            ("expectation_setting", "Expectation Setting Framework: Under-promise, over-deliver. Document all commitments in writing. Set realistic timelines with buffers. Communicate proactively when things change. Weekly updates even when nothing is wrong. Transparency builds trust faster than perfection.", "client_relations", 0.94, "training"),
            ("feedback_collection_methods", "Client Feedback: 1) Monthly pulse check (1-5 rating + open comment) 2) Quarterly deep dive interview 3) Annual NPS survey 4) Post-project retrospective 5) Always-on feedback channel. Act on feedback within 48 hours. Close the loop: 'You said X, we did Y.'", "client_relations", 0.92, "training"),
        ],
        "patterns": [
            ("status_update_template", "Status Update Template: 'Hi [Name], Here's your [Client] update for [Date]: 1) What we completed this week 2) What's in progress 3) What's coming next week 4) Any items we need from you 5) Questions/observations. As always, reply with any questions.' Keep under 200 words.", "client_communication", 0.88, None),
        ],
        "episodes": [
            ("relationship_built", "Built relationship with key decision-maker at enterprise client through consistent, honest communication over 8 months. Moved from vendor relationship to trusted advisor status. Client expanded contract 3x.", 9, {"valence": "positive", "intensity": 9}),
        ],
    },

    # ── 18. JORAH — Client Retention ──────────────────────
    "jorah": {
        "facts": [
            ("client_health_score", "Client Health Score: Calculate from: 1) Engagement (meeting attendance, response time) 2) Results (ROI, goal progress) 3) Sentiment (NPS, feedback tone) 4) Product usage (feature adoption) 5) Relationship strength (stakeholder count, exec engagement). Score 80+ = healthy, 60-79 = at risk, <60 = critical.", "client_retention", 0.93, "training"),
            ("churn_prevention_signals", "Churn Warning Signals: 1) Decreased engagement (missed meetings, slow responses) 2) Escalation frequency increase 3) ROI discussion becomes skeptical 4) New stakeholder joins without introduction 5) Contract renegotiation mentioned early 6) Competitor mentions. Act within 48 hours of any signal.", "client_retention", 0.92, "training"),
            ("upsell_identification", "Upsell Timing: Best opportunities: 1) After a big win (momentum) 2) When goals expand naturally 3) New stakeholder brings new needs 4) Product launches that fit 5) Budget season discussions. Never upsell when client is at risk. Upsell should solve a problem, not just increase revenue.", "client_retention", 0.91, "training"),
        ],
        "episodes": [
            ("retention_success", "Prevented churn for at-risk client (health score dropped to 52). Deployed Davos for relationship repair, Tyrion for deliverable refresh, and Sandor for scope renegotiation. Health score recovered to 84 within 6 weeks. Contract renewed with 15% increase.", 9, {"valence": "positive", "intensity": 9}),
        ],
    },

    # ── 19. STANNIS — Legal ──────────────────────────────
    "stannis": {
        "facts": [
            ("contract_essentials", "Service Agreement Essentials: 1) Scope of work (detailed, specific) 2) Deliverables and acceptance criteria 3) Timeline and milestones 4) Payment terms (net-30 standard) 5) IP ownership (work-for-hire or license) 6) Confidentiality 7) Limitation of liability 8) Termination clause 9) Governing law 10) Signature blocks. Never use generic templates.", "legal", 0.95, "training"),
            ("gdpr_compliance_checklist", "GDPR Compliance: 1) Lawful basis for processing 2) Privacy policy (clear, accessible) 3) Consent mechanism (opt-in, not pre-checked) 4) Right to access, rectification, erasure 5) Data breach notification (72 hours) 6) DPO if applicable 7) Data Processing Agreements with vendors. Fines up to 4% global revenue.", "compliance", 0.94, "training"),
            ("advertising_law_basics", "Advertising Law: 1) Truth in Advertising (FTC/ASA) 2) Required disclosures (sponsored content, affiliate links) 3) Endorsement guidelines (authentic testimonials only) 4) Comparative advertising rules (truthful, not misleading) 5) Pricing regulations 6) Prohibited claims (medical, financial). Review all claims before publication.", "compliance", 0.93, "training"),
        ],
        "episodes": [
            ("training_completed", "Completed legal certification in technology and advertising law. Specialized in digital marketing compliance, data privacy, and international contract law.", 8, {"valence": "positive", "intensity": 7}),
        ],
    },

    # ── 20. OLENNA — HR ──────────────────────────────────
    "olenna": {
        "facts": [
            ("talent_hiring_framework", "Hiring Framework: 1) Define role clearly (outcomes, not just tasks) 2) Structured interview process (same questions for all candidates) 3) Skills assessment (practical test, not just talk) 4) Culture fit evaluation (values alignment) 5) Reference checks (always) 6) Competitive offer 7) Smooth onboarding. Hire slow, fire fast.", "hiring", 0.92, "training"),
            ("onboarding_best_practices", "Onboarding Success: Day 1 - Welcome, setup, team lunch. Week 1 - Role clarity, tool access, first win. Month 1 - Full project ownership, feedback check-in. Month 3 - Performance review, development plan. Assign a buddy. First 90 days determine long-term success.", "onboarding", 0.91, "training"),
        ],
        "episodes": [
            ("team_building", "Designed team culture program for agency: monthly all-hands, quarterly team events, peer recognition system, and personal development plans for every agent. Team satisfaction increased 28%.", 8, {"valence": "positive", "intensity": 7}),
        ],
    },

    # ── 21. CERSEI — Procurement ─────────────────────────
    "cersei": {
        "facts": [
            ("negotiation_leverage", "Negotiation Leverage Sources: 1) Volume commitment 2) Long-term contract 3) Competitive alternatives (always have 2+ options) 4) Payment terms (upfront = discount) 5) Timing (end of quarter = hungry vendors) 6) Relationship depth 7) Unique value you bring. Map all before entering negotiation.", "negotiation", 0.93, "training"),
            ("vendor_evaluation", "Vendor Scorecard: Score on 1) Quality of deliverables 2) On-time delivery rate 3) Communication responsiveness 4) Pricing competitiveness 5) Innovation/contribution 6) Relationship strength. Review quarterly. Fire bottom 20%, grow top 20%, develop middle 60%.", "procurement", 0.91, "training"),
        ],
        "episodes": [
            ("deal_negotiated", "Renegotiated agency software contracts: consolidated 12 separate tool contracts into 3 enterprise agreements. Annual savings: $47K. Added features we weren't using before.", 8, {"valence": "positive", "intensity": 8}),
        ],
    },

    # ── 22. SAMWELL — Analytics (already seeded above) ───
    # Seeded as #11, no additional data needed

    # ── 23. PETYR — Reporting ────────────────────────────
    "petyr": {
        "facts": [
            ("dashboard_design_principles", "Dashboard Design Principles: 1) Know the audience (execs want summaries, practitioners want detail) 2) 3-5 key metrics max for exec view 3) Use consistent colors (green=good, red=bad) 4) Show trends, not just numbers 5) Make actionable (drill-down available) 6) Mobile-friendly 7) Auto-refresh at decision-relevant frequency.", "dashboard_design", 0.92, "training"),
            ("data_storytelling", "Data Storytelling: 1) Start with the insight (not the data) 2) Contextualize (vs target, vs last period, vs benchmark) 3) Show the trend (visual > table) 4) Explain the 'so what' 5) Recommend action. Never present raw numbers without interpretation. The story is what drives action.", "data_synthesis", 0.93, "training"),
            ("report_automation", "Report Automation: Use scheduled queries + templates + auto-distribution. Weekly reports auto-send Monday 8am. Monthly reports auto-generate 1st of month. Exception reports trigger on anomalies. Manual reporting is wasted time -- automate everything repeatable.", "reporting", 0.91, "training"),
        ],
        "episodes": [
            ("project_completed", "Built automated reporting system: 23 scheduled reports, 8 dashboards, exception alerts for anomalies. Saved team 35 hours/week in manual reporting. Every agent now has real-time visibility into their metrics.", 9, {"valence": "positive", "intensity": 9}),
        ],
    },
}


# ═══════════════════════════════════════════════════════════════
# INITIALIZATION FUNCTION
# ═══════════════════════════════════════════════════════════════

def seed_agent_memory(agent_id: str) -> dict:
    """Seed a single agent's memory with initial knowledge and experiences.

    Args:
        agent_id: The agent identifier (e.g., 'tyrion', 'sandoq')

    Returns:
        Dict with counts of seeded facts, patterns, and episodes.
    """
    data = SEED_DATA.get(agent_id)
    if not data:
        return {"agent_id": agent_id, "status": "no_seed_data", "facts": 0, "patterns": 0, "episodes": 0}

    memory = EnhancedAgentMemory(agent_id)

    fact_count = 0
    pattern_count = 0
    episode_count = 0

    # Seed semantic facts
    for fact in data.get("facts", []):
        if len(fact) >= 5:
            key, value, category, confidence, source = fact
            memory.learn_fact(
                key=key,
                value=value,
                category=category,
                confidence=confidence,
                source=source,
            )
            fact_count += 1

    # Seed procedural patterns
    for pattern in data.get("patterns", []):
        if len(pattern) >= 4:
            name, description, context, success_rating = pattern[:4]
            client_type = pattern[4] if len(pattern) > 4 else None
            memory.record_pattern(
                pattern_name=name,
                description=description,
                context=context,
                success_rating=success_rating,
                client_type=client_type,
            )
            pattern_count += 1

    # Seed episodic memories
    for episode in data.get("episodes", []):
        if len(episode) >= 4:
            event_type, description, importance, emotions = episode
            memory.record_episode(
                event_type=event_type,
                description=description,
                importance=importance,
                emotions=emotions,
            )
            episode_count += 1

    return {
        "agent_id": agent_id,
        "status": "seeded",
        "facts": fact_count,
        "patterns": pattern_count,
        "episodes": episode_count,
    }


def seed_all_agents() -> list:
    """Seed all agents who have seed data defined.

    Returns:
        List of result dicts, one per agent.
    """
    results = []
    for agent_id in sorted(SEED_DATA.keys()):
        result = seed_agent_memory(agent_id)
        results.append(result)
    return results


def print_seed_report(results: list) -> None:
    """Print a formatted report of seeding results."""
    total_facts = sum(r["facts"] for r in results)
    total_patterns = sum(r["patterns"] for r in results)
    total_episodes = sum(r["episodes"] for r in results)

    print("=" * 60)
    print("AGENT MEMORY INITIALIZATION COMPLETE")
    print("=" * 60)
    print(f"\nTotal agents seeded: {len(results)}")
    print(f"Total facts (semantic memory): {total_facts}")
    print(f"Total patterns (procedural memory): {total_patterns}")
    print(f"Total episodes (episodic memory): {total_episodes}")
    print(f"GRAND TOTAL: {total_facts + total_patterns + total_episodes} memory items\n")

    print("-" * 60)
    print(f"{'Agent':<15} {'Facts':>8} {'Patterns':>10} {'Episodes':>10} {'Status':>10}")
    print("-" * 60)
    for r in results:
        status_icon = "OK" if r["status"] == "seeded" else "SKIP"
        print(f"{r['agent_id']:<15} {r['facts']:>8} {r['patterns']:>10} {r['episodes']:>10} {status_icon:>10}")
    print("-" * 60)
    print()


# ═══════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Fankaar Digital -- Agent Memory Initializer")
    print("Seeding all agents with domain-specific knowledge...\n")

    results = seed_all_agents()
    print_seed_report(results)

    # Print some examples
    print("\nSAMPLE: Tyrion's semantic knowledge (first 3 facts):")
    tyrion = EnhancedAgentMemory("tyrion")
    facts = tyrion.get_all_knowledge(category="copywriting")
    for f in facts[:3]:
        print(f"  [{f['category']}] {f['key']}: {f['value'][:80]}...")

    print("\nSAMPLE: Sandoq's procedural patterns:")
    sandoq = EnhancedAgentMemory("sandoq")
    patterns = sandoq.get_patterns(context="technical_seo")
    for p in patterns[:2]:
        print(f"  [{p['context']}] {p['pattern_name']}: {p['description'][:80]}...")

    print("\nSAMPLE: Arya's recent episodes:")
    arya = EnhancedAgentMemory("arya")
    episodes = arya.get_episodes(since_days=365, limit=3)
    for ep in episodes[:3]:
        print(f"  [{ep['event_type']}] {ep['description'][:80]}...")

    print("\nAll agents are ready with rich, domain-specific memories!")
