-- 98_teardown.sql - remove everything the lab created. Run as ACCOUNTADMIN from a warehouse other than PI_LAB_WH.
-- Co-authored with CoCo
USE ROLE ACCOUNTADMIN;
-- Drop attendee roles listed in the roster before the database goes
EXECUTE IMMEDIATE $$
DECLARE c CURSOR FOR SELECT role_name FROM BORROWELL_AGENT_LAB.ADMIN.ROSTER;
BEGIN
  FOR r IN c DO
    LET rl VARCHAR := r.role_name;
    EXECUTE IMMEDIATE 'DROP ROLE IF EXISTS ' || rl;
  END FOR;
  RETURN 'attendee roles dropped';
END;
$$;
DROP DATABASE IF EXISTS BORROWELL_AGENT_LAB;
DROP WAREHOUSE IF EXISTS PI_LAB_WH;
DROP RESOURCE MONITOR IF EXISTS PI_LAB_MONITOR;
DROP ROLE IF EXISTS PI_LAB_ATTENDEE;
DROP ROLE IF EXISTS PI_LAB_ADMIN;
