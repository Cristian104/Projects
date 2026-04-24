"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, useInView, useReducedMotion, type Variants } from "framer-motion";
import { useRef } from "react";
import {
  ArrowUpRight,
  Github,
  Mail,
  Terminal,
  ChevronDown,
  Menu,
  X,
} from "lucide-react";
import { projects, skills, experience } from "./projects/data";

// ── Animation variants ──────────────────────────────────────────────────────

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: "easeOut" } },
};

const stagger = (delay = 0.08): Variants => ({
  hidden: {},
  show: { transition: { staggerChildren: delay } },
});

function Section({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  const prefersReduced = useReducedMotion();
  return (
    <motion.div
      ref={ref}
      variants={prefersReduced ? {} : stagger()}
      initial={prefersReduced ? false : "hidden"}
      animate={prefersReduced ? undefined : (inView ? "show" : "hidden")}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// ── Small components ────────────────────────────────────────────────────────

function Dot({ color = "var(--accent)" }: { color?: string }) {
  return (
    <span
      className="inline-block w-2 h-2 rounded-full"
      style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}` }}
    />
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <span
      className="text-xs font-medium px-3 py-1 rounded-full inline-block mb-4"
      style={{ background: "var(--surface)", color: "var(--accent)", border: "1px solid var(--border)" }}
    >
      {children}
    </span>
  );
}

function SectionHeader({ label, title, subtitle }: { label: string; title: string; subtitle?: string }) {
  return (
    <motion.div variants={fadeUp} className="mb-14">
      <Label>{label}</Label>
      <h2 className="text-4xl md:text-5xl font-black mb-4" style={{ fontFamily: "Archivo, sans-serif" }}>
        {title}
      </h2>
      {subtitle && (
        <p className="text-lg max-w-xl" style={{ color: "var(--text-muted)" }}>
          {subtitle}
        </p>
      )}
    </motion.div>
  );
}

// ── Nav ─────────────────────────────────────────────────────────────────────

function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <>
      <nav
        className="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
        style={{
          background: scrolled ? "rgba(15,23,42,0.92)" : "transparent",
          backdropFilter: scrolled ? "blur(14px)" : "none",
          borderBottom: scrolled ? "1px solid var(--border)" : "none",
        }}
      >
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="font-bold text-lg tracking-tight" style={{ fontFamily: "Archivo, sans-serif" }}>
            jorg<span style={{ color: "var(--accent)" }}>.</span>dev
          </Link>
          <div className="hidden md:flex items-center gap-8">
            {["Projects", "Experience", "Skills", "Contact"].map((item) => (
              <a
                key={item}
                href={`#${item.toLowerCase()}`}
                className="text-sm transition-colors duration-200"
                style={{ color: "var(--text-muted)" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
              >
                {item}
              </a>
            ))}
            <a
              href="mailto:hello@jorg.dev"
              className="text-sm font-medium px-4 py-2 rounded-full transition-all duration-200"
              style={{ background: "var(--accent-dim)", color: "var(--accent)", border: "1px solid rgba(34,197,94,0.2)" }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.background = "var(--accent)";
                (e.currentTarget as HTMLElement).style.color = "#0F172A";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.background = "var(--accent-dim)";
                (e.currentTarget as HTMLElement).style.color = "var(--accent)";
              }}
            >
              Get in touch
            </a>
          </div>
          {/* Hamburger — mobile only */}
          <button
            className="md:hidden flex items-center justify-center p-2 rounded-lg"
            style={{ color: "var(--text-muted)", background: "var(--surface)" }}
            onClick={() => setMenuOpen(true)}
            aria-label="Open menu"
          >
            <Menu size={20} />
          </button>
        </div>
      </nav>

      {/* Mobile fullscreen overlay */}
      {menuOpen && (
        <div
          className="fixed inset-0 z-40 flex flex-col items-center justify-center gap-8 md:hidden"
          style={{ background: "rgba(15,23,42,0.97)" }}
        >
          {/* Close button */}
          <button
            className="absolute top-4 right-6 flex items-center justify-center p-2 rounded-lg"
            style={{ color: "var(--text-muted)", background: "var(--surface)" }}
            onClick={() => setMenuOpen(false)}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>

          {["Projects", "Experience", "Skills", "Contact"].map((item) => (
            <a
              key={item}
              href={`#${item.toLowerCase()}`}
              className="text-3xl font-bold transition-colors duration-200"
              style={{ fontFamily: "Archivo, sans-serif", color: "var(--text)" }}
              onClick={() => setMenuOpen(false)}
            >
              {item}
            </a>
          ))}
          <a
            href="mailto:hello@jorg.dev"
            className="mt-4 inline-flex items-center gap-2 px-8 py-3 rounded-full font-semibold text-base"
            style={{ background: "var(--accent)", color: "#0F172A" }}
            onClick={() => setMenuOpen(false)}
          >
            Get in touch
          </a>
        </div>
      )}
    </>
  );
}

// ── Hero ────────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section
      className="relative flex items-center px-4 md:px-6"
      style={{
        minHeight: "100svh",
        backgroundImage: `
          linear-gradient(to right, rgba(34,197,94,0.07) 1px, transparent 1px),
          linear-gradient(to bottom, rgba(34,197,94,0.07) 1px, transparent 1px)
        `,
        backgroundSize: "48px 48px",
      }}
    >
      {/* Radial glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse 80% 60% at 50% 40%, rgba(34,197,94,0.09) 0%, transparent 70%)",
        }}
      />
      {/* Fade to bg at bottom */}
      <div
        className="absolute bottom-0 left-0 right-0 h-40 pointer-events-none"
        style={{ background: "linear-gradient(to bottom, transparent, var(--bg))" }}
      />

      <motion.div
        className="max-w-6xl mx-auto w-full relative z-10 pt-24 pb-16"
        variants={stagger(0.1)}
        initial="hidden"
        animate="show"
      >
        <motion.div variants={fadeUp} className="flex items-center gap-2 mb-10">
          <Dot />
          <span className="text-sm tracking-wide" style={{ color: "var(--text-muted)" }}>Available for projects</span>
        </motion.div>

        <motion.h1
          variants={fadeUp}
          className="font-black mb-6 leading-[0.9] tracking-tight"
          style={{
            fontFamily: "Archivo, sans-serif",
            fontSize: "clamp(4rem, 12vw, 9.5rem)",
          }}
        >
          Jorg
        </motion.h1>

        <motion.div variants={fadeUp} className="flex flex-wrap items-center gap-3 mb-8">
          {["AI Systems", "Full-Stack", "Automation"].map((tag) => (
            <span
              key={tag}
              className="text-sm font-medium px-3 py-1 rounded-full"
              style={{ background: "var(--surface)", color: "var(--text-muted)", border: "1px solid var(--border)" }}
            >
              {tag}
            </span>
          ))}
        </motion.div>

        <motion.p
          variants={fadeUp}
          className="text-lg md:text-xl max-w-xl leading-relaxed mb-10"
          style={{ color: "var(--text-muted)" }}
        >
          I build{" "}
          <span style={{ color: "var(--text)", fontWeight: 500 }}>AI-powered systems</span> that actually run in
          production — trading bots, multi-agent gateways, personal dashboards, e-commerce storefronts.
        </motion.p>

        <motion.div variants={fadeUp} className="flex flex-wrap items-center gap-4 mb-16">
          <a
            href="#projects"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full font-medium text-sm cursor-pointer"
            style={{ background: "var(--accent)", color: "#0F172A", transition: "opacity 200ms" }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.opacity = "0.85")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.opacity = "1")}
          >
            View Projects <ChevronDown size={15} />
          </a>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full font-medium text-sm cursor-pointer"
            style={{ background: "var(--surface)", color: "var(--text)", border: "1px solid var(--border)", transition: "border-color 200ms" }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.2)")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "var(--border)")}
          >
            <Github size={15} /> GitHub
          </a>
        </motion.div>

        <motion.div
          variants={fadeUp}
          className="pt-8 border-t grid grid-cols-3 md:flex md:flex-wrap gap-6 md:gap-10"
          style={{ borderColor: "var(--border)" }}
        >
          {[
            { label: "Systems in production", value: "5+" },
            { label: "AI agents running live", value: "3" },
            { label: "Stack languages", value: "Python · TS · SQL" },
          ].map((stat) => (
            <div key={stat.label}>
              <div
                className="text-2xl font-bold mb-0.5"
                style={{ fontFamily: "Archivo, sans-serif", color: "var(--text)" }}
              >
                {stat.value}
              </div>
              <div className="text-xs" style={{ color: "var(--text-muted)" }}>{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </motion.div>
    </section>
  );
}

// ── Featured project ─────────────────────────────────────────────────────────

function FeaturedProject() {
  const featured = projects[0];
  const Icon = featured.icon;

  return (
    <section id="projects" className="py-4 px-4 md:px-6">
      <div className="max-w-6xl mx-auto">
        <Section>
          <SectionHeader
            label="Projects"
            title="Things I've built"
            subtitle="Real systems, running in production. Each one solving an actual problem I had — or an experiment that became something more."
          />

          {/* Featured card */}
          <motion.div variants={fadeUp} className="mb-6">
            <Link href={`/projects/${featured.id}`} className="block group">
              <div
                className="rounded-3xl transition-all duration-300 relative overflow-hidden"
                style={{
                  background: "var(--surface)",
                  border: `1px solid ${featured.color}25`,
                }}
              >
                {/* Project image strip */}
                {featured.image && (
                  <div className="w-full h-48 md:h-64 overflow-hidden">
                    <img
                      src={featured.image}
                      alt={featured.name}
                      className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity duration-300"
                    />
                  </div>
                )}
                <div className="p-6 md:p-12">
                <div
                  className="absolute top-0 right-0 w-96 h-96 rounded-full pointer-events-none opacity-40"
                  style={{ background: `radial-gradient(circle, ${featured.color}10 0%, transparent 70%)` }}
                />

                <div className="relative z-10 md:flex items-start justify-between gap-8">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-6">
                      <div
                        className="w-12 h-12 rounded-xl flex items-center justify-center"
                        style={{ background: featured.accent, border: `1px solid ${featured.color}25` }}
                      >
                        <Icon size={22} style={{ color: featured.color }} />
                      </div>
                      <span
                        className="text-xs font-medium px-2.5 py-1 rounded-full"
                        style={{ background: `${featured.color}15`, color: featured.color, border: `1px solid ${featured.color}30` }}
                      >
                        ✦ Featured
                      </span>
                      <span
                        className="text-xs font-medium px-2.5 py-1 rounded-full"
                        style={{ background: "rgba(34,197,94,0.1)", color: "#22C55E", border: "1px solid rgba(34,197,94,0.2)" }}
                      >
                        {featured.status}
                      </span>
                    </div>

                    <h3 className="text-3xl md:text-4xl font-black mb-2" style={{ fontFamily: "Archivo, sans-serif" }}>
                      {featured.name}
                    </h3>
                    <p className="text-sm mb-4" style={{ color: featured.color }}>{featured.tag}</p>
                    <p className="text-base leading-relaxed mb-6 max-w-xl" style={{ color: "var(--text-muted)" }}>
                      {featured.description}
                    </p>

                    <div className="flex flex-wrap gap-2 mb-6">
                      {featured.stack.map((tech) => (
                        <span
                          key={tech}
                          className="text-xs px-2.5 py-1 rounded-full"
                          style={{ background: "var(--bg)", color: "var(--text-muted)", border: "1px solid var(--border)" }}
                        >
                          {tech}
                        </span>
                      ))}
                    </div>

                    <div
                      className="inline-flex items-center gap-2 text-sm font-medium transition-all duration-200 group-hover:gap-3"
                      style={{ color: featured.color }}
                    >
                      View case study <ArrowUpRight size={16} />
                    </div>
                  </div>

                  {/* Highlights */}
                  <div className="hidden md:block mt-8 md:mt-0 w-72 flex-shrink-0">
                    <div
                      className="rounded-2xl p-5"
                      style={{ background: "var(--bg)", border: "1px solid var(--border)" }}
                    >
                      <p className="text-xs font-semibold mb-4 uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                        Highlights
                      </p>
                      <ul className="space-y-3">
                        {featured.highlights.map((h, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
                            <span style={{ color: featured.color, flexShrink: 0, marginTop: "2px" }}>›</span>
                            {h}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
                </div>{/* close p-6 md:p-12 */}
              </div>
            </Link>
          </motion.div>

          {/* Rest of the projects grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {projects.slice(1).map((project) => {
              const PIcon = project.icon;
              return (
                <motion.div key={project.id} variants={fadeUp}>
                  <Link href={`/projects/${project.id}`} className="block group h-full">
                    <div
                      className="rounded-2xl overflow-hidden h-full flex flex-col"
                      style={{
                        background: "var(--surface)",
                        border: "1px solid var(--border)",
                        cursor: "pointer",
                        transition: "border-color 200ms, background 200ms, transform 200ms",
                      }}
                      onMouseEnter={(e) => {
                        (e.currentTarget as HTMLElement).style.borderColor = `${project.color}30`;
                        (e.currentTarget as HTMLElement).style.background = project.accent;
                        (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)";
                      }}
                      onMouseLeave={(e) => {
                        (e.currentTarget as HTMLElement).style.borderColor = "var(--border)";
                        (e.currentTarget as HTMLElement).style.background = "var(--surface)";
                        (e.currentTarget as HTMLElement).style.transform = "none";
                      }}
                    >
                      {project.image && (
                        <div className="w-full h-36 overflow-hidden flex-shrink-0">
                          <img
                            src={project.image}
                            alt={project.name}
                            className="w-full h-full object-cover opacity-70 group-hover:opacity-90 transition-opacity duration-300"
                          />
                        </div>
                      )}
                      <div className="p-7 flex-1 flex flex-col">
                      <div className="flex items-start justify-between mb-5">
                        <div
                          className="w-11 h-11 rounded-xl flex items-center justify-center"
                          style={{ background: project.accent, border: `1px solid ${project.color}20` }}
                        >
                          <PIcon size={20} style={{ color: project.color }} />
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className="text-xs font-medium px-2 py-0.5 rounded-full"
                            style={{ background: "rgba(34,197,94,0.1)", color: "#22C55E", border: "1px solid rgba(34,197,94,0.2)" }}
                          >
                            {project.status}
                          </span>
                          <ArrowUpRight size={16} style={{ color: "var(--text-muted)" }} />
                        </div>
                      </div>

                      <h3 className="text-xl font-bold mb-1" style={{ fontFamily: "Archivo, sans-serif" }}>
                        {project.name}
                      </h3>
                      <p className="text-xs mb-3" style={{ color: project.color }}>{project.tag}</p>
                      <p className="text-sm leading-relaxed mb-5" style={{ color: "var(--text-muted)" }}>
                        {project.description}
                      </p>

                      <div className="flex flex-wrap gap-2">
                        {project.stack.map((tech) => (
                          <span
                            key={tech}
                            className="text-xs px-2.5 py-1 rounded-full"
                            style={{ background: "var(--bg)", color: "var(--text-muted)", border: "1px solid var(--border)" }}
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                      </div>{/* close p-7 */}
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </Section>
      </div>
    </section>
  );
}

// ── Experience ───────────────────────────────────────────────────────────────

function Experience() {
  return (
    <section id="experience" className="py-16 md:py-24 px-4 md:px-6">
      <div className="max-w-6xl mx-auto">
        <Section>
          <SectionHeader
            label="Experience"
            title="Where I've been"
            subtitle="Building production systems since 2019 — from personal automation to client work to AI infrastructure."
          />

          <div className="space-y-0">
            {experience.map((entry, i) => (
              <motion.div key={i} variants={fadeUp} className="flex gap-6">

                {/* Left column: dot + connecting line — flex-col keeps them geometrically aligned */}
                <div className="hidden md:flex flex-col items-center flex-shrink-0 w-4">
                  <div
                    className="w-3 h-3 rounded-full border-2 flex-shrink-0 mt-8 z-10"
                    style={{
                      backgroundColor: i === 0 ? "var(--accent)" : "var(--surface-2)",
                      borderColor: "var(--accent)",
                      boxShadow: i === 0 ? "0 0 8px rgba(34,197,94,0.5)" : "none",
                    }}
                  />
                  {i < experience.length - 1 && (
                    <div
                      className="w-px flex-1 mt-1"
                      style={{ background: "linear-gradient(to bottom, rgba(34,197,94,0.4), rgba(34,197,94,0.08))" }}
                    />
                  )}
                </div>

                {/* Right column: card */}
                <div className="flex-1 pb-6">
                  <div
                    className="rounded-2xl p-7 transition-all duration-200"
                    style={{
                      background: "var(--surface)",
                      border: "1px solid var(--border)",
                      borderLeft: i === 0 ? "3px solid var(--accent)" : "1px solid var(--border)",
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLElement).style.borderColor = "rgba(34,197,94,0.25)";
                      (e.currentTarget as HTMLElement).style.transform = "translateY(-1px)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLElement).style.borderColor = i === 0 ? "var(--accent)" : "var(--border)";
                      (e.currentTarget as HTMLElement).style.transform = "none";
                    }}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
                      <div>
                        <h3 className="text-xl font-bold" style={{ fontFamily: "Archivo, sans-serif" }}>
                          {entry.role}
                        </h3>
                        <p className="text-sm mt-0.5" style={{ color: "var(--text-muted)" }}>
                          {entry.company}
                        </p>
                      </div>
                      <span
                        className="text-xs font-medium px-3 py-1 rounded-full flex-shrink-0"
                        style={{ background: "rgba(34,197,94,0.1)", color: "var(--accent)", border: "1px solid rgba(34,197,94,0.2)" }}
                      >
                        {entry.period}
                      </span>
                    </div>

                    <ul className="space-y-2 mb-5">
                      {entry.highlights.map((h, j) => (
                        <li key={j} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
                          <span style={{ color: "var(--accent)", flexShrink: 0, marginTop: "2px" }}>›</span>
                          {h}
                        </li>
                      ))}
                    </ul>

                    <div className="flex flex-wrap gap-2">
                      {entry.stack.map((tech) => (
                        <span
                          key={tech}
                          className="text-xs px-2.5 py-1 rounded-full"
                          style={{ background: "var(--bg)", color: "var(--text-muted)", border: "1px solid var(--border)" }}
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

              </motion.div>
            ))}
          </div>
        </Section>
      </div>
    </section>
  );
}

// ── Skills ───────────────────────────────────────────────────────────────────

function Skills() {
  return (
    <section id="skills" className="py-16 md:py-24 px-4 md:px-6">
      <div className="max-w-6xl mx-auto">
        <Section>
          <SectionHeader
            label="Stack"
            title="What I work with"
            subtitle="Tools and technologies I reach for when building production systems."
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {skills.map((group) => (
              <motion.div
                key={group.category}
                variants={fadeUp}
                className="rounded-2xl p-6 transition-all duration-200"
                style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "rgba(34,197,94,0.2)")}
                onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "var(--border)")}
              >
                <div className="flex items-center gap-2 mb-4">
                  <Terminal size={13} style={{ color: "var(--accent)" }} />
                  <span className="text-sm font-semibold" style={{ color: "var(--accent)" }}>
                    {group.category}
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {group.items.map((item) => (
                    <span
                      key={item}
                      className="text-sm px-3 py-1 rounded-lg"
                      style={{ background: "var(--bg)", color: "var(--text-muted)", border: "1px solid var(--border)" }}
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </Section>
      </div>
    </section>
  );
}

// ── Contact ──────────────────────────────────────────────────────────────────

function Contact() {
  return (
    <section id="contact" className="py-16 md:py-24 px-4 md:px-6">
      <div className="max-w-6xl mx-auto">
        <Section>
          <motion.div
            variants={fadeUp}
            className="rounded-3xl p-8 md:p-20 text-center relative overflow-hidden"
            style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
          >
            <div
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full pointer-events-none"
              style={{ background: "radial-gradient(circle, rgba(34,197,94,0.06) 0%, transparent 70%)" }}
            />
            <div className="relative z-10">
              <Dot />
              <h2 className="text-4xl md:text-6xl font-black mt-6 mb-6" style={{ fontFamily: "Archivo, sans-serif" }}>
                Let's build something
              </h2>
              <p className="text-lg max-w-lg mx-auto mb-10" style={{ color: "var(--text-muted)" }}>
                Open to collaboration on AI systems, automation, trading tech,
                or ambitious full-stack projects.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <a
                  href="mailto:hello@jorg.dev"
                  className="inline-flex items-center gap-2 px-8 py-4 rounded-full font-semibold text-sm transition-opacity duration-200"
                  style={{ background: "var(--accent)", color: "#0F172A" }}
                  onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.opacity = "0.88")}
                  onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.opacity = "1")}
                >
                  <Mail size={16} /> hello@jorg.dev
                </a>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-8 py-4 rounded-full font-semibold text-sm transition-colors duration-200"
                  style={{ background: "var(--bg)", color: "var(--text)", border: "1px solid var(--border)" }}
                  onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.18)")}
                  onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.borderColor = "var(--border)")}
                >
                  <Github size={16} /> GitHub
                </a>
              </div>
            </div>
          </motion.div>
        </Section>
      </div>
    </section>
  );
}

// ── Footer ───────────────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer className="px-6 py-8 border-t" style={{ borderColor: "var(--border)" }}>
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <span className="font-bold text-sm" style={{ fontFamily: "Archivo, sans-serif" }}>
          jorg<span style={{ color: "var(--accent)" }}>.</span>dev
        </span>
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          Built with Next.js · Framer Motion · Deployed on VPS
        </p>
      </div>
    </footer>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function Home() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <FeaturedProject />
        <Experience />
        <Skills />
        <Contact />
      </main>
      <Footer />
    </>
  );
}
