-- answer_key.sql - everything an attendee builds, as plain SQL (what CoCo generates). Run as PI_LAB_<NAME>.
-- Replace LAB_DEMO / PI_LAB_DEMO with your name. Sessions 2-5 + stretch.
-- Co-authored with CoCo

USE ROLE PI_LAB_DEMO;
USE SECONDARY ROLES NONE;
USE WAREHOUSE PI_LAB_WH;
USE SCHEMA BORROWELL_AGENT_LAB.LAB_DEMO;

-- =============================================================================================
-- Session 2a: curated views that fix the three known data issues before any metric is defined
-- =============================================================================================
CREATE OR REPLACE VIEW MEMBERS_V COMMENT = 'Real (non-test) members with their EXP-114 arm' AS
SELECT m.member_id, m.signup_date, m.province, m.score_band, m.score_band_idx, m.is_newcomer,
       COALESCE(a.variant, 'not assigned') AS exp114_variant
FROM BORROWELL_AGENT_LAB.DATA.MEMBERS m
LEFT JOIN BORROWELL_AGENT_LAB.DATA.EXPERIMENT_ASSIGNMENTS a ON a.member_id = m.member_id AND a.experiment_id = 'EXP-114'
WHERE NOT m.is_test;

CREATE OR REPLACE VIEW OFFER_EVENTS_V COMMENT = 'Deduplicated member telemetry: no bots, no test accounts, one row per client_event_id' AS
SELECT e.client_event_id, e.event_ts, e.event_date, e.member_id, e.session_id, e.event_type, e.offer_id,
       e.slot_position, e.surface, e.platform, e.app_version
FROM BORROWELL_AGENT_LAB.DATA.TELEMETRY_EVENTS e
JOIN MEMBERS_V m ON m.member_id = e.member_id          -- drops bots (member_id NULL) and test accounts
WHERE NOT e.is_bot
QUALIFY ROW_NUMBER() OVER (PARTITION BY e.client_event_id ORDER BY e.event_ts) = 1;   -- Android 5.2.0 double-fire

CREATE OR REPLACE VIEW APPLICATIONS_V COMMENT = 'Applications from real members' AS
SELECT a.* FROM BORROWELL_AGENT_LAB.DATA.APPLICATIONS a JOIN MEMBERS_V m ON m.member_id = a.member_id;

CREATE OR REPLACE VIEW OFFERS_V AS SELECT * FROM BORROWELL_AGENT_LAB.DATA.PARTNER_OFFERS;

-- =============================================================================================
-- Session 2b: the semantic view - one governed definition of CTR, approval rate and revenue
-- =============================================================================================
CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML('BORROWELL_AGENT_LAB.LAB_DEMO', $$
name: PRODUCT_INSIGHTS_SV
description: >
  Borrowell offers-marketplace funnel for product data science: impressions, clicks, applications,
  approvals and referral revenue (CAD), by offer, partner, surface, platform, member segment and experiment arm.
  Bots, internal test accounts and duplicate client events are already removed.
tables:
  - name: members
    description: Real Borrowell members (test accounts excluded), one row per member.
    base_table: {database: BORROWELL_AGENT_LAB, schema: LAB_DEMO, table: MEMBERS_V}
    primary_key: {columns: [member_id]}
    dimensions:
      - name: province
        synonyms: ["region"]
        expr: province
        data_type: VARCHAR
        sample_values: ["ON", "QC", "BC", "AB"]
      - name: score_band
        synonyms: ["credit score band", "credit tier"]
        description: Equifax score band - Poor, Fair, Good, Excellent.
        expr: score_band
        data_type: VARCHAR
        sample_values: ["Poor", "Fair", "Good", "Excellent"]
      - name: is_newcomer
        synonyms: ["newcomer to Canada"]
        expr: is_newcomer
        data_type: BOOLEAN
      - name: exp114_variant
        synonyms: ["experiment arm", "EXP-114 arm", "variant"]
        description: Arm of experiment EXP-114 (payout-ranked carousel) - control, treatment or not assigned.
        expr: exp114_variant
        data_type: VARCHAR
        sample_values: ["control", "treatment"]
    time_dimensions:
      - name: signup_date
        expr: signup_date
        data_type: DATE
    facts:
      - name: member_id
        expr: member_id
        data_type: NUMBER
  - name: offers
    description: Partner offers and their referral payout.
    base_table: {database: BORROWELL_AGENT_LAB, schema: LAB_DEMO, table: OFFERS_V}
    primary_key: {columns: [offer_id]}
    dimensions:
      - name: offer_name
        expr: offer_name
        data_type: VARCHAR
      - name: partner_name
        synonyms: ["partner", "lender"]
        expr: partner_name
        data_type: VARCHAR
      - name: product_type
        synonyms: ["product category"]
        expr: product_type
        data_type: VARCHAR
        sample_values: ["Credit Card", "Personal Loan", "Mortgage", "Auto Loan"]
    facts:
      - name: payout_cad
        description: Referral fee per approved application, CAD.
        expr: payout_cad
        data_type: NUMBER
  - name: events
    description: Offer telemetry - impressions, clicks, application starts and submits. Deduplicated.
    base_table: {database: BORROWELL_AGENT_LAB, schema: LAB_DEMO, table: OFFER_EVENTS_V}
    primary_key: {columns: [client_event_id]}
    dimensions:
      - name: event_type
        expr: event_type
        data_type: VARCHAR
        sample_values: ["offer_impression", "offer_click", "apply_start", "apply_submit"]
      - name: surface
        synonyms: ["placement", "channel"]
        expr: surface
        data_type: VARCHAR
        sample_values: ["dashboard", "offers_tab", "email", "push"]
      - name: platform
        expr: platform
        data_type: VARCHAR
        sample_values: ["ios", "android", "web"]
      - name: app_version
        expr: app_version
        data_type: VARCHAR
      - name: slot_position
        synonyms: ["carousel position", "rank"]
        expr: slot_position
        data_type: NUMBER
    time_dimensions:
      - name: event_date
        synonyms: ["date", "day"]
        expr: event_date
        data_type: DATE
    facts:
      - name: event_member_id
        expr: member_id
        data_type: NUMBER
      - name: event_offer_id
        expr: offer_id
        data_type: NUMBER
    metrics:
      - name: impressions
        synonyms: ["offer impressions", "views"]
        description: Distinct offer impressions.
        expr: COUNT(DISTINCT CASE WHEN event_type = 'offer_impression' THEN client_event_id END)
      - name: clicks
        synonyms: ["offer clicks"]
        expr: COUNT(DISTINCT CASE WHEN event_type = 'offer_click' THEN client_event_id END)
      - name: ctr
        synonyms: ["click-through rate", "click through rate", "offer CTR"]
        description: Offer click-through rate = distinct clicks / distinct impressions.
        expr: COUNT(DISTINCT CASE WHEN event_type = 'offer_click' THEN client_event_id END) / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'offer_impression' THEN client_event_id END), 0)
      - name: exposed_members
        synonyms: ["members who saw an offer", "reach"]
        expr: COUNT(DISTINCT CASE WHEN event_type = 'offer_impression' THEN member_id END)
  - name: applications
    description: Submitted applications and the partner decision. Revenue is earned only on approval.
    base_table: {database: BORROWELL_AGENT_LAB, schema: LAB_DEMO, table: APPLICATIONS_V}
    primary_key: {columns: [application_id]}
    dimensions:
      - name: decision
        expr: decision
        data_type: VARCHAR
        sample_values: ["approved", "declined"]
    time_dimensions:
      - name: submitted_date
        synonyms: ["application date"]
        expr: submitted_date
        data_type: DATE
    facts:
      - name: app_member_id
        expr: member_id
        data_type: NUMBER
      - name: app_offer_id
        expr: offer_id
        data_type: NUMBER
    metrics:
      - name: submitted_applications
        synonyms: ["applications"]
        expr: COUNT(application_id)
      - name: approved_applications
        synonyms: ["approvals"]
        expr: COUNT_IF(decision = 'approved')
      - name: approval_rate
        description: Approved / submitted applications.
        expr: COUNT_IF(decision = 'approved') / NULLIF(COUNT(application_id), 0)
      - name: referral_revenue
        synonyms: ["revenue", "referral fees"]
        description: Referral revenue in CAD, earned on approved applications.
        expr: SUM(referral_revenue_cad)
      - name: applying_members
        expr: COUNT(DISTINCT member_id)
relationships:
  - name: events_to_members
    left_table: events
    right_table: members
    relationship_columns: [{left_column: event_member_id, right_column: member_id}]
  - name: events_to_offers
    left_table: events
    right_table: offers
    relationship_columns: [{left_column: event_offer_id, right_column: offer_id}]
  - name: applications_to_members
    left_table: applications
    right_table: members
    relationship_columns: [{left_column: app_member_id, right_column: member_id}]
  - name: applications_to_offers
    left_table: applications
    right_table: offers
    relationship_columns: [{left_column: app_offer_id, right_column: offer_id}]
custom_instructions: >
  EXP-114 ran from 2026-08-15 to 2026-10-15; for EXP-114 questions filter event_date or submitted_date to that window
  and group by exp114_variant. Revenue is in CAD.
$$);

-- Session 2 checkpoint: governed weekly CTR is flat (~6%), so the late-September "drop" was a data issue
SELECT * FROM SEMANTIC_VIEW(PRODUCT_INSIGHTS_SV
  DIMENSIONS DATE_TRUNC('week', events.event_date) AS week
  METRICS events.impressions, events.clicks, events.ctr) ORDER BY week;

-- =============================================================================================
-- Session 3: Cortex Search over the product data science knowledge base
-- =============================================================================================
CREATE OR REPLACE CORTEX SEARCH SERVICE EXPERIMENT_DOCS_SEARCH
  ON body
  ATTRIBUTES doc_type, experiment_id, title
  WAREHOUSE = PI_LAB_WH
  TARGET_LAG = '1 day'
  AS SELECT doc_id, title, doc_type, experiment_id, updated_date, body FROM BORROWELL_AGENT_LAB.DATA.EXPERIMENT_DOCS;

SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW('BORROWELL_AGENT_LAB.LAB_DEMO.EXPERIMENT_DOCS_SEARCH',
  '{"query": "why did CTR drop in late September", "columns": ["title", "doc_type"], "limit": 3}')):results;

-- =============================================================================================
-- Session 4: the Product Insights agent (Analyst + Search)
-- =============================================================================================
CREATE OR REPLACE AGENT PRODUCT_INSIGHTS_AGENT
  COMMENT = 'Borrowell product data science agent: funnel, experiments, data issues (lab)'
  PROFILE = '{"display_name": "Product Insights Agent"}'
  FROM SPECIFICATION $$
{
  "models": {"orchestration": "claude-sonnet-4-5"},
  "instructions": {
    "orchestration": "You help Borrowell's product, marketing and data science teams understand the offers marketplace. Use funnel_metrics for any number (impressions, clicks, CTR, applications, approval rate, referral revenue, exposed members). Use experiment_knowledge for experiment briefs, metric definitions, guardrails and known data issues. For an experiment readout, get the brief first (window, primary metric, guardrails), then compare both arms on CTR, approval rate, referral revenue and revenue per exposed member (referral_revenue / exposed_members). When a metric moves suddenly, check experiment_knowledge for a known data issue before calling it real.",
    "response": "Lead with the answer in one or two sentences, then a compact table. Name the metrics and the date window. Revenue is CAD. Say whether a guardrail was breached. Never promise a member will be approved for a product.",
    "sample_questions": [
      {"question": "Read out EXP-114: did the payout-ranked carousel win?"},
      {"question": "Why did offer CTR drop in late September?"},
      {"question": "Which partners drive the most referral revenue per click?"}
    ]
  },
  "tools": [
    {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "funnel_metrics",
      "description": "Governed offers-marketplace metrics: impressions, clicks, CTR, exposed members, applications, approvals, approval rate, referral revenue (CAD), by date, offer, partner, product type, surface, platform, app version, province, score band, newcomer flag and EXP-114 arm."}},
    {"tool_spec": {"type": "cortex_search", "name": "experiment_knowledge",
      "description": "Product data science knowledge base: experiment briefs (EXP-114, EXP-121), metric definitions, known data issues (duplicate impressions, bots, test accounts), payout policy and how to read out an experiment."}}
  ],
  "tool_resources": {
    "funnel_metrics": {
      "semantic_view": "BORROWELL_AGENT_LAB.LAB_DEMO.PRODUCT_INSIGHTS_SV",
      "execution_environment": {"type": "warehouse", "warehouse": "PI_LAB_WH"}
    },
    "experiment_knowledge": {
      "search_service": "BORROWELL_AGENT_LAB.LAB_DEMO.EXPERIMENT_DOCS_SEARCH",
      "max_results": 4, "title_column": "title", "id_column": "doc_id"
    }
  }
}
$$;

-- =============================================================================================
-- Session 5: expose the agent to Workwell (MCP) - run tools/agent_eval.py for the eval
-- =============================================================================================
CREATE OR REPLACE MCP SERVER PRODUCT_INSIGHTS_MCP
  FROM SPECIFICATION $$
  tools:
    - title: "Borrowell product insights"
      name: "product_insights"
      type: "CORTEX_AGENT_RUN"
      identifier: "BORROWELL_AGENT_LAB.LAB_DEMO.PRODUCT_INSIGHTS_AGENT"
      description: "Governed answers about the offers funnel, experiments and known data issues. Read-only."
      annotations:
        readOnlyHint: true
        destructiveHint: false
        openWorldHint: false
  $$;
SHOW MCP SERVERS IN SCHEMA BORROWELL_AGENT_LAB.LAB_DEMO;

-- =============================================================================================
-- Session 5b: the eval caught a fan-out (events x applications) in the EXP-114 readout.
-- Fix it in the semantic layer: a member-grain readout table + an instruction. Then re-run the eval.
-- =============================================================================================
CREATE OR REPLACE VIEW EXP114_MEMBER_OUTCOMES_V COMMENT = 'EXP-114: one row per assigned member, outcomes in the window' AS
WITH e AS (
  SELECT member_id,
         COUNT_IF(event_type = 'offer_impression') AS impressions,
         COUNT_IF(event_type = 'offer_click') AS clicks
  FROM OFFER_EVENTS_V WHERE event_date BETWEEN '2026-08-15' AND '2026-10-15' GROUP BY 1),
a AS (
  SELECT member_id, COUNT(*) AS applications, COUNT_IF(decision = 'approved') AS approvals,
         SUM(referral_revenue_cad) AS referral_revenue_cad
  FROM APPLICATIONS_V WHERE submitted_date BETWEEN '2026-08-15' AND '2026-10-15' GROUP BY 1)
SELECT m.member_id, m.exp114_variant AS variant, m.score_band,
       COALESCE(e.impressions, 0) impressions, COALESCE(e.clicks, 0) clicks,
       COALESCE(a.applications, 0) applications, COALESCE(a.approvals, 0) approvals,
       COALESCE(a.referral_revenue_cad, 0) referral_revenue_cad
FROM MEMBERS_V m LEFT JOIN e ON e.member_id = m.member_id LEFT JOIN a ON a.member_id = m.member_id
WHERE m.exp114_variant IN ('control', 'treatment');

CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML('BORROWELL_AGENT_LAB.LAB_DEMO', $$
name: PRODUCT_INSIGHTS_SV
description: >
  Borrowell offers-marketplace funnel for product data science: impressions, clicks, applications,
  approvals and referral revenue (CAD), by offer, partner, surface, platform, member segment and experiment arm.
  Bots, internal test accounts and duplicate client events are already removed.
tables:
  - name: members
    description: Real Borrowell members (test accounts excluded), one row per member.
    base_table: {database: BORROWELL_AGENT_LAB, schema: LAB_DEMO, table: MEMBERS_V}
    primary_key: {columns: [member_id]}
    dimensions:
      - name: province
        synonyms: ["region"]
        expr: province
        data_type: VARCHAR
        sample_values: ["ON", "QC", "BC", "AB"]
      - name: score_band
        synonyms: ["credit score band", "credit tier"]
        description: Equifax score band - Poor, Fair, Good, Excellent.
        expr: score_band
        data_type: VARCHAR
        sample_values: ["Poor", "Fair", "Good", "Excellent"]
      - name: is_newcomer
        synonyms: ["newcomer to Canada"]
        expr: is_newcomer
        data_type: BOOLEAN
      - name: exp114_variant
        synonyms: ["experiment arm", "EXP-114 arm", "variant"]
        description: Arm of experiment EXP-114 (payout-ranked carousel) - control, treatment or not assigned.
        expr: exp114_variant
        data_type: VARCHAR
        sample_values: ["control", "treatment"]
    time_dimensions:
      - name: signup_date
        expr: signup_date
        data_type: DATE
    facts:
      - name: member_id
        expr: member_id
        data_type: NUMBER
  - name: offers
    description: Partner offers and their referral payout.
    base_table: {database: BORROWELL_AGENT_LAB, schema: LAB_DEMO, table: OFFERS_V}
    primary_key: {columns: [offer_id]}
    dimensions:
      - name: offer_name
        expr: offer_name
        data_type: VARCHAR
      - name: partner_name
        synonyms: ["partner", "lender"]
        expr: partner_name
        data_type: VARCHAR
      - name: product_type
        synonyms: ["product category"]
        expr: product_type
        data_type: VARCHAR
        sample_values: ["Credit Card", "Personal Loan", "Mortgage", "Auto Loan"]
    facts:
      - name: payout_cad
        description: Referral fee per approved application, CAD.
        expr: payout_cad
        data_type: NUMBER
  - name: events
    description: Offer telemetry - impressions, clicks, application starts and submits. Deduplicated.
    base_table: {database: BORROWELL_AGENT_LAB, schema: LAB_DEMO, table: OFFER_EVENTS_V}
    primary_key: {columns: [client_event_id]}
    dimensions:
      - name: event_type
        expr: event_type
        data_type: VARCHAR
        sample_values: ["offer_impression", "offer_click", "apply_start", "apply_submit"]
      - name: surface
        synonyms: ["placement", "channel"]
        expr: surface
        data_type: VARCHAR
        sample_values: ["dashboard", "offers_tab", "email", "push"]
      - name: platform
        expr: platform
        data_type: VARCHAR
        sample_values: ["ios", "android", "web"]
      - name: app_version
        expr: app_version
        data_type: VARCHAR
      - name: slot_position
        synonyms: ["carousel position", "rank"]
        expr: slot_position
        data_type: NUMBER
    time_dimensions:
      - name: event_date
        synonyms: ["date", "day"]
        expr: event_date
        data_type: DATE
    facts:
      - name: event_member_id
        expr: member_id
        data_type: NUMBER
      - name: event_offer_id
        expr: offer_id
        data_type: NUMBER
    metrics:
      - name: impressions
        synonyms: ["offer impressions", "views"]
        description: Distinct offer impressions.
        expr: COUNT(DISTINCT CASE WHEN event_type = 'offer_impression' THEN client_event_id END)
      - name: clicks
        synonyms: ["offer clicks"]
        expr: COUNT(DISTINCT CASE WHEN event_type = 'offer_click' THEN client_event_id END)
      - name: ctr
        synonyms: ["click-through rate", "click through rate", "offer CTR"]
        description: Offer click-through rate = distinct clicks / distinct impressions.
        expr: COUNT(DISTINCT CASE WHEN event_type = 'offer_click' THEN client_event_id END) / NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'offer_impression' THEN client_event_id END), 0)
      - name: exposed_members
        synonyms: ["members who saw an offer", "reach"]
        expr: COUNT(DISTINCT CASE WHEN event_type = 'offer_impression' THEN member_id END)
  - name: applications
    description: Submitted applications and the partner decision. Revenue is earned only on approval.
    base_table: {database: BORROWELL_AGENT_LAB, schema: LAB_DEMO, table: APPLICATIONS_V}
    primary_key: {columns: [application_id]}
    dimensions:
      - name: decision
        expr: decision
        data_type: VARCHAR
        sample_values: ["approved", "declined"]
    time_dimensions:
      - name: submitted_date
        synonyms: ["application date"]
        expr: submitted_date
        data_type: DATE
    facts:
      - name: app_member_id
        expr: member_id
        data_type: NUMBER
      - name: app_offer_id
        expr: offer_id
        data_type: NUMBER
    metrics:
      - name: submitted_applications
        synonyms: ["applications"]
        expr: COUNT(application_id)
      - name: approved_applications
        synonyms: ["approvals"]
        expr: COUNT_IF(decision = 'approved')
      - name: approval_rate
        description: Approved / submitted applications.
        expr: COUNT_IF(decision = 'approved') / NULLIF(COUNT(application_id), 0)
      - name: referral_revenue
        synonyms: ["revenue", "referral fees"]
        description: Referral revenue in CAD, earned on approved applications.
        expr: SUM(referral_revenue_cad)
      - name: applying_members
        expr: COUNT(DISTINCT member_id)
  - name: exp114
    description: >
      EXP-114 readout grain - one row per assigned member with their outcomes inside the experiment window
      (2026-08-15 to 2026-10-15). Use this table for any EXP-114 arm comparison; never join events to applications.
    base_table: {database: BORROWELL_AGENT_LAB, schema: LAB_DEMO, table: EXP114_MEMBER_OUTCOMES_V}
    primary_key: {columns: [member_id]}
    dimensions:
      - name: arm
        synonyms: ["experiment arm", "EXP-114 variant", "variant"]
        expr: variant
        data_type: VARCHAR
        sample_values: ["control", "treatment"]
    facts:
      - name: exp_member_id
        expr: member_id
        data_type: NUMBER
    metrics:
      - name: exp_assigned_members
        expr: COUNT(member_id)
      - name: exp_exposed_members
        expr: COUNT_IF(impressions > 0)
      - name: exp_ctr
        description: EXP-114 offer CTR = clicks / impressions within the window.
        expr: SUM(clicks) / NULLIF(SUM(impressions), 0)
      - name: exp_approval_rate
        expr: SUM(approvals) / NULLIF(SUM(applications), 0)
      - name: exp_referral_revenue
        expr: SUM(referral_revenue_cad)
      - name: exp_revenue_per_exposed_member
        synonyms: ["revenue per exposed member", "RPEM"]
        description: EXP-114 referral revenue (CAD) / members who saw at least one offer in the window.
        expr: SUM(referral_revenue_cad) / NULLIF(COUNT_IF(impressions > 0), 0)
relationships:
  - name: events_to_members
    left_table: events
    right_table: members
    relationship_columns: [{left_column: event_member_id, right_column: member_id}]
  - name: events_to_offers
    left_table: events
    right_table: offers
    relationship_columns: [{left_column: event_offer_id, right_column: offer_id}]
  - name: applications_to_members
    left_table: applications
    right_table: members
    relationship_columns: [{left_column: app_member_id, right_column: member_id}]
  - name: applications_to_offers
    left_table: applications
    right_table: offers
    relationship_columns: [{left_column: app_offer_id, right_column: offer_id}]
custom_instructions: >
  For any EXP-114 readout or arm comparison use only the exp114 table metrics (exp_ctr, exp_approval_rate,
  exp_referral_revenue, exp_revenue_per_exposed_member) grouped by arm. Never join events and applications in one
  query: they have different grains and inflate revenue. Revenue is in CAD.
$$);

SELECT * FROM SEMANTIC_VIEW(PRODUCT_INSIGHTS_SV DIMENSIONS exp114.arm
  METRICS exp114.exp_ctr, exp114.exp_approval_rate, exp114.exp_referral_revenue, exp114.exp_revenue_per_exposed_member);

-- =============================================================================================
-- Stretch: approval-aware offer ranking (expected revenue = P(approval) x payout)
-- =============================================================================================
-- Historical approval odds by score band and offer, from real applications
CREATE OR REPLACE TABLE APPROVAL_ODDS AS
SELECT m.score_band_idx, a.offer_id, COUNT(*) AS apps, AVG(IFF(a.decision = 'approved', 1, 0)) AS approval_rate
FROM APPLICATIONS_V a JOIN MEMBERS_V m ON m.member_id = a.member_id
WHERE a.submitted_date < '2026-08-15'          -- learn only from pre-experiment data
GROUP BY 1, 2;

-- Top-N offers for a member by expected revenue. Falls back to the band-gap prior when history is thin.
CREATE OR REPLACE FUNCTION RECOMMEND_OFFERS(P_MEMBER_ID NUMBER, P_TOP_N NUMBER)
RETURNS TABLE (rnk NUMBER, offer_id NUMBER, offer_name VARCHAR, partner_name VARCHAR, payout_cad FLOAT,
               approval_odds FLOAT, expected_revenue_cad FLOAT)
AS $$
  SELECT ROW_NUMBER() OVER (ORDER BY p * o.payout_cad DESC) rnk, o.offer_id, o.offer_name, o.partner_name, o.payout_cad::FLOAT,
         ROUND(p, 3)::FLOAT, ROUND(p * o.payout_cad, 2)::FLOAT
  FROM (SELECT o.*, m.score_band_idx,
               COALESCE(IFF(ao.apps >= 20, ao.approval_rate, NULL),
                        CASE WHEN m.score_band_idx - o.min_score_band_idx >= 1 THEN .78
                             WHEN m.score_band_idx - o.min_score_band_idx = 0 THEN .55
                             WHEN m.score_band_idx - o.min_score_band_idx = -1 THEN .08 ELSE .02 END) AS p
        FROM MEMBERS_V m CROSS JOIN OFFERS_V o
        LEFT JOIN APPROVAL_ODDS ao ON ao.score_band_idx = m.score_band_idx AND ao.offer_id = o.offer_id
        WHERE m.member_id = P_MEMBER_ID) o
  QUALIFY rnk <= P_TOP_N
$$;
SELECT * FROM TABLE(RECOMMEND_OFFERS(42, 3));

-- Agent custom tools call SCALAR functions, so wrap the table function: same rows, returned as a JSON array
CREATE OR REPLACE FUNCTION RECOMMEND_OFFERS_TOOL(P_MEMBER_ID NUMBER, P_TOP_N NUMBER) RETURNS ARRAY
  COMMENT = 'Agent tool wrapper: RECOMMEND_OFFERS rows as a JSON array'
  AS $$ SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*)) WITHIN GROUP (ORDER BY rnk) FROM TABLE(RECOMMEND_OFFERS(P_MEMBER_ID, P_TOP_N)) $$;
SELECT RECOMMEND_OFFERS_TOOL(42, 3);

-- Projected business outcome: expected revenue of the top-4 carousel under each policy, per score band mix
CREATE OR REPLACE VIEW RANKING_POLICY_COMPARISON AS
WITH odds AS (
  SELECT m.score_band_idx, o.offer_id, o.payout_cad,
         COALESCE(IFF(ao.apps >= 20, ao.approval_rate, NULL),
           CASE WHEN m.score_band_idx - o.min_score_band_idx >= 1 THEN .78 WHEN m.score_band_idx - o.min_score_band_idx = 0 THEN .55
                WHEN m.score_band_idx - o.min_score_band_idx = -1 THEN .08 ELSE .02 END) p
  FROM (SELECT DISTINCT score_band_idx FROM MEMBERS_V) m CROSS JOIN OFFERS_V o
  LEFT JOIN APPROVAL_ODDS ao ON ao.score_band_idx = m.score_band_idx AND ao.offer_id = o.offer_id),
ev AS (SELECT score_band_idx, offer_id, payout_cad, p, p * payout_cad ev,
              ROW_NUMBER() OVER (PARTITION BY score_band_idx ORDER BY p * payout_cad DESC) rnk FROM odds),
pol AS (
  SELECT policy, score_band_idx, offer_id, rnk FROM BORROWELL_AGENT_LAB.DATA.OFFER_RANKINGS WHERE rnk <= 4
  UNION ALL SELECT 'approval_aware', score_band_idx, offer_id, rnk FROM ev WHERE rnk <= 4),
mix AS (SELECT score_band_idx, COUNT(*) members FROM MEMBERS_V GROUP BY 1)
SELECT pol.policy,
       ROUND(SUM(ev.ev * mix.members) / SUM(mix.members), 2) AS expected_revenue_per_application_cad,
       ROUND(SUM(ev.p * mix.members) / SUM(mix.members), 3) AS avg_approval_odds
FROM pol JOIN ev ON ev.score_band_idx = pol.score_band_idx AND ev.offer_id = pol.offer_id
JOIN mix ON mix.score_band_idx = pol.score_band_idx
GROUP BY 1;
SELECT * FROM RANKING_POLICY_COMPARISON ORDER BY expected_revenue_per_application_cad DESC;

-- Give the agent the new tool
CREATE OR REPLACE AGENT PRODUCT_INSIGHTS_AGENT
  COMMENT = 'Borrowell product data science agent with approval-aware offer ranking (lab stretch)'
  PROFILE = '{"display_name": "Product Insights Agent"}'
  FROM SPECIFICATION $$
{
  "models": {"orchestration": "claude-sonnet-4-5"},
  "instructions": {
    "orchestration": "You help Borrowell's product, marketing and data science teams understand the offers marketplace. Use funnel_metrics for any number (impressions, clicks, CTR, applications, approval rate, referral revenue, exposed members). Use experiment_knowledge for experiment briefs, metric definitions, guardrails and known data issues. For an experiment readout, get the brief first (window, primary metric, guardrails), then compare both arms on CTR, approval rate, referral revenue and revenue per exposed member (referral_revenue / exposed_members). When a metric moves suddenly, check experiment_knowledge for a known data issue before calling it real. Use recommend_offers to rank offers for a member by expected revenue (approval odds x payout). Report its rows exactly as returned (offers, approval odds, expected revenue) and do not recompute them with funnel_metrics. To contrast with payout-only ranking, list the member's top offers by payout_cad without inventing approval odds.",
    "response": "Lead with the answer in one or two sentences, then a compact table. Name the metrics and the date window. Revenue is CAD. Say whether a guardrail was breached. Never promise a member will be approved for a product; describe approval odds as historical rates.",
    "sample_questions": [
      {"question": "Read out EXP-114: did the payout-ranked carousel win?"},
      {"question": "Why did offer CTR drop in late September?"},
      {"question": "Which 3 offers should we show member 42, and why?"}
    ]
  },
  "tools": [
    {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "funnel_metrics",
      "description": "Governed offers-marketplace metrics: impressions, clicks, CTR, exposed members, applications, approvals, approval rate, referral revenue (CAD), by date, offer, partner, product type, surface, platform, app version, province, score band, newcomer flag and EXP-114 arm."}},
    {"tool_spec": {"type": "cortex_search", "name": "experiment_knowledge",
      "description": "Product data science knowledge base: experiment briefs (EXP-114, EXP-121), metric definitions, known data issues (duplicate impressions, bots, test accounts), payout policy and how to read out an experiment."}},
    {"tool_spec": {"type": "generic", "name": "recommend_offers",
      "description": "Ranks partner offers for one member by expected referral revenue = historical approval odds for the member's score band x payout. Returns rank, offer, partner, payout, approval odds and expected revenue.",
      "input_schema": {"type": "object", "properties": {
        "p_member_id": {"type": "number", "description": "Borrowell member id"},
        "p_top_n": {"type": "number", "description": "How many offers to return, usually 3 or 4"}},
        "required": ["p_member_id", "p_top_n"]}}}
  ],
  "tool_resources": {
    "funnel_metrics": {
      "semantic_view": "BORROWELL_AGENT_LAB.LAB_DEMO.PRODUCT_INSIGHTS_SV",
      "execution_environment": {"type": "warehouse", "warehouse": "PI_LAB_WH"}
    },
    "experiment_knowledge": {
      "search_service": "BORROWELL_AGENT_LAB.LAB_DEMO.EXPERIMENT_DOCS_SEARCH",
      "max_results": 4, "title_column": "title", "id_column": "doc_id"
    },
    "recommend_offers": {
      "type": "function",
      "identifier": "BORROWELL_AGENT_LAB.LAB_DEMO.RECOMMEND_OFFERS_TOOL",
      "execution_environment": {"type": "warehouse", "warehouse": "PI_LAB_WH"}
    }
  }
}
$$;
