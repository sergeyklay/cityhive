-- PostgreSQL initialization script to enable PostGIS extension
-- This script will be run automatically when the container starts

-- Enable PostGIS extension for the default database
CREATE EXTENSION IF NOT EXISTS postgis;

-- Log that PostGIS has been enabled
DO $$
BEGIN
    RAISE NOTICE 'PostGIS extension enabled for database: %', current_database();
END $$;
