#!/bin/bash
# ============================================================
#  RaoMySQL 一键部署脚本 (Ubuntu/Debian/Oracle Linux ARM)
#  用法: bash deploy.sh [你的域名]
# ============================================================
set -e

DOMAIN="${1:-}"

echo "╔══════════════════════════════════════════════════╗"
echo "║     RaoMySQL 一键部署脚本 v1.6.0                ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── 1. 检查系统 ──
echo "[1/6] 检查系统环境..."
if ! command -v docker &> /dev/null; then
    echo "  安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "  ✅ Docker 已安装"
else
    echo "  ✅ Docker $(docker --version | grep -oP '\d+\.\d+\.\d+')"
fi

if ! docker compose version &> /dev/null 2>&1; then
    echo "  安装 Docker Compose 插件..."
    apt-get install -y docker-compose-plugin 2>/dev/null || yum install -y docker-compose-plugin 2>/dev/null
fi

# ── 2. 克隆项目 ──
PROJECT_DIR="/opt/raomysql"
if [ -d "$PROJECT_DIR" ]; then
    echo "[2/6] 更新项目代码..."
    cd "$PROJECT_DIR"
    git pull origin main
else
    echo "[2/6] 克隆项目..."
    git clone https://github.com/rao5201/RaoMySQL.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# ── 3. 配置环境变量 ──
echo "[3/6] 配置环境..."
if [ ! -f .env ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -hex 32)
    cat > .env << EOF
SECRET_KEY=$SECRET_KEY
ENCRYPTION_KEY=$(openssl rand -hex 16)
OPENAI_API_KEY=
AI_PROVIDER=openai
AI_MODEL=gpt-4
AI_ENDPOINT=
EOF
    echo "  ✅ .env 已生成（请编辑填写 OPENAI_API_KEY）"
else
    echo "  ✅ .env 已存在"
fi

# ── 4. SSL 证书 (如果提供了域名) ──
if [ -n "$DOMAIN" ]; then
    echo "[4/6] 配置 HTTPS (域名: $DOMAIN)..."
    # 替换 nginx.ssl.conf 中的域名
    sed -i "s/raomysql\.pages\.dev/$DOMAIN/g" docker/nginx.ssl.conf

    # 先用 HTTP 配置启动获取证书
    docker compose -f docker/docker-compose.yml --env-file .env up -d --build frontend

    # 获取 SSL 证书
    docker run --rm \
        -v certbot-etc:/etc/letsencrypt \
        -v certbot-var:/var/lib/letsencrypt \
        -v webroot:/var/www/certbot \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        -d "$DOMAIN" \
        --email rao5201@126.com \
        --agree-tos \
        --no-eff-email || echo "  ⚠️ SSL 证书获取失败，将使用 HTTP"

    # 切换到 SSL 配置
    docker compose -f docker/docker-compose.yml --env-file .env down
    docker compose -f docker/docker-compose.yml --env-file .env up -d --build
else
    echo "[4/6] 跳过 HTTPS（未提供域名，使用 HTTP）"
    docker compose -f docker/docker-compose.yml --env-file .env up -d --build
fi

# ── 5. 等待启动 ──
echo "[5/6] 等待服务启动..."
sleep 5
for i in $(seq 1 12); do
    if curl -s http://localhost/health > /dev/null 2>&1; then
        echo "  ✅ 后端服务已就绪"
        break
    fi
    echo "  等待中... ($i/12)"
    sleep 5
done

# ── 6. 完成 ──
IP=$(hostname -I | awk '{print $1}')
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║     🎉 RaoMySQL 部署成功！                      ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  网站首页: http://$IP                     ║"
echo "║  管理后台: http://$IP/app.html#/login       ║"
echo "║  API文档:  http://$IP/docs                    ║"
echo "║  默认账号: admin / admin123                     ║"
echo "║                                                  ║"
echo "║  如果提供了域名，HTTPS 会自动配置               ║"
echo "╚══════════════════════════════════════════════════╝"
