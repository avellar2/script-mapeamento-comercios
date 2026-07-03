# Taste (Continuously Learned by [CommandCode][cmd])

[cmd]: https://commandcode.ai/

# infrastructure
- Prefer Supabase CLI over Docker for local PostgreSQL setup. Confidence: 0.70

# postgres
- Never add 'extensions' to search_path in SECURITY DEFINER functions. Instead schema-qualify pgcrypto calls (e.g., extensions.digest(), extensions.gen_random_uuid()) and keep search_path as 'pg_catalog, public'. Confidence: 0.85


