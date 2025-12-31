# 🚀 Cugar Agent - Quick Start Guide

Welcome to Cugar Agent! This guide will get you up and running in minutes.

## 📋 Table of Contents

- [Immediate Onboarding](#immediate-onboarding)
- [5-Minute Setup](#5-minute-setup)
- [Essential Commands](#essential-commands)
- [Common Workflows](#common-workflows)
- [Troubleshooting](#troubleshooting)

---

## Immediate Onboarding

### What is Cugar Agent?

Cugar Agent is a powerful tool designed to [describe your agent's purpose here]. It enables developers to [key functionality] and streamlines [main use cases].

### Prerequisites

Before you begin, ensure you have:

- **Node.js** v16+ or **Python** 3.8+ (depending on your implementation)
- **Git** installed
- A terminal/command line interface
- Basic understanding of [your platform/framework]

### Key Resources

- 📖 [Full Documentation](./docs)
- 🐛 [Report Issues](https://github.com/TylrDn/cugar-agent/issues)
- 💬 [Discussions & Support](https://github.com/TylrDn/cugar-agent/discussions)
- 📝 [Changelog](./CHANGELOG.md)

---

## 5-Minute Setup

### Step 1: Clone the Repository (1 min)

```bash
git clone https://github.com/TylrDn/cugar-agent.git
cd cugar-agent
```

### Step 2: Install Dependencies (2 min)

**For Node.js projects:**
```bash
npm install
# or
yarn install
```

**For Python projects:**
```bash
pip install -r requirements.txt
# or
pip install -e .
```

### Step 3: Configuration (1 min)

```bash
# Copy the example configuration
cp .env.example .env

# Edit with your settings
nano .env  # or use your preferred editor
```

### Step 4: Verify Installation (1 min)

```bash
# Check version
cugar-agent --version

# Run a test
npm test  # or pytest
```

✅ **You're ready to go!**

---

## Essential Commands

### Basic Operations

```bash
# Initialize a new project
cugar-agent init [project-name]

# Start the agent
cugar-agent start

# Stop the agent
cugar-agent stop

# Check status
cugar-agent status

# View help
cugar-agent --help
```

### Development Commands

```bash
# Run in development mode
npm run dev  # or python -m cugar_agent.dev

# Build for production
npm run build  # or python setup.py build

# Run tests
npm test  # or pytest

# Lint code
npm run lint  # or flake8 .

# Format code
npm run format  # or black .
```

### Configuration & Debugging

```bash
# View current configuration
cugar-agent config show

# Update configuration
cugar-agent config set [key] [value]

# Enable debug logging
DEBUG=cugar-agent:* cugar-agent start

# View logs
cugar-agent logs --tail 50
```

---

## Common Workflows

### Workflow 1: Setting Up Your First Agent

```bash
# 1. Initialize project
cugar-agent init my-first-agent

# 2. Navigate to project
cd my-first-agent

# 3. Review the generated config
cat .env

# 4. Start the agent
cugar-agent start

# 5. Test with a simple command
curl http://localhost:3000/health
```

### Workflow 2: Creating a Custom Integration

```bash
# 1. Create a new integration file
touch src/integrations/my-service.js  # or .py

# 2. Implement your integration
# See docs/INTEGRATIONS.md for the template

# 3. Register the integration
# Update config/integrations.json

# 4. Test your integration
npm test -- src/integrations/my-service.test.js

# 5. Deploy
npm run deploy
```

### Workflow 3: Debugging Issues

```bash
# 1. Enable debug mode
DEBUG=cugar-agent:* cugar-agent start

# 2. Check logs
cugar-agent logs --filter ERROR

# 3. Test connectivity
cugar-agent health-check

# 4. Review configuration
cugar-agent config show

# 5. Check logs for specific module
DEBUG=cugar-agent:database cugar-agent start
```

### Workflow 4: Updating & Upgrading

```bash
# Check for updates
cugar-agent update --check

# Update to latest version
npm update cugar-agent  # or pip install --upgrade cugar-agent

# Update dependencies
npm update  # or pip install --upgrade -r requirements.txt

# Verify upgrade
cugar-agent --version
```

### Workflow 5: Deploying to Production

```bash
# 1. Build the project
npm run build  # or python setup.py build

# 2. Run tests
npm test  # or pytest

# 3. Create environment file
cp .env.example .env.production

# 4. Configure for production
# Edit .env.production with production settings

# 5. Start with production config
NODE_ENV=production npm start

# 6. Verify deployment
curl https://your-production-url/health
```

---

## Troubleshooting

### Common Issues & Solutions

#### ❌ **Issue: "Module not found" error**

**Solution:**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Or for Python
pip install --force-reinstall -r requirements.txt
```

#### ❌ **Issue: Port already in use**

**Solution:**
```bash
# Find what's using the port (replace 3000 with your port)
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows

# Kill the process or change port in .env
PORT=3001 cugar-agent start
```

#### ❌ **Issue: Environment variables not loading**

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check file is readable
cat .env

# Ensure correct format (KEY=VALUE)
# Try with explicit path
source .env && cugar-agent start  # Linux/macOS
```

#### ❌ **Issue: Configuration validation fails**

**Solution:**
```bash
# Validate configuration
cugar-agent config validate

# Check required environment variables
cugar-agent config show --required

# Review example configuration
cat .env.example

# Compare your config with example
diff .env .env.example
```

#### ❌ **Issue: Connection/Network errors**

**Solution:**
```bash
# Test connectivity
ping your-service-url

# Check firewall settings
sudo ufw status  # Linux

# Verify API endpoints
cugar-agent health-check --verbose

# Test with verbose logging
DEBUG=cugar-agent:* cugar-agent start --verbose
```

#### ❌ **Issue: Agent crashes on startup**

**Solution:**
```bash
# 1. Check logs for errors
cugar-agent logs --all

# 2. Verify all required services are running
cugar-agent status --all

# 3. Clear cache and restart
rm -rf .cache
cugar-agent start

# 4. Reset to default config (backup first!)
cp .env .env.backup
cp .env.example .env
cugar-agent start
```

#### ❌ **Issue: Tests failing locally**

**Solution:**
```bash
# Clear test cache
npm test -- --clearCache  # or pytest --cache-clear

# Run tests with verbose output
npm test -- --verbose  # or pytest -v

# Run specific test file
npm test -- src/__tests__/specific.test.js

# Check test environment setup
cat .env.test
```

### Getting More Help

- **Check logs:** `cugar-agent logs --tail 100`
- **Enable debug mode:** `DEBUG=cugar-agent:* cugar-agent start`
- **Review documentation:** See `/docs` folder
- **Search issues:** https://github.com/TylrDn/cugar-agent/issues
- **Ask in discussions:** https://github.com/TylrDn/cugar-agent/discussions
- **Report bugs:** Create a new issue with:
  - Your OS and Node/Python version
  - Steps to reproduce
  - Full error logs
  - Configuration (without secrets)

---

## Next Steps

1. ✅ Complete the 5-Minute Setup above
2. 📖 Read the [full documentation](./docs)
3. 🔧 Explore the [examples](./examples) folder
4. 🚀 Try a [common workflow](#common-workflows)
5. 💡 Check out [best practices](./docs/BEST_PRACTICES.md)

---

## Quick Links

| Resource | Link |
|----------|------|
| GitHub Repository | https://github.com/TylrDn/cugar-agent |
| Documentation | [./docs](./docs) |
| Examples | [./examples](./examples) |
| Issues | https://github.com/TylrDn/cugar-agent/issues |
| Discussions | https://github.com/TylrDn/cugar-agent/discussions |
| License | [./LICENSE](./LICENSE) |

---

**Happy coding! 🎉 If you have feedback on this guide, please [let us know](https://github.com/TylrDn/cugar-agent/discussions).**
