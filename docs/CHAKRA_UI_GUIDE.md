# 🎨 Chakra UI Interface - Modern React Frontend

Beautiful, modern interface built with React and Chakra UI for your Milvus AI data management system.

## ✨ What's New?

- 🎨 **Modern Design** - Built with Chakra UI component library
- ⚡ **Fast & Responsive** - React-powered single-page application
- 🌈 **Gradient Theme** - Beautiful purple gradient design
- 📱 **Mobile Friendly** - Responsive design works on all devices
- 🎯 **Smooth Animations** - Framer Motion for silky transitions
- 🔥 **Better UX** - Improved user experience with loading states

## 🚀 Quick Start

### Option 1: One-Command Start
```bash
cd "/Users/komaragiri.satyadev/Desktop/Personal Projects/Sonatype-Personal"
./start-chakra-ui.sh
```

### Option 2: Manual Start

**Terminal 1 - Start Milvus:**
```bash
cd "/Users/komaragiri.satyadev/Desktop/Personal Projects/Sonatype-Personal"
./milvus.sh start
```

**Terminal 2 - Start Flask Backend:**
```bash
cd "/Users/komaragiri.satyadev/Desktop/Personal Projects/Sonatype-Personal"
source venv/bin/activate
python web_interface.py
```

**Terminal 3 - Start React Frontend:**
```bash
cd "/Users/komaragiri.satyadev/Desktop/Personal Projects/Sonatype-Personal/frontend"
npm start
```

**Terminal 4 (Optional) - Start Ollama:**
```bash
ollama serve
```

## 🌐 Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Chakra UI Frontend** | **http://localhost:3000** | Main interface (React) |
| Flask Backend API | http://localhost:5000 | REST API |
| Milvus Database | localhost:19530 | Vector DB |
| Ollama AI | http://localhost:11434 | AI reasoning |

**👉 Open your browser to: http://localhost:3000**

## 📦 Tech Stack

```
┌─────────────────────────────────────┐
│   React + Chakra UI (Port 3000)    │  ← Beautiful Frontend
├─────────────────────────────────────┤
│   Flask REST API (Port 5000)       │  ← Backend API
├─────────────────────────────────────┤
│   Milvus Vector DB (Port 19530)    │  ← Data Storage
├─────────────────────────────────────┤
│   Ollama AI (Port 11434)           │  ← AI Reasoning
└─────────────────────────────────────┘
```

**Frontend:**
- React 18
- Chakra UI 2.8
- Framer Motion (animations)
- React Icons
- Axios (API calls)

**Backend:**
- Flask (existing)
- Flask-CORS (enabled)

## 🎯 Features

### 📤 Upload Files
- Drag & drop support
- File type validation
- Progress indicators
- Beautiful alerts

### 🎫 Fetch Jira Tickets
- Multi-ticket input
- Real-time feedback
- Collection selection

### 🐙 Import GitHub PRs
- URL validation
- PR data extraction
- Automatic embedding

### 🔍 Semantic Search
- Live search results
- Score badges
- Clickable links
- Smooth animations

### 🤖 Ollama AI Q&A
- Status indicator
- Model selection
- Context control
- Beautiful answer display
- Source documents

## 🎨 Chakra UI Components Used

- **Container** - Responsive layout
- **Box** - Flexible containers
- **VStack/HStack** - Vertical/horizontal stacks
- **Tabs** - Navigation
- **FormControl** - Form fields
- **Button** - Beautiful buttons with icons
- **Alert** - Success/error messages
- **Spinner** - Loading indicators
- **Badge** - Score indicators
- **Heading/Text** - Typography
- **Icon** - React Icons integration

## 🔧 Development

### Install Dependencies
```bash
cd frontend
npm install
```

### Run Development Server
```bash
npm start
```

### Build for Production
```bash
npm run build
```

### Customize Theme
Edit `frontend/src/index.js`:
```javascript
const theme = extendTheme({
  colors: {
    brand: {
      500: '#667eea',  // Change primary color
      // ... more colors
    },
  },
});
```

## 📁 Project Structure

```
Sonatype-Personal/
├── frontend/                    # React + Chakra UI
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadTab.js    # File upload
│   │   │   ├── JiraTab.js      # Jira integration
│   │   │   ├── GitHubTab.js    # GitHub PRs
│   │   │   ├── SearchTab.js    # Search UI
│   │   │   └── OllamaTab.js    # AI Q&A
│   │   ├── App.js              # Main app
│   │   └── index.js            # Entry + theme
│   ├── package.json
│   └── node_modules/
│
├── web_interface.py             # Flask backend (CORS enabled)
├── ollama_rag.py               # AI reasoning
├── jira_client.py              # Jira API
├── start-chakra-ui.sh          # Startup script
└── docker-compose.yml          # Milvus config
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill processes on port 3000
lsof -ti:3000 | xargs kill -9

# Kill processes on port 5000
lsof -ti:5000 | xargs kill -9
```

### React Not Starting
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

### CORS Errors
Make sure Flask backend has CORS enabled:
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # This should be in web_interface.py
```

### Ollama Not Detected
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull a model
ollama pull deepseek-r1:8b
```

## 🎨 Customization

### Change Colors
Edit `frontend/src/index.js`:
```javascript
const theme = extendTheme({
  colors: {
    brand: {
      500: '#FF6B6B',  // Red theme
      // or
      500: '#51CF66',  // Green theme
    },
  },
});
```

### Add More Models
Edit `frontend/src/components/OllamaTab.js`:
```javascript
<Select value={model} onChange={(e) => setModel(e.target.value)}>
  <option value="llama3.2">Llama 3.2</option>
  <option value="deepseek-r1:8b">DeepSeek R1</option>
  <option value="your-model">Your Model</option>  // Add here
</Select>
```

### Change Layout
Edit `frontend/src/App.js` to modify:
- Header gradient
- Container width
- Tab order
- Colors

## 🚀 Performance Tips

1. **Build for Production:**
```bash
cd frontend
npm run build
```
Then serve `build/` folder with a production server.

2. **Use Smaller Models:**
- `llama3.2` for speed
- `deepseek-r1:8b` for reasoning

3. **Limit Results:**
- Set lower `top_k` values for faster searches

## 📚 Learn More

- [Chakra UI Docs](https://chakra-ui.com/)
- [React Docs](https://react.dev/)
- [Framer Motion](https://www.framer.com/motion/)
- [Ollama](https://ollama.ai/)

## 🎉 Benefits Over Plain HTML

| Feature | Plain HTML | Chakra UI React |
|---------|-----------|-----------------|
| Performance | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Design | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Responsiveness | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Animations | ⭐ | ⭐⭐⭐⭐⭐ |
| Maintainability | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Developer Experience | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

**Your beautiful Chakra UI interface is ready!** 🎨

**Access at: http://localhost:3000**
