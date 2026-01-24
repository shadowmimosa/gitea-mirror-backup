#!/bin/bash

#############################################
# Gitea Docker 镜像仓库备份系统
# 适用于: Docker 运行的 Gitea
# 功能: 每日快照 + 每周汇总报告
#############################################

# ============ 配置区域 ============
# Docker 容器名称
DOCKER_CONTAINER="gitea"

# Gitea 数据卷路径（宿主机上的路径）
# 通常是: /var/lib/docker/volumes/gitea_data/_data
# 或者你自己映射的路径，比如: /data/gitea
GITEA_DATA_VOLUME="/opt/gitea/gitea"

# Gitea 仓库在卷中的相对路径
GITEA_REPOS_PATH="git/repositories"

# 备份根目录（宿主机路径）
BACKUP_ROOT="/opt/backup/gitea-mirrors"

# 只备份特定组织的仓库（留空则备份所有镜像仓库）
# 多个组织用空格分隔: "BackupHub AnotherOrg"
BACKUP_ORGANIZATIONS="BackupHubTest"

# 快照保留天数
SNAPSHOT_RETENTION_DAYS=30

# 每月归档保留月数
ARCHIVE_RETENTION_MONTHS=12

# 仓库大小异常阈值（减少百分比）
SIZE_DECREASE_THRESHOLD=30

# 日志文件
LOG_FILE="/var/log/gitea-mirror-backup.log"

# 报告文件
REPORT_FILE="$BACKUP_ROOT/weekly-report.md"

# ============ 函数定义 ============

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# 检查 Docker 容器是否运行
check_docker() {
    if ! docker ps | grep -q "$DOCKER_CONTAINER"; then
        log_error "Docker 容器 $DOCKER_CONTAINER 未运行"
        exit 1
    fi
    log "✓ Docker 容器运行正常"
}

# 获取仓库完整路径
get_repo_path() {
    local owner=$1
    local repo=$2
    echo "$GITEA_DATA_VOLUME/$GITEA_REPOS_PATH/$owner/$repo.git"
}

# 检查是否是镜像仓库
is_mirror_repo() {
    local repo_path=$1
    
    # 在 Docker 容器中执行 git 命令检查
    docker exec "$DOCKER_CONTAINER" \
        git -C "/data/git/repositories/$(basename $(dirname $repo_path))/$(basename $repo_path)" \
        config --get remote.origin.url >/dev/null 2>&1
    
    return $?
}

# 创建快照
create_snapshot() {
    local repo_path=$1
    local repo_name=$2
    local snapshot_dir="$BACKUP_ROOT/$repo_name/snapshots"
    local date_stamp=$(date +%Y%m%d-%H%M%S)
    local snapshot_path="$snapshot_dir/$date_stamp"
    
    log $repo_path
    mkdir -p "$snapshot_dir"
    log $repo_path
    
    log "创建快照: $repo_name"
    
    # 使用硬链接创建快照
    if cp -al "$repo_path" "$snapshot_path" 2>/dev/null; then
        # 记录元数据
        cat > "$snapshot_path/.snapshot_meta" << EOF
timestamp=$(date -Iseconds)
source=$repo_path
repo_name=$repo_name
EOF
        log "  ✓ 快照成功: $(basename $snapshot_path)"
        return 0
    else
        log_error "  ✗ 快照失败: $repo_name"
        return 1
    fi
}

# 计算仓库大小
get_repo_size() {
    local repo_path=$1
    du -sk "$repo_path" 2>/dev/null | awk '{print $1}'
}

# 检测并记录异常变化
check_repo_changes() {
    local repo_path=$1
    local repo_name=$2
    local size_tracking_file="$BACKUP_ROOT/$repo_name/.size_tracking"
    
    current_size=$(get_repo_size "$repo_path")
    
    if [ ! -f "$size_tracking_file" ]; then
        echo "$current_size" > "$size_tracking_file"
        return 0
    fi
    
    prev_size=$(cat "$size_tracking_file")
    
    if [ "$current_size" -lt "$prev_size" ]; then
        decrease=$(( (prev_size - current_size) * 100 / prev_size ))
        
        if [ "$decrease" -gt "$SIZE_DECREASE_THRESHOLD" ]; then
            # 记录到异常日志
            local alert_file="$BACKUP_ROOT/$repo_name/.alerts"
            cat >> "$alert_file" << EOF
[$(date -Iseconds)]
仓库大小异常减少: ${decrease}%
上次: ${prev_size}KB → 当前: ${current_size}KB
可能原因: force push 或分支删除
EOF
            log "  ⚠️  大小减少 ${decrease}%"
            echo "$repo_name" >> "$BACKUP_ROOT/.need_review"
            return 1
        fi
    fi
    
    echo "$current_size" > "$size_tracking_file"
    return 0
}

# 清理旧快照
cleanup_old_snapshots() {
    local repo_name=$1
    local snapshot_dir="$BACKUP_ROOT/$repo_name/snapshots"
    
    if [ ! -d "$snapshot_dir" ]; then
        return 0
    fi
    
    # 删除超过保留期的快照
    local deleted_count=0
    while IFS= read -r snapshot; do
        rm -rf "$snapshot"
        ((deleted_count++))
    done < <(find "$snapshot_dir" -maxdepth 1 -type d -mtime +$SNAPSHOT_RETENTION_DAYS 2>/dev/null)
    
    if [ $deleted_count -gt 0 ]; then
        log "  清理旧快照: $deleted_count 个"
    fi
}

# 创建月度归档
create_monthly_archive() {
    local repo_path=$1
    local repo_name=$2
    local archive_dir="$BACKUP_ROOT/$repo_name/archives"
    local month_stamp=$(date +%Y%m)
    local archive_file="$archive_dir/archive-$month_stamp.bundle"
    
    # 检查本月是否已创建
    if [ -f "$archive_file" ]; then
        return 0
    fi
    
    mkdir -p "$archive_dir"
    
    log "  创建月度归档..."
    
    # 使用 Docker 容器中的 git 创建 bundle
    local container_repo_path="/data/git/repositories/$(basename $(dirname $repo_path))/$(basename $repo_path)"
    
    docker exec "$DOCKER_CONTAINER" \
        git -C "$container_repo_path" bundle create /tmp/temp.bundle --all 2>/dev/null
    
    if [ $? -eq 0 ]; then
        docker cp "$DOCKER_CONTAINER:/tmp/temp.bundle" "$archive_file"
        docker exec "$DOCKER_CONTAINER" rm /tmp/temp.bundle
        log "  ✓ 归档成功"
        
        # 清理旧归档
        find "$archive_dir" -name "*.bundle" -mtime +$((ARCHIVE_RETENTION_MONTHS * 30)) \
            -exec rm -f {} \; 2>/dev/null
    fi
}

# 处理单个仓库
process_repository() {
    local repo_path=$1
    local owner=$(basename $(dirname "$repo_path"))
    local repo=$(basename "$repo_path" .git)
    local repo_name="$owner/$repo"

    log "检查仓库: $repo_name"
    
    # 如果指定了组织，检查是否匹配
    if [ -n "$BACKUP_ORGANIZATIONS" ]; then
        local match=false
        for org in $BACKUP_ORGANIZATIONS; do
            if [ "$owner" = "$org" ]; then
                match=true
                break
            fi
        done
        
        if [ "$match" = false ]; then
            return 0
        fi
    fi

    log "检查仓库: $repo_name"

    # 检查是否是镜像仓库
    if ! is_mirror_repo "$repo_path"; then
        return 0
    fi
    
    log "----------------------------------------"
    log "处理: $repo_name"
    
    # 1. 创建快照
    create_snapshot "$repo_path" "$repo_name"
    
    # 2. 检测异常
    check_repo_changes "$repo_path" "$repo_name"
    
    # 3. 清理旧快照
    cleanup_old_snapshots "$repo_name"
    
    # 4. 每月1号创建归档
    if [ $(date +%d) -eq 01 ]; then
        create_monthly_archive "$repo_path" "$repo_name"
    fi
}

# 生成每周报告
generate_weekly_report() {
    log "生成每周报告..."
    
    mkdir -p "$(dirname $REPORT_FILE)"
    
    cat > "$REPORT_FILE" << 'EOF'
# Gitea 镜像仓库备份报告

**生成时间**: 
EOF
    echo "$(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # 统计信息
    local total_repos=0
    local total_snapshots=0
    local total_archives=0
    local total_size=0
    
    cat >> "$REPORT_FILE" << 'EOF'
## 📊 总体统计

EOF
    
    # 遍历所有仓库
    for repo_dir in "$BACKUP_ROOT"/*/*; do
        if [ ! -d "$repo_dir" ]; then
            continue
        fi
        
        repo_name=$(echo $repo_dir | sed "s|$BACKUP_ROOT/||")
        ((total_repos++))
        
        # 统计快照
        if [ -d "$repo_dir/snapshots" ]; then
            snapshot_count=$(find "$repo_dir/snapshots" -maxdepth 1 -type d ! -path "$repo_dir/snapshots" | wc -l)
            total_snapshots=$((total_snapshots + snapshot_count))
        fi
        
        # 统计归档
        if [ -d "$repo_dir/archives" ]; then
            archive_count=$(find "$repo_dir/archives" -name "*.bundle" 2>/dev/null | wc -l)
            total_archives=$((total_archives + archive_count))
        fi
        
        # 计算大小
        dir_size=$(du -sk "$repo_dir" 2>/dev/null | awk '{print $1}')
        total_size=$((total_size + dir_size))
    done
    
    cat >> "$REPORT_FILE" << EOF
- **备份仓库数**: $total_repos
- **快照总数**: $total_snapshots
- **归档总数**: $total_archives
- **占用空间**: $(numfmt --to=iec-i --suffix=B $((total_size * 1024)) 2>/dev/null || echo "${total_size}KB")

EOF
    
    # 异常报告
    if [ -f "$BACKUP_ROOT/.need_review" ]; then
        cat >> "$REPORT_FILE" << 'EOF'
## ⚠️ 需要关注的仓库

以下仓库检测到大小异常减少，可能发生了 force push：

EOF
        
        while IFS= read -r repo_name; do
            alert_file="$BACKUP_ROOT/$repo_name/.alerts"
            if [ -f "$alert_file" ]; then
                echo "### $repo_name" >> "$REPORT_FILE"
                echo '```' >> "$REPORT_FILE"
                tail -20 "$alert_file" >> "$REPORT_FILE"
                echo '```' >> "$REPORT_FILE"
                echo "" >> "$REPORT_FILE"
                
                # 恢复建议
                latest_snapshot=$(ls -td "$BACKUP_ROOT/$repo_name/snapshots"/* 2>/dev/null | head -1)
                cat >> "$REPORT_FILE" << EOF
**最新快照**: $(basename "$latest_snapshot" 2>/dev/null || echo "无")

**恢复命令**:
\`\`\`bash
$BACKUP_ROOT/$repo_name/restore.sh
\`\`\`

---

EOF
            fi
        done
        
        # 清空待审核列表
        rm "$BACKUP_ROOT/.need_review"
    else
        cat >> "$REPORT_FILE" << 'EOF'
## ✅ 全部正常

本周期内所有仓库均未检测到异常。

EOF
    fi
    
    # 仓库详情
    cat >> "$REPORT_FILE" << 'EOF'
## 📦 仓库备份详情

| 仓库 | 快照数 | 最新快照 | 归档数 | 占用空间 |
|------|--------|----------|--------|----------|
EOF
    
    for repo_dir in "$BACKUP_ROOT"/*/*; do
        if [ ! -d "$repo_dir" ]; then
            continue
        fi
        
        repo_name=$(echo $repo_dir | sed "s|$BACKUP_ROOT/||")
        
        # 快照信息
        snapshot_count=0
        latest_snapshot="无"
        if [ -d "$repo_dir/snapshots" ]; then
            snapshot_count=$(find "$repo_dir/snapshots" -maxdepth 1 -type d ! -path "$repo_dir/snapshots" | wc -l)
            latest=$(ls -td "$repo_dir/snapshots"/* 2>/dev/null | head -1)
            if [ -n "$latest" ]; then
                latest_snapshot=$(basename "$latest")
            fi
        fi
        
        # 归档信息
        archive_count=0
        if [ -d "$repo_dir/archives" ]; then
            archive_count=$(find "$repo_dir/archives" -name "*.bundle" 2>/dev/null | wc -l)
        fi
        
        # 大小
        dir_size=$(du -sh "$repo_dir" 2>/dev/null | awk '{print $1}')
        
        echo "| $repo_name | $snapshot_count | $latest_snapshot | $archive_count | $dir_size |" >> "$REPORT_FILE"
    done
    
    cat >> "$REPORT_FILE" << 'EOF'

## 💾 磁盘使用情况

EOF
    
    df -h "$BACKUP_ROOT" | tail -1 | awk '{print "- **分区**: "$1"\n- **总空间**: "$2"\n- **已用**: "$3" ("$5")\n- **可用**: "$4}' >> "$REPORT_FILE"
    
    cat >> "$REPORT_FILE" << 'EOF'

---

**说明**:
- 快照使用硬链接技术，实际占用空间远小于显示值
- 建议每周查看此报告，关注"需要关注的仓库"部分
- 如需恢复仓库，使用对应的 restore.sh 脚本
EOF
    
    log "✓ 报告生成: $REPORT_FILE"
}

# 生成恢复脚本
generate_restore_script() {
    local repo_name=$1
    local restore_script="$BACKUP_ROOT/$repo_name/restore.sh"
    
    mkdir -p "$(dirname $restore_script)"
    
    cat > "$restore_script" << 'EOFSCRIPT'
#!/bin/bash

REPO_NAME="__REPO_NAME__"
SNAPSHOT_DIR="__SNAPSHOT_DIR__"
CONTAINER="__CONTAINER__"
CONTAINER_REPO_PATH="__CONTAINER_REPO_PATH__"

echo "=========================================="
echo "Gitea 镜像仓库恢复工具"
echo "=========================================="
echo "仓库: $REPO_NAME"
echo ""

# 列出可用快照
echo "可用的快照:"
snapshots=($(ls -td $SNAPSHOT_DIR/* 2>/dev/null))
if [ ${#snapshots[@]} -eq 0 ]; then
    echo "错误: 没有找到快照"
    exit 1
fi

for i in "${!snapshots[@]}"; do
    snapshot_name=$(basename "${snapshots[$i]}")
    echo "  [$i] $snapshot_name"
    
    # 显示快照信息
    if [ -f "${snapshots[$i]}/.snapshot_meta" ]; then
        grep timestamp "${snapshots[$i]}/.snapshot_meta" | sed 's/^/      /'
    fi
done

echo ""
read -p "选择要恢复的快照编号 [0]: " choice
choice=${choice:-0}

if [ -z "${snapshots[$choice]}" ]; then
    echo "错误: 无效的选择"
    exit 1
fi

SELECTED_SNAPSHOT="${snapshots[$choice]}"
echo ""
echo "已选择: $(basename $SELECTED_SNAPSHOT)"
echo ""
echo "⚠️  警告: 此操作将覆盖容器中的仓库"
read -p "确认继续? (yes/NO): " confirm

if [ "$confirm" != "yes" ]; then
    echo "已取消"
    exit 0
fi

echo ""
echo "正在恢复..."

# 停止容器
echo "1. 停止 Docker 容器..."
docker stop $CONTAINER

# 备份当前仓库（在宿主机上）
HOST_REPO_PATH="__HOST_REPO_PATH__"
BACKUP_CURRENT="${HOST_REPO_PATH}.backup-$(date +%Y%m%d-%H%M%S)"
echo "2. 备份当前仓库到: $BACKUP_CURRENT"
mv "$HOST_REPO_PATH" "$BACKUP_CURRENT"

# 恢复快照
echo "3. 恢复快照..."
cp -a "$SELECTED_SNAPSHOT" "$HOST_REPO_PATH"

# 启动容器
echo "4. 启动 Docker 容器..."
docker start $CONTAINER

echo ""
echo "✓ 恢复完成!"
echo ""
echo "如需回滚，当前仓库已备份至:"
echo "  $BACKUP_CURRENT"
echo ""
echo "验证命令:"
echo "  docker exec $CONTAINER git -C $CONTAINER_REPO_PATH log --oneline -5"

EOFSCRIPT
    
    # 替换变量
    owner=$(dirname "$repo_name")
    repo=$(basename "$repo_name")
    
    sed -i "s|__REPO_NAME__|$repo_name|g" "$restore_script"
    sed -i "s|__SNAPSHOT_DIR__|$BACKUP_ROOT/$repo_name/snapshots|g" "$restore_script"
    sed -i "s|__CONTAINER__|$DOCKER_CONTAINER|g" "$restore_script"
    sed -i "s|__CONTAINER_REPO_PATH__|/data/git/repositories/$owner/$repo.git|g" "$restore_script"
    sed -i "s|__HOST_REPO_PATH__|$GITEA_DATA_VOLUME/$GITEA_REPOS_PATH/$owner/$repo.git|g" "$restore_script"
    
    chmod +x "$restore_script"
}

# 主函数
main() {
    log "=========================================="
    log "Gitea Docker 镜像备份任务开始"
    log "=========================================="
    
    # 检查 Docker
    check_docker
    
    # 确保备份目录存在
    mkdir -p "$BACKUP_ROOT"
    
    # 获取仓库路径
    REPOS_FULL_PATH="$GITEA_DATA_VOLUME/$GITEA_REPOS_PATH"
    
    if [ ! -d "$REPOS_FULL_PATH" ]; then
        log_error "仓库目录不存在: $REPOS_FULL_PATH"
        exit 1
    fi
    
    # 处理所有仓库
    local processed_count=0
    for repo_path in "$REPOS_FULL_PATH"/*/*.git; do
        if [ -d "$repo_path" ]; then
            process_repository "$repo_path"
            
            # 生成恢复脚本
            owner=$(basename $(dirname "$repo_path"))
            repo=$(basename "$repo_path" .git)
            generate_restore_script "$owner/$repo"
            
            ((processed_count++))
        fi
    done
    
    log "处理了 $processed_count 个仓库"
    
    # 每周一生成报告
    if [ $(date +%u) -eq 1 ]; then
        generate_weekly_report
    fi
    
    log "=========================================="
    log "备份任务完成"
    log "=========================================="
}

# 执行
main