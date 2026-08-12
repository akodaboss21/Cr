# Carai Receptionist Environment Strategy

## Overview
This document outlines the environment management strategy for the Carai Receptionist project, ensuring consistency across development, testing, and production environments.

## Environment Variables
All environment-specific configurations are managed through `.env` files:

### Development
- `.env.example`: Base configuration with placeholder values
- `.env.local.example`: Local development overrides (e.g., localhost URLs)
- `.env.production.example`: Production-ready configuration

### Key Variables
| Variable          | Description                          | Required in All Environments |
|-------------------|--------------------------------------|------------------------------|
| `API_ENDPOINT`    | API service URL                      | Yes                          |
| `DATABASE_URL`    | Database connection string           | Yes                          |
| `SECRET_KEY`      | Application security key              | Yes                          |
| `ALLOWED_ORIGINS` | CORS allowed origins                 | Yes                          |
| `MAX_CONNECTIONS` | Database connection pool size        | Yes                          |

## Validation Strategy
Configuration validation is enforced via `config_validator.py`, which checks for required environment variables at startup. Missing variables trigger immediate failure with clear error messages.

## Environment-Specific Configuration
- **Development**: Uses `.env.local.example` for local testing
- **Production**: Uses `.env.production.example` with secure values
- **Staging**: Can be added similarly with `.env.staging.example`

## Best Practices
1. Never commit `.env` files to version control
2. Use `.env.example` as a template for new environments
3. Validate configuration on every deployment
4. Rotate secrets regularly in production

## Future Considerations
- Implement environment-specific feature flags
- Add automated environment validation checks
- Consider secret management tools for production