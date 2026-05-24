-- BRAHMO Citation Safety Engine - Seed Data
-- 6 Citation Patterns, 30 Section Mappings, 8 Legal Matters

-- ============================================================
-- CITATION PATTERNS (6 patterns for Indian legal citations)
-- ============================================================

INSERT INTO citation_patterns (pattern_name, regex, format_template, example, jurisdiction) VALUES
('SCC', '\\((\\d{4})\\)\\s+(\\d{1,2})\\s+SCC\\s*(\\d{1,5})', '({year}) {volume} SCC {page}', '(2024) 5 SCC 123', 'India'),
('SCC_OnLine', '(\\d{4})\\s+SCC\\s+On(?:line|Line)\\s+(SC|Del|Bom|Cal|Mad|All|Kar|Ker|Pat|Raj|MP|AP|Guj|Delhi|Bombay|Calcutta|Madras|Allahabad|Karnataka|Kerala|Patna|Rajasthan)\\s+(\\d{1,6})', '{year} SCC OnLine {court} {num}', '2024 SCC OnLine Del 456', 'India'),
('AIR', 'AIR\\s+(\\d{4})\\s+(SC|Del|Bom|Cal|Mad|All|Kar|Ker|Pat|Raj|MP|AP|Guj|NOC|Delhi|Bombay|Calcutta|Madras|Allahabad|Karnataka|Kerala|Patna|Rajasthan)\\s+(\\d{1,5})', 'AIR {year} {court} {page}', 'AIR 2024 SC 123', 'India'),
('Cri_LJ', '[\\(]?(\\d{4})[\\)]?\\s+Cri\\s+LJ\\s+(\\d{1,5})', '{year} Cri LJ {page}', '2024 Cri LJ 789', 'India'),
('SCR', '\\((\\d{4})\\)\\s+(\\d{1,2})\\s+SCR\\s+(\\d{1,5})', '({year}) {volume} SCR {page}', '(2024) 5 SCR 123', 'India'),
('MANU', 'MANU/(SC|DE|MH|KA|KE|WB|TN|AP|GJ|RJ|MP|UP)/\\d{4}/\\d{4,6}', 'MANU/{court}/{year}/{num}', 'MANU/SC/0123/2024', 'India');

-- ============================================================
-- SECTION MAPPINGS (30 mappings: 20 IPC→BNS, 8 CrPC→BNSS, 2 IEA→BSA)
-- ============================================================

INSERT INTO section_mappings (old_section, new_section, old_act, new_act) VALUES
-- IPC → BNS (20 mappings)
('Section 302 IPC', 'Section 101 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 304 IPC', 'Section 105 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 304A IPC', 'Section 106 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 304B IPC', 'Section 80 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 306 IPC', 'Section 108 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 307 IPC', 'Section 109 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 323 IPC', 'Section 115 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 326 IPC', 'Section 119 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 354 IPC', 'Section 74 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 376 IPC', 'Section 63 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 379 IPC', 'Section 303 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 384 IPC', 'Section 308 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 392 IPC', 'Section 309 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 406 IPC', 'Section 316 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 420 IPC', 'Section 318 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 467 IPC', 'Section 336 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 498A IPC', 'Section 85 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 499 IPC', 'Section 356 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 506 IPC', 'Section 351 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 34 IPC', 'Section 3(5) BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
('Section 120B IPC', 'Section 61 BNS', 'Indian Penal Code', 'Bharatiya Nyaya Sanhita'),
-- CrPC → BNSS (8 mappings)
('Section 125 CrPC', 'Section 144 BNSS', 'Code of Criminal Procedure', 'Bharatiya Nagarik Suraksha Sanhita'),
('Section 154 CrPC', 'Section 173 BNSS', 'Code of Criminal Procedure', 'Bharatiya Nagarik Suraksha Sanhita'),
('Section 156(3) CrPC', 'Section 175(3) BNSS', 'Code of Criminal Procedure', 'Bharatiya Nagarik Suraksha Sanhita'),
('Section 167 CrPC', 'Section 187 BNSS', 'Code of Criminal Procedure', 'Bharatiya Nagarik Suraksha Sanhita'),
('Section 437 CrPC', 'Section 480 BNSS', 'Code of Criminal Procedure', 'Bharatiya Nagarik Suraksha Sanhita'),
('Section 438 CrPC', 'Section 482 BNSS', 'Code of Criminal Procedure', 'Bharatiya Nagarik Suraksha Sanhita'),
('Section 439 CrPC', 'Section 483 BNSS', 'Code of Criminal Procedure', 'Bharatiya Nagarik Suraksha Sanhita'),
('Section 482 CrPC', 'Section 528 BNSS', 'Code of Criminal Procedure', 'Bharatiya Nagarik Suraksha Sanhita'),
-- IEA → BSA (1 mapping)
('Section 65B IEA', 'Section 63 BSA', 'Indian Evidence Act', 'Bharatiya Sakshya Adhiniyam');

-- ============================================================
-- LEGAL MATTERS (8 matters — 4 demo scenarios + 4 general)
-- ============================================================

INSERT INTO legal_matters (title, client_name, practice_area, court, query, scenario_type, sample_output) VALUES

-- Scenario 1: The Hallucinated Citation
('Anticipatory Bail — Economic Offences', 'Rajesh Kumar', 'Criminal', 'Delhi High Court',
'What are the key Supreme Court precedents on anticipatory bail in economic offences?',
'hallucinated',
'The legal framework for anticipatory bail in economic offences:

The Supreme Court in Rajesh Sharma v. State of UP (2023) 4 SCC 789 held that economic offences alone cannot be ground for denying anticipatory bail.

In Siddharth v. State of UP (2021) 10 SCC 1, the Court emphasized the need for a balanced approach to bail.

In Amit Kumar v. Union of India AIR 2024 SC 567, the Court reiterated that personal liberty under Article 21 must be given primacy.

In Satender Kumar Antil v. CBI (2022) 10 SCC 51, offences were classified by severity for bail consideration.

In Arnesh Kumar v. State of Bihar (2014) 8 SCC 273, the Court issued guidelines on arrest.

In Sushila Aggarwal v. State (2020) 5 SCC 12, the Court confirmed that anticipatory bail orders need not be time-limited.

In Vikram Singh v. State (2024) 8 SCC 234, the Court held that economic offences must be distinguished from serious crimes for bail purposes.'),

-- Scenario 2: The Repealed Law Catastrophe
('Criminal Complaint — Cheating & Criminal Breach of Trust', 'Priya Sharma', 'Criminal', 'Delhi Metropolitan Magistrate',
'Draft a complaint for cheating under Section 420 IPC with criminal breach of trust under Section 406 IPC',
'repealed_law',
'COMPLAINT UNDER SECTION 420 IPC AND SECTION 406 IPC

The complainant respectfully submits that the accused has committed offences punishable under Section 420 of the Indian Penal Code (cheating and dishonestly inducing delivery of property) read with Section 120B IPC (criminal conspiracy) and Section 34 IPC (common intention).

The accused, acting in conspiracy, induced the complainant to part with Rs. 50,00,000 under the false pretense of a business partnership.

The complainant prays that an FIR be registered under Sections 420, 406, 120B and 34 of the Indian Penal Code against the accused persons.'),

-- Scenario 3: The Impossible Citation
('NDPS Act Bail Research', 'Amit Verma', 'Criminal', 'Supreme Court of India',
'Summarize SC approach to bail in NDPS cases over last 5 years',
'impossible_citation',
'The Supreme Court has evolved a nuanced approach to bail in NDPS cases:

In State of Punjab v. Balbir Singh (2028) 3 SCC 45, the Court revisited the strict bail provisions under Section 37 of the NDPS Act.

In Tofan Singh v. State of Tamil Nadu (2024) 47 SCC 123, the majority held that Section 37 imposes stringent conditions for grant of bail.

In Mohd. Arif @ Ashfaq v. State (2023) 19 SCC 456, the Court distinguished between commercial and small quantity offences for bail purposes.

In Union of India v. Shiv Shankar (2021) 8 SCC 456, the Court held that NDPS bail provisions must be read with Article 21.

In R v. State of Karnataka (2020) 10 SCC 123, the Court clarified the burden of proof in NDPS bail applications.

In Abdul Rashid v. State (2022) 5 SCC 789, the Court held that prolonged incarceration warrants bail even under NDPS.

In Priya v. State (2019) 12 SCC 345, the Court examined therebutter presumption under Section 54 of the NDPS Act.

In State v. Rajesh Kumar (2023) 9 SCC 123, the Court noted that bail in NDPS cases requires satisfaction of dual conditions under Section 37.'),

-- Scenario 4: The Format Error
('Criminal Revision — Section 482 BNSS Powers', 'Vikram Malhotra', 'Criminal', 'Delhi High Court',
'Key Delhi HC decisions on Section 482 BNSS powers in last 2 years',
'format_error',
'The Delhi High Court has exercised its inherent powers under Section 482 BNSS in several important decisions:

In Deepak Kumar v. State (2024) 7 SCC 234, the Court quashed proceedings where the complaint was manifestly absurd.

In Priya Gupta v. NCT of Delhi 2024 SCC Online Del 3456, the Court held that inherent powers must be used sparingly to prevent abuse of process.

In Amit Singh v. State AIR 2024 Delhi 234, the Court clarified that Section 482 BNSS powers cannot be used to evaluate evidence.

In Rajesh v. State (2023) 5 SCC 398, the Court set aside the impugned order as being contrary to settled principles.

In Suresh Kumar v. NCT of Delhi MANU/DE/0567/2023, the Court laid down guidelines for exercise of inherent jurisdiction.

In Meera v. State (2023) 5 SCC123, the Court held that criminal proceedings cannot be quashed merely because parties have settled.'),

-- Additional matters (no specific demo scenario)
('Corporate NDA Review', 'TechCorp India Pvt. Ltd.', 'Corporate', 'N/A (Transactional)',
'Review this NDA and flag missing clauses for Indian law compliance',
NULL, NULL),

('Shareholders Dispute — Oppression & Mismanagement', 'Sunita Reddy', 'Corporate', 'NCLT Delhi',
'Grounds for NCLT petition under oppression and mismanagement under Companies Act Sections 241-242',
NULL, NULL),

('Specific Performance — Sale Agreement', 'Ramesh Gupta', 'Property', 'Civil Court Delhi',
'Specific performance of immovable property sale agreement under Specific Relief Act',
NULL, NULL),

('Contested Divorce — Hindu Marriage Act', 'Anita Sharma', 'Family', 'Family Court Delhi',
'Grounds for contested divorce under Hindu Marriage Act Section 13',
NULL, NULL);