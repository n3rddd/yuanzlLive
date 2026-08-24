"""
酒店源抓取模块 — 从速度测试站获取 IPTV 节点并按类型解析
"""
import asyncio
import json
import logging
import re
import aiohttp
import config

logger = logging.getLogger(__name__)


async def _fetch_json(session, url, timeout):
    """通用 JSON 请求"""
    try:
        async with session.get(url, timeout=timeout) as resp:
            resp.raise_for_status()
            text = await resp.text()
            return json.loads(text)
    except Exception as e:
        return None


async def _fetch_text(session, url, timeout):
    """通用文本请求（UTF-8）"""
    try:
        async with session.get(url, timeout=timeout) as resp:
            resp.raise_for_status()
            return await resp.text(encoding="utf-8")
    except Exception as e:
        return None


async def fetch_nodes():
    """从速度测试站拉取节点列表，按 allowed_orgs 过滤。"""
    hotel_api = config.hotel_config.get("hotel_api", "https://iptvs-speed.humorously.cn/")
    allowed_orgs = config.hotel_config.get("allowed_orgs", [])
    timeout = aiohttp.ClientTimeout(total=15)
    connector = aiohttp.TCPConnector(limit=5, ssl=False)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        data = await _fetch_json(session, hotel_api, 15)
    if not data or "results" not in data:
        logger.warning("[酒店源] 未获取到节点数据")
        return []
    all_nodes = data["results"]
    logger.info(f"[酒店源] 共获取 {len(all_nodes)} 个节点")
    if allowed_orgs:
        filtered = [n for n in all_nodes if n.get("org", "") in allowed_orgs]
        logger.info(f"[酒店源] 按运营商过滤后剩余 {len(filtered)} 个节点")
    else:
        filtered = all_nodes
    type_count = {}
    for n in filtered:
        t = n.get("matchType", "unknown")
        type_count[t] = type_count.get(t, 0) + 1
    logger.info(f"[酒店源] 类型分布: {type_count}")
    return filtered


async def parse_txiptv(session, host, timeout):
    """TXIPTV: 返回 {channel_name: url}"""
    result = {}
    url = f"{host}/iptv/live/1000.json?key=txiptv"
    data = await _fetch_json(session, url, timeout)
    if not data or data.get("code") != 0:
        return result
    for ch in data.get("data", []):
        name = ch.get("name", "").strip()
        path = ch.get("url", "").strip()
        if name and path:
            full_url = path if path.startswith("http") else f"{host}{path}"
            result[name] = full_url
    return result


async def parse_zhgxtrv(session, host, timeout):
    """ZHGXTV: 返回 {channel_name: url}，过滤乱码行"""
    result = {}
    url = f"{host}/ZHGXTV/Public/json/live_interface.txt"
    text = await _fetch_text(session, url, timeout)
    if not text:
        return result
    for line in text.splitlines():
        line = line.strip()
        if not line or "," not in line:
            continue
        parts = line.split(",", 1)
        if len(parts) != 2:
            continue
        name = parts[0].strip()
        channel_url = parts[1].strip()
        if not name or not channel_url:
            continue
        if re.search(r"[\u4e00-\u9fa5]", name):
            result[name] = channel_url
    return result


async def parse_jsmpeg(session, host, timeout):
    """JSMPEG: 返回 {channel_name: rtp_url}"""
    result = {}
    url = f"{host}/streamer/list"
    data = await _fetch_json(session, url, timeout)
    if not data or not isinstance(data, list):
        return result
    for item in data:
        name = item.get("name", "").strip()
        source = item.get("source", "").strip()
        if name and source:
            result[name] = source
    return result


async def fetch_all_from_hotel():
    """
    主入口：获取所有节点，按类型解析，返回 channels 格式。
    返回: {category: {channel_name: [urls]}}
    category 使用 matchType 作为分类名（txiptv / zhgxtv / jsmpeg）
    """
    nodes = await fetch_nodes()
    if not nodes:
        return {}
    by_type = {}
    for node in nodes:
        mt = node.get("matchType", "unknown")
        by_type.setdefault(mt, []).append(node)
    check_timeout = getattr(config, "check_timeout", 5)
    max_conn = getattr(config, "check_max_conn", 20)
    timeout = aiohttp.ClientTimeout(total=check_timeout)
    connector = aiohttp.TCPConnector(limit=max_conn, ssl=False)
    channels = {}
    async def _parse_node_with_mt(mt, node):
        host = node.get("link", "").rstrip("/")
        try:
            if mt == "txiptv":
                result = await parse_txiptv(session, host, timeout)
            elif mt == "zhgxtv":
                result = await parse_zhgxtrv(session, host, timeout)
            elif mt == "jsmpeg":
                result = await parse_jsmpeg(session, host, timeout)
            else:
                return
            for name, url in result.items():
                channels.setdefault(mt, {}).setdefault(name, []).append(url)
        except Exception as e:
            logger.warning(f"[酒店源] {node.get('link')} 解析异常: {e}")
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [_parse_node_with_mt(mt, node) for mt, nl in by_type.items() for node in nl]
        await asyncio.gather(*tasks)
    for cat in channels:
        for name in channels[cat]:
            channels[cat][name] = list(dict.fromkeys(channels[cat][name]))
    total = sum(len(urls) for ch in channels.values() for urls in ch.values())
    logger.info(f"[酒店源] 解析完成，共 {total} 个频道-URL 组合")
    return channels
