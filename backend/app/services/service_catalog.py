"""
Claude Mythos — Service Catalog & Quote Generation
Complete service definitions for all 23 agents, 3 subscription tiers,
and intelligent auto-quote generation based on client needs.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# ═══════════════════════════════════════════════════════════════════
# SERVICE DEFINITIONS — Each maps to an agent
# ═══════════════════════════════════════════════════════════════════

SERVICES: Dict[str, Dict[str, Any]] = {
    # ── Marketing Operations ──
    "social_media_management": {
        "name": "Social Media Management",
        "agent": "missandei",
        "agent_name": "Missandei",
        "category": "Marketing Operations",
        "description": "Full social media strategy, content creation, scheduling, community management, and platform optimization across all major social networks.",
        "deliverables": [
            "30 curated posts/month",
            "Content calendar & scheduling",
            "Community engagement & responses",
            "Monthly analytics & growth report",
            "Hashtag strategy & optimization",
            "Platform-specific content adaptation",
        ],
        "base_price": 800,
        "tier": "starter",
        "addons": {
            "influencer_outreach": {"name": "Influencer Outreach", "price": 500, "agent": "cersei"},
            "paid_social": {"name": "Paid Social Advertising", "price": 600, "agent": "bronn"},
            "social_crisis_management": {"name": "Social Crisis Management", "price": 400, "agent": "sansa"},
        },
    },
    "seo_optimization": {
        "name": "SEO Optimization",
        "agent": "sandoq",
        "agent_name": "Sandoq",
        "category": "Marketing Operations",
        "description": "Technical SEO, keyword research, on-page optimization, link building strategy, and ranking monitoring to improve organic visibility.",
        "deliverables": [
            "Comprehensive SEO audit",
            "Keyword strategy & mapping",
            "On-page optimization recommendations",
            "Monthly rankings report",
            "Backlink analysis & outreach",
            "Technical SEO fixes & monitoring",
        ],
        "base_price": 600,
        "tier": "starter",
        "addons": {
            "local_seo": {"name": "Local SEO Package", "price": 400, "agent": "sandoq"},
            "content_seo": {"name": "SEO Content Writing", "price": 500, "agent": "tyrion"},
            "seo_reporting": {"name": "Advanced SEO Reporting", "price": 300, "agent": "samwell"},
        },
    },
    "reporting_analytics": {
        "name": "Reporting & Analytics",
        "agent": "samwell",
        "agent_name": "Samwell",
        "category": "Marketing Operations",
        "description": "Comprehensive analytics, dashboard creation, KPI tracking, and data-driven insights across all marketing channels.",
        "deliverables": [
            "Monthly performance dashboards",
            "KPI tracking & goal analysis",
            "Attribution modeling",
            "Custom report creation",
            "Data visualization & insights",
            "Quarterly business reviews",
        ],
        "base_price": 500,
        "tier": "starter",
        "addons": {
            "advanced_attribution": {"name": "Advanced Attribution", "price": 400, "agent": "samwell"},
            "predictive_analytics": {"name": "Predictive Analytics", "price": 600, "agent": "bran"},
            "executive_dashboard": {"name": "Executive Dashboard", "price": 300, "agent": "petyr"},
        },
    },
    "client_reporting": {
        "name": "Client Reporting & Data Viz",
        "agent": "petyr",
        "agent_name": "Petyr",
        "category": "Marketing Operations",
        "description": "Beautiful client-facing reports, data visualizations, and executive summaries that make results tangible.",
        "deliverables": [
            "Executive summary reports",
            "Interactive data visualizations",
            "ROI presentation decks",
            "Trend analysis & forecasting",
            "Competitive benchmarking",
            "Custom report templates",
        ],
        "base_price": 500,
        "tier": "starter",
        "addons": {
            "white_label_reports": {"name": "White-Label Reports", "price": 300, "agent": "petyr"},
            "automated_reporting": {"name": "Automated Report Delivery", "price": 200, "agent": "samwell"},
        },
    },
    "copyediting_qa": {
        "name": "Copyediting & Quality Assurance",
        "agent": "podrick",
        "agent_name": "Podrick",
        "category": "Marketing Operations",
        "description": "Meticulous copyediting, proofreading, and quality assurance for all client-facing content.",
        "deliverables": [
            "Copyediting & proofreading",
            "Brand voice consistency checks",
            "Grammar & style verification",
            "Content quality scoring",
            "Accessibility compliance review",
            "Multi-format QA (web, print, social)",
        ],
        "base_price": 400,
        "tier": "starter",
        "addons": {
            "technical_editing": {"name": "Technical Content Editing", "price": 300, "agent": "podrick"},
            "translation_review": {"name": "Translation Quality Review", "price": 400, "agent": "missandei"},
        },
    },
    # ── Content & Creative ──
    "copywriting": {
        "name": "Copywriting & Creative Direction",
        "agent": "tyrion",
        "agent_name": "Tyrion",
        "category": "Content & Creative",
        "description": "World-class copywriting across all formats — ads, landing pages, emails, scripts, and long-form content with strategic creative direction.",
        "deliverables": [
            "Ad copy & creative concepts",
            "Landing page copy",
            "Email campaign copy",
            "Brand storytelling",
            "Script writing (video/audio)",
            "Creative direction & oversight",
        ],
        "base_price": 900,
        "tier": "growth",
        "addons": {
            "long_form_content": {"name": "Long-Form Content", "price": 500, "agent": "tyrion"},
            "brand_messaging": {"name": "Brand Messaging Framework", "price": 600, "agent": "tyrion"},
            "creative_workshop": {"name": "Creative Strategy Workshop", "price": 800, "agent": "tyrion"},
        },
    },
    "brand_design": {
        "name": "Brand & Visual Design",
        "agent": "rhaegar",
        "agent_name": "Rhaegar",
        "category": "Content & Creative",
        "description": "Stunning visual design — brand identity, social graphics, ad creatives, presentations, and comprehensive brand systems.",
        "deliverables": [
            "Social media graphics (30+/month)",
            "Ad creative sets",
            "Brand identity assets",
            "Presentation decks",
            "Infographics & data viz",
            "Brand guidelines maintenance",
        ],
        "base_price": 900,
        "tier": "growth",
        "addons": {
            "brand_refresh": {"name": "Brand Refresh Package", "price": 1200, "agent": "rhaegar"},
            "motion_graphics": {"name": "Motion Graphics", "price": 700, "agent": "gendry"},
            "print_design": {"name": "Print Design Suite", "price": 500, "agent": "rhaegar"},
        },
    },
    "video_production": {
        "name": "Video & Photo Production",
        "agent": "gendry",
        "agent_name": "Gendry",
        "category": "Content & Creative",
        "description": "Professional video editing, motion graphics, photo retouching, and multimedia content production.",
        "deliverables": [
            "Video editing & post-production",
            "Motion graphics & animation",
            "Photo retouching & optimization",
            "Video ad creation",
            "Reels/TikTok/Shorts production",
            "Video asset library management",
        ],
        "base_price": 800,
        "tier": "growth",
        "addons": {
            "video_ads": {"name": "Video Ad Creation", "price": 600, "agent": "gendry"},
            "animation": {"name": "Custom Animation", "price": 900, "agent": "gendry"},
            "live_streaming": {"name": "Live Streaming Setup", "price": 500, "agent": "gendry"},
        },
    },
    "landing_pages": {
        "name": "Landing Pages & Web Development",
        "agent": "greyworm",
        "agent_name": "Greyworm",
        "category": "Content & Creative",
        "description": "High-converting landing pages, website optimization, A/B testing infrastructure, and web development for marketing campaigns.",
        "deliverables": [
            "Custom landing page design & build",
            "A/B testing setup & management",
            "Conversion rate optimization",
            "Page speed optimization",
            "Form & CTA optimization",
            "Mobile-responsive development",
        ],
        "base_price": 800,
        "tier": "growth",
        "addons": {
            "multi_variant": {"name": "Multi-Variant Testing", "price": 500, "agent": "greyworm"},
            "funnel_building": {"name": "Full Funnel Build", "price": 900, "agent": "greyworm"},
            "cms_integration": {"name": "CMS Integration", "price": 600, "agent": "greyworm"},
        },
    },
    # ── Advertising & Growth ──
    "paid_advertising": {
        "name": "Paid Advertising Management",
        "agent": "bronn",
        "agent_name": "Bronn",
        "category": "Advertising & Growth",
        "description": "Expert management of paid campaigns across Google, Meta, TikTok, LinkedIn, and programmatic — focused on ROAS and efficient spend.",
        "deliverables": [
            "Campaign strategy & setup",
            "Daily bid & budget optimization",
            "A/B testing of ad creatives",
            "Audience targeting refinement",
            "Weekly performance reports",
            "Monthly strategy reviews",
        ],
        "base_price": 1000,
        "tier": "growth",
        "addons": {
            "programmatic": {"name": "Programmatic Advertising", "price": 700, "agent": "bronn"},
            "remarketing": {"name": "Advanced Remarketing", "price": 500, "agent": "bronn"},
            "google_shopping": {"name": "Google Shopping", "price": 600, "agent": "bronn"},
        },
    },
    "email_marketing": {
        "name": "Email Marketing",
        "agent": "margaery",
        "agent_name": "Margaery",
        "category": "Advertising & Growth",
        "description": "Strategic email campaigns, automation flows, list segmentation, and deliverability optimization for maximum engagement.",
        "deliverables": [
            "Email campaign strategy & execution",
            "Automation flow setup",
            "List segmentation & targeting",
            "A/B subject line testing",
            "Deliverability optimization",
            "Monthly performance analysis",
        ],
        "base_price": 700,
        "tier": "growth",
        "addons": {
            "advanced_automation": {"name": "Advanced Automation", "price": 500, "agent": "margaery"},
            "personalization": {"name": "Dynamic Personalization", "price": 400, "agent": "margaery"},
            "deliverability_audit": {"name": "Deliverability Audit", "price": 300, "agent": "margaery"},
        },
    },
    "growth_hacking": {
        "name": "Growth Hacking & Experiments",
        "agent": "arya",
        "agent_name": "Arya",
        "category": "Advertising & Growth",
        "description": "Rapid experimentation, viral growth strategies, unconventional tactics, and creative scaling approaches.",
        "deliverables": [
            "Growth experiment pipeline",
            "Viral campaign concepts",
            "Referral program design",
            "Channel expansion strategy",
            "Conversion loop optimization",
            "Weekly experiment reports",
        ],
        "base_price": 800,
        "tier": "enterprise",
        "addons": {
            "viral_campaign": {"name": "Viral Campaign Execution", "price": 1000, "agent": "arya"},
            "referral_system": {"name": "Referral System Build", "price": 800, "agent": "arya"},
        },
    },
    # ── Strategy & Intelligence ──
    "strategy": {
        "name": "Marketing Strategy & Planning",
        "agent": "bran",
        "agent_name": "Bran",
        "category": "Strategy & Intelligence",
        "description": "Data-driven marketing strategy, market analysis, competitive intelligence, and comprehensive planning.",
        "deliverables": [
            "Marketing strategy development",
            "Competitive landscape analysis",
            "Market opportunity assessment",
            "Channel strategy recommendations",
            "Quarterly planning & roadmaps",
            "Data-driven decision frameworks",
        ],
        "base_price": 1000,
        "tier": "growth",
        "addons": {
            "market_research": {"name": "Deep Market Research", "price": 800, "agent": "olenna"},
            "competitive_intel": {"name": "Competitive Intelligence", "price": 600, "agent": "bran"},
            "scenario_planning": {"name": "Scenario Planning", "price": 700, "agent": "bran"},
        },
    },
    "market_research": {
        "name": "Market Research & Consumer Insights",
        "agent": "olenna",
        "agent_name": "Olenna",
        "category": "Strategy & Intelligence",
        "description": "Deep consumer research, market sizing, trend analysis, and audience intelligence to inform strategy.",
        "deliverables": [
            "Consumer research reports",
            "Market sizing & opportunity analysis",
            "Trend identification & forecasting",
            "Audience segmentation studies",
            "Brand perception research",
            "Quarterly insight reports",
        ],
        "base_price": 900,
        "tier": "enterprise",
        "addons": {
            "focus_groups": {"name": "Focus Group Analysis", "price": 700, "agent": "olenna"},
            "brand_tracking": {"name": "Brand Tracking Study", "price": 800, "agent": "olenna"},
        },
    },
    "influencer_marketing": {
        "name": "Influencer Marketing",
        "agent": "cersei",
        "agent_name": "Cersei",
        "category": "Strategy & Intelligence",
        "description": "Strategic influencer partnerships, campaign management, and ambassador program development.",
        "deliverables": [
            "Influencer identification & vetting",
            "Partnership negotiation & contracts",
            "Campaign brief creation",
            "Content coordination & approval",
            "Performance tracking & ROI",
            "Ambassador program management",
        ],
        "base_price": 900,
        "tier": "enterprise",
        "addons": {
            "ambassador_program": {"name": "Ambassador Program", "price": 800, "agent": "cersei"},
            "micro_influencer": {"name": "Micro-Influencer Campaigns", "price": 600, "agent": "cersei"},
            "influencer_events": {"name": "Influencer Events", "price": 1000, "agent": "cersei"},
        },
    },
    # ── PR & Communications ──
    "pr_comms": {
        "name": "PR & Media Relations",
        "agent": "sansa",
        "agent_name": "Sansa",
        "category": "PR & Communications",
        "description": "Reputation management, media relations, press release distribution, and crisis communications.",
        "deliverables": [
            "Press release writing & distribution",
            "Media list management",
            "Pitch creation & outreach",
            "Reputation monitoring",
            "Crisis communication plans",
            "Interview coordination",
        ],
        "base_price": 900,
        "tier": "enterprise",
        "addons": {
            "crisis_retainer": {"name": "Crisis Management Retainer", "price": 1000, "agent": "sansa"},
            "thought_leadership": {"name": "Thought Leadership Program", "price": 700, "agent": "sansa"},
        },
    },
    # ── Sales & Business Development ──
    "sales": {
        "name": "Sales & Lead Generation",
        "agent": "sandor",
        "agent_name": "Sandor",
        "category": "Sales & Business Development",
        "description": "Lead qualification, prospecting, deal closing, and sales pipeline management with ruthless efficiency.",
        "deliverables": [
            "Lead qualification & scoring",
            "Discovery call execution",
            "Proposal creation & negotiation",
            "Pipeline management",
            "Sales forecasting",
            "CRM maintenance & reporting",
        ],
        "base_price": 1000,
        "tier": "enterprise",
        "addons": {
            "outbound_campaign": {"name": "Outbound Campaign", "price": 800, "agent": "sandor"},
            "sales_training": {"name": "Sales Training Materials", "price": 600, "agent": "sandor"},
        },
    },
    # ── Client Management ──
    "client_relations": {
        "name": "Client Relations & Success",
        "agent": "davos",
        "agent_name": "Davos",
        "category": "Client Management",
        "description": "Dedicated client success management, regular check-ins, and ensuring client satisfaction throughout the engagement.",
        "deliverables": [
            "Weekly check-in calls",
            "Quarterly business reviews",
            "Escalation management",
            "Feedback collection & action",
            "Client satisfaction tracking",
            "Renewal & expansion planning",
        ],
        "base_price": 800,
        "tier": "enterprise",
        "addons": {
            "dedicated_manager": {"name": "Dedicated Success Manager", "price": 1000, "agent": "davos"},
            "client_workshops": {"name": "Client Strategy Workshops", "price": 800, "agent": "davos"},
        },
    },
    "retention_loyalty": {
        "name": "Retention & Loyalty Programs",
        "agent": "jorah",
        "agent_name": "Jorah",
        "category": "Client Management",
        "description": "Customer retention strategies, loyalty programs, and long-term relationship building to maximize LTV.",
        "deliverables": [
            "Loyalty program design",
            "Retention campaign strategy",
            "Win-back campaign execution",
            "Customer lifecycle management",
            "Churn analysis & prevention",
            "LTV optimization strategies",
        ],
        "base_price": 700,
        "tier": "enterprise",
        "addons": {
            "loyalty_program": {"name": "Full Loyalty Program Build", "price": 1000, "agent": "jorah"},
            "churn_analysis": {"name": "Deep Churn Analysis", "price": 600, "agent": "jorah"},
        },
    },
    "project_management": {
        "name": "Project Management",
        "agent": "brienne",
        "agent_name": "Brienne",
        "category": "Client Management",
        "description": "Rigorous project management, timeline coordination, resource allocation, and delivery excellence.",
        "deliverables": [
            "Project planning & timelines",
            "Resource allocation",
            "Timeline & milestone tracking",
            "Risk management",
            "Cross-team coordination",
            "Delivery quality assurance",
        ],
        "base_price": 800,
        "tier": "growth",
        "addons": {
            "agile_sprints": {"name": "Agile Sprint Management", "price": 500, "agent": "brienne"},
            "resource_planning": {"name": "Resource Planning", "price": 400, "agent": "brienne"},
        },
    },
    # ── Compliance & Operations ──
    "legal_compliance": {
        "name": "Legal & Compliance",
        "agent": "tywin",
        "agent_name": "Tywin",
        "category": "Compliance & Operations",
        "description": "Marketing compliance, contract review, data privacy adherence, and risk management.",
        "deliverables": [
            "Marketing compliance review",
            "Contract template management",
            "Data privacy compliance (GDPR/CCPA)",
            "Risk assessment",
            "Terms & conditions review",
            "Ad standards compliance",
        ],
        "base_price": 700,
        "tier": "enterprise",
        "addons": {
            "gdpr_audit": {"name": "GDPR Compliance Audit", "price": 800, "agent": "tywin"},
            "contract_drafting": {"name": "Contract Drafting", "price": 600, "agent": "tywin"},
        },
    },
    "finance_budgeting": {
        "name": "Finance & Budget Management",
        "agent": "stannis",
        "agent_name": "Stannis",
        "category": "Compliance & Operations",
        "description": "Marketing budget management, ROI tracking, financial reporting, and fiscal discipline.",
        "deliverables": [
            "Marketing budget planning",
            "ROI analysis & reporting",
            "Spend optimization",
            "Financial forecasting",
            "Cost-per-acquisition analysis",
            "Budget variance reporting",
        ],
        "base_price": 600,
        "tier": "enterprise",
        "addons": {
            "budget_modeling": {"name": "Budget Scenario Modeling", "price": 500, "agent": "stannis"},
            "financial_forecasting": {"name": "Financial Forecasting", "price": 600, "agent": "stannis"},
        },
    },
    # ── Leadership (CEO) ──
    "ceo_oversight": {
        "name": "CEO Oversight & Strategic Direction",
        "agent": "jon",
        "agent_name": "Jon",
        "category": "Leadership",
        "description": "Strategic oversight from the AI CEO, including daily reports, decision-making, and executive guidance.",
        "deliverables": [
            "Daily CEO reports",
            "Strategic decision-making",
            "Team coordination & oversight",
            "Executive briefings",
            "Crisis leadership",
            "Vision & direction setting",
        ],
        "base_price": 1500,
        "tier": "enterprise",
        "addons": {
            "weekly_briefing": {"name": "Weekly Executive Briefing", "price": 500, "agent": "jon"},
            "crisis_oversight": {"name": "Crisis Management Leadership", "price": 1000, "agent": "jon"},
        },
    },
}

# ═══════════════════════════════════════════════════════════════════
# PACKAGE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

PACKAGES: Dict[str, Dict[str, Any]] = {
    "starter": {
        "id": "starter",
        "name": "Starter",
        "tagline": "Perfect for small businesses starting their marketing journey",
        "description": "Essential marketing services to establish your brand presence, build organic reach, and get foundational reporting. Ideal for small businesses with 1-2 active campaigns.",
        "price_monthly": 499,
        "price_annual": 4990,
        "annual_discount_pct": 17,
        "campaigns": 2,
        "services": [
            "social_media_management",
            "seo_optimization",
            "reporting_analytics",
            "client_reporting",
            "copyediting_qa",
        ],
        "agents": ["missandei", "sandoq", "samwell", "petyr", "podrick"],
        "features": [
            "Up to 2 active campaigns",
            "5 dedicated AI marketing specialists",
            "30 social posts per month",
            "Monthly SEO audit & optimization",
            "Monthly performance reports",
            "Community management",
            "Standard support (business hours)",
            "Content quality assurance",
        ],
        "not_included": [
            "Paid advertising management",
            "Landing page development",
            "Email marketing campaigns",
            "Video production",
            "Growth hacking experiments",
            "Dedicated account manager",
            "Weekly strategy calls",
            "Priority support",
        ],
        "ideal_for": [
            "Small businesses (< 20 employees)",
            "Local/regional brands",
            "Startups in pre-seed/seed stage",
            "Companies with <$1M annual revenue",
        ],
    },
    "growth": {
        "id": "growth",
        "name": "Growth",
        "tagline": "Scale your marketing with our full creative and advertising team",
        "description": "Comprehensive marketing services with advertising, creative production, landing pages, and dedicated project management. Built for growing companies running 3-5 concurrent campaigns.",
        "price_monthly": 1499,
        "price_annual": 14990,
        "annual_discount_pct": 17,
        "campaigns": 5,
        "services": [
            "social_media_management",
            "seo_optimization",
            "reporting_analytics",
            "client_reporting",
            "copyediting_qa",
            "copywriting",
            "brand_design",
            "video_production",
            "landing_pages",
            "paid_advertising",
            "email_marketing",
            "strategy",
            "project_management",
        ],
        "agents": [
            "missandei", "sandoq", "samwell", "petyr", "podrick",
            "tyrion", "rhaegar", "gendry", "greyworm", "bronn",
            "margaery", "bran", "brienne",
        ],
        "features": [
            "Up to 5 active campaigns",
            "13 dedicated AI marketing specialists",
            "Everything in Starter, plus:",
            "Paid advertising across all platforms",
            "Custom landing page development",
            "Email marketing campaigns & automation",
            "Professional video editing & motion graphics",
            "Brand design & creative production",
            "Strategic planning & market analysis",
            "Dedicated project management",
            "Weekly performance reports",
            "Priority support (extended hours)",
            "A/B testing & optimization",
        ],
        "not_included": [
            "Growth hacking experiments",
            "Influencer marketing campaigns",
            "PR & media relations",
            "Dedicated client success manager",
            "Legal & compliance review",
            "CEO weekly briefings",
            "Unlimited campaigns",
        ],
        "ideal_for": [
            "Growing companies (20-100 employees)",
            "Multi-region brands",
            "Series A/B startups",
            "Companies with $1M-$10M annual revenue",
            "E-commerce businesses scaling ads",
        ],
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise",
        "tagline": "The full power of Claude Mythos — all 23 AI agents at your service",
        "description": "Unlimited access to all 23 AI marketing specialists. Unlimited campaigns, dedicated client success, executive reporting, legal compliance, and strategic oversight from our AI CEO. For enterprises that demand the best.",
        "price_monthly": 3999,
        "price_annual": 39990,
        "annual_discount_pct": 17,
        "campaigns": -1,
        "services": list(SERVICES.keys()),
        "agents": [
            "missandei", "sandoq", "samwell", "petyr", "podrick",
            "tyrion", "rhaegar", "gendry", "greyworm", "bronn",
            "margaery", "bran", "brienne",
            "sandor", "sansa", "cersei", "davos", "jorah",
            "jon", "olenna", "stannis", "tywin", "arya",
        ],
        "features": [
            "Unlimited active campaigns",
            "All 23 AI marketing specialists",
            "Everything in Growth, plus:",
            "Influencer marketing & ambassador programs",
            "PR & media relations",
            "Growth hacking & viral experiments",
            "Deep market research & consumer insights",
            "Legal & compliance review",
            "Financial planning & ROI management",
            "Dedicated client success manager",
            "CEO strategic oversight & daily reports",
            "Weekly executive briefings",
            "Priority support (24/7)",
            "Custom integrations & development",
            "White-label reporting",
            "Quarterly business reviews",
            "Annual strategy retreats",
        ],
        "not_included": [],
        "ideal_for": [
            "Enterprise companies (100+ employees)",
            "Global/multi-market brands",
            "Series C+ startups & unicorns",
            "Companies with $10M+ annual revenue",
            "Agencies managing multiple brands",
            "Organizations needing full marketing departments",
        ],
    },
}

# ═══════════════════════════════════════════════════════════════════
# AGENT-TO-SERVICE MAPPING
# ═══════════════════════════════════════════════════════════════════

AGENT_SERVICE_MAP: Dict[str, str] = {
    "missandei": "social_media_management",
    "sandoq": "seo_optimization",
    "samwell": "reporting_analytics",
    "petyr": "client_reporting",
    "podrick": "copyediting_qa",
    "tyrion": "copywriting",
    "rhaegar": "brand_design",
    "gendry": "video_production",
    "greyworm": "landing_pages",
    "bronn": "paid_advertising",
    "margaery": "email_marketing",
    "bran": "strategy",
    "olenna": "market_research",
    "cersei": "influencer_marketing",
    "sansa": "pr_comms",
    "sandor": "sales",
    "davos": "client_relations",
    "jorah": "retention_loyalty",
    "brienne": "project_management",
    "tywin": "legal_compliance",
    "stannis": "finance_budgeting",
    "jon": "ceo_oversight",
    "arya": "growth_hacking",
}



# ═══════════════════════════════════════════════════════════════════
# SERVICE CATALOG CLASS
# ═══════════════════════════════════════════════════════════════════

class ServiceCatalog:
    """Complete service catalog with quote generation capabilities."""

    @staticmethod
    def get_all_services() -> Dict[str, Dict[str, Any]]:
        """Return all available services."""
        return SERVICES

    @staticmethod
    def get_service(service_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific service by ID."""
        return SERVICES.get(service_id)

    @staticmethod
    def get_services_by_category(category: str) -> Dict[str, Dict[str, Any]]:
        """Get services filtered by category."""
        return {
            sid: svc for sid, svc in SERVICES.items()
            if svc.get("category") == category
        }

    @staticmethod
    def get_services_by_agent(agent_id: str) -> List[Dict[str, Any]]:
        """Get all services handled by a specific agent."""
        return [
            {**svc, "service_id": sid}
            for sid, svc in SERVICES.items()
            if svc.get("agent") == agent_id
        ]

    @staticmethod
    def get_all_packages() -> Dict[str, Dict[str, Any]]:
        """Return all subscription packages."""
        return PACKAGES

    @staticmethod
    def get_package(package_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific package by ID."""
        return PACKAGES.get(package_id)

    @staticmethod
    def get_agent_for_service(service_id: str) -> Optional[str]:
        """Get the agent ID responsible for a service."""
        service = SERVICES.get(service_id)
        return service["agent"] if service else None

    @staticmethod
    def get_services_for_package(package_id: str) -> List[Dict[str, Any]]:
        """Get full service details for a package."""
        package = PACKAGES.get(package_id)
        if not package:
            return []
        return [
            {**SERVICES[sid], "service_id": sid}
            for sid in package["services"]
            if sid in SERVICES
        ]

    @staticmethod
    def calculate_package_value(package_id: str) -> int:
        """Calculate the total value of services in a package."""
        services = ServiceCatalog.get_services_for_package(package_id)
        return sum(s["base_price"] for s in services)

    @staticmethod
    def get_addons_for_service(service_id: str) -> Dict[str, Dict[str, Any]]:
        """Get available addons for a service."""
        service = SERVICES.get(service_id)
        return service.get("addons", {}) if service else {}

    @staticmethod
    def generate_quote(client_needs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an intelligent quote based on client needs."""
        goals = client_needs.get("goals", [])
        company_size = client_needs.get("company_size", "small")
        campaign_count = client_needs.get("campaign_count", 1)
        needs_paid_ads = client_needs.get("needs_paid_ads", False)
        needs_landing_pages = client_needs.get("needs_landing_pages", False)
        needs_email = client_needs.get("needs_email", False)
        needs_video = client_needs.get("needs_video", False)
        needs_influencer = client_needs.get("needs_influencer", False)
        needs_pr = client_needs.get("needs_pr", False)
        needs_growth = client_needs.get("needs_growth", False)
        budget_range = client_needs.get("budget_range", "")
        timeline = client_needs.get("timeline", "standard")

        starter_score = 0
        growth_score = 0
        enterprise_score = 0
        reasons = []

        if campaign_count <= 2:
            starter_score += 3
            growth_score += 1
        elif campaign_count <= 5:
            starter_score -= 2
            growth_score += 3
            enterprise_score += 1
        else:
            starter_score -= 5
            growth_score -= 2
            enterprise_score += 4
            reasons.append(f"{campaign_count} campaigns requires Enterprise (unlimited)")

        if company_size in ("startup", "small"):
            starter_score += 2
            growth_score += 1
        elif company_size == "medium":
            starter_score += 1
            growth_score += 3
            enterprise_score += 1
        elif company_size == "enterprise":
            starter_score -= 3
            growth_score += 1
            enterprise_score += 4
            reasons.append("Enterprise company size suggests Enterprise package")

        if needs_paid_ads:
            growth_score += 2
            enterprise_score += 1
            reasons.append("Paid advertising requires Growth or higher")
        if needs_landing_pages:
            growth_score += 1
            enterprise_score += 1
        if needs_email:
            growth_score += 1
            enterprise_score += 1
        if needs_video:
            growth_score += 1
            enterprise_score += 1
        if needs_influencer:
            enterprise_score += 3
            reasons.append("Influencer marketing is Enterprise-only")
        if needs_pr:
            enterprise_score += 2
            reasons.append("PR & media relations is Enterprise-only")
        if needs_growth:
            enterprise_score += 2
            reasons.append("Growth hacking is Enterprise-only")

        goal_lower = [g.lower() for g in goals]
        if any(g in goal_lower for g in ("sales", "revenue", "roas", "conversions")):
            growth_score += 2
            enterprise_score += 1
        if any(g in goal_lower for g in ("brand awareness", "awareness", "reach", "visibility")):
            growth_score += 1
            enterprise_score += 1
        if any(g in goal_lower for g in ("engagement", "community", "social")):
            starter_score += 1
            growth_score += 1

        budget_lower = budget_range.lower() if budget_range else ""
        if "500" in budget_lower or "499" in budget_lower:
            starter_score += 2
        if "1500" in budget_lower or "1499" in budget_lower:
            growth_score += 2
        if "4000" in budget_lower or "3999" in budget_lower:
            enterprise_score += 2

        if timeline == "urgent":
            enterprise_score += 1

        scores = {"starter": starter_score, "growth": growth_score, "enterprise": enterprise_score}
        recommended_package_id = max(scores, key=scores.get)
        recommended_package = PACKAGES[recommended_package_id]

        recommended_addons = []
        for service_id in recommended_package["services"]:
            service = SERVICES.get(service_id)
            if not service:
                continue
            for addon_id, addon in service.get("addons", {}).items():
                relevance = 0
                addon_name_lower = addon["name"].lower()
                if needs_paid_ads and "paid" in addon_name_lower:
                    relevance += 3
                if needs_video and "video" in addon_name_lower:
                    relevance += 3
                if needs_email and "automat" in addon_name_lower:
                    relevance += 2
                if timeline == "urgent" and "automat" in addon_name_lower:
                    relevance += 1
                if company_size == "enterprise" and "advanced" in addon_name_lower:
                    relevance += 1
                if relevance >= 2:
                    recommended_addons.append({
                        "addon_id": addon_id,
                        **addon,
                        "relevance_score": relevance,
                        "parent_service": service_id,
                        "parent_service_name": service["name"],
                    })

        recommended_addons.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_addons = recommended_addons[:5]

        base_price = recommended_package["price_monthly"]
        addons_total = sum(a["price"] for a in top_addons)
        total_monthly = base_price + addons_total
        annual_price = recommended_package["price_annual"]
        annual_savings = (total_monthly * 12) - (annual_price + addons_total * 12)

        service_value = ServiceCatalog.calculate_package_value(recommended_package_id)
        savings_vs_individual = service_value - total_monthly

        return {
            "quote_id": f"quote_{uuid.uuid4().hex[:12]}",
            "generated_at": datetime.utcnow().isoformat(),
            "recommended_package": {
                "id": recommended_package_id,
                "name": recommended_package["name"],
                "price_monthly": recommended_package["price_monthly"],
                "price_annual": recommended_package["price_annual"],
                "campaigns": recommended_package["campaigns"],
                "agent_count": len(recommended_package["agents"]),
                "service_count": len(recommended_package["services"]),
            },
            "score_breakdown": scores,
            "recommendation_reasons": reasons if reasons else [
                f"Based on your {company_size} company size and {campaign_count} campaign(s)",
                f"Goals: {', '.join(goals) if goals else 'General marketing'}",
            ],
            "recommended_addons": top_addons,
            "pricing": {
                "base_monthly": base_price,
                "addons_monthly": addons_total,
                "total_monthly": total_monthly,
                "annual_commitment": {
                    "annual_base": annual_price,
                    "annual_addons_total": addons_total * 12,
                    "total_annual": annual_price + (addons_total * 12),
                    "estimated_savings": max(0, annual_savings),
                },
            },
            "value_metrics": {
                "individual_service_value": service_value,
                "package_savings": savings_vs_individual,
                "savings_percentage": round((savings_vs_individual / service_value) * 100, 1) if service_value > 0 else 0,
            },
            "alternative_packages": [
                {
                    "id": pid,
                    "name": pkg["name"],
                    "price_monthly": pkg["price_monthly"],
                    "campaigns": pkg["campaigns"],
                    "agent_count": len(pkg["agents"]),
                    "why_consider": ServiceCatalog._why_consider(pid, client_needs),
                }
                for pid, pkg in PACKAGES.items()
                if pid != recommended_package_id
            ],
            "custom_package_available": True,
            "valid_until": datetime.utcnow().isoformat(),
            "note": "This quote is valid for 30 days. Custom packages available upon request.",
        }

    @staticmethod
    def _why_consider(package_id: str, client_needs: Dict[str, Any]) -> str:
        if package_id == "starter":
            return "Budget-friendly option if you want to start small and upgrade later"
        elif package_id == "growth":
            return "Best value for scaling businesses with advertising needs"
        elif package_id == "enterprise":
            return "Full team access with unlimited campaigns and executive oversight"
        return ""

    @staticmethod
    def build_custom_package(
        service_ids: List[str],
        addon_selections: Dict[str, List[str]] = None,
    ) -> Dict[str, Any]:
        """Build a custom package from individual services."""
        addon_selections = addon_selections or {}
        included_services = []
        included_agents = []
        base_total = 0
        addons_detail = []
        addons_total = 0

        for sid in service_ids:
            service = SERVICES.get(sid)
            if not service:
                continue
            included_services.append({
                "service_id": sid,
                "name": service["name"],
                "agent": service["agent"],
                "agent_name": service["agent_name"],
                "base_price": service["base_price"],
                "category": service.get("category", ""),
            })
            included_agents.append(service["agent"])
            base_total += service["base_price"]

            selected = addon_selections.get(sid, [])
            for addon_id in selected:
                addon = service.get("addons", {}).get(addon_id)
                if addon:
                    addons_detail.append({
                        "addon_id": addon_id,
                        "name": addon["name"],
                        "price": addon["price"],
                        "agent": addon["agent"],
                        "parent_service": sid,
                    })
                    addons_total += addon["price"]

        total_monthly = base_total + addons_total
        nearest_package = None
        min_diff = float("inf")
        for pid, pkg in PACKAGES.items():
            diff = abs(pkg["price_monthly"] - total_monthly)
            if diff < min_diff:
                min_diff = diff
                nearest_package = pkg

        return {
            "package_type": "custom",
            "services": included_services,
            "agents": list(set(included_agents)),
            "agent_count": len(set(included_agents)),
            "addons": addons_detail,
            "pricing": {
                "base_monthly": base_total,
                "addons_monthly": addons_total,
                "total_monthly": total_monthly,
                "total_annual": total_monthly * 10,
            },
            "nearest_package": {
                "id": nearest_package["id"],
                "name": nearest_package["name"],
                "price_monthly": nearest_package["price_monthly"],
                "difference": total_monthly - nearest_package["price_monthly"],
            } if nearest_package else None,
            "generated_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def get_agent_service_matrix() -> Dict[str, Any]:
        """Get a matrix showing which agents are in which packages."""
        matrix = {}
        for agent_id, service_id in AGENT_SERVICE_MAP.items():
            service = SERVICES.get(service_id, {})
            packages_in = []
            for pid, pkg in PACKAGES.items():
                if agent_id in pkg.get("agents", []):
                    packages_in.append(pid)
            matrix[agent_id] = {
                "agent_id": agent_id,
                "service_id": service_id,
                "service_name": service.get("name", ""),
                "category": service.get("category", ""),
                "packages": packages_in,
                "base_price": service.get("base_price", 0),
            }
        return matrix


# ═══════════════════════════════════════════════════════════════════
# Global instance
# ═══════════════════════════════════════════════════════════════════

service_catalog = ServiceCatalog()
