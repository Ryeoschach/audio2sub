# 🚀 Audio2Sub 前端部署指南

## 📋 部署概览

Audio2Sub 前端支持多种部署方式，从开发测试到生产环境，提供灵活的部署选择。

## 🏗️ 构建准备

### 1. 环境变量配置
创建对应环境的配置文件：

```bash
# .env.production
VITE_API_BASE_URL=https://your-api-domain.com
VITE_MAX_FILE_SIZE=100
VITE_SUPPORTED_FORMATS=mp3,wav,flac,m4a,mp4,avi,mov
VITE_LOG_LEVEL=warn
```

### 2. 构建生产版本
```bash
# 安装依赖
pnpm install

# 类型检查
pnpm type-check

# 代码检查
pnpm lint

# 构建生产版本
pnpm build
```

构建后的文件在 `dist/` 目录中。

## 🐳 Docker 部署 (推荐)

### Dockerfile 说明
```dockerfile
# 多阶段构建，优化镜像大小
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# 生产环境
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 构建和运行
```bash
# 构建镜像
docker build -t audio2sub-frontend .

# 运行容器
docker run -d \
  --name audio2sub-frontend \
  -p 3000:80 \
  audio2sub-frontend

# 或使用环境变量
docker run -d \
  --name audio2sub-frontend \
  -p 3000:80 \
  -e VITE_API_BASE_URL=https://api.example.com \
  audio2sub-frontend
```

### Docker Compose 集成
```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    environment:
      - VITE_API_BASE_URL=http://backend:8000
    depends_on:
      - backend
    networks:
      - audio2sub-network

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    networks:
      - audio2sub-network

networks:
  audio2sub-network:
    driver: bridge
```

## 🌐 静态站点部署

### Netlify 部署
1. **连接 Git 仓库**
   - 登录 Netlify
   - 选择 "New site from Git"
   - 连接 GitHub/GitLab 仓库

2. **构建设置**
   ```
   Build command: pnpm build
   Publish directory: dist
   ```

3. **环境变量设置**
   ```
   VITE_API_BASE_URL=https://your-api.netlify.app
   ```

4. **部署配置文件**
   ```toml
   # netlify.toml
   [build]
     command = "pnpm build"
     publish = "dist"

   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200

   [build.environment]
     NODE_VERSION = "18"
   ```

### Vercel 部署
1. **安装 Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **部署命令**
   ```bash
   # 登录
   vercel login
   
   # 部署
   vercel --prod
   ```

3. **配置文件**
   ```json
   // vercel.json
   {
     "buildCommand": "pnpm build",
     "outputDirectory": "dist",
     "framework": "vite",
     "rewrites": [
       {
         "source": "/(.*)",
         "destination": "/index.html"
       }
     ]
   }
   ```

### GitHub Pages 部署
1. **工作流配置**
   ```yaml
   # .github/workflows/deploy.yml
   name: Deploy to GitHub Pages
   
   on:
     push:
       branches: [ main ]
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Setup Node.js
           uses: actions/setup-node@v3
           with:
             node-version: '18'
             cache: 'pnpm'
             
         - name: Install dependencies
           run: pnpm install
           
         - name: Build
           run: pnpm build
           env:
             VITE_API_BASE_URL: ${{ secrets.API_BASE_URL }}
             
         - name: Deploy
           uses: peaceiris/actions-gh-pages@v3
           with:
             github_token: ${{ secrets.GITHUB_TOKEN }}
             publish_dir: ./dist
   ```

## ☁️ 云服务部署

### AWS S3 + CloudFront
1. **S3 存储桶设置**
   ```bash
   # 创建存储桶
   aws s3 mb s3://audio2sub-frontend
   
   # 上传文件
   aws s3 sync dist/ s3://audio2sub-frontend --delete
   
   # 设置公共读取权限
   aws s3 website s3://audio2sub-frontend \
     --index-document index.html \
     --error-document index.html
   ```

2. **CloudFront 配置**
   ```json
   {
     "Origins": [{
       "DomainName": "audio2sub-frontend.s3.amazonaws.com",
       "OriginPath": "",
       "CustomOriginConfig": {
         "HTTPPort": 80,
         "HTTPSPort": 443,
         "OriginProtocolPolicy": "https-only"
       }
     }],
     "DefaultCacheBehavior": {
       "TargetOriginId": "S3-audio2sub-frontend",
       "ViewerProtocolPolicy": "redirect-to-https",
       "Compress": true
     }
   }
   ```

### Azure Static Web Apps
1. **配置文件**
   ```json
   // staticwebapp.config.json
   {
     "routes": [
       {
         "route": "/*",
         "serve": "/index.html",
         "statusCode": 200
       }
     ],
     "mimeTypes": {
       ".json": "application/json"
     }
   }
   ```

2. **GitHub Actions 集成**
   ```yaml
   # Azure 自动生成的工作流
   name: Azure Static Web Apps CI/CD
   
   on:
     push:
       branches: [ main ]
   
   jobs:
     build_and_deploy_job:
       runs-on: ubuntu-latest
       name: Build and Deploy Job
       steps:
         - uses: actions/checkout@v2
         
         - name: Build And Deploy
           uses: Azure/static-web-apps-deploy@v1
           with:
             azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
             repo_token: ${{ secrets.GITHUB_TOKEN }}
             action: "upload"
             app_location: "/"
             api_location: ""
             output_location: "dist"
   ```

## 🔧 Nginx 自定义部署

### Nginx 配置文件
```nginx
# nginx.conf
server {
    listen 80;
    server_name your-domain.com;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # 缓存静态资源
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # SPA 路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理 (可选)
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL 配置
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # SSL 优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # 其他配置...
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 📊 性能优化

### 构建优化
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          api: ['axios']
        }
      }
    },
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
});
```

### CDN 优化
```html
<!-- index.html -->
<head>
  <!-- 预加载关键资源 -->
  <link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
  
  <!-- DNS 预解析 -->
  <link rel="dns-prefetch" href="//api.audio2sub.com">
  
  <!-- 预连接 -->
  <link rel="preconnect" href="https://api.audio2sub.com">
</head>
```

## 🔍 监控和日志

### 错误监控集成
```typescript
// 集成 Sentry
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "YOUR_SENTRY_DSN",
  environment: import.meta.env.MODE,
  tracesSampleRate: 1.0,
});

// 错误边界
const ErrorBoundary = Sentry.withErrorBoundary(App, {
  fallback: ({ error, resetError }) => (
    <div>出现错误: {error.message}</div>
  ),
});
```

### 分析工具
```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

## 🚨 故障排除

### 常见部署问题

#### 1. 路由 404 错误
**问题**: SPA 路由在刷新时显示 404
**解决**: 配置服务器将所有路由重定向到 `index.html`

#### 2. API 跨域问题
**问题**: 前端无法访问后端 API
**解决**: 
- 配置后端 CORS
- 使用代理服务器
- 确保 API 域名正确

#### 3. 静态资源加载失败
**问题**: JS/CSS 文件 404
**解决**: 
- 检查构建输出路径
- 确认服务器配置
- 验证资源路径

#### 4. 环境变量不生效
**问题**: 生产环境变量未正确设置
**解决**:
- 确保变量以 `VITE_` 开头
- 检查构建时变量是否可用
- 验证部署平台的环境变量配置

### 部署检查清单
- [ ] 环境变量正确配置
- [ ] 构建成功无错误
- [ ] 静态资源正确加载
- [ ] API 连接正常
- [ ] 路由功能正常
- [ ] 响应式布局正常
- [ ] 性能指标达标
- [ ] 错误监控正常
- [ ] SSL 证书有效

## 📋 部署脚本

### 自动化部署脚本
```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 开始部署 Audio2Sub 前端..."

# 1. 检查环境
if [ ! -f ".env.production" ]; then
  echo "❌ 缺少 .env.production 文件"
  exit 1
fi

# 2. 安装依赖
echo "📦 安装依赖..."
pnpm install

# 3. 类型检查
echo "🔍 类型检查..."
pnpm type-check

# 4. 代码检查
echo "🧹 代码检查..."
pnpm lint

# 5. 构建
echo "🏗️ 构建生产版本..."
pnpm build

# 6. 部署 (根据部署方式选择)
echo "🚀 部署到服务器..."
# rsync -avz --delete dist/ user@server:/var/www/html/
# docker build -t audio2sub-frontend .
# aws s3 sync dist/ s3://your-bucket --delete

echo "✅ 部署完成!"
```

---

**最后更新**: 2025年6月19日  
**维护者**: Audio2Sub 开发团队
