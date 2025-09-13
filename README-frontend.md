# TikTok Live Recorder — Frontend Dashboard

A modern, responsive dashboard for managing TikTok Live Recorder operations, built with **Next.js 14**, **React 18**, **TypeScript**, and **Tailwind CSS**.

## ✨ Features

### 🏠 Dashboard

- **Health Monitoring**: Real-time API and worker status
- **Metrics Cards**: Active watchers, running jobs, success/failure rates
- **System Overview**: Quick glance at system health

### 👁️ Watchers Management

- **Create Watchers**: Monitor TikTok live streams automatically
- **Form Validation**: Comprehensive input validation with Zod
- **Delete Watchers**: Remove watchers by room_id or URL
- **Toast Notifications**: User feedback for all actions

### 🎬 Recording Control

- **Instant Recording**: Start recording TikTok live streams
- **Flexible Input**: Support both room_id and URL input
- **Configuration Options**: Duration limits, proxy, cookies support
- **Job Tracking**: Automatic redirect to job monitoring

### 📋 Jobs Monitoring

- **Jobs List**: Comprehensive job listing with filters
- **Status Tracking**: Real-time job status updates
- **Job Details**: Detailed view with live polling
- **File Management**: View generated files and S3 uploads

### 📁 Files Browser

- **Advanced Filtering**: Filter by room_id, URL, date range
- **Pagination**: Efficient browsing of large file sets
- **Copy Functionality**: One-click copy of file paths
- **File Metadata**: Size, modification time, and path information

### ⚙️ Settings

- **Theme Support**: Light/dark/system theme options
- **Timezone Configuration**: Multiple timezone support
- **Date Formats**: Customizable date display formats
- **System Information**: Version and build details

## 🛠️ Tech Stack

- **Framework**: Next.js 14 (App Router) + React 18 + TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: TanStack Query (server state) + React Hook Form (forms)
- **Validation**: Zod schema validation
- **Icons**: Lucide React
- **Testing**: Vitest + React Testing Library + Playwright
- **Build**: Docker containerization

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or pnpm

### Installation

1. **Clone and navigate**:

   ```bash
   cd frontend
   ```

2. **Install dependencies**:

   ```bash
   npm install
   # or
   pnpm install
   ```

3. **Environment setup**:

   ```bash
   cp .env.local.example .env.local
   ```

   Configure your environment variables:

   ```env
   API_BASE_URL=http://localhost:8000
   API_KEY=your-api-key
   NODE_ENV=development
   ```

4. **Development server**:

   ```bash
   npm run dev
   # or
   pnpm dev
   ```

5. **Open browser**: Navigate to [http://localhost:3000](http://localhost:3000)

## 📁 Project Structure

```
src/
├── app/                    # Next.js 14 App Router
│   ├── (dashboard)/       # Route groups
│   ├── api/               # BFF API routes
│   │   ├── _utils.ts      # API utilities
│   │   ├── healthz/       # Health check proxy
│   │   ├── jobs/          # Jobs API proxy
│   │   ├── files/         # Files API proxy
│   │   ├── recordings/    # Recordings API proxy
│   │   └── watchers/      # Watchers API proxy
│   ├── files/             # Files browser page
│   ├── jobs/              # Jobs management
│   ├── record/            # Recording control
│   ├── settings/          # Configuration
│   └── watchers/          # Watchers management
├── components/
│   ├── layout/            # Layout components
│   │   └── AppShell.tsx   # Main application shell
│   └── ui/                # shadcn/ui components
├── lib/
│   ├── api.ts             # API client & types
│   └── utils.ts           # Utility functions
└── hooks/
    └── use-toast.ts       # Toast hook
```

## 🔒 Security & Architecture

### Backend-for-Frontend (BFF) Pattern

- **API Key Protection**: Never exposes API keys to client
- **Request Proxy**: All API calls go through `/api/*` routes
- **Error Standardization**: Consistent error handling and formatting
- **CORS Security**: Proper cross-origin request handling

### Type Safety

- **TypeScript**: Full type coverage
- **API Types**: Generated from backend schema
- **Form Validation**: Runtime validation with Zod
- **Build-time Checks**: TypeScript compiler integration

## 🧪 Testing

### Unit Tests (Vitest + RTL)

```bash
npm run test              # Run tests once
npm run test:watch        # Watch mode
npm run test:coverage     # Coverage report
```

### E2E Tests (Playwright)

```bash
npm run test:e2e          # Run E2E tests
npm run test:e2e:ui       # Interactive UI mode
```

### Test Coverage

- **Utils**: Utility functions (formatBytes, formatDuration)
- **Components**: Key UI components and interactions
- **API Integration**: Mocked API calls and error handling
- **User Flows**: Complete user journeys (create watcher → monitor job)

## 📊 Performance

### Optimization Features

- **Code Splitting**: Automatic route-based splitting
- **Image Optimization**: Next.js built-in optimization
- **Bundle Analysis**: Webpack bundle analyzer integration
- **Caching Strategy**: Smart query caching with TanStack Query

### Metrics

- **First Contentful Paint**: < 1.5s (internal network)
- **Bundle Size**: < 300KB gzipped (main bundle)
- **Lighthouse Score**: 90+ (performance, accessibility, best practices)

## 🌐 API Integration

### Supported Endpoints

- `GET /healthz` - System health check
- `GET /ready` - Worker readiness check
- `POST /recordings` - Create recording job
- `GET /jobs` - List jobs with pagination/filtering
- `GET /jobs/{id}` - Job status and details
- `POST /watchers` - Create watcher
- `DELETE /watchers/{key}` - Remove watcher
- `GET /files` - Browse files with filters

### Error Handling

```typescript
{
  error_code: "string",
  error_message: "string",
  correlation_id?: "uuid"
}
```

## 🐳 Docker Deployment

### Build Production Image

```bash
# Build
docker build -t tiktok-frontend .

# Run
docker run -p 3000:3000 \
  -e API_BASE_URL=http://backend:8000 \
  -e API_KEY=production-key \
  tiktok-frontend
```

### Docker Compose

```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - API_BASE_URL=http://backend:8000
      - API_KEY=${API_KEY}
    depends_on:
      - backend
```

## 🔄 Development Workflow

### Scripts

```bash
npm run dev         # Development server
npm run build       # Production build
npm run start       # Production server
npm run lint        # ESLint check
npm run test        # Unit tests
npm run test:e2e    # E2E tests
```

### Code Quality

- **ESLint**: Code linting with Next.js rules
- **TypeScript**: Strict type checking
- **Prettier**: Code formatting (configured in ESLint)
- **Git Hooks**: Pre-commit linting and testing

## 🚦 Status & Roadmap

### ✅ Completed

- [x] Core dashboard functionality
- [x] All major pages implemented
- [x] shadcn/ui integration
- [x] Toast notifications
- [x] Form validation
- [x] API integration with BFF
- [x] Real-time job polling
- [x] File browsing with pagination
- [x] Testing framework setup
- [x] Docker containerization

### 🔄 In Progress

- [ ] Theme switching implementation
- [ ] Internationalization (i18n)
- [ ] Advanced metrics dashboard

### 📅 Future Enhancements

- [ ] WebSocket real-time updates
- [ ] Advanced filtering and search
- [ ] Bulk operations
- [ ] Export/import configurations
- [ ] Mobile responsiveness improvements

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Run tests**: `npm test && npm run test:e2e`
4. **Commit changes**: `git commit -m 'Add amazing feature'`
5. **Push branch**: `git push origin feature/amazing-feature`
6. **Create Pull Request**

## 📄 License

This project is part of the TikTok Live Recorder system. See the main repository for license information.

---

**Note**: This is an internal dashboard application. Do not expose API keys or deploy publicly without proper security measures.
