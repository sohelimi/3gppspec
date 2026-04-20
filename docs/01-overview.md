# Project Overview

## What is 3gppSpec?

3gppSpec is an **Agentic RAG (Retrieval-Augmented Generation) chatbot** that lets you ask natural-language questions about 3GPP telecommunications standards and get accurate, cited answers in real time.

Instead of manually searching through thousands of pages of dense technical specifications, you simply type a question like:

> *"How does beam management work in 5G NR?"*

and the system finds the relevant passages across multiple specs, synthesises a coherent answer, and tells you exactly which 3GPP Technical Specifications it sourced from.

---

## Why This Project Exists

3GPP specifications are the foundation of all modern mobile telecommunications — 4G LTE, 5G NR, and beyond. They are:

- **Massive** — thousands of documents totalling gigabytes of text
- **Highly technical** — dense with abbreviations, cross-references, and domain-specific terminology
- **Frequently updated** — new releases every few years, with incremental updates

This tool makes that knowledge instantly accessible to telecom engineers, researchers, and students.

---

## Key Features

| Feature | Description |
|---|---|
| **Agentic query planning** | Automatically decomposes complex questions into focused sub-queries |
| **Multi-hop retrieval** | Searches across multiple specs simultaneously and deduplicates results |
| **Real-time streaming** | Answers stream token-by-token like ChatGPT |
| **Source citations** | Every answer shows which 3GPP spec it came from, with release and series |
| **Fully free stack** | Zero API costs — Groq free tier + local embeddings + local vector DB |
| **Open source** | MIT licensed, deployable by anyone |

---

## Covered Specifications

| Release | Series | Coverage |
|---|---|---|
| Rel-17 | 23, 24, 33, 38 | 5G NR, Core, Security, Protocols |
| Rel-18 | 23, 24, 33, 38 | 5G Advanced (main focus) |
| Rel-19 | 23, 24, 33, 38 | Latest release |

**Series guide:**
- **23_series** — System architecture, procedures (TS 23.501, 23.502, 23.503...)
- **24_series** — Protocol specifications
- **33_series** — Security architecture (TS 33.501...)
- **38_series** — 5G NR radio access (TS 38.101, 38.211, 38.300...)

---

## Live Demo

**[https://3gpp.deltatechus.com](https://3gpp.deltatechus.com)**

---

## Repository

**[https://github.com/sohelimi/3gppspec](https://github.com/sohelimi/3gppspec)**
