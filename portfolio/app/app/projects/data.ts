import { Bot, LayoutDashboard, Network, ShoppingBag, Rss, Search, Brain, Shield, Zap, Code2, Database, Cloud, Container, ScanLine, Globe, Cpu, ShoppingCart, Palette, Server, Satellite, Archive, Sparkles, Smartphone, Repeat } from "lucide-react";

export type Project = {
  id: string;
  name: string;
  tag: string;
  description: string;
  stack: string[];
  icon: React.ElementType;
  color: string;
  accent: string;
  status: string;
  highlights: string[];
  image?: string;
  // Case study extras
  tagline: string;
  metrics: { label: string; value: string }[];
  architecture: { name: string; description: string; icon: React.ElementType }[];
  challenges: { title: string; description: string }[];
  features: string[];
};

export const projects: Project[] = [
  {
    id: "glomeriato",
    image: "/images/project-glomeriato.png",
    name: "Glomeriato",
    tag: "AI · Trading · Finance",
    tagline: "Algorithmic trading system powered by dual-agent AI",
    description:
      "Algorithmic trading system for Trading 212. Dual-agent AI (Gemini Flash + Pro) drives a 30-minute cycle: sentiment analysis, portfolio risk assessment, Guardian exit matrix, and automated order execution. PostgreSQL-backed memory across sessions.",
    stack: ["Python", "Gemini 2.5", "PostgreSQL", "Docker", "Trading 212 API"],
    icon: Bot,
    color: "#22C55E",
    accent: "rgba(34,197,94,0.08)",
    status: "Live",
    highlights: [
      "Dual-agent brain: Sentinel (entry) + QuantBrain (exit strategy)",
      "Market hours awareness across EU + US sessions",
      "Telegram digest notifications every 2h during market hours",
      "Self-improving via Argos autonomous agent loop",
    ],
    metrics: [
      { label: "Trading cycle", value: "30 min" },
      { label: "AI agents", value: "2" },
      { label: "Live months", value: "5+" },
      { label: "Markets", value: "EU + US" },
    ],
    architecture: [
      { name: "Sentinel", icon: Search, description: "Scans portfolio for entry signals — liquidity, momentum, mean-reversion triggers" },
      { name: "QuantBrain", icon: Brain, description: "Gemini 2.5 Pro analyses each signal, scores conviction, sizes the position" },
      { name: "Guardian", icon: Shield, description: "Exit authority — manages stop-loss, take-profit tiers, trailing stops" },
      { name: "Executor", icon: Zap, description: "Places orders via T212 API, logs trades to PostgreSQL, sends Telegram digest" },
    ],
    challenges: [
      {
        title: "Market hours across timezones",
        description: "EU stocks trade 08:48–17:42 Warsaw time, US markets 14:30–22:30. The bot had to be aware of overlap windows and avoid placing orders on closed markets without relying on external APIs.",
      },
      {
        title: "FX fee precision",
        description: "Trading 212 charges 0.15% on currency conversions. Every order quantity calculation divides by 1.0015 to ensure the total never exceeds the allocated amount — off-by-one here means rejected orders.",
      },
      {
        title: "Agent memory across sessions",
        description: "Gemini sessions are stateless. Designed a PostgreSQL-backed context layer that reconstructs relevant trade history, open positions, and recent decisions at the start of each 30-min cycle.",
      },
    ],
    features: [
      "30-minute autonomous trading cycle — no manual intervention",
      "Dual Gemini model stack: Flash for speed, Pro for deep analysis",
      "Guardian exit matrix with tiered take-profit levels",
      "Telegram briefings every 2h during market hours + EOD summary",
      "Argos self-improvement loop — reviews its own decisions daily",
      "PostgreSQL trade journal with full decision audit trail",
    ],
  },
  {
    id: "mybrain",
    image: "/images/project-mybrain.png",
    name: "MyBrain Portal",
    tag: "Dashboard · Productivity · Self-hosting",
    tagline: "Personal intelligence dashboard — everything in one place",
    description:
      "Personal intelligence dashboard with task management, gym workout tracking, nutrition planning, system monitoring, and a real-time applications launcher. Runs on VPS behind Cloudflare Zero Trust with Google OAuth.",
    stack: ["Python", "Flask", "PostgreSQL", "Docker", "Tailwind CSS"],
    icon: LayoutDashboard,
    color: "#60A5FA",
    accent: "rgba(96,165,250,0.08)",
    status: "Live",
    highlights: [
      "Gym tracking: exercises, sets, progressive overload charting",
      "Nutrition planner with meal plans and calorie logging",
      "Cloudflare Tunnel + Zero Trust auth — no open ports",
      "Dev panel with per-user module access control",
    ],
    metrics: [
      { label: "Modules", value: "5" },
      { label: "Auth", value: "Zero Trust" },
      { label: "Uptime", value: "99.9%" },
      { label: "Data", value: "Self-hosted" },
    ],
    architecture: [
      { name: "Flask App", icon: Code2, description: "Blueprint-based modular Flask app, each feature is an isolated module" },
      { name: "PostgreSQL", icon: Database, description: "Central DB for all user data — workouts, nutrition, tasks, sessions" },
      { name: "Cloudflare", icon: Cloud, description: "Zero Trust tunnel — no open ports, Google OAuth, per-route access policies" },
      { name: "Docker", icon: Container, description: "Containerised on VPS, auto-deploys on git push via GitHub Actions" },
    ],
    challenges: [
      {
        title: "Zero Trust with no open ports",
        description: "All traffic routes through a Cloudflare tunnel — the VPS has no public ports except SSH. Google OAuth sits in front of every route, meaning the app itself never handles auth tokens directly.",
      },
      {
        title: "Modular access control",
        description: "Different users need different module access. Built a per-user, per-module permission system in the dev panel without reaching for a full RBAC library — simple DB flags, checked in Flask's before_request hook.",
      },
      {
        title: "Gym progressive overload tracking",
        description: "Detecting PRs across different rep ranges (1RM, 5RM, 10RM) requires normalising volume across sets. Implemented an Epley formula estimator to compare performance across sessions reliably.",
      },
    ],
    features: [
      "Gym tracker with PR detection, progressive overload charts, per-side exercises",
      "Nutrition planner: daily macros, meal plans, calorie targets, supplement reminders",
      "Task manager with priority levels and due dates",
      "Application launcher — quick links to all self-hosted services",
      "Dev panel: per-user module access control",
      "Full self-hosted — your data never leaves your VPS",
    ],
  },
  {
    id: "openclaw",
    image: "/images/project-openclaw.png",
    name: "OpenClaw 2.0",
    tag: "AI Gateway · Multi-agent · Automation",
    tagline: "Multi-agent AI gateway with Telegram integration and sandboxed execution",
    description:
      "Multi-agent AI gateway with Telegram integration. Hosts Vanitas (primary assistant), Peccata (engineering sub-agent), and Argos (autonomous self-improvement loop). Sandboxed Docker execution, session delegation, and cron-based briefings.",
    stack: ["TypeScript", "Node.js", "Gemini 2.5 Pro/Flash", "Docker", "Telegram Bot API"],
    icon: Network,
    color: "#A78BFA",
    accent: "rgba(167,139,250,0.08)",
    status: "Live",
    highlights: [
      "Vanitas: primary Telegram assistant (Gemini 2.5 Flash)",
      "Peccata: engineering sub-agent with full VPS access",
      "Argos: autonomous agent — daily AI research + bot improvement",
      "Perplexity + NotebookLM + Gemini synthesis pipeline",
    ],
    metrics: [
      { label: "Agents", value: "3" },
      { label: "Gateway", value: "24/7" },
      { label: "Sandbox", value: "Docker" },
      { label: "Interface", value: "Telegram" },
    ],
    architecture: [
      { name: "Gateway", icon: Globe, description: "Node.js gateway routes Telegram messages to the right agent session" },
      { name: "Agents", icon: Cpu, description: "Vanitas (Flash), Peccata (Pro), Argos (Pro) — each with distinct identity and tools" },
      { name: "Sandbox", icon: Container, description: "Isolated Docker container per agent — full filesystem + network access within bounds" },
      { name: "Argos Loop", icon: Repeat, description: "Autonomous daily loop: research → synthesis → Claude Code implementation → rebuild" },
    ],
    challenges: [
      {
        title: "Session delegation between agents",
        description: "Vanitas can spawn Peccata for engineering tasks mid-conversation. Designed a delegation protocol where context is serialised, passed to the sub-agent session, and results returned to the parent — all within Telegram's message flow.",
      },
      {
        title: "Sandboxed code execution",
        description: "Agents needed to run code, edit files, and call APIs without risk to the host system. Each agent gets a Docker container with a mounted workspace — full capability within the sandbox, hard limits outside.",
      },
      {
        title: "Autonomous self-improvement",
        description: "Argos reads the trading bot's DB metrics, queries Perplexity for research, synthesises improvements with Gemini, runs Claude Code to implement them, and triggers a docker rebuild — all without human intervention.",
      },
    ],
    features: [
      "Three specialised AI agents, each with distinct personality and capability set",
      "Telegram-native interface — no app to install, works on any device",
      "Docker-sandboxed execution — safe code running, file editing, API calls",
      "Argos autonomous loop: research, implement, and deploy improvements daily",
      "Mundi research agent: 3-source pipeline (Gemini + Perplexity + NotebookLM)",
      "Cron-based briefings and heartbeat monitoring",
    ],
  },
  {
    id: "saleor",
    image: "/images/project-ecomm.png",
    name: "Saleor Storefront",
    tag: "E-commerce · React · GraphQL",
    tagline: "Production-grade e-commerce frontend on Saleor's GraphQL API",
    description:
      "Production-grade e-commerce frontend built on Saleor's GraphQL API. Server Components by default, OKLCH design tokens, type-safe GraphQL queries with automatic code generation.",
    stack: ["Next.js 15", "TypeScript", "GraphQL", "Tailwind CSS", "Saleor API"],
    icon: ShoppingBag,
    color: "#F472B6",
    accent: "rgba(244,114,182,0.08)",
    status: "Production",
    highlights: [
      "Next.js App Router with React Server Components",
      "OKLCH color system — device-accurate colors",
      "Auto-generated GraphQL types via pnpm generate",
      "Full cart, checkout, auth, and product catalog flows",
    ],
    metrics: [
      { label: "Framework", value: "Next 15" },
      { label: "Data layer", value: "GraphQL" },
      { label: "Color system", value: "OKLCH" },
      { label: "Type safety", value: "100%" },
    ],
    architecture: [
      { name: "Next.js RSC", icon: Server, description: "App Router with Server Components by default — data fetched at the edge" },
      { name: "GraphQL", icon: ScanLine, description: "Type-safe queries with auto-generated types — zero runtime type errors" },
      { name: "Saleor API", icon: ShoppingCart, description: "Headless commerce backend: products, cart, checkout, payments, auth" },
      { name: "OKLCH Tokens", icon: Palette, description: "Device-accurate color system — what you design is what users see" },
    ],
    challenges: [
      {
        title: "Type-safe GraphQL at scale",
        description: "Hand-writing GraphQL types is error-prone and tedious. Set up codegen to generate all types from the Saleor schema — any API change surfaces immediately as a TypeScript error at build time.",
      },
      {
        title: "Server vs client component boundary",
        description: "Next.js 15 RSC requires deliberate decisions about what runs on the server vs client. Designed a clear boundary: data fetching stays server-side, interactivity (cart, auth state) is client-only with Suspense boundaries.",
      },
      {
        title: "OKLCH color accuracy",
        description: "sRGB hex colors look different across devices. Migrated the entire design token system to OKLCH — perceptually uniform, P3-wide-gamut, and consistent across monitors, phones, and MacBook Pro displays.",
      },
    ],
    features: [
      "Next.js 15 App Router — RSC by default, minimal client JS",
      "Auto-generated TypeScript types from Saleor GraphQL schema",
      "Full e-commerce: product catalog, cart, checkout, order history",
      "OKLCH design tokens — perceptually accurate colors on all devices",
      "Google OAuth + Saleor native auth",
      "ISR and streaming for fast page loads",
    ],
  },
  {
    id: "morning-brief",
    image: "/images/project-portfolio.png",
    name: "Morning Brief",
    tag: "News · AI Briefing · Pipeline",
    tagline: "Automated AI news intelligence — delivered to Telegram at 8AM",
    description:
      "Automated news intelligence feed. Hourly RSS collection from Verge, BBC, NYT, Al Jazeera, and Hacker News. Gemini AI synthesizes a morning briefing delivered via Telegram at 8AM on weekdays.",
    stack: ["Python", "Flask", "SQLite", "Gemini Flash", "RSS/Feedparser"],
    icon: Rss,
    color: "#FB923C",
    accent: "rgba(251,146,60,0.08)",
    status: "Live",
    highlights: [
      "Web reader at news.mybrain.world",
      "AI-synthesized briefings — not just link dumps",
      "Delivered via Vanitas on Telegram",
      "Persistent article database with deduplication",
    ],
    metrics: [
      { label: "Sources", value: "5+" },
      { label: "Collect cycle", value: "1 hour" },
      { label: "Briefing", value: "8AM daily" },
      { label: "Delivery", value: "Telegram" },
    ],
    architecture: [
      { name: "RSS Collector", icon: Satellite, description: "Hourly cron fetches articles from Verge, BBC, NYT, Al Jazeera, Hacker News" },
      { name: "SQLite Store", icon: Archive, description: "Deduplicates by URL, stores full article metadata and content" },
      { name: "Gemini Flash", icon: Sparkles, description: "Synthesises overnight articles into a structured briefing — not a link dump" },
      { name: "Telegram", icon: Smartphone, description: "Delivered via Vanitas at 8AM weekdays — readable in under 2 minutes" },
    ],
    challenges: [
      {
        title: "Deduplication across sources",
        description: "Same story gets picked up by multiple outlets. Implemented URL-level dedup plus a title similarity check — so the briefing covers the story once, from the best source, not five times.",
      },
      {
        title: "Synthesis vs summarisation",
        description: "A simple summary is just a shorter version of each article. Designed the Gemini prompt to synthesise across all overnight articles — finding connections, contrasting viewpoints, and surfacing what actually matters.",
      },
      {
        title: "Reliable 8AM delivery",
        description: "Cron jobs on VPS are fragile — missed runs, timezone drift, container restarts. Added a heartbeat check: if no briefing has been sent by 8:05AM, Vanitas self-triggers via the OpenClaw gateway.",
      },
    ],
    features: [
      "Hourly RSS collection from 5+ major sources",
      "AI synthesis — not summaries, but a coherent morning briefing",
      "Web reader at news.mybrain.world for browsing full articles",
      "SQLite article store with URL and content deduplication",
      "Delivered via Telegram at 8AM weekdays",
      "Heartbeat self-trigger if cron misses the delivery window",
    ],
  },
];

export const skills = [
  { category: "AI / LLMs", items: ["Gemini 2.5 Pro/Flash", "Claude (Anthropic)", "Perplexity Sonar", "Prompt engineering", "Agent orchestration"] },
  { category: "Backend", items: ["Python", "Flask", "Node.js", "TypeScript", "PostgreSQL", "SQLite", "REST APIs"] },
  { category: "Frontend", items: ["Next.js 15", "React", "Tailwind CSS", "shadcn/ui", "TypeScript", "GraphQL"] },
  { category: "Infrastructure", items: ["Docker", "VPS (Hostinger KVM 4)", "Cloudflare Tunnels", "Zero Trust", "SSH hardening", "fail2ban"] },
  { category: "Systems", items: ["Telegram Bot API", "Trading 212 API", "Saleor GraphQL", "n8n automation", "MkDocs", "Dockge"] },
];

export const experience = [
  {
    role: "Freelance AI & Full-Stack Developer",
    company: "Independent",
    period: "2023 — Present",
    highlights: [
      "Built Glomeriato: algorithmic trading bot with dual-agent Gemini 2.5 AI",
      "Architected OpenClaw 2.0: multi-agent gateway with Telegram + sandboxed Docker execution",
      "Delivered e-commerce projects on Saleor + Next.js 15 for production clients",
      "Designed and deployed full personal cloud infrastructure on VPS",
    ],
    stack: ["Python", "TypeScript", "Next.js", "PostgreSQL", "Docker", "Gemini 2.5"],
  },
  {
    role: "Full-Stack Developer",
    company: "Various clients",
    period: "2021 — 2023",
    highlights: [
      "React/Next.js frontends for SaaS products",
      "REST API design and PostgreSQL database architecture",
      "Delivered end-to-end projects from design to deployment",
    ],
    stack: ["React", "Node.js", "TypeScript", "PostgreSQL"],
  },
  {
    role: "Self-taught & Open Source",
    company: "Personal projects",
    period: "2019 — 2021",
    highlights: [
      "Deep dive into Python, systems programming, and automation",
      "Built first trading scripts and personal productivity tools",
      "Contributed to open source projects across web and data tooling",
    ],
    stack: ["Python", "JavaScript", "Linux"],
  },
];
