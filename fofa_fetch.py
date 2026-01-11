import os
import re
import requests
import time
import concurrent.futures
import subprocess
from datetime import datetime, timezone, timedelta

# ===============================
# 配置区
FOFA_URLS = {
    "https://fofa.info/result?qbase64=InVkcHh5IiAmJiBjb3VudHJ5PSJDTiI%3D": "ip.txt",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

COUNTER_FILE = "计数.txt"
IP_DIR = "ip"
RTP_DIR = "rtp"
ZUBO_FILE = "zubo.txt"
IPTV_FILE = "IPTV.txt"

# ===============================

# 分类与映射配置
CHANNEL_CATEGORIES = {
    "央视频道": [
        "CCTV-1综合","CCTV-2财经","CCTV-3综艺","CCTV-4中文国际","CCTV-5体育","CCTV-5+体育赛事","CCTV-6电影","CCTV-7国防军事","CCTV-8电视剧","CCTV-9纪录","CCTV-10科教",
        "CCTV-11戏曲","CCTV-12社会与法","CCTV-13新闻","CCTV-14少儿","CCTV-15音乐","CCTV-16奥林匹克","CCTV-17农业农村",
        "CCTV4欧洲", "CCTV4美洲", "CCTV-兵器科技","CCTV-第一剧场","CCTV-电视指南","CCTV-风云剧场","CCTV-风云音乐","CCTV-风云足球","CCTV-高尔夫网球","CCTV-怀旧剧场",
        "CCTV-女性时尚","CCTV-世界地理","CCTV-央视台球","CCTV-文化精品","CCTV-卫生健康"
    ],
    "卫视频道": [
        "北京卫视","湖南卫视","深圳卫视","江苏卫视","东方卫视","浙江卫视","湖北卫视","天津卫视","广东卫视","山东卫视","辽宁卫视","安徽卫视","河北卫视","贵州卫视","东南卫视","重庆卫视","江西卫视","黑龙江卫视","云南卫视","河南卫视","四川卫视","广西卫视","吉林卫视","陕西卫视","山西卫视","内蒙古卫视","青海卫视","海南卫视","宁夏卫视","西藏卫视","新疆卫视","甘肃卫视","厦门卫视","兵团卫视","三沙卫视","延边卫视","安多卫视","康巴卫视","农林卫视"
    ],
    "凤凰频道": [
         "凤凰卫视中文台", "凤凰卫视资讯台", "凤凰卫视电影台"
    ],
    "4K频道": [
        "CCTV-4K超高清","CCTV-16奥林匹克4K",
        "北京卫视4K","东方卫视4K","广东卫视4K","深圳卫视4K","湖南卫视4K","江苏卫视4K","浙江卫视4K","山东卫视4K","四川卫视4K",
        "北京IPTV4K超清","广东4K超高清","华数爱上4K","云南4K频道","南国都市4K","欢笑剧场4K",
        "百事通电影4K","百事通纪实4K","百事通少儿4K","百事通4K-1","百事通4K-2",
        "4K乐享超清","中录动漫4K","亲子趣学4K","绚影4K"    
    ],
    "CHC频道": [
        "CHC动作电影", "CHC家庭影院", "CHC影迷电影"
    ],
    "华数频道": [
        "华数热播剧场","华数武侠剧场","华数谍战剧场","华数城市剧场","华数军旅剧场","华数古装剧场","华数经典电影","华数喜剧影院","华数动作影院","华数家庭影院","华数少儿动画","华数魅力时尚","华数星影","华数影视","华数动画","华数精选"
    ],
    "数字频道": [
        "重温经典","星空卫视",
        "求索纪录", "求索科学","求索生活", "求索动物", "纪实人文", "金鹰纪实", "纪实科教", "睛彩青少", "睛彩竞技", "睛彩篮球", "睛彩广场舞", "魅力足球", "五星体育",
        "劲爆体育", "快乐垂钓", "茶频道", "先锋乒羽", "天元围棋", "汽摩", "梨园频道", "文物宝库", "武术世界", "哒啵赛事", "哒啵电竞", "黑莓电影", "黑莓动画", 
        "乐游", "生活时尚", "都市剧场", "欢笑剧场", "游戏风云", "金色学堂", "动漫秀场", "新动漫", "卡酷少儿", "金鹰卡通", "优漫卡通", "哈哈炫动", "嘉佳卡通", 
        "中国交通", "中国天气","CETV-1","CETV-2","CETV-3","CETV-4","CETV早期教育"
    ],
    "北京频道": [
        "北京文艺频道","北京纪实科教","北京影视频道","北京财经频道","北京体育休闲","北京生活频道","北京新闻频道","北京卡酷少儿","北京国际频道",
        "北京IPTV淘BABY","北京IPTV淘剧场","北京IPTV淘电影","北京IPTV淘娱乐","北京IPTV萌宠TV"
    ] #任意添加，与仓库中rtp/省份运营商.txt内频道一致即可，或在下方频道名映射中改名
}

# ===== 映射（别名 -> 标准名） =====
CHANNEL_MAPPING = {
    "CCTV4欧洲": ["CCTV-4中文国际 欧洲"],
    "CCTV4美洲": ["CCTV-4中文国际 美洲"],
    "CCTV-5+体育赛事": ["CCTV5+体育赛事"],
    "CCTV-兵器科技": ["CCTV兵器科技"],
    "CCTV-第一剧场": ["CCTV第一剧场"],
    "CCTV-电视指南": ["CCTV电视指南"],
    "CCTV-风云剧场": ["CCTV风云剧场"],
    "CCTV-风云音乐": ["CCTV风云音乐"],
    "CCTV-风云足球": ["CCTV风云足球"],  
    "CCTV-高尔夫网球": ["CCTV高尔夫网球","CCTV-高尔夫·网球"],
    "CCTV-怀旧剧场": ["CCTV怀旧剧场"],
    "CCTV-女性时尚": ["CCTV女性时尚"],
    "CCTV-世界地理": ["CCTV世界地理"],
    "CCTV-卫生健康": ["CCTV卫生健康"],
    "CCTV-央视台球": ["CCTV央视台球"],
    "CCTV-文化精品": ["CCTV文化精品", "CCTV央视文化精品"],    
    "湖南卫视": ["湖南卫视FHD"],
    "凤凰卫视中文台": ["凤凰中文"],
    "凤凰卫视资讯台": ["凤凰资讯"],
    "凤凰卫视电影台": ["湖南卫视FHD"],
    "CCTV-4K超高清": ["CCTV4K超","CCTV4K超高清"],
    "北京卫视4K": ["北京卫视4K超","北京卫视4K超高清"],
    "湖南卫视4K": ["湖南卫视4K超高清"],
    "东方卫视4K": ["东方卫视4K超高清"],
    "广东卫视4K": ["广东卫视4K超高清"],
    "深圳卫视4K": ["深圳卫视4K超高清"],
    "山东卫视4K": ["山东卫视4K超高清"],
    "四川卫视4K": ["四川卫视4K超高清"],
    "浙江卫视4K": ["浙江卫视4K超高清"],
    "广东4K超高清": ["广东综艺4K"],
    "华数爱上4K": ["爱上4K","爱上-4K","爱上-4K","华数4K电影","华数爱上4K电影","华数电影4K"],
    "欢笑剧场4K": ["上海欢笑剧场4K"],
    "CHC动作电影": ["CHC-动作电影"],
    "CHC家庭影院": ["CHC-家庭影院"],
    "CHC影迷电影": ["CHC-影迷电影","CHC高清电影"],
    "华数电影": ["华数影视"],
    "CETV-1": ["CETV1"],
    "CETV-2": ["CETV2"],
    "CETV-3": ["CETV3"],
    "CETV-4": ["CETV4"],
    "北京卡酷少儿": ["北京KAKU少儿"]
}#格式为"频道分类中的标准名": ["rtp/中的名字"]

# ===============================


def get_run_count():
    if os.path.exists(COUNTER_FILE):
        try:
            return int(open(COUNTER_FILE, "r", encoding="utf-8").read().strip() or "0")
        except Exception:
            return 0
    return 0

def save_run_count(count):
    try:
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            f.write(str(count))
    except Exception as e:
        print(f"⚠️ 写计数文件失败：{e}")


# ===============================
def get_isp_from_api(data):
    isp_raw = (data.get("isp") or "").lower()

    if "telecom" in isp_raw or "ct" in isp_raw or "chinatelecom" in isp_raw:
        return "电信"
    elif "unicom" in isp_raw or "cu" in isp_raw or "chinaunicom" in isp_raw:
        return "联通"
    elif "mobile" in isp_raw or "cm" in isp_raw or "chinamobile" in isp_raw:
        return "移动"

    return "未知"


def get_isp_by_regex(ip):
    if re.match(r"^(1[0-9]{2}|2[0-3]{2}|42|43|58|59|60|61|110|111|112|113|114|115|116|117|118|119|120|121|122|123|124|125|126|127|175|180|182|183|184|185|186|187|188|189|223)\.", ip):
        return "电信"

    elif re.match(r"^(42|43|58|59|60|61|110|111|112|113|114|115|116|117|118|119|120|121|122|123|124|125|126|127|175|180|182|183|184|185|186|187|188|189|223)\.", ip):
        return "联通"

    elif re.match(r"^(223|36|37|38|39|100|101|102|103|104|105|106|107|108|109|134|135|136|137|138|139|150|151|152|157|158|159|170|178|182|183|184|187|188|189)\.", ip):
        return "移动"

    return "未知"


# ===============================
# 第一阶段
def first_stage():
    os.makedirs(IP_DIR, exist_ok=True)
    all_ips = set()

    for url, filename in FOFA_URLS.items():
        print(f"📡 正在爬取 {filename} ...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            urls_all = re.findall(r'<a href="http://(.*?)"', r.text)
            all_ips.update(u.strip() for u in urls_all if u.strip())
        except Exception as e:
            print(f"❌ 爬取失败：{e}")
        time.sleep(3)

    province_isp_dict = {}

    for ip_port in all_ips:
        try:
            host = ip_port.split(":")[0]

            is_ip = re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host)

            if not is_ip:
                try:
                    resolved_ip = socket.gethostbyname(host)
                    print(f"🌐 域名解析成功: {host} → {resolved_ip}")
                    ip = resolved_ip
                except Exception:
                    print(f"❌ 域名解析失败，跳过：{ip_port}")
                    continue
            else:
                ip = host

            res = requests.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=10)
            data = res.json()

            province = data.get("regionName", "未知")
            isp = get_isp_from_api(data)

            if isp == "未知":
                isp = get_isp_by_regex(ip)

            if isp == "未知":
                print(f"⚠️ 无法判断运营商，跳过：{ip_port}")
                continue

            fname = f"{province}{isp}.txt"
            province_isp_dict.setdefault(fname, set()).add(ip_port)

        except Exception as e:
            print(f"⚠️ 解析 {ip_port} 出错：{e}")
            continue

    count = get_run_count() + 1
    save_run_count(count)

    for filename, ip_set in province_isp_dict.items():
        path = os.path.join(IP_DIR, filename)
        try:
            with open(path, "a", encoding="utf-8") as f:
                for ip_port in sorted(ip_set):
                    f.write(ip_port + "\n")
            print(f"{path} 已追加写入 {len(ip_set)} 个 IP")
        except Exception as e:
            print(f"❌ 写入 {path} 失败：{e}")

    print(f"✅ 第一阶段完成，当前轮次：{count}")
    return count


# ===============================
# 第二阶段
def second_stage():
    print("🔔 第二阶段触发：生成 zubo.txt")
    if not os.path.exists(IP_DIR):
        print("⚠️ ip 目录不存在，跳过第二阶段")
        return

    combined_lines = []

    if not os.path.exists(RTP_DIR):
        print("⚠️ rtp 目录不存在，无法进行第二阶段组合，跳过")
        return

    for ip_file in os.listdir(IP_DIR):
        if not ip_file.endswith(".txt"):
            continue

        ip_path = os.path.join(IP_DIR, ip_file)
        rtp_path = os.path.join(RTP_DIR, ip_file)

        if not os.path.exists(rtp_path):
            continue

        try:
            with open(ip_path, encoding="utf-8") as f1, open(rtp_path, encoding="utf-8") as f2:
                ip_lines = [x.strip() for x in f1 if x.strip()]
                rtp_lines = [x.strip() for x in f2 if x.strip()]
        except Exception as e:
            print(f"⚠️ 文件读取失败：{e}")
            continue

        if not ip_lines or not rtp_lines:
            continue

        for ip_port in ip_lines:
            for rtp_line in rtp_lines:
                if "," not in rtp_line:
                    continue

                ch_name, rtp_url = rtp_line.split(",", 1)

                if "rtp://" in rtp_url:
                    part = rtp_url.split("rtp://", 1)[1]
                    combined_lines.append(f"{ch_name},http://{ip_port}/rtp/{part}")

                elif "udp://" in rtp_url:
                    part = rtp_url.split("udp://", 1)[1]
                    combined_lines.append(f"{ch_name},http://{ip_port}/udp/{part}")

    # 去重
    unique = {}
    for line in combined_lines:
        url_part = line.split(",", 1)[1]
        if url_part not in unique:
            unique[url_part] = line

    try:
        with open(ZUBO_FILE, "w", encoding="utf-8") as f:
            for line in unique.values():
                f.write(line + "\n")
        print(f"🎯 第二阶段完成，写入 {len(unique)} 条记录")
    except Exception as e:
        print(f"❌ 写文件失败：{e}")


# ===============================
# 第三阶段
def third_stage():
    print("🧩 第三阶段：多线程检测代表频道生成 IPTV.txt 并写回可用 IP 到 ip/目录（覆盖）")

    if not os.path.exists(ZUBO_FILE):
        print("⚠️ zubo.txt 不存在，跳过第三阶段")
        return

    def check_stream(url, timeout=5):
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_streams", "-i", url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout + 2
            )
            return b"codec_type" in result.stdout
        except Exception:
            return False

    # 别名映射
    alias_map = {}
    for main_name, aliases in CHANNEL_MAPPING.items():
        for alias in aliases:
            alias_map[alias] = main_name

    # 读取现有 ip 文件，建立 ip_port -> operator 映射
    ip_info = {}
    if os.path.exists(IP_DIR):
        for fname in os.listdir(IP_DIR):
            if not fname.endswith(".txt"):
                continue
            province_operator = fname.replace(".txt", "")
            try:
                with open(os.path.join(IP_DIR, fname), encoding="utf-8") as f:
                    for line in f:
                        ip_port = line.strip()
                        if ip_port:
                            ip_info[ip_port] = province_operator
            except Exception as e:
                print(f"⚠️ 读取 {fname} 失败：{e}")

    # 读取 zubo.txt 并按 ip:port 分组
    groups = {}
    with open(ZUBO_FILE, encoding="utf-8") as f:
        for line in f:
            if "," not in line:
                continue

            ch_name, url = line.strip().split(",", 1)
            ch_main = alias_map.get(ch_name, ch_name)
            m = re.match(r"http://([^/]+)/", url)
            if not m:
                continue

            ip_port = m.group(1)

            groups.setdefault(ip_port, []).append((ch_main, url))

    # 选择代表频道并检测
    def detect_ip(ip_port, entries):
        rep_channels = [u for c, u in entries if c == "CCTV1"]
        if not rep_channels and entries:
            rep_channels = [entries[0][1]]
        playable = any(check_stream(u) for u in rep_channels)
        return ip_port, playable

    print(f"🚀 启动多线程检测（共 {len(groups)} 个 IP）...")
    playable_ips = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(detect_ip, ip, chs): ip for ip, chs in groups.items()}
        for future in concurrent.futures.as_completed(futures):
            try:
                ip_port, ok = future.result()
            except Exception as e:
                print(f"⚠️ 线程检测返回异常：{e}")
                continue
            if ok:
                playable_ips.add(ip_port)

    print(f"✅ 检测完成，可播放 IP 共 {len(playable_ips)} 个")

    valid_lines = []
    seen = set()
    operator_playable_ips = {}

    for ip_port in playable_ips:
        operator = ip_info.get(ip_port, "未知")

        for c, u in groups.get(ip_port, []):
            key = f"{c},{u}"
            if key not in seen:
                seen.add(key)
                valid_lines.append(f"{c},{u}${operator}")

                operator_playable_ips.setdefault(operator, set()).add(ip_port)

    for operator, ip_set in operator_playable_ips.items():
        target_file = os.path.join(IP_DIR, operator + ".txt")
        try:
            with open(target_file, "w", encoding="utf-8") as wf:
                for ip_p in sorted(ip_set):
                    wf.write(ip_p + "\n")
            print(f"📥 写回 {target_file}，共 {len(ip_set)} 个可用地址")
        except Exception as e:
            print(f"❌ 写回 {target_file} 失败：{e}")

    # 写 IPTV.txt（包含更新时间与分类）
    beijing_now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    disclaimer_url = "http://ali-m-l.cztv.com/channels/lantian/channel001/1080p.m3u8"

    try:
        with open(IPTV_FILE, "w", encoding="utf-8") as f:
    #       f.write(f"更新时间: {beijing_now}（北京时间）\n\n")
            f.write("更新时间,#genre#\n")
            f.write(f"{beijing_now},{disclaimer_url}\n\n")

            for category, ch_list in CHANNEL_CATEGORIES.items():
                f.write(f"{category},#genre#\n")
                for ch in ch_list:
                    for line in valid_lines:
                        name = line.split(",", 1)[0]
                        if name == ch:
                            f.write(line + "\n")
                f.write("\n")
        print(f"🎯 IPTV.txt 生成完成，共 {len(valid_lines)} 条频道")
    except Exception as e:
        print(f"❌ 写 IPTV.txt 失败：{e}")

# ===============================
# 文件推送
def push_all_files():
    print("🚀 推送所有更新文件到 GitHub...")
    try:
        os.system('git config --global user.name "github-actions"')
        os.system('git config --global user.email "github-actions@users.noreply.github.com"')
    except Exception:
        pass

    os.system("git add 计数.txt || true")
    os.system("git add ip/*.txt || true")
    os.system("git add IPTV.txt || true")
    os.system('git commit -m "自动更新：计数、IP文件、IPTV.txt" || echo "⚠️ 无需提交"')
    os.system("git push origin main || echo '⚠️ 推送失败'")

# ===============================
# 主执行逻辑
if __name__ == "__main__":
    # 确保目录存在
    os.makedirs(IP_DIR, exist_ok=True)
    os.makedirs(RTP_DIR, exist_ok=True)

    run_count = first_stage()

    if run_count % 10 == 0:
        second_stage()
        third_stage()
    else:
        print("ℹ️ 本次不是 10 的倍数，跳过第二、三阶段")

    push_all_files()
