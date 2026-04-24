"use client";

import { notFound } from "next/navigation";
import Link from "next/link";
import { useParams } from "next/navigation";
import { motion, type Variants } from "framer-motion";
import { ArrowLeft, ArrowUpRight, Github, Mail } from "lucide-react";
import { projects } from "../data";

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

const stagger: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};

function Dot({ color }: { color: string }) {
  return (
    <span
      className="inline-block w-2 h-2 rounded-full animate-pulse"
      style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}` }}
    />
  );
}

export default function CaseStudy() {
  const params = useParams();
  const project = projects.find((p) => p.id === params.slug);
  if (!project) return notFound();

  const Icon = project.icon;

  return (
    <div style={{ background: "var(--bg)", minHeight: "100vh", color: "var(--text)" }}>
      {/* Top nav */}
      <div
        className="fixed top-0 left-0 right-0 z-50"
        style={{
          background: "rgba(15,23,42,0.85)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2 text-sm transition-colors duration-200"
            style={{ color: "var(--text-muted)" }}
          >
            <ArrowLeft size={16} />
            Back to portfolio
          </Link>
          <span className="hidden md:flex items-center text-xs" style={{ color: "var(--text-muted)" }}>
            <span style={{ color: "var(--text-muted)" }}>jorg.dev</span>
            <span className="mx-2" style={{ color: "var(--border)" }}>/</span>
            <span style={{ color: "var(--text-muted)" }}>projects</span>
            <span className="mx-2" style={{ color: "var(--border)" }}>/</span>
            <span style={{ color: project.color }}>{project.name}</span>
          </span>
        </div>
      </div>

      <main className="max-w-5xl mx-auto px-4 md:px-6 pt-20 md:pt-28 pb-16 md:pb-24">

        {/* ── Hero ─────────────────────────────────────────────────────── */}
        <motion.section
          variants={stagger}
          initial="hidden"
          animate="show"
          className="mb-20"
        >
          {/* Icon + status */}
          <motion.div variants={fadeUp} className="flex items-center gap-4 mb-8">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center"
              style={{ background: project.accent, border: `1px solid ${project.color}30` }}
            >
              <Icon size={26} style={{ color: project.color }} />
            </div>
            <div className="flex items-center gap-2">
              <Dot color={project.color} />
              <span
                className="text-sm font-medium px-3 py-1 rounded-full"
                style={{
                  background: `${project.color}15`,
                  color: project.color,
                  border: `1px solid ${project.color}30`,
                }}
              >
                {project.status}
              </span>
            </div>
          </motion.div>

          {/* Glow + title */}
          <motion.div variants={fadeUp} className="relative mb-4">
            <div
              className="absolute -top-8 -left-8 w-64 h-64 rounded-full pointer-events-none"
              style={{ background: `radial-gradient(circle, ${project.color}12 0%, transparent 70%)` }}
            />
            <h1
              className="text-5xl md:text-7xl font-black relative z-10"
              style={{ fontFamily: "Archivo, sans-serif" }}
            >
              {project.name}
            </h1>
          </motion.div>

          <motion.p variants={fadeUp} className="text-xl mb-6" style={{ color: project.color }}>
            {project.tagline}
          </motion.p>

          <motion.p variants={fadeUp} className="text-lg max-w-2xl mb-10 leading-relaxed" style={{ color: "var(--text-muted)" }}>
            {project.description}
          </motion.p>

          {/* Metrics */}
          <motion.div variants={stagger} className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {project.metrics.map((m) => (
              <motion.div
                key={m.label}
                variants={fadeUp}
                className="rounded-2xl p-5 text-center"
                style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
              >
                <div
                  className="text-3xl font-black mb-1"
                  style={{ fontFamily: "Archivo, sans-serif", color: project.color }}
                >
                  {m.value}
                </div>
                <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {m.label}
                </div>
              </motion.div>
            ))}
          </motion.div>
        </motion.section>

        {/* ── Architecture ──────────────────────────────────────────────── */}
        <motion.section
          variants={stagger}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-80px" }}
          className="mb-20"
        >
          <motion.div variants={fadeUp} className="mb-10">
            <span
              className="text-xs font-medium px-3 py-1 rounded-full mb-4 inline-block"
              style={{ background: "var(--surface)", color: project.color, border: "1px solid var(--border)" }}
            >
              Architecture
            </span>
            <h2 className="text-3xl md:text-4xl font-black" style={{ fontFamily: "Archivo, sans-serif" }}>
              How it works
            </h2>
          </motion.div>

          {/* Flow diagram */}
          <div className="flex flex-col md:flex-row items-stretch gap-2 md:gap-0">
            {project.architecture.map((node, i) => {
              const NodeIcon = node.icon;
              return (
              <motion.div key={node.name} variants={fadeUp} className="flex flex-col md:flex-row items-center flex-1 min-w-0">
                <div
                  className="flex-1 rounded-2xl p-5 w-full"
                  style={{ background: "var(--surface)", border: `1px solid ${project.color}20` }}
                >
                  <div className="mb-3" style={{ color: project.color }}>
                    <NodeIcon size={20} />
                  </div>
                  <div className="font-bold mb-1 text-sm" style={{ fontFamily: "Archivo, sans-serif" }}>
                    {node.name}
                  </div>
                  <p className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
                    {node.description}
                  </p>
                </div>
                {i < project.architecture.length - 1 && (
                  <div
                    className="flex-shrink-0 text-lg mx-3 my-2 md:my-0 rotate-90 md:rotate-0"
                    style={{ color: project.color }}
                  >
                    →
                  </div>
                )}
              </motion.div>
              );
            })}
          </div>
        </motion.section>

        {/* ── Details: stack + features ─────────────────────────────────── */}
        <motion.section
          variants={stagger}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-80px" }}
          className="grid md:grid-cols-2 gap-6 mb-20"
        >
          {/* Stack */}
          <motion.div
            variants={fadeUp}
            className="rounded-2xl p-7"
            style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
          >
            <h3 className="font-bold mb-5" style={{ fontFamily: "Archivo, sans-serif", color: project.color }}>
              Tech Stack
            </h3>
            <div className="flex flex-wrap gap-2">
              {project.stack.map((tech) => (
                <span
                  key={tech}
                  className="px-3 py-1.5 rounded-xl text-sm font-medium"
                  style={{
                    background: `${project.color}12`,
                    color: project.color,
                    border: `1px solid ${project.color}25`,
                  }}
                >
                  {tech}
                </span>
              ))}
            </div>
          </motion.div>

          {/* Features */}
          <motion.div
            variants={fadeUp}
            className="rounded-2xl p-7"
            style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
          >
            <h3 className="font-bold mb-5" style={{ fontFamily: "Archivo, sans-serif", color: project.color }}>
              Key Features
            </h3>
            <ul className="space-y-2.5">
              {project.features.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
                  <span style={{ color: project.color, flexShrink: 0, marginTop: "2px" }}>›</span>
                  {f}
                </li>
              ))}
            </ul>
          </motion.div>
        </motion.section>

        {/* ── Challenges ────────────────────────────────────────────────── */}
        <motion.section
          variants={stagger}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-80px" }}
          className="mb-20"
        >
          <motion.div variants={fadeUp} className="mb-10">
            <span
              className="text-xs font-medium px-3 py-1 rounded-full mb-4 inline-block"
              style={{ background: "var(--surface)", color: project.color, border: "1px solid var(--border)" }}
            >
              Engineering
            </span>
            <h2 className="text-3xl md:text-4xl font-black" style={{ fontFamily: "Archivo, sans-serif" }}>
              Challenges & solutions
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-5">
            {project.challenges.map((c, i) => (
              <motion.div
                key={i}
                variants={fadeUp}
                className="rounded-2xl p-6"
                style={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderLeft: `3px solid ${project.color}`,
                }}
              >
                <h4 className="font-bold mb-3 text-sm" style={{ fontFamily: "Archivo, sans-serif" }}>
                  {c.title}
                </h4>
                <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
                  {c.description}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.section>

        {/* ── Other projects ────────────────────────────────────────────── */}
        <motion.section
          variants={stagger}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-80px" }}
          className="mb-20"
        >
          <motion.h2 variants={fadeUp} className="text-2xl font-black mb-6" style={{ fontFamily: "Archivo, sans-serif" }}>
            Other projects
          </motion.h2>
          {/* Desktop grid */}
          <div className="hidden md:grid grid-cols-4 gap-4">
            {projects.filter((p) => p.id !== project.id).map((p) => {
              const PIcon = p.icon;
              return (
                <motion.div key={p.id} variants={fadeUp}>
                  <Link
                    href={`/projects/${p.id}`}
                    className="block rounded-xl p-4 transition-all duration-200 group"
                    style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
                  >
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center mb-3"
                      style={{ background: p.accent }}
                    >
                      <PIcon size={16} style={{ color: p.color }} />
                    </div>
                    <div className="text-sm font-semibold mb-1">{p.name}</div>
                    <div className="text-xs flex items-center gap-1" style={{ color: "var(--text-muted)" }}>
                      View <ArrowUpRight size={10} />
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </div>
          {/* Mobile horizontal scroll */}
          <div className="flex md:hidden gap-3 overflow-x-auto pb-2 snap-x snap-mandatory">
            {projects.filter((p) => p.id !== project.id).map((p) => {
              const PIcon = p.icon;
              return (
                <Link
                  key={p.id}
                  href={`/projects/${p.id}`}
                  className="flex-shrink-0 w-[160px] snap-start block rounded-xl p-4 transition-all duration-200 group"
                  style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
                >
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center mb-3"
                    style={{ background: p.accent }}
                  >
                    <PIcon size={16} style={{ color: p.color }} />
                  </div>
                  <div className="text-sm font-semibold mb-1">{p.name}</div>
                  <div className="text-xs flex items-center gap-1" style={{ color: "var(--text-muted)" }}>
                    View <ArrowUpRight size={10} />
                  </div>
                </Link>
              );
            })}
          </div>
        </motion.section>

        {/* ── CTA ───────────────────────────────────────────────────────── */}
        <motion.section
          variants={stagger}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-80px" }}
        >
          <motion.div
            variants={fadeUp}
            className="rounded-3xl p-10 md:p-14 text-center relative overflow-hidden"
            style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
          >
            <div
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full pointer-events-none"
              style={{ background: `radial-gradient(circle, ${project.color}08 0%, transparent 70%)` }}
            />
            <div className="relative z-10">
              <p className="text-sm mb-4" style={{ color: "var(--text-muted)" }}>
                Interested in this project?
              </p>
              <h2 className="text-3xl md:text-4xl font-black mb-8" style={{ fontFamily: "Archivo, sans-serif" }}>
                Let's build something together
              </h2>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <a
                  href="mailto:hello@jorg.dev"
                  className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full font-semibold text-sm"
                  style={{ background: "var(--accent)", color: "#0F172A" }}
                >
                  <Mail size={15} /> hello@jorg.dev
                </a>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full font-semibold text-sm"
                  style={{ background: "var(--bg)", color: "var(--text)", border: "1px solid var(--border)" }}
                >
                  <Github size={15} /> GitHub
                </a>
              </div>
            </div>
          </motion.div>
        </motion.section>
      </main>
    </div>
  );
}
