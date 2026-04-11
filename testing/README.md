# 🧪 AstroBot Testing Suite

Comprehensive testing framework for the AstroBot v2.0 project.

**Total Test Coverage Target:** 80%+ across all layers

---

## 📁 Directory Structure

```
testing/
├── README.md (you are here)
├── setup.py (test configuration)
├── pytest.ini (pytest config)
│
├── backend/
│   ├── conftest.py (pytest fixtures)
│   ├── fixtures/ (test data)
│   │   ├── documents.py
│   │   ├── users.py
│   │   └── mocks.py
│   │
│   ├── test_auth.py (130+ tests)
│   ├── test_chat.py (100+ tests)
│   ├── test_documents.py (80+ tests)
│   ├── test_rag_pipeline.py (90+ tests)
│   ├── test_providers.py (70+ tests)
│   ├── test_database.py (60+ tests)
│   └── test_rate_limiting.py (50+ tests)
│
├── frontend/
│   ├── jest.config.js (Jest configuration)
│   ├── setup.js (test setup)
│   │
│   ├── components/
│   │   ├── __tests__/
│   │   │   ├── Button.test.jsx
│   │   │   ├── Input.test.jsx
│   │   │   ├── Card.test.jsx
│   │   │   ├── Modal.test.jsx
│   │   │   └── ... (8 more UI components)
│   │
│   ├── pages/
│   │   ├── __tests__/
│   │   │   ├── LoginPage.test.jsx
│   │   │   ├── ChatPage.test.jsx
│   │   │   └── admin/
│   │   │       ├── AnalyticsPage.test.jsx
│   │   │       ├── DocumentsPage.test.jsx
│   │   │       ├── UsersPage.test.jsx
│   │   │       └── ... (4 more admin pages)
│   │
│   ├── services/
│   │   ├── __tests__/
│   │   │   └── api.test.js (API client mock tests)
│   │
│   └── hooks/
│       ├── __tests__/
│       │   ├── useAuth.test.js
│       │   └── ... (other custom hooks)
│
├── integration/
│   ├── e2e_chat_flow.py (End-to-end tests)
│   ├── e2e_document_pipeline.py (Document upload → embed → retrieve)
│   ├── e2e_provider_fallback.py (Multi-provider fallback chain)
│   ├── e2e_voice_pipeline.py (Voice recording → transcription)
│   └── e2e_authentication_flow.py (Login → chat → logout)
│
├── performance/
│   ├── load_test.py (PyTest-based load testing)
│   ├── stress_test.py (Stress testing)
│   └── benchmark.py (Performance benchmarking)
│
├── utils/
│   ├── test_helpers.py (Shared test utilities)
│   ├── mocks.py (Mock objects)
│   ├── data_factory.py (Test data generation)
│   └── api_client.py (Test API client)
│
├── docker/
│   ├── Dockerfile.test (Test environment)
│   └── docker-compose.test.yml (Test orchestration)
│
└── scripts/
    ├── run_all_tests.sh (Run all tests)
    ├── run_backend_tests.sh (Backend only)
    ├── run_frontend_tests.sh (Frontend only)
    ├── run_integration_tests.sh (Integration only)
    ├── coverage_report.sh (Generate coverage)
    └── ci_tests.sh (CI/CD pipeline tests)
```

---

## 🚀 Quick Start

### Backend Tests (Python/pytest)

```bash
# Install test dependencies
pip install -r requirements.txt pytest pytest-cov pytest-asyncio pytest-mock

# Run all backend tests
pytest testing/backend/

# Run with coverage
pytest testing/backend/ --cov=. --cov-report=html

# Run specific test file
pytest testing/backend/test_auth.py

# Run specific test
pytest testing/backend/test_auth.py::test_login_success

# Run in verbose mode
pytest testing/backend/ -v

# Run with markers
pytest testing/backend/ -m "not slow"
```

### Frontend Tests (JavaScript/Jest)

```bash
# Install test dependencies
npm install --save-dev jest @testing-library/react @testing-library/jest-dom @babel/preset-react

# Run all frontend tests
npm run test:frontend

# Run with coverage
npm run test:frontend -- --coverage

# Run specific test file
npm test components/Button.test.jsx

# Run in watch mode
npm run test:frontend -- --watch

# Update snapshots
npm run test:frontend -- -u
```

### Integration Tests

```bash
# Run all integration tests
pytest testing/integration/ -v

# Run specific integration test
pytest testing/integration/e2e_chat_flow.py -v

# Run with slowest tests first
pytest testing/integration/ --durations=10
```

---

## 📊 Test Categories

### Backend Tests (500+ test cases total)

#### Authentication (test_auth.py) - 130 tests
- ✅ Login with valid credentials
- ✅ Login with invalid credentials
- ✅ Password hashing and verification
- ✅ JWT token generation and validation
- ✅ Token expiration
- ✅ Token refresh
- ✅ Role-based access control (admin/faculty/student)
- ✅ Logout and token blacklist
- ✅ Registration with validation
- ✅ Password reset flow

#### Chat Endpoint (test_chat.py) - 100 tests
- ✅ Chat endpoint responses
- ✅ Message formatting
- ✅ Context handling
- ✅ Error responses
- ✅ Rate limiting on chat
- ✅ Authorization checks
- ✅ Input validation
- ✅ Streaming responses
- ✅ Conversation history

#### Document Processing (test_documents.py) - 80 tests
- ✅ File upload (various formats)
- ✅ File validation
- ✅ File size limits
- ✅ Chunking logic
- ✅ Embedding generation
- ✅ Document metadata
- ✅ Duplicate detection
- ✅ Deletion and cleanup

#### RAG Pipeline (test_rag_pipeline.py) - 90 tests
- ✅ Document retrieval accuracy
- ✅ Semantic search ranking
- ✅ Response generation
- ✅ Context window management
- ✅ Conversation memory
- ✅ Query preprocessing
- ✅ Answer formatting

#### LLM Providers (test_providers.py) - 70 tests
- ✅ Ollama provider integration
- ✅ Groq provider integration
- ✅ Gemini provider integration
- ✅ Provider fallback chain
- ✅ Error handling per provider
- ✅ Token counting
- ✅ Model switching

#### Database (test_database.py) - 60 tests
- ✅ Connection pooling
- ✅ CRUD operations
- ✅ Query performance
- ✅ Transaction handling
- ✅ Index usage
- ✅ Constraint validation
- ✅ Migration testing

#### Rate Limiting (test_rate_limiting.py) - 50 tests
- ✅ Per-endpoint limits
- ✅ Per-user limits
- ✅ Global limits
- ✅ Limit reset
- ✅ Admin override

---

### Frontend Tests (300+ test cases total)

#### UI Components (test files in components/__tests__/) - 120 tests
- Button.test.jsx - 12 tests
- Input.test.jsx - 15 tests
- Card.test.jsx - 10 tests
- Modal.test.jsx - 15 tests
- Badge.test.jsx - 8 tests
- Spinner.test.jsx - 8 tests
- Alert.test.jsx - 12 tests
- Avatar.test.jsx - 10 tests
- Select.test.jsx - 15 tests
- Tabs.test.jsx - 15 tests

#### Pages (test files in pages/__tests__/) - 80 tests
- LoginPage.test.jsx - 20 tests (login, error handling, form validation)
- ChatPage.test.jsx - 30 tests (message display, input, API integration)
- Admin pages (50 tests total) - AnalyticsPage, DocumentsPage, UsersPage, etc.

#### Services (test files in services/__tests__/) - 50 tests
- api.test.js - API client mocking and integration

#### Hooks (test files in hooks/__tests__/) - 50 tests
- useAuth.test.js - 20 tests
- Custom hooks - 30 tests

---

### Integration Tests (150+ test cases)

#### End-to-End Flows
1. **Chat Flow** (e2e_chat_flow.py) - 40 tests
   - Upload document → Embed → Query → Get response
   - Multi-turn conversation
   - Context preservation

2. **Document Pipeline** (e2e_document_pipeline.py) - 30 tests
   - File upload (all formats)
   - Parsing & chunking
   - Embedding generation
   - Vector DB storage

3. **Provider Fallback** (e2e_provider_fallback.py) - 35 tests
   - Ollama → Groq → Gemini chain
   - Error recovery
   - Performance comparison

4. **Voice Pipeline** (e2e_voice_pipeline.py) - 25 tests
   - Audio recording
   - Transcription
   - Integration with chat

5. **Auth Flow** (e2e_authentication_flow.py) - 20 tests
   - Registration
   - Login
   - Chat access
   - Logout

---

### Performance Tests

#### Load Testing (performance/load_test.py)
```python
- Concurrent users: 10, 50, 100
- Request rate: 1-100 req/sec
- Response time targets: <500ms
- Throughput targets: >100 req/sec
```

#### Stress Testing (performance/stress_test.py)
```python
- Peak load: 500 concurrent users
- Memory usage monitoring
- Database connection pool stress
- Vector search scale testing
```

#### Benchmarking (performance/benchmark.py)
```python
- API endpoint latency
- RAG retrieval speed
- LLM response time
- Database query performance
```

---

## 🔧 Test Configuration Files

### pytest.ini
```ini
[pytest]
testpaths = testing/backend testing/integration
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: marks tests as slow
    integration: marks tests as integration
    unit: marks tests as unit
```

### jest.config.js (Frontend)
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/testing/frontend/setup.js'],
  moduleNameMapper: {
    '\\.(css|less|scss)$': 'identity-obj-proxy',
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/index.jsx',
    '!src/main.jsx',
  ],
  coverageThreshold: {
    global: {
      branches: 60,
      functions: 60,
      lines: 60,
      statements: 60,
    },
  },
};
```

---

## 📈 Coverage Targets

| Layer | Target | Current | Gap |
|-------|--------|---------|-----|
| Backend (Python) | 85% | ~20% | -65% |
| Frontend (React) | 80% | ~0% | -80% |
| Integration | 70% | ~0% | -70% |
| **Overall** | **80%** | **~15%** | **-65%** |

---

## ✅ Prerequisites

### Backend Requirements
```bash
# From requirements.txt
pytest==7.4.0
pytest-cov==4.1.0
pytest-asyncio==0.21.0
pytest-mock==3.11.1
httpx==0.24.0
factory-boy==3.3.0
faker==19.0.0
```

### Frontend Requirements
```bash
# Add to package.json devDependencies
jest@^29
@testing-library/react@^14
@testing-library/jest-dom@^6
@testing-library/user-event@^14
babel-jest@^29
identity-obj-proxy@^3
```

---

## 🎯 How to Run Tests

### All Tests
```bash
npm run test:all          # Runs all tests (frontend + backend)
```

### Backend Only
```bash
pytest testing/backend/ --cov --cov-report=html
```

### Frontend Only
```bash
npm run test:frontend -- --coverage
```

### Integration Only
```bash
pytest testing/integration/ -v
```

### Performance Tests
```bash
pytest testing/performance/ -v
```

### With Docker
```bash
docker-compose -f testing/docker/docker-compose.test.yml up
```

---

## 📝 Writing Tests

### Backend Test Example (pytest)

```python
# testing/backend/test_auth.py
import pytest
from app.auth.auth import hash_password, verify_password

class TestAuthentication:
    def test_hash_password_success(self):
        password = "secure_pass_123"
        hashed = hash_password(password)
        assert hashed != password

    def test_verify_password_success(self):
        password = "secure_pass_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) == True
```

### Frontend Test Example (Jest)

```javascript
// src/components/__tests__/Button.test.jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Button from '../Button';

describe('Button Component', () => {
  it('renders with text', () => {
    render(<Button>Click Me</Button>);
    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  it('handles click events', async () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    await userEvent.click(screen.getByText('Click'));
    expect(handleClick).toHaveBeenCalled();
  });
});
```

---

## 🚨 Test Status

| Category | Count | Status |
|----------|-------|--------|
| Backend Tests | 500+ | 📝 To be created |
| Frontend Tests | 300+ | 📝 To be created |
| Integration Tests | 150+ | 📝 To be created |
| Performance Tests | 100+ | 📝 To be created |
| **TOTAL** | **1050+** | **📝 To be created** |

---

## 🔍 Continuous Integration

Tests run automatically on:
- ✅ Every git push (via GitHub Actions)
- ✅ Every pull request
- ✅ Before merge to main
- ✅ Nightly full test suite

See `.github/workflows/test.yml` for CI configuration.

---

## 📊 Coverage Reports

After running tests with coverage:

```bash
# Generate HTML report
pytest testing/backend/ --cov=. --cov-report=html
open htmlcov/index.html

# Or for frontend
npm run test:frontend -- --coverage
open coverage/lcov-report/index.html
```

---

## 🐛 Debugging Tests

### Backend (pytest)
```bash
# Drop into debugger on failure
pytest testing/backend/ --pdb

# Show print statements
pytest testing/backend/ -s

# Stop on first failure
pytest testing/backend/ -x
```

### Frontend (Jest)
```bash
# Debug mode
node --inspect-brk node_modules/.bin/jest --runInBand

# Watch mode for development
npm test -- --watch

# Show coverage for specific file
npm test -- Button.test.jsx --coverage
```

---

## 📚 Resources

- [pytest documentation](https://docs.pytest.org/)
- [Jest documentation](https://jestjs.io/)
- [Testing Library docs](https://testing-library.com/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [React Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

---

## ✍️ Contributing Tests

When adding new features:

1. Write tests FIRST (TDD approach)
2. Ensure all tests pass locally
3. Push tests along with feature code
4. Maintain 80%+ coverage
5. Update this README if adding new test categories

---

**Last Updated:** April 11, 2026
**Test Framework:** pytest (backend) + Jest (frontend)
**Target Coverage:** 80%+
**Status:** Framework ready, test suite in progress
