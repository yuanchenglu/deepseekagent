# OpenStudy 方舟众测产物整合参考

> 本文件记录方舟众测产物整合到活动项目的完整工作流。
> 适用于后续类似的多期产物合并任务。

## 整合总览

方舟众测 3 期共 12 个 OpenStudy 任务，分 3 个 Phase 整合进 ~/Code/miniappStudyTools。

## 产物解压策略

- **绝对不要用 /tmp** — 整合跨多天，重启后 /tmp 可能清空
- 直接在 `~/Code/fangzhouzhongce/第N期/3产物/` 下解压最佳变体
- 产物目录自动由 `get_tools()` 扫描发现，无需修改 index.php

## 最佳变体选择

| 任务 | 最佳变体 | 理由 |
|------|---------|------|
| 架构重构 | T29.1 granite/eclipse | 减重 71%/68%，完整五阶段流程 |
| Bug修复 | T29.2 granite | 27个Bug（含3个独特P0） |
| AI批改 | T29.3 falcon | PHP原生实现，无外部依赖 |
| 用户体系 | T26.2 jetty | 手机号登录+点赞系统完整 |
| 作文教练 | T26.4 nimbus | 诊断→引导→点评→12周计划 |
| 认知工具 | T25.2 crane | 10个教材同步练习 |
| 益智游戏 | T25.3 crane | 15款经典益智游戏 |

## 核心命令

### OpenCode session 管理
```bash
# 继续上一个 session（重要！不要新开）
opencode run -c '按计划执行 Phase N'

# 查看 session 状态
opencode session list --max-count 5

# 查看 token 用量判断是否卡了
opencode stats --days 1

# 产详细计划（plan-only 模式）
opencode run --model clawadmin/deepseek-v4-flash '产出一份详细计划...不要修改代码'
```

### PHP 服务器
```bash
# 启动
php -S localhost:8082 -t h5web/studytools/
# 测试
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8082/
```

### 验证方法
```bash
# 语法检查
php -l h5web/studytools/index.php

# 文件内容验证（不依赖PHP服务器路由）
grep -o '<title>[^<]*</title>' h5web/studytools/FifteenPuzzle/index.html

# 文件大小对比（确认不是首页回退）
wc -c h5web/studytools/FifteenPuzzle/index.html

# curl 验证
curl -s "http://localhost:8082/FifteenPuzzle/" | grep '15数码'

# 三方 diff 对比
diff -rq baseline/ product/ target/
```

### Cloudflare Tunnel
```bash
# 启动
cloudflared tunnel run <tunnel-name>
# 状态查询
curl -s "https://api.cloudflare.com/client/v4/accounts/<account_id>/cfd_tunnel/<tunnel_id>" \
  -H "X-Auth-Email: ..." -H "X-Auth-Key: ..."
```

## commit 规范

每个 task 一个 commit，格式：
```
feat: English description | 中文描述
fix: English description | 中文描述
```

## 技术债务移交

当某个任务暂不整合时，输出 handoff 文档到桌面，包含：
- 任务描述
- 产物路径
- 改动范围
- 约束条件
- 操作命令
