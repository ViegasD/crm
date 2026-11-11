-- Creates extra databases on first postgres init (only runs on a fresh volume)
SELECT 'CREATE DATABASE evolution OWNER crm'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evolution')\gexec
