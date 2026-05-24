# Data Sources

## Citation Verification Data

### Indian Kanoon API
- **Source:** https://api.indiankanoon.org
- **Purpose:** Verification of Indian legal case citations
- **Coverage:** 30M+ Indian court decisions (Supreme Court, High Courts, Tribunals)
- **Access:** API key required (₹500 free credit on signup)
- **Cost:** ₹0.3/docmeta, ₹0.5/search, ₹2.00/full doc

### Citation Patterns
All 6 regex patterns are from the BRAHMO assessment Setup Guide:

| Pattern | Format | Source |
|---------|--------|--------|
| SCC | (2024) 5 SCC 123 | Setup Guide — standard Indian Supreme Court citation |
| SCC OnLine | 2024 SCC OnLine Del 456 | Setup Guide — SCC online database format |
| AIR | AIR 2024 SC 123 | Setup Guide — All India Reporter format |
| Cri LJ | 2024 Cri LJ 789 | Setup Guide — Criminal Law Journal format |
| SCR | (2024) 5 SCR 123 | Setup Guide — Supreme Court Reports format |
| MANU | MANU/SC/0123/2024 | Setup Guide — MANU/NIU database format |

## Section Mapping Data

### IPC → BNS (Indian Penal Code → Bharatiya Nyaya Sanhita)
- **Source:** The Bharatiya Nyaya Sanhita, 2023 (Act No. 45 of 2023)
- **Effective:** July 1, 2024
- **Reference:** Official Gazette of India, Ministry of Home Affairs notification
- **21 mappings** provided in the assessment Setup Guide covering the most commonly referenced IPC sections in criminal law practice

### CrPC → BNSS (Code of Criminal Procedure → Bharatiya Nagarik Suraksha Sanhita)
- **Source:** The Bharatiya Nagarik Suraksha Sanhita, 2023 (Act No. 46 of 2023)
- **Effective:** July 1, 2024
- **8 mappings** covering bail, FIR, and investigation provisions

### IEA → BSA (Indian Evidence Act → Bharatiya Sakshya Adhiniyam)
- **Source:** The Bharatiya Sakshya Adhiniyam, 2023 (Act No. 47 of 2023)
- **Effective:** July 1, 2024
- **1 mapping** — Section 65B IEA (electronic evidence) → Section 63 BSA

## Sample Legal Data

### 8 Legal Matters
- **Source:** All 8 matters provided in the assessment Setup Guide
- 4 matters correspond to demo scenarios (anticipatory bail, criminal complaint, NDPS research, criminal revision)
- 4 additional matters for general testing (corporate NDA, shareholders dispute, property, family law)

### 3 Sample AI Outputs
- **Source:** All 3 sample outputs provided in the assessment Setup Guide
  1. Clean output (all citations real) — for testing extractor on valid text
  2. Hallucinated output (2 fake citations) — for testing hallucination detection
  3. Repealed law output (4 IPC sections) — for testing section normalizer

### Hallucination Detection Rules
- **Source:** 4 rules from the assessment Setup Guide:
  1. Future year: year > 2026
  2. Impossible volume: SCC volume > 25
  3. Impossible page: page > 5000
  4. Pre-1900 date: year < 1900

### Historical Context
- **Mata v. Avianca Airlines** — US District Court, SDNY, 2023 — attorneys sanctioned for ChatGPT-fabricated citations
- **IPC replacement** — Criminal law reform effective July 1, 2024 — all IPC, CrPC, IEA sections replaced by BNS, BNSS, BSA