# ═══════════════════════════════════════════════════════════════════
# IPTV 直播源自动聚合工具 — 配置文件
# 所有开关和阈值均可在此调整
# ═══════════════════════════════════════════════════════════════════

# ── IP 优先级 ───────────────────────────────────────────────────────
# "ipv6" = IPv6 地址优先排在前面；"ipv4" = IPv4 优先
ip_version_priority = "ipv6"

# ── 源优先级 ────────────────────────────────────────────────────────
# "hotel" = 酒店源优先排在前面；"subscription" = 订阅源优先
source_priority = "hotel"

# 每频道最大线路数，0 = 不限制
max_lines_per_channel = 8

# ── 订阅源 ───────────────────────────────────────────────────────
# 每个 URL 都是一个 IPTV 直播源文件（支持 m3u 或 txt 格式）
# main.py 会依次请求这些地址，提取频道名和播放地址
# 注：被注释掉的源暂时停用，可取消注释启用
source_urls = [
    
]

# ── 酒店源 ────────────────────────────────────────────
# hotel_api   : 酒店源 API 地址
# enabled   : True=启用酒店源抓取，False=跳过
# allowed_orgs : 只保留指定运营商的节点，空列表=不过滤
#              可选值: "China Telecom", "China Unicom", "China Mobile",
#                      "Alibaba Cloud", "Tencent" 等
hotel_config = {
    "hotel_api": "",
    "enabled": True,
    "allowed_orgs": ["China Mobile","Alibaba Cloud"],
}

# ── URL 黑名单 ───────────────────────────────────────────────────────
# 播放地址包含以下任意子串时会被自动过滤掉
# 用途：屏蔽已知失效、广告插播、低质量或不稳定的源
url_blacklist = [
    "epg.pw/stream/",
    "45.192.97.170:8880"
]

# ── 公告条目 ────────────────────────────────────────────────────────
# 这些条目会写在直播源文件的最前面，位于所有频道之前
# 用途：展示公告信息，如主播链接、更新时间等
#
# name 的三种写法：
#   None                  → 自动替换为当天日期（如 "2026-08-22"）
#   "__TIME__"             → 同上，也替换为当天日期
#   "更新时间：__TIME__"   → 替换为 "更新时间：2026-08-22"
#
# channel   → 该公告在 live.txt 中的分类名（#genre# 分组）
# url       → 播放地址
# logo      → 频道图标 URL（m3u 中 tvg-logo 属性）
announcements = [
    {
        "channel": "公告-yuanzl77",
        "entries": [
                    ]
    }
]

# ── EPG 电子节目单 ────────────────────────────────────────────────────
# 同时用于两件事：
#   1. M3U 头部的 x-tvg-url 属性，供播放器读取节目指南
#   2. 频道 ID 映射（{频道名: tvg-id}），让播放器正确显示节目单
# 建议将最全面的源放在最后，作为保底
epg_urls = [
 
]

# ── 质量检测 — HTTP 快筛 ─────────────────────────────────────────────
# enable_quality_check : True=启用质量检测（测活后过滤失效源），False=直接输出不过滤
# check_timeout        : 单个 URL HTTP 请求超时时间（秒），超时视为失效
# check_max_conn       : 最大并发检测数，调高可加速但更占带宽
enable_quality_check = True
check_timeout    = 3.5
check_max_conn   = 80

# ── 质量检测 — FFprobe 中度探测 ───────────────────────────────────────
# enable_ffprobe     : True=启用第二层 FFprobe 探测，False=仅 HTTP 快筛
#                      建议先在少量频道上测试稳定性，再全量开启
# ffmpeg_path        : FFprobe 可执行文件路径
#                      空字符串 = 使用系统 PATH 里的 ffprobe
#                      Windows 如不在 PATH 中，填绝对路径即可
# ffprobe_timeout    : 单个 URL FFprobe 探流超时（秒）
#                      IPTV 流通常 1~3 秒即可探完，设为 8 秒以容忍慢源
# min_bitrate        : 最低码率阈值（bps），低于此值且 ffprobe 能读到码率时被过滤
#                      设为 0 = 不限制码率（IPTV 流常读不到码率字段，此时代偿跳过检查）
# min_resolution     : 最低分辨率宽度要求（字符串，如 "720" 表示宽 >= 720px）
#                      设为空字符串 "" = 不限制分辨率
# ffprobe_max_streams: ffprobe 最多读取的流数量，避免大文件探流耗时过长
ffmpeg_path        = ""        # 空 = 使用系统 PATH 里的 ffprobe
enable_ffprobe     = True
ffprobe_timeout    = 3.5
min_bitrate        = 0         # min_bitrate = 200000 → 码率>0 且 <200kbps 的源会被淘汰；码率=0 的源不受影响
min_resolution     = "720"     # 宽度最低 720px
ffprobe_max_streams = 3

# ── 深度探测配置 ───────────────────────────────────────────────────────
# enable_deep_probe  : True=启用第三层深度探测（仅对 m3u8 流），False=仅中度探测
#                      深度探测会检查分片时长、数量等，更准确但更慢
# deep_probe_timeout : 单个 URL 深度探测超时（秒）
#                      IPTV 流通常 5~10 秒即可探完，设为 10 秒以容忍慢源
# min_speed_kbps     : 最小速度阈值（kbps），低于此值的源会被过滤
#                      0 = 不过滤（只评分不淘汰）
#                      建议 2000（2 Mbps）避免推流卡顿
enable_deep_probe  = True
deep_probe_timeout = 5.0
min_speed_kbps     = 2500  # 2.5 Mbps
