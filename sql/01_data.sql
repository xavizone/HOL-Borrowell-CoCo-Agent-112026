-- 01_data.sql - Borrowell Product Insights Agent lab: shared synthetic telemetry (read-only for attendees)
-- Run as PI_LAB_ADMIN after 00_admin_setup.sql. ~1-2 min on XSMALL. Deterministic: every value comes from
-- HASH() of stable keys, so two rebuilds give identical numbers (seeded RANDOM() does not).
-- All partners, offers and members are fictional. No real Borrowell data.
-- Co-authored with CoCo

USE ROLE PI_LAB_ADMIN;
USE WAREHOUSE PI_LAB_WH;
CREATE SCHEMA IF NOT EXISTS BORROWELL_AGENT_LAB.DATA COMMENT = 'Shared read-only product telemetry (synthetic)';
CREATE SCHEMA IF NOT EXISTS BORROWELL_AGENT_LAB.ADMIN COMMENT = 'Facilitator procedures and answer key';
USE SCHEMA BORROWELL_AGENT_LAB.DATA;

-- Deterministic uniform [0,1) from any seed string
CREATE OR REPLACE FUNCTION ADMIN_U(seed VARCHAR) RETURNS FLOAT
  AS $$ ((ABS(HASH(seed)) % 1000000) / 1000000.0)::FLOAT $$;

-- ---------------------------------------------------------------------------------------------
-- MEMBERS: 20,000 members, ~2% internal QA/test accounts
-- ---------------------------------------------------------------------------------------------
CREATE OR REPLACE TABLE MEMBERS (
  member_id      NUMBER  COMMENT 'Member id',
  signup_date    DATE    COMMENT 'Date the member joined Borrowell',
  province       VARCHAR COMMENT 'Two-letter Canadian province code',
  score_band     VARCHAR COMMENT 'Equifax score band at last refresh: Poor, Fair, Good, Excellent',
  score_band_idx NUMBER  COMMENT '1=Poor 2=Fair 3=Good 4=Excellent',
  is_newcomer    BOOLEAN COMMENT 'Joined within 3 years of arriving in Canada (self-reported)',
  is_test        BOOLEAN COMMENT 'Internal QA / employee test account. Exclude from every business metric.'
) COMMENT = 'Borrowell members (synthetic). One row per member.';

INSERT INTO MEMBERS
WITH g AS (SELECT SEQ4() + 1 AS id FROM TABLE(GENERATOR(ROWCOUNT => 20000))),
u AS (SELECT id, ADMIN_U(id || 'band') ub, ADMIN_U(id || 'prov') up, ADMIN_U(id || 'test') ut,
             ADMIN_U(id || 'new') un, ADMIN_U(id || 'signup') us FROM g)
SELECT id,
       DATEADD(day, FLOOR(us * 2700)::INT, '2019-01-01'::DATE),
       CASE WHEN up < .40 THEN 'ON' WHEN up < .60 THEN 'QC' WHEN up < .74 THEN 'BC' WHEN up < .86 THEN 'AB'
            WHEN up < .90 THEN 'MB' WHEN up < .93 THEN 'SK' WHEN up < .97 THEN 'NS' WHEN up < .99 THEN 'NB' ELSE 'NL' END,
       CASE WHEN ub < .15 THEN 'Poor' WHEN ub < .40 THEN 'Fair' WHEN ub < .75 THEN 'Good' ELSE 'Excellent' END,
       CASE WHEN ub < .15 THEN 1 WHEN ub < .40 THEN 2 WHEN ub < .75 THEN 3 ELSE 4 END,
       un < .12,
       ut < .02
FROM u;

-- ---------------------------------------------------------------------------------------------
-- PARTNER_OFFERS: 16 fictional partner products with referral payouts
-- ---------------------------------------------------------------------------------------------
CREATE OR REPLACE TABLE PARTNER_OFFERS (
  offer_id           NUMBER  COMMENT 'Offer id',
  offer_name         VARCHAR COMMENT 'Product name shown to members',
  partner_name       VARCHAR COMMENT 'Lending / financial partner (fictional)',
  product_type       VARCHAR COMMENT 'Credit Card, Personal Loan, Mortgage, Auto Loan, Insurance, Bank Account, Investing',
  min_score_band_idx NUMBER  COMMENT 'Partner''s target score band: 1=Poor 2=Fair 3=Good 4=Excellent',
  payout_cad         NUMBER(10,2) COMMENT 'Referral fee Borrowell earns per APPROVED application, CAD'
) COMMENT = 'Partner offers in the Borrowell marketplace (fictional partners).';

INSERT INTO PARTNER_OFFERS VALUES
 ( 1,'Cash Back Visa','Maple Bank','Credit Card',3,140),
 ( 2,'Secured Mastercard','Maple Bank','Credit Card',1,45),
 ( 3,'Travel Rewards Card','Northwind Financial','Credit Card',4,210),
 ( 4,'No-Fee Card','Northwind Financial','Credit Card',2,70),
 ( 5,'Low-Rate Card','Lakeshore Bank','Credit Card',2,85),
 ( 6,'Personal Loan','Summit Lending','Personal Loan',2,180),
 ( 7,'Debt Consolidation Loan','Summit Lending','Personal Loan',3,240),
 ( 8,'Member Personal Loan','Prairie Credit Union','Personal Loan',3,150),
 ( 9,'Instant Loan','FastFund','Personal Loan',1,95),
 (10,'5-Year Fixed Mortgage','Harbour Mortgage','Mortgage',4,450),
 (11,'Mortgage Renewal','Harbour Mortgage','Mortgage',3,320),
 (12,'Auto Loan','Evergreen Auto Finance','Auto Loan',2,160),
 (13,'Auto Insurance','True North Insurance','Insurance',1,40),
 (14,'Digital Chequing','Beacon Bank','Bank Account',1,55),
 (15,'High-Interest Savings','Beacon Bank','Bank Account',1,50),
 (16,'TFSA','Cedar Wealth','Investing',2,65);

-- Two ranking policies the marketplace used (top 6 per score band)
--   relevance     : offers the member qualifies for, closest fit first (production default)
--   payout_ranked : EXP-114 treatment - highest payout first, includes one-band "reach" offers
CREATE OR REPLACE TABLE OFFER_RANKINGS COMMENT = 'Offer order per score band for each ranking policy' AS
WITH b AS (SELECT column1 AS band FROM VALUES (1),(2),(3),(4))
SELECT 'relevance' AS policy, band AS score_band_idx, offer_id,
       ROW_NUMBER() OVER (PARTITION BY band ORDER BY band - min_score_band_idx, payout_cad DESC) AS rnk
FROM b JOIN PARTNER_OFFERS o ON o.min_score_band_idx <= b.band
QUALIFY rnk <= 6
UNION ALL
SELECT 'payout_ranked', band, offer_id,
       ROW_NUMBER() OVER (PARTITION BY band ORDER BY payout_cad DESC) AS rnk
FROM b JOIN PARTNER_OFFERS o ON o.min_score_band_idx <= b.band + 1
QUALIFY rnk <= 6;

-- ---------------------------------------------------------------------------------------------
-- EXPERIMENTS + assignments
-- ---------------------------------------------------------------------------------------------
CREATE OR REPLACE TABLE EXPERIMENTS (
  experiment_id VARCHAR, experiment_name VARCHAR, owner_team VARCHAR, start_date DATE, end_date DATE,
  status VARCHAR, primary_metric VARCHAR, hypothesis VARCHAR
) COMMENT = 'Product experiments (A/B tests) run on the marketplace';
INSERT INTO EXPERIMENTS VALUES
 ('EXP-114','Payout-ranked offer carousel','Marketplace Growth','2026-08-15','2026-10-15','completed','offer_ctr',
  'Ranking offers by referral payout instead of relevance will raise offer click-through rate and revenue.'),
 ('EXP-121','Credit Builder nudge after score drop','Engagement','2026-09-01','2026-11-30','running','credit_builder_signups',
  'A push nudge within 24h of a score drop will lift Credit Builder sign-ups.');

CREATE OR REPLACE TABLE EXPERIMENT_ASSIGNMENTS (
  experiment_id VARCHAR, member_id NUMBER, variant VARCHAR COMMENT 'control or treatment', assigned_at TIMESTAMP_NTZ
) COMMENT = 'Which members were in which experiment arm (non-test members only)';
INSERT INTO EXPERIMENT_ASSIGNMENTS
SELECT 'EXP-114', member_id, IFF(ADMIN_U(member_id || 'exp114') < .5, 'control', 'treatment'), '2026-08-15 00:00:00'
FROM MEMBERS WHERE NOT is_test;

-- ---------------------------------------------------------------------------------------------
-- TELEMETRY_EVENTS: impressions, clicks, application starts/submits. Aug 1 - Oct 31 2026.
-- Known data issues (documented in EXPERIMENT_DOCS, discoverable by the agent):
--   * internal test accounts and bot traffic are present
--   * Android 5.2.0 (rolled out 2026-09-20) double-fires dashboard impressions: same client_event_id twice
-- ---------------------------------------------------------------------------------------------
CREATE OR REPLACE TABLE TELEMETRY_EVENTS (
  event_id        VARCHAR COMMENT 'Unique row id assigned by the collector',
  client_event_id VARCHAR COMMENT 'Id generated by the app. Duplicate client_event_id = the same event sent twice; count DISTINCT client_event_id.',
  event_ts        TIMESTAMP_NTZ COMMENT 'Event time (UTC)',
  event_date      DATE    COMMENT 'Event date',
  member_id       NUMBER  COMMENT 'Member id; NULL for logged-out / bot traffic',
  session_id      VARCHAR COMMENT 'App session',
  event_type      VARCHAR COMMENT 'offer_impression, offer_click, apply_start, apply_submit',
  offer_id        NUMBER  COMMENT 'Offer shown or clicked',
  slot_position   NUMBER  COMMENT 'Position of the offer in the carousel, 1 = first',
  surface         VARCHAR COMMENT 'dashboard, offers_tab, email, push',
  platform        VARCHAR COMMENT 'ios, android, web',
  app_version     VARCHAR COMMENT 'Client app version',
  is_bot          BOOLEAN COMMENT 'Flagged by the bot filter (crawler / scripted traffic). Exclude from metrics.'
) COMMENT = 'Raw product telemetry for the offers marketplace (synthetic). Grain: one row per collected event.';

INSERT INTO TELEMETRY_EVENTS
WITH k AS (SELECT SEQ4() + 1 AS k FROM TABLE(GENERATOR(ROWCOUNT => 14))),
sess AS (   -- member sessions: engagement varies by member
  SELECT m.member_id, m.score_band_idx, m.is_test, k.k,
         'S' || m.member_id || '-' || k.k AS session_id,
         DATEADD(second, FLOOR(ADMIN_U(m.member_id || 'ts' || k.k) * 92 * 86400)::INT, '2026-08-01'::TIMESTAMP_NTZ) AS ts,
         ADMIN_U(m.member_id || 'surf' || k.k) AS us, ADMIN_U(m.member_id || 'plat') AS upl
  FROM MEMBERS m JOIN k ON ADMIN_U(m.member_id || 'sess' || k.k) < 0.15 + 0.55 * ADMIN_U(m.member_id || 'eng')
),
sess2 AS (
  SELECT s.*, s.ts::DATE AS d,
         CASE WHEN us < .55 THEN 'dashboard' WHEN us < .85 THEN 'offers_tab' WHEN us < .95 THEN 'email' ELSE 'push' END AS surface,
         CASE WHEN upl < .45 THEN 'ios' WHEN upl < .85 THEN 'android' ELSE 'web' END AS platform,
         COALESCE(a.variant, 'control') AS variant,
         IFF(s.ts >= '2026-08-15' AND s.ts < '2026-10-16' AND a.variant = 'treatment', 'payout_ranked', 'relevance') AS policy
  FROM sess s LEFT JOIN EXPERIMENT_ASSIGNMENTS a ON a.member_id = s.member_id AND a.experiment_id = 'EXP-114'
),
sess3 AS (
  SELECT s.*,
         CASE WHEN platform = 'android' AND ts >= '2026-09-20' AND ADMIN_U(member_id || 'upg') < .75 THEN '5.2.0'
              WHEN platform = 'android' THEN '5.1.4' WHEN platform = 'ios' THEN '7.8.1' ELSE 'web' END AS app_version
  FROM sess2 s
),
slots AS (SELECT column1 AS slot FROM VALUES (1),(2),(3),(4)),
imp AS (   -- 4 offers per session from the active ranking policy, small rotation for variety
  SELECT s.*, sl.slot, r.offer_id, o.payout_cad, o.min_score_band_idx,
         s.session_id || '-' || sl.slot AS ckey
  FROM sess3 s CROSS JOIN slots sl
  JOIN OFFER_RANKINGS r ON r.policy = s.policy AND r.score_band_idx = s.score_band_idx
       AND r.rnk = LEAST(6, sl.slot + FLOOR(ADMIN_U(s.session_id || 'rot') * 3)::INT)
  JOIN PARTNER_OFFERS o ON o.offer_id = r.offer_id
),
funnel AS (
  SELECT i.*,
         ADMIN_U(ckey || 'click') < IFF(is_test, 0.45,
              DECODE(slot, 1, .075, 2, .055, 3, .040, .030) * IFF(payout_cad >= 200, 1.35, 1.0)
              * IFF(surface IN ('email','push'), 1.3, 1.0)) AS clicked,
         ADMIN_U(ckey || 'start') < IFF(is_test, .8, .55) AS started,
         ADMIN_U(ckey || 'submit') < IFF(is_test, .8, .62) AS submitted
  FROM imp i
),
ev AS (
  SELECT session_id, ckey, ts, member_id, 'offer_impression' et, offer_id, slot, surface, platform, app_version, 0 AS lag_s, 0 AS dup FROM funnel
  UNION ALL   -- Android 5.2.0 double-fires dashboard impressions
  SELECT session_id, ckey, ts, member_id, 'offer_impression', offer_id, slot, surface, platform, app_version, 0, 1 FROM funnel
   WHERE app_version = '5.2.0' AND surface = 'dashboard'
  UNION ALL SELECT session_id, ckey, ts, member_id, 'offer_click', offer_id, slot, surface, platform, app_version, 8, 0 FROM funnel WHERE clicked
  UNION ALL SELECT session_id, ckey, ts, member_id, 'apply_start', offer_id, slot, surface, platform, app_version, 40, 0 FROM funnel WHERE clicked AND started
  UNION ALL SELECT session_id, ckey, ts, member_id, 'apply_submit', offer_id, slot, surface, platform, app_version, 400, 0 FROM funnel WHERE clicked AND started AND submitted
)
SELECT MD5(ckey || et || dup), MD5(ckey || et),
       DATEADD(millisecond, lag_s * 1000 + dup * 180, ts), DATEADD(millisecond, lag_s * 1000 + dup * 180, ts)::DATE,
       member_id, session_id, et, offer_id, slot, surface, platform, app_version, FALSE
FROM ev;

-- Bot / crawler traffic: logged-out sessions that "click" everything
INSERT INTO TELEMETRY_EVENTS
WITH b AS (SELECT SEQ4() + 1 AS b FROM TABLE(GENERATOR(ROWCOUNT => 2500))),
slots AS (SELECT column1 AS slot FROM VALUES (1),(2),(3),(4)),
x AS (
  SELECT 'BOT-' || b AS session_id, 'BOT-' || b || '-' || slot AS ckey, slot,
         DATEADD(second, FLOOR(ADMIN_U(b || 'bts') * 92 * 86400)::INT, '2026-08-01'::TIMESTAMP_NTZ) AS ts,
         1 + FLOOR(ADMIN_U(b || 'boff' || slot) * 16)::INT AS offer_id
  FROM b CROSS JOIN slots
)
SELECT MD5(ckey || et), MD5(ckey || et), DATEADD(second, lag_s, ts), DATEADD(second, lag_s, ts)::DATE,
       NULL, session_id, et, offer_id, slot, 'offers_tab', 'web', 'web', TRUE
FROM (SELECT x.*, 'offer_impression' et, 0 lag_s FROM x
      UNION ALL SELECT x.*, 'offer_click', 2 FROM x WHERE ADMIN_U(ckey || 'bclk') < .6);

-- ---------------------------------------------------------------------------------------------
-- APPLICATIONS: partner decisions on submitted applications. Revenue = payout on approval.
-- Approval odds fall sharply when a member applies above their score band ("reach" offers).
-- ---------------------------------------------------------------------------------------------
CREATE OR REPLACE TABLE APPLICATIONS (
  application_id  VARCHAR COMMENT 'Application id',
  member_id       NUMBER  COMMENT 'Member id',
  offer_id        NUMBER  COMMENT 'Offer applied for',
  session_id      VARCHAR COMMENT 'Session the application came from (joins to TELEMETRY_EVENTS)',
  submitted_at    TIMESTAMP_NTZ COMMENT 'When the application was submitted',
  submitted_date  DATE    COMMENT 'Submission date',
  decision        VARCHAR COMMENT 'approved or declined (partner decision)',
  decision_date   DATE    COMMENT 'Partner decision date, 1-6 days after submission',
  referral_revenue_cad NUMBER(10,2) COMMENT 'Referral fee earned, CAD. Payout when approved, 0 when declined.'
) COMMENT = 'Applications submitted through the marketplace and the partner decision.';

INSERT INTO APPLICATIONS
SELECT MD5('APP' || e.client_event_id), e.member_id, e.offer_id, e.session_id, e.event_ts, e.event_date,
       IFF(ADMIN_U(e.client_event_id || 'dec') <
           CASE WHEN m.score_band_idx - o.min_score_band_idx >= 1 THEN .78
                WHEN m.score_band_idx - o.min_score_band_idx = 0  THEN .55
                WHEN m.score_band_idx - o.min_score_band_idx = -1 THEN .08 ELSE .02 END, 'approved', 'declined'),
       DATEADD(day, 1 + FLOOR(ADMIN_U(e.client_event_id || 'dd') * 6)::INT, e.event_date),
       0
FROM TELEMETRY_EVENTS e JOIN MEMBERS m ON m.member_id = e.member_id JOIN PARTNER_OFFERS o ON o.offer_id = e.offer_id
WHERE e.event_type = 'apply_submit';
UPDATE APPLICATIONS a SET referral_revenue_cad = o.payout_cad FROM PARTNER_OFFERS o
 WHERE o.offer_id = a.offer_id AND a.decision = 'approved';

-- ---------------------------------------------------------------------------------------------
-- EXPERIMENT_DOCS: experiment briefs, metric definitions, known data issues (Cortex Search corpus)
-- ---------------------------------------------------------------------------------------------
CREATE OR REPLACE TABLE EXPERIMENT_DOCS (
  doc_id VARCHAR, title VARCHAR, doc_type VARCHAR COMMENT 'experiment_brief, metric_definition, data_issue, readout, policy',
  experiment_id VARCHAR, updated_date DATE, body VARCHAR
) COMMENT = 'Product data science knowledge base: briefs, metric definitions, data issues';
INSERT INTO EXPERIMENT_DOCS VALUES
('DOC-001','EXP-114 brief: payout-ranked offer carousel','experiment_brief','EXP-114','2026-08-10',
 'Owner: Marketplace Growth. Hypothesis: ranking the offer carousel by referral payout instead of relevance will lift offer CTR and revenue. Design: 50/50 split of non-test members, assigned 2026-08-15, runs to 2026-10-15. Primary metric: offer CTR. Secondary: application rate, approval rate, referral revenue per exposed member. Guardrail: approval rate must not fall more than 5 points, because declined applications create hard credit inquiries that can lower a member''s score and erode trust.'),
('DOC-002','Metric definition: offer click-through rate (CTR)','metric_definition',NULL,'2026-06-02',
 'Offer CTR = distinct offer clicks / distinct offer impressions. Always count DISTINCT client_event_id, never rows. Exclude bot traffic (is_bot = TRUE) and internal test accounts (MEMBERS.is_test = TRUE). Logged-out traffic (member_id NULL) is excluded from member metrics. CTR is a leading indicator only; the marketplace earns revenue on approvals, not clicks.'),
('DOC-003','Metric definition: approval rate and referral revenue','metric_definition',NULL,'2026-06-02',
 'Approval rate = approved applications / submitted applications, by submission date. Referral revenue (CAD) = sum of APPLICATIONS.referral_revenue_cad, earned only on approval. Revenue per exposed member = referral revenue / members who saw at least one offer impression in the period. Test accounts are excluded from all three.'),
('DOC-004','Known data issue: Android 5.2.0 duplicate impressions','data_issue',NULL,'2026-10-02',
 'From 2026-09-20 the Android app 5.2.0 sends every dashboard offer impression twice (same client_event_id, about 180 ms apart). Row counts of offer_impression on Android dashboard roughly doubled, which makes CTR look like it dropped in late September. It did not. Fix: count DISTINCT client_event_id. A client fix ships in 5.2.1.'),
('DOC-005','Known data issue: bot and crawler traffic','data_issue',NULL,'2026-07-15',
 'Logged-out scripted traffic hits the public offers page and clicks most offers. The collector flags it with is_bot = TRUE. Bot clicks inflate CTR by several points if not excluded. Bot rows have member_id NULL.'),
('DOC-006','Known data issue: internal test accounts','data_issue',NULL,'2026-05-20',
 'About 2% of member ids are QA and employee test accounts (MEMBERS.is_test = TRUE). They click and apply far more often than real members and must be excluded from every business metric, experiment readout and dashboard.'),
('DOC-007','EXP-121 brief: Credit Builder nudge after a score drop','experiment_brief','EXP-121','2026-08-25',
 'Owner: Engagement. A push notification within 24 hours of a score drop offers Credit Builder. Primary metric: Credit Builder sign-ups per notified member. Running 2026-09-01 to 2026-11-30. Do not read out before the end date.'),
('DOC-008','Partner payout policy','policy',NULL,'2026-01-12',
 'Partners pay Borrowell a referral fee only when an application is approved. Payouts range from 40 CAD (insurance) to 450 CAD (mortgages). A high payout on an offer the member is unlikely to be approved for earns nothing and costs the member a hard inquiry. Recommendations must not promise approval.'),
('DOC-009','How to read out an experiment','policy',NULL,'2026-03-03',
 'Compare arms on the primary metric and every guardrail over the full experiment window. Use members assigned in EXPERIMENT_ASSIGNMENTS, not everyone who saw the surface. Report absolute values for both arms and the relative lift. A win on a leading metric (CTR) that loses on revenue or a guardrail is not a win.'),
('DOC-010','Score bands and partner targeting','policy',NULL,'2026-02-14',
 'Score bands: Poor, Fair, Good, Excellent. Each partner offer targets a minimum band (PARTNER_OFFERS.min_score_band_idx). Historically, approval odds are about 78% one band above target, 55% at target, 8% one band below and about 2% two bands below.');

-- ---------------------------------------------------------------------------------------------
-- Read access for every attendee
-- ---------------------------------------------------------------------------------------------
GRANT USAGE ON DATABASE BORROWELL_AGENT_LAB TO ROLE PI_LAB_ATTENDEE;
GRANT USAGE ON SCHEMA BORROWELL_AGENT_LAB.DATA TO ROLE PI_LAB_ATTENDEE;
GRANT SELECT ON ALL TABLES IN SCHEMA BORROWELL_AGENT_LAB.DATA TO ROLE PI_LAB_ATTENDEE;
GRANT USAGE ON FUNCTION BORROWELL_AGENT_LAB.DATA.ADMIN_U(VARCHAR) TO ROLE PI_LAB_ATTENDEE;
ALTER TABLE TELEMETRY_EVENTS CLUSTER BY (event_date);
ALTER TABLE EXPERIMENT_DOCS SET CHANGE_TRACKING = TRUE;   -- attendees build Cortex Search services on it

SELECT 'MEMBERS' t, COUNT(*) n FROM MEMBERS UNION ALL SELECT 'TELEMETRY_EVENTS', COUNT(*) FROM TELEMETRY_EVENTS
UNION ALL SELECT 'APPLICATIONS', COUNT(*) FROM APPLICATIONS UNION ALL SELECT 'EXPERIMENT_DOCS', COUNT(*) FROM EXPERIMENT_DOCS;
