# 🔄 Feature Development Workflow

Quick checklist and workflow for adding features to AstroBot.

---

## 📝 Before You Start

1. **Understand the feature** - What does it do? Who uses it?
2. **Identify the layers** - Which parts of the stack need changes?
3. **Check existing patterns** - Look at similar features in the code

---

## 🚦 Feature Development Checklist

### Planning
- [ ] Feature requirements clear
- [ ] Identified all files to modify
- [ ] Checked for similar existing code to reference

### Backend (Python)
- [ ] Added endpoint to `api_server.py`
- [ ] Added request/response models (if needed)
- [ ] Added database functions (if needed)
- [ ] Added business logic in appropriate module
- [ ] Error handling with proper HTTP codes
- [ ] Tested with curl

### Backend (Spring Boot)
- [ ] Added Controller class (if new feature area)
- [ ] Added PythonApiService methods
- [ ] Added DTOs (if needed)
- [ ] Tested through proxy

### Frontend (React)
- [ ] Added api.js functions
- [ ] Created page component
- [ ] Added route in App.jsx
- [ ] Added navigation link
- [ ] Error handling in UI
- [ ] Loading states work

### Testing
- [ ] Python API starts without errors
- [ ] Spring Boot compiles and starts
- [ ] React builds without warnings
- [ ] Feature works end-to-end
- [ ] Error cases handled gracefully
- [ ] No console errors

### Documentation
- [ ] Updated relevant docs (if API changed)
- [ ] Added comments for complex logic
- [ ] Updated CHANGELOG.md

---

## 🏃 Quick Commands

```bash
# Start all servers
.\start-all-servers.bat

# Test Python endpoint
curl http://localhost:8001/api/your-endpoint

# Test through Spring Boot
curl http://localhost:8080/api/your-endpoint

# Check logs
Get-Content logs/app.log -Tail 50

# Check running ports
netstat -ano | findstr "8001 8080 3000"
```

---

## 🗂️ File Locations by Feature Type

### API Endpoint
```
api_server.py                                    # FastAPI endpoint
springboot-backend/.../controller/XController.java  # Spring controller
springboot-backend/.../service/PythonApiService.java # Add method
react-frontend/src/services/api.js               # Add function
```

### Database Feature
```
database/db.py                                   # Table + CRUD
api_server.py                                    # API endpoint
```

### Document Processing
```
ingestion/parser.py                              # Parse new format
ingestion/chunker.py                             # Chunk text
ingestion/embedder.py                            # Store vectors
```

### LLM Provider
```
rag/providers/new_provider.py                    # Provider class
rag/providers/manager.py                         # Register provider
config.py                                        # Config vars
.env                                             # API keys
```

### UI Page
```
react-frontend/src/pages/NewPage.jsx             # Page component
react-frontend/src/App.jsx                       # Add route
react-frontend/src/components/Sidebar.jsx        # Nav link
```

---

## 💡 Tips

1. **Copy existing patterns** - Don't reinvent; copy from similar features
2. **Test at each layer** - Test Python alone, then Spring Boot, then React
3. **Check error handling** - Test what happens when things fail
4. **Use browser dev tools** - Network tab shows exact requests/responses
5. **Read the logs** - Python logs are your friend

---

## ⚠️ Common Mistakes

| Mistake | How to Avoid |
|---------|--------------|
| Forgetting Spring Boot proxy | Always add PythonApiService method |
| Missing error handling | Use try/except with HTTPException |
| Wrong HTTP method | Match React, Spring, Python methods |
| Forgot to restart servers | Python auto-reloads; Spring Boot needs restart |
| CORS issues | Check allowed origins in both backends |

---

## 📞 Need Help?

1. **Check existing code** for patterns
2. **Read error messages** carefully
3. **Check browser Network tab** for request/response details
4. **Check Python logs** in `logs/` folder
5. **Refer to CONTRIBUTING.md** for detailed guides
