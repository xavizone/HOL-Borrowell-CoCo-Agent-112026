-- 00_admin_setup.sql - Borrowell Product Insights Agent lab: account objects
-- Run as ACCOUNTADMIN. Idempotent. ~10 s.
-- Creates: database BORROWELL_AGENT_LAB, warehouse PI_LAB_WH (10-credit monitor),
--          admin role PI_LAB_ADMIN, shared attendee role PI_LAB_ATTENDEE.
-- Co-authored with CoCo

USE ROLE ACCOUNTADMIN;
SET CURRENT_USER_FOR_LAB = CURRENT_USER();

CREATE ROLE IF NOT EXISTS PI_LAB_ADMIN    COMMENT = 'Owns the Borrowell Product Insights Agent lab';
CREATE ROLE IF NOT EXISTS PI_LAB_ATTENDEE COMMENT = 'Common grants for every lab attendee role';
GRANT ROLE PI_LAB_ADMIN    TO ROLE SYSADMIN;
GRANT ROLE PI_LAB_ATTENDEE TO ROLE PI_LAB_ADMIN;
GRANT ROLE PI_LAB_ADMIN    TO USER IDENTIFIER($CURRENT_USER_FOR_LAB);   -- set below

-- Warehouse + cost cap
CREATE WAREHOUSE IF NOT EXISTS PI_LAB_WH
  WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Borrowell Product Insights Agent lab';
CREATE RESOURCE MONITOR IF NOT EXISTS PI_LAB_MONITOR WITH CREDIT_QUOTA = 10
  TRIGGERS ON 80 PERCENT DO NOTIFY ON 100 PERCENT DO SUSPEND;
ALTER WAREHOUSE PI_LAB_WH SET RESOURCE_MONITOR = PI_LAB_MONITOR;
GRANT USAGE, OPERATE ON WAREHOUSE PI_LAB_WH TO ROLE PI_LAB_ADMIN;
GRANT USAGE ON WAREHOUSE PI_LAB_WH TO ROLE PI_LAB_ATTENDEE;

-- Lab database (owned by the admin role so teardown is one DROP DATABASE)
CREATE DATABASE IF NOT EXISTS BORROWELL_AGENT_LAB
  COMMENT = 'Borrowell Product Insights Agent hands-on lab (synthetic telemetry, no real member data)';
GRANT OWNERSHIP ON DATABASE BORROWELL_AGENT_LAB TO ROLE PI_LAB_ADMIN COPY CURRENT GRANTS;
GRANT CREATE ROLE ON ACCOUNT TO ROLE PI_LAB_ADMIN;          -- per-attendee roles
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE PI_LAB_ADMIN;        -- grant attendee roles to users

-- Cortex: agents, Analyst, Search, AI functions
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE PI_LAB_ATTENDEE;

-- Pre-flight (record the results on the "Before you start" checklist)
SELECT CURRENT_ACCOUNT(), CURRENT_REGION();
SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;   -- Azure Canada Central: claude models need cross-region
SHOW CORTEX BASE MODELS;                                          -- confirm claude-sonnet-4-5 (or the model you pick) is listed

-- Next: 01_data.sql (as PI_LAB_ADMIN), then 02_attendee_procs.sql
