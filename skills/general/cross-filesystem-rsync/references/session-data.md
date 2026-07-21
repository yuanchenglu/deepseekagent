# Session Data — AIPC U盘 → Share 分区 迁移

## Device Topology

| 设备 | 路径 | 类型 | 总线 | RQ-SIZE | 大小 |
|------|------|------|------|---------|------|
| U盘 (源) | `/dev/sdc1` | ext4 | USB 3.2 | 2 | 115G |
| Share分区 (目标) | `/dev/sdb2` | exFAT | SATA | 64 | 1.3T |
| 系统盘 | `/dev/nvme0n1p8` | ext4 | NVMe | - | 111G |

## Source Data

- 路径: `/media/bluth/BACKUP/bluth/Code/`
- 文件数: 184,427
- 目录数: 31,489
- 符号链接: 106
- 总大小: ~19 GB

## Speed Before/After

| 方法 | 速度 | 根因 |
|------|------|------|
| `rsync -avP` (3进程, exFAT) | **~150 KB/s** | `-a` 含 `-p -o -g`，exFAT 上每个文件 chmod 失败 |
| `rsync -rtP --no-perms --no-owner --no-group` | **~22 MB/s** | 跳过权限操作 |
| `cp` (ISO 703 MB) | **~168 MB/s** | sendfile() 零拷贝 |
| `dd` (大文件连续读) | **~168 MB/s** | 纯顺序读，无文件系统元数据开销 |

**提升**: 去掉 `-a` (权限) → 150× 提速。

## RQ-SIZE 影响

U盘 RQ-SIZE=2 意味着同时最多排队 2 个 I/O 请求。rsync 3 进程（sender + receiver + generator）同时读写，在 RQ-SIZE=2 的 U 盘上抢队列槽位。对小文件（venv/node_modules），每个文件需要 seek + read + write，队列深度不足导致大量等待。

对比: Share 分区位于 SATA 盘，RQ-SIZE=64，写入不受限。

## Final rsync Stats

```
Number of files: 216,020 (reg: 184,425, dir: 31,489, link: 106)
Number of created files: 4,008 (reg: 3,412, dir: 596)
Number of regular files transferred: 3,414
Total file size: 12,073,124,588 bytes
Total bytes sent: 351,021,798
Total bytes received: 108,829
Speedup: 34.38
```

## Commands Used

```bash
# Diagnose
df -T /media/bluth/BACKUP /media/bluth/Shared
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,RM,ROTA,TRAN,RQ-SIZE
dd if=/path/to/large/file of=/dev/null bs=1M count=200 status=progress

# Fast copy
cp /source/ISO/file.iso /dest/ISO/
rsync -rtP --partial --no-perms --no-owner --no-group \
  --exclude='*.iso' /source/ /dest/

# Verify
md5sum /source/file /dest/file
```
