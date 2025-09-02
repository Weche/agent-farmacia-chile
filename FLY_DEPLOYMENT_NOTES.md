# Fly.io Deployment Configuration for Pharmacy Finder

## Environment Variables for Production

# Add these to your fly.toml or set via fly secrets

[env]
  APP_NAME = "Farmacias Chile"
  ENV = "production"
  
  # Redis (use Fly Redis or Upstash)
  REDIS_URL = "redis://your-redis-instance"
  
  # APIs - Set via fly secrets set
  # fly secrets set OPENAI_API_KEY="your-key"
  # fly secrets set GOOGLE_MAPS_API_KEY="your-key"
  # fly secrets set ANTHROPIC_API_KEY="your-key"

## Dependencies Check
- ✅ SQLite database (included in container)
- ✅ Google Maps API (external service)
- ✅ OpenAI API (external service)
- ⚠️ Redis (needs external instance)

## Resource Requirements
- Memory: 512MB - 1GB (depending on usage)
- CPU: 1 shared CPU sufficient for MVP
- Storage: 1GB for SQLite database and assets

## Scaling Considerations
- Horizontal scaling: ✅ Stateless design
- Database: SQLite works for single instance
- Cache: Redis required for multi-instance
- Sessions: Redis-backed, scales well

## Security Notes
- API keys via Fly secrets
- HTTPS enforced
- Environment isolation
- Database included in container (no external DB needed)
