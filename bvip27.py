import base64
import hashlib
import json
import os
import platform
import random
import re
import string
import subprocess
import sys
import time
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone, date
from time import sleep
import glob
import threading

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    import pytz
    import requests
except ImportError:
    print('__Đang cài đặt các thư viện cần thiết, vui lòng chờ...__')
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "colorama", "pytz"])
    print('__Cài đặt hoàn tất, vui lòng chạy lại Tool__')
    sys.exit()

print_lock = threading.Lock()
job_history_lock = threading.Lock()
stats_lock = threading.Lock()

total_completed_tasks_count = 0
demsk_count = 0
SO_NV = 0
job_history = {}
proxy_list = []
proxy_rotator = None

FREE_CACHE_FILE = 'free_key_cache.json'    
VIP_CACHE_FILE = 'vip_cache.json'            
HANOI_TZ = pytz.timezone('Asia/Ho_Chi_Minh') 
VIP_KEY_URL = "https://raw.githubusercontent.com/DUONGKP2401/KEY-VIP.txt/main/KEY-VIP.txt" 
LAST_CLEAR_DATE_FILE = 'last_clear_date.txt'

def encrypt_data(data):
    return base64.b64encode(data.encode()).decode()

def decrypt_data(encrypted_data):
    return base64.b64decode(encrypted_data.encode()).decode()

xnhac = "\033[1;36m"
do = "\033[1;31m"
luc = "\033[1;32m"
vang = "\033[1;33m"
xduong = "\033[1;34m"
hong = "\033[1;35m"
trang = "\033[1;39m"
end = '\033[0m'

def authentication_banner():
    os.system("cls" if os.name == "nt" else "clear")
    banner_text = f"""
████████╗██████╗░██╗░░██╗
╚══██╔══╝██╔══██╗██║░██╔╝
░░░██║░░░██║░░██║█████═╝░
░░░██║░░░██║░░██║██╔═██╗░
░░░██║░░░██████╔╝██║░╚██╗
░░░╚═╝░░░╚═════╝░╚═╝░░╚═╝
══════════════════════════
👑Admin: DUONG PHUNG
🐬Tool BUMX FB-TDK- hỗ trợ proxy-VIP - ĐA LUỒNG
══════════════════════════
"""
    with print_lock:
        for char in banner_text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.0001)

def get_device_id():
    system = platform.system()
    try:
        if system == "Windows":
            cpu_info = subprocess.check_output('wmic cpu get ProcessorId', shell=True, text=True, stderr=subprocess.DEVNULL)
            cpu_info = ''.join(line.strip() for line in cpu_info.splitlines() if line.strip() and "ProcessorId" not in line)
        else:
            try:
                cpu_info = subprocess.check_output("cat /proc/cpuinfo", shell=True, text=True)
            except:
                cpu_info = platform.processor()
        if not cpu_info:
            cpu_info = platform.processor()
    except Exception:
        cpu_info = "Unknown"

    hash_hex = hashlib.sha256(cpu_info.encode()).hexdigest()
    only_digits = re.sub(r'\D', '', hash_hex)
    if len(only_digits) < 16:
        only_digits = (only_digits * 3)[:16]

    return f"DEVICE-{only_digits[:16]}"

def get_ip_address():
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        ip_data = response.json()
        return ip_data.get('ip')
    except Exception as e:
        prints(do, f"Lỗi lấy IP: {e}")
        return None

def display_machine_info(ip_address, device_id):
    authentication_banner()
    if ip_address:
        prints(f"{trang}[{do}<>{trang}] {do}Địa chỉ IP: {vang}{ip_address}{trang}")
    else:
        prints(f"{do}Không thể lấy địa chỉ IP.{trang}")

    if device_id:
        prints(f"{trang}[{do}<>{trang}] {do}Mã Máy: {vang}{device_id}{trang}")
    else:
        prints(f"{do}Không thể lấy Mã Máy.{trang}")

def save_vip_key_info(device_id, key, expiration_date_str):
    data = {'device_id': device_id, 'key': key, 'expiration_date': expiration_date_str}
    encrypted_data = encrypt_data(json.dumps(data))
    with open(VIP_CACHE_FILE, 'w') as file:
        file.write(encrypted_data)
    prints(f"{luc}Đã lưu thông tin Key VIP.{trang}")

def load_vip_key_info():
    try:
        with open(VIP_CACHE_FILE, 'r') as file:
            encrypted_data = file.read()
        return json.loads(decrypt_data(encrypted_data))
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return None

def display_remaining_time(expiry_date_str):
    try:
        expiry_date = datetime.strptime(expiry_date_str, '%d/%m/%Y').replace(hour=23, minute=59, second=59)
        now = datetime.now()

        if expiry_date > now:
            delta = expiry_date - now
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            prints(f"{xnhac}Key VIP còn lại: {luc}{days} ngày, {hours} giờ, {minutes} phút.{trang}")
        else:
            prints(f"{do}Key VIP đã hết hạn.{trang}")
    except ValueError:
        prints(f"{vang}Không thể xác định ngày hết hạn.{trang}")

def check_vip_key(machine_id, user_key):
    prints(f"{vang}Đang kiểm tra Key VIP...{trang}")
    try:
        response = requests.get(VIP_KEY_URL, timeout=10)
        if response.status_code != 200:
            prints(f"{do}Lỗi: Không thể tải danh sách key (Code: {response.status_code}).{trang}")
            return 'error', None

        key_list = response.text.strip().split('\n')
        for line in key_list:
            parts = line.strip().split('|')
            if len(parts) >= 4:
                key_ma_may, key_value, _, key_ngay_het_han = parts

                if key_ma_may == machine_id and key_value == user_key:
                    try:
                        expiry_date = datetime.strptime(key_ngay_het_han, '%d/%m/%Y')
                        if expiry_date.date() >= datetime.now().date():
                            return 'valid', key_ngay_het_han
                        else:
                            return 'expired', None
                    except ValueError:
                        continue
        return 'not_found', None
    except requests.exceptions.RequestException as e:
        prints(f"{do}Lỗi server key: {e}{trang}")
        return 'error', None
        
def seeded_shuffle_js_equivalent(array, seed):
    seed_value = 0
    for i, char in enumerate(seed):
        seed_value = (seed_value + ord(char) * (i + 1)) % 1_000_000_000
    def custom_random():
        nonlocal seed_value
        seed_value = (seed_value * 9301 + 49297) % 233280
        return seed_value / 233280.0
    shuffled_array = array[:]
    current_index = len(shuffled_array)
    while current_index != 0:
        random_index = int(custom_random() * current_index)
        current_index -= 1
        shuffled_array[current_index], shuffled_array[random_index] = shuffled_array[random_index], shuffled_array[current_index]
    return shuffled_array

def save_free_key_info(device_id, key, expiration_date):
    data = {device_id: {'key': key, 'expiration_date': expiration_date.isoformat()}}
    encrypted_data = encrypt_data(json.dumps(data))
    with open(FREE_CACHE_FILE, 'w') as file:
        file.write(encrypted_data)

def load_free_key_info():
    try:
        with open(FREE_CACHE_FILE, 'r') as file:
            encrypted_data = file.read()
        return json.loads(decrypt_data(encrypted_data))
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def check_saved_free_key(device_id):
    data = load_free_key_info()
    if data and device_id in data:
        try:
            expiration_date = datetime.fromisoformat(data[device_id]['expiration_date'])
            if expiration_date > datetime.now(HANOI_TZ):
                return data[device_id]['key']
        except (ValueError, KeyError):
            return None
    return None

def generate_free_key_and_url(device_id):
    today_str = datetime.now(HANOI_TZ).strftime('%Y-%m-%d')
    seed_str = f"TDK_FREE_KEY_{device_id}_{today_str}"
    hashed_seed = hashlib.sha256(seed_str.encode()).hexdigest()
    digits = [d for d in hashed_seed if d.isdigit()][:10]
    letters = [l for l in hashed_seed if 'a' <= l <= 'f'][:5]
    while len(digits) < 10:
        digits.extend(random.choices(string.digits))
    while len(letters) < 5:
        letters.extend(random.choices(string.ascii_lowercase))
    key_list = digits + letters
    shuffled_list = seeded_shuffle_js_equivalent(key_list, hashed_seed)
    key = "".join(shuffled_list)
    now_hanoi = datetime.now(HANOI_TZ)
    expiration_date = now_hanoi.replace(hour=21, minute=0, second=0, microsecond=0)
    url = f'https://tdkbumxkey.blogspot.com/2025/10/lay-link.html?m={key}'
    return url, key, expiration_date

def get_shortened_link_phu(url):
    try:
        token = "6725c7b50c661e3428736919"
        api_url = f"https://link4m.co/api-shorten/v2?api={token}&url={urllib.parse.quote(url)}"
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "message": f"Lỗi {response.status_code}: Lỗi dịch vụ rút gọn URL."}
    except Exception as e:
        return {"status": "error", "message": f"Lỗi rút gọn URL: {e}"}

def process_free_key(device_id):
    if datetime.now(HANOI_TZ).hour >= 21:
        prints(f"{do}Đã qua 21:00, key miễn phí đã hết hạn.{trang}")
        prints(f"{vang}Vui lòng quay lại vào ngày mai.{trang}")
        time.sleep(3)
        return False

    url, key, expiration_date = generate_free_key_and_url(device_id)
    shortened_data = get_shortened_link_phu(url)

    if shortened_data and shortened_data.get('status') == "error":
        prints(f"{do}{shortened_data.get('message')}{trang}")
        return False

    link_key_shortened = shortened_data.get('shortenedUrl')
    if not link_key_shortened:
        prints(f"{do}Không thể tạo link rút gọn. Thử lại.{trang}")
        return False

    prints(f'{trang}[{do}<>{trang}] {hong}Vui Lòng Vượt Link Lấy Key Free (Hết hạn 21:00).{trang}')
    prints(f'{trang}[{do}<>{trang}] {hong}Link Để Vượt Key {xnhac}: {link_key_shortened}{trang}')

    while True:
        keynhap = input(f'{trang}[{do}<>{trang}] {vang}Key Đã Vượt Là: {luc}')
        if keynhap == key:
            prints(f'{luc}Key Đúng! Mời Bạn Dùng Tool{trang}')
            if datetime.now(HANOI_TZ) >= expiration_date:
                prints(f"{do}Rất tiếc, key đã hết hạn lúc 21:00.{trang}")
                return False
            time.sleep(2)
            save_free_key_info(device_id, keynhap, expiration_date)
            return True
        else:
            prints(f'{trang}[{do}<>{trang}] {hong}Key Sai! Vui Lòng Vượt Lại Link {xnhac}: {link_key_shortened}{trang}')

def main_authentication():
    ip_address = get_ip_address()
    device_id = get_device_id()
    display_machine_info(ip_address, device_id)

    if not device_id:
        prints(f"{do}Không thể lấy Mã Máy.{trang}")
        return False

    cached_vip_info = load_vip_key_info()
    if cached_vip_info and cached_vip_info.get('device_id') == device_id:
        try:
            expiry_date = datetime.strptime(cached_vip_info['expiration_date'], '%d/%m/%Y')
            if expiry_date.date() >= datetime.now().date():
                prints(f"{luc}Tìm thấy Key VIP, tự động đăng nhập...{trang}")
                display_remaining_time(cached_vip_info['expiration_date'])
                sleep(3)
                return True
            else:
                prints(f"{vang}Key VIP đã lưu đã hết hạn.{trang}")
        except (ValueError, KeyError):
            prints(f"{do}Lỗi file lưu key VIP. Vui lòng nhập lại.{trang}")

    if check_saved_free_key(device_id):
        expiry_str = f"21:00 ngày {datetime.now(HANOI_TZ).strftime('%d/%m/%Y')}"
        prints(f"{trang}[{do}<>{trang}] {hong}Key free hôm nay vẫn còn hạn (Hết hạn {expiry_str}).{trang}")
        time.sleep(2)
        return True

    while True:
        prints(f"{trang}========== {vang}MENU LỰA CHỌN{trang} ==========")
        prints(f"{trang}[{luc}1{trang}] {xduong}Nhập Key VIP{trang}")
        prints(f"{trang}[{luc}2{trang}] {xduong}Lấy Key Free (Hết hạn 21:00){trang}")
        prints(f"{trang}======================================")

        try:
            choice = input(f"{trang}[{do}<>{trang}] {xduong}Nhập lựa chọn: {trang}")
            prints(f"{trang}═══════════════════════════════════")

            if choice == '1':
                vip_key_input = input(f'{trang}[{do}<>{trang}] {vang}Vui lòng nhập Key VIP: {luc}')
                status, expiry_date_str = check_vip_key(device_id, vip_key_input)

                if status == 'valid':
                    prints(f"{luc}Xác thực Key VIP thành công!{trang}")
                    save_vip_key_info(device_id, vip_key_input, expiry_date_str)
                    display_remaining_time(expiry_date_str)
                    sleep(3)
                    return True
                elif status == 'expired':
                    prints(f"{do}Key VIP đã hết hạn.{trang}")
                elif status == 'not_found':
                    prints(f"{do}Key VIP không hợp lệ.{trang}")
                else: 
                    prints(f"{do}Lỗi xác thực. Thử lại.{trang}")
                sleep(2)

            elif choice == '2':
                return process_free_key(device_id)

            else:
                prints(f"{vang}Lựa chọn không hợp lệ, nhập 1 hoặc 2.{trang}")

        except KeyboardInterrupt:
            prints(f"\n{trang}[{do}<>{trang}] {do}Cảm ơn bạn đã dùng Tool!{trang}")
            sys.exit()

def clear_caches_if_needed():
    prints(255, 255, 0, "Kiểm tra thời hạn cache...")
    try:
        today = date.today()
        last_clear_date_str = ""
        
        if os.path.exists(LAST_CLEAR_DATE_FILE):
            with open(LAST_CLEAR_DATE_FILE, 'r') as f:
                last_clear_date_str = f.read().strip()
        
        if not last_clear_date_str:
            with open(LAST_CLEAR_DATE_FILE, 'w') as f:
                f.write(today.isoformat())
            prints(0, 255, 0, "Thiết lập ngày dọn dẹp cache lần đầu.")
            return

        last_clear_date = date.fromisoformat(last_clear_date_str)
        days_passed = (today - last_clear_date).days

        if days_passed >= 2:
            prints(255, 165, 0, f"Đã {days_passed} ngày, đang dọn dẹp cache...")
            
            with job_history_lock:
                if os.path.exists(JOB_HISTORY_FILE):
                    try:
                        with open(JOB_HISTORY_FILE, 'w') as f:
                            json.dump({}, f)
                        prints(0, 255, 0, f"Đã dọn dẹp {JOB_HISTORY_FILE}")
                    except Exception as e:
                        prints(255, 0, 0, f"Lỗi dọn dẹp {JOB_HISTORY_FILE}: {e}")

            cookie_files = glob.glob('tdk-cookie-fb-bumx-*.txt')
            if cookie_files:
                prints(0, 255, 255, f"Tìm thấy {len(cookie_files)} file cookie để dọn dẹp...")
                for f_path in cookie_files:
                    try:
                        with open(f_path, 'w', encoding='utf-8') as f:
                            f.write("")
                        prints(0, 255, 0, f"Đã dọn dẹp {f_path}")
                    except Exception as e:
                        prints(255, 0, 0, f"Lỗi dọn dẹp {f_path}: {e}")
            
            with open(LAST_CLEAR_DATE_FILE, 'w') as f:
                f.write(today.isoformat())
            
            prints(0, 255, 0, "Dọn dẹp cache hoàn tất.")
        
        else:
            prints(0, 255, 0, f"Chưa đến 2 ngày, không dọn dẹp (còn {2 - days_passed} ngày).")
            
    except Exception as e:
        prints(255, 0, 0, f"Lỗi kiểm tra cache: {e}")

JOB_HISTORY_FILE = 'job_history.json'
COOKIE_JOB_LIMIT = 50
CONSECUTIVE_FAILURE_LIMIT = 4

SENSITIVE_KEYWORDS_VI = [
    'lừa đảo', 'scam', 'đảo chính', 'phản động', 'bạo lực', 'giết người',
    'khủng bố', 'biểu tình', 'ma túy', 'cờ bạc', 'mại dâm', 'khiêu dâm',
    'đồi trụy', 'xúc phạm', 'nhục mạ', 'chính trị', 'tôn giáo', 'sắc tộc',
    'lừa gạt', 'vay nặng lãi', 'tín dụng đen'
]


def load_job_history():
    with job_history_lock:
        try:
            with open(JOB_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

def save_job_history(history):
    with job_history_lock:
        try:
            with open(JOB_HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            prints(255, 0, 0, f"LỖI NGHIÊM TRỌNG: Không thể lưu job_history: {e}")


def has_job_been_done(history, user_id, buff_id):
    with job_history_lock:
        return buff_id in history.get(str(user_id), [])

def record_job_done(history, user_id, buff_id):
    with job_history_lock:
        user_id_str = str(user_id)
        if user_id_str not in history:
            history[user_id_str] = []
        if buff_id not in history[user_id_str]:
            history[user_id_str].append(buff_id)

class ProxyRotator:
    def __init__(self, proxies: list):
        self.proxies = proxies[:] if proxies else []
        self.i = 0
        self.lock = threading.Lock()

    def has_proxy(self):
        return bool(self.proxies)

    def current(self):
        with self.lock:
            if not self.proxies:
                return None
            return self.proxies[self.i % len(self.proxies)]

    def rotate(self):
        with self.lock:
            if not self.proxies:
                return None
            self.i = (self.i + 1) % len(self.proxies)
            return self.current()

def to_requests_proxies(proxy_str):
    if not proxy_str:
        return None
    p = proxy_str.strip().split(':')
    if len(p) == 4:
        try:
            host, port, user, past = p
            int(port)
        except ValueError:
            user, past, host, port = p
        return {
            'http':  f'http://{user}:{past}@{host}:{port}',
            'https': f'http://{user}:{past}@{host}:{port}',
        }
    if len(p) == 2:
        host, port = p
        return {
            'http':  f'http://{host}:{port}',
            'https': f'http://{host}:{port}',
        }
    return None

def check_proxy_fast(proxy_str):
    try:
        _sess = requests.Session()
        r = _sess.get(
            'http://www.google.com/generate_204',
            proxies=to_requests_proxies(proxy_str),
            timeout=6
        )
        return r.status_code in (204, 200)
    except Exception:
        return False

def get_proxy_info(proxy_str):
    try:
        _sess = requests.Session()
        r = _sess.get(
            'https://api64.ipify.org',
            proxies=to_requests_proxies(proxy_str),
            timeout=10
        )
        if r.status_code == 200:
            return r.text.strip()
    except:
        try:
            _sess = requests.Session()
            r = _sess.get(
                'http://api.ipify.org',
                proxies=to_requests_proxies(proxy_str),
                timeout=10
            )
            if r.status_code == 200:
                return r.text.strip()
        except:
            pass
    return "Unknown"

def check_proxy(proxy):
    session = requests.Session()
    try:
        response = session.post('https://kiemtraip.vn/check-proxy',
            data={'option': 'checkCountry', 'changeTimeout': '5000', 
                  'changeUrl': 'http://www.google.com', 'proxies': str(proxy)},
            timeout=10).text
        if '<span class="text-success copy">' in response:
            ip = response.split('<span class="text-success copy">')[1].split()[0].split('</span>')[0]
            return {'status': "success", 'ip': ip}
        else:
            return {'status': "error", 'ip': None}
    except:
        return {'status': "error", 'ip': None}

def add_proxy():
    i = 1
    proxy_list_local = []
    prints(255,255,0,"Nhập Proxy: user:pass:host:port hoặc host:port:user:pass")
    prints(255,255,0,"Nhấn Enter để bỏ qua.")
    while True:
        proxy = input(f'Nhập Proxy Số {i}: ').strip()
        if proxy == '':
            if i == 1:
                return []
            break
        try:
            check = check_proxy(proxy)
            if check['status'] == "success":
                i += 1
                prints(0,255,0,f'Proxy Hoạt Động: {check["ip"]}')
                proxy_list_local.append(proxy)
            else:
                prints(255,0,0,'Proxy Die! Nhập Lại!')
        except Exception as e:
            prints(255,0,0,f'Lỗi Check Proxy: {str(e)}')
    return proxy_list_local

def rotate_proxy():
    global proxy_rotator
    if not proxy_rotator or not proxy_rotator.has_proxy():
        return None
    
    tried = 0
    prints(255,255,0,'🔄 Đang tìm proxy live...')
    while tried < len(proxy_rotator.proxies):
        new_proxy = proxy_rotator.rotate()
        prints(255,255,0,f'🔍 Kiểm tra proxy: {new_proxy}')
        if check_proxy_fast(new_proxy):
            proxy_ip = get_proxy_info(new_proxy)
            prints(0,255,0,f'✅ Proxy live: {new_proxy} (IP: {proxy_ip})')
            return new_proxy
        else:
            prints(255,0,0,f'❌ Proxy die: {new_proxy}')
        tried += 1
    
    prints(255,0,0,'❌ Không tìm thấy proxy live nào!')
    return None

def clear_screen():
    os.system('cls' if platform.system() == "Windows" else 'clear')

def banner():
    clear_screen()
    banner_text = """
████████╗██████╗░██╗░░██╗
╚══██╔══╝██╔══██╗██║░██╔╝
░░░██║░░░██║░░██║█████═╝░
░░░██║░░░██║░░██║██╔═██╗░
░░░██║░░░██████╔╝██║░╚██╗
░░░╚═╝░░░╚═════╝░╚═╝░░╚═╝
    """
    colors = [
        (255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0),
        (0, 0, 255), (75, 0, 130), (148, 0, 211)
    ]
    color_index = 0
    for line in banner_text.split('\n'):
        for char in line:
            if char != ' ':
                r, g, b = colors[color_index % len(colors)]
                print(f"\033[38;2;{r};{g};{b}m{char}\033[0m", end='')
                time.sleep(0.0005)
                color_index += 1
            else:
                print(' ', end='')
        print()

    print(f"\033[38;2;{247};{255};{97}m" + "═" * 50 + "\033[0m")

    contacts = [
        ("👥 Zalo Group", "https://zalo.me/g/ddxsyp497"),
        ("✈️ Telegram", "@tankeko12"),
        ("👑 Admin", "DUONG PHUNG"),
        ("🌏Mua proxy tại ", "https://long2k4.id.vn/")
    ]

    for label, info in contacts:
        print(f"\033[38;2;{100};{200};{255}m  {label:<15}: \033[0m", end="")
        print(f"\033[38;2;{255};{255};{255}m{info}\033[0m")

    print(f"\033[38;2;{247};{255};{97}m" + "═" * 50 + "\033[0m")
    print()


def decode_base64(encoded_str):
    decoded_bytes = base64.b64decode(encoded_str)
    decoded_str = decoded_bytes.decode('utf-8')
    return decoded_str

def encode_to_base64(_data):
    byte_representation = _data.encode('utf-8')
    base64_bytes = base64.b64encode(byte_representation)
    base64_string = base64_bytes.decode('utf-8')
    return base64_string

def prints(*args, **kwargs):
    r, g, b = 255, 255, 255
    text = "text"
    end = "\n"

    if len(args) == 1:
        text = args[0]
    elif len(args) >= 3:
        r, g, b = args[0], args[1], args[2]
        if len(args) >= 4:
            text = args[3]
    if "text" in kwargs:
        text = kwargs["text"]
    if "end" in kwargs:
        end = kwargs["end"]

    with print_lock:
        print(f"\033[38;2;{r};{g};{b}m{text}\033[0m", end=end)

def facebook_info(cookie: str, proxy: str = None, timeout: int = 15):
    try:
        session = requests.Session()
        
        if proxy:
            session.proxies = to_requests_proxies(proxy)
        
        session_id = str(uuid.uuid4())
        fb_dtsg = ""
        jazoest = ""
        lsd = ""
        name = ""
        user_id = cookie.split("c_user=")[1].split(";")[0]

        headers = {
            "authority": "www.facebook.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-language": "vi",
            "sec-ch-prefers-color-scheme": "light",
            "sec-ch-ua": '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/106.0.0.0 Safari/537.36",
            "viewport-width": "1366",
            "Cookie": cookie
        }

        url = session.get(f"https://www.facebook.com/{user_id}", headers=headers, timeout=timeout).url
        response = session.get(url, headers=headers, timeout=timeout).text

        fb_token = re.findall(r'\["DTSGInitialData",\[\],\{"token":"(.*?)"\}', response)
        if fb_token:
            fb_dtsg = fb_token[0]

        jazo = re.findall(r'jazoest=(.*?)\"', response)
        if jazo:
            jazoest = jazo[0]

        lsd_match = re.findall(r'"LSD",\[\],\{"token":"(.*?)"\}', response)
        if lsd_match:
            lsd = lsd_match[0]

        get = session.get("https://www.facebook.com/me", headers=headers, timeout=timeout).url
        url = "https://www.facebook.com/" + get.split("%2F")[-2] + "/" if "next=" in get else get
        response = session.get(url, headers=headers, params={"locale": "vi_VN"}, timeout=timeout)

        data_split = response.text.split('"CurrentUserInitialData",[],{')
        json_data_raw = "{" + data_split[1].split("},")[0] + "}"
        parsed_data = json.loads(json_data_raw)

        user_id = parsed_data.get("USER_ID", "0")
        name = parsed_data.get("NAME", "")

        if user_id == "0" and name == "":
            prints(255, 0, 0, "Lỗi: Cookie die.")
            return {'success': False}
        elif "828281030927956" in response.text:
            prints(255, 0, 0, "Lỗi: Cookie checkpoint 956.")
            return {'success': False}
        elif "1501092823525282" in response.text:
            prints(255, 0, 0, "Lỗi: Cookie checkpoint 282.")
            return {'success': False}
        elif "601051028565049" in response.text:
            prints(255, 0, 0, "Lỗi: Cookie bị chặn spam.")
            return {'success': False}

        json_data = {
            'success': True,
            'user_id': user_id,
            'fb_dtsg': fb_dtsg,
            'jazoest': jazoest,
            'lsd': lsd,
            'name': name,
            'session': session,
            'session_id': session_id,
            'cookie': cookie,
            'headers': headers
        }
        return json_data

    except Exception as e:
        prints(255, 0, 0, f"Lỗi check cookie: {e}")
        return {'success': False}

def get_post_id(session,cookie,link):
    prints(255,255,0,f'Đang lấy post id',end='\r')
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'dpr': '1',
        'priority': 'u=0, i',
        'sec-ch-prefers-color-scheme': 'light',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v"140"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'cookie': cookie,
    }
    try:
        response = session.get(link, headers=headers, timeout=15).text
        response= re.sub(r"\\", "", response)
        
        page_id=''
        post_id=''
        stories_id=''
        permalink_id=''
        try:
            if '"post_id":"' in str(response):
                permalink_id=re.findall('"post_id":".*?"',response)[0].split(':"')[1].split('"')[0]
                prints(255,255,0,f'permalink_id: {permalink_id[:20]}      ',end='\r')
        except:
            pass
        try:
            if 'posts' in str(response):
                post_id=response.split('posts')[1].split('"')[0]
                post_id=post_id.replace("/", "")
                post_id = re.sub(r"\\", "", post_id)
                prints(255,255,0,f'Post id: {post_id[:20]}       ',end='\r')
        except:
            pass
        try:
            if 'storiesTrayType' in response and not '"profile_type_name_for_content":"PAGE"' in response:
                stories_id=re.findall('"card_id":".*?"',response)[0].split('":"')[1].split('"')[0]
                prints(255,255,0,f'stories_id: {stories_id[:20]}      ',end='\r')
        except:
            pass
        try:
            if '"page_id"' in response:
                page_id=re.findall('"page_id":".*?"',response)[0].split('id":"')[1].split('"')[0]
                prints(255,255,0,f'page_id: {page_id[:20]}        ',end='\r')
        except:
            pass
        return {'success':True,'post_id':post_id,'permalink_id':permalink_id,'stories_id':stories_id,'page_id':page_id}
    except Exception as e:
        prints(255,0,0,f'Lỗi lấy Post ID: {e}')
        return {'success':False}

def _parse_graphql_response(response):
    try:
        response_json = response.json()
        if 'errors' in response_json:
            error = response_json['errors'][0]
            error_msg = error.get('message', '').lower()
            
            if 'login required' in error_msg or 'session has expired' in error_msg:
                return {'status': 'cookie_dead', 'message': 'Cookie die (hết hạn).'}
            if 'temporarily blocked' in error_msg or 'spam' in error_msg:
                 return {'status': 'action_failed', 'message': 'Bị chặn spam.'}
            if 'permission' in error_msg:
                return {'status': 'action_failed', 'message': 'Không có quyền.'}

            return {'status': 'action_failed', 'message': f"Lỗi Facebook: {error.get('message', 'Không rõ')}"}
        
        if 'data' in response_json and response_json.get('data'):
            if any(v is None for v in response_json['data'].values()):
                 return {'status': 'action_failed', 'message': 'Lỗi: Dữ liệu trả về null.'}
            return {'status': 'success', 'data': response_json['data']}

        return {'status': 'action_failed', 'message': 'Lỗi: Phản hồi không có data.'}
    except json.JSONDecodeError:
        return {'status': 'action_failed', 'message': 'Lỗi giải mã JSON Facebook.'}
    except Exception as e:
        return {'status': 'action_failed', 'message': f'Lỗi phân tích JSON: {e}'}


def react_post_perm(data,object_id,type_react, proxy=None):
    prints(255,255,0,f'Đang thả {type_react} vào {object_id[:20]}       ',end='\r')
    headers = {
        'accept': '*/*', 'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.facebook.com',
        'priority': 'u=1, i', 'referer': 'https://www.facebook.com/'+str(object_id),
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'x-fb-friendly-name': 'CometUFIFeedbackReactMutation', 'x-fb-lsd': data['lsd'], 'cookie': data['cookie'],
    }
    react_list = {"LIKE": "1635855486666999","LOVE": "1678524932434102","CARE": "613557422527858","HAHA": "115940658764963","WOW": "478547315650144","SAD": "908563459236466","ANGRY": "444813342392137"}
    json_data = {
        'av': str(data['user_id']), '__user': str(data['user_id']), 'fb_dtsg': data['fb_dtsg'],
        'jazoest': str(data['jazoest']), 'lsd': str(data['lsd']), 'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'CometUFIFeedbackReactMutation',
        'variables': '{"input":{"attribution_id_v2":"CometSinglePostDialogRoot.react,comet.post.single_dialog,via_cold_start,'+str(int(time.time()*1000))+',893597,,,","feedback_id":"'+encode_to_base64(str('feedback:'+object_id))+'","feedback_reaction_id":"'+str(react_list.get(type_react.upper()))+'","feedback_source":"OBJECT","is_tracking_encrypted":true,"tracking":["AZWEqXNx7ELYfHNA7b4CrfdPexzmIf2rUloFtOZ9zOxrcEuXq9Nr8cAdc1kP5DWdKx-DdpkffT5hoGfKYfh0Jm8VlJztxP7elRZBQe5FqkP58YxifFUwdqGzQnJPfhGupHYBjoq5I5zRHXPrEeuJk6lZPblpsrYQTO1aDBDb8UcDpW8F82ROTRSaXpL-T0gnE3GyKCzqqN0x99CSBp1lCZQj8291oXhMoeESvV__sBVqPWiELtFIWvZFioWhqpoAe_Em15uPs4EZgWgQmQ-LfgOMAOUG0TOb6wDVO75_PyQ4b8uTdDWVSEbMPTCglXWn5PJzqqN4iQzyEKVe8sk708ldiDug7SlNS7Bx0LknC7p_ihIfVQqWLQpLYK6h4JWZle-ugySqzonCzb6ay09yrsvupxPUGp-EDKhjyEURONdtNuP-Fl3Oi1emIy61-rqISLQc-jp3vzvnIIk7r_oA1MKT065zyX-syapAs-4xnA_12Un5wQAgwu5sP9UmJ8ycf4h1xBPGDmC4ZkaMWR_moqpx1k2Wy4IbdcHNMvGbkkqu12sgHWWznxVfZzrzonXKLPBVW9Y3tlQImU9KBheHGL_ADG_8D-zj2S9JG2y7OnxiZNVAUb1yGrVVrJFnsWNPISRJJMZEKiYXgTaHVbZBX6CdCrA7gO25-fFBvVfxp2Do3M_YKDc5TtqBeiZgPCKogeTkSQt1B67Kq7FTpBYJ05uEWLpHpk1jYLH8ppQQpSEasmmKKYj9dg7PqbHPMUkeyBtL69_HkdxtVhDgkNzh1JerLPokIkdGkUv0RALcahWQK4nR8RRU2IAFMQEp-FsNk_VKs_mTnZQmlmSnzPDymkbGLc0S1hIlm9FdBTQ59--zU4cJdOGnECzfZq4B5YKxqxs0ijrcY6T-AOn4_UuwioY"],"session_id":"'+data['session_id']+'","actor_id":"'+str(data['user_id'])+'","client_mutation_id":"1"},"useDefaultActor":false,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false}',
        'server_timestamps': 'true', 'doc_id': '24034997962776771',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=json_data, timeout=15)
        response.raise_for_status()
        return _parse_graphql_response(response)
    except requests.exceptions.RequestException as e:
        return {'status': 'action_failed', 'message': f'Lỗi kết nối: {e}'}

def react_post_defaul(data,object_id,type_react, proxy=None):
    prints(255,255,0,f'Đang thả {type_react} vào {object_id[:20]}       ',end='\r')
    react_list = {"LIKE": "1635855486666999","LOVE": "1678524932434102","CARE": "613557422527858","HAHA": "115940658764963","WOW": "478547315650144","SAD": "908563459236466","ANGRY": "444813342392137"}
    headers = {
        'accept': '*/*', 'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.facebook.com',
        'priority': 'u=1, i', 'referer': 'https://www.facebook.com/'+str(object_id),
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'x-fb-friendly-name': 'CometUFIFeedbackReactMutation', 'x-fb-lsd': data['lsd'], 'cookie': data['cookie'],
    }
    json_data = {
        'av': str(data['user_id']), '__user': str(data['user_id']), 'fb_dtsg': data['fb_dtsg'],
        'jazoest': data['jazoest'], 'lsd': data['lsd'], 'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'CometUFIFeedbackReactMutation',
        'variables': '{"input":{"attribution_id_v2":"CometSinglePostDialogRoot.react,comet.post.single_dialog,via_cold_start,'+str(int(time.time()*1000))+',912367,,,","feedback_id":"'+encode_to_base64(str('feedback:'+object_id))+'","feedback_reaction_id":"'+str(react_list.get(type_react.upper()))+'","feedback_source":"OBJECT","is_tracking_encrypted":true,"tracking":["AZWEqXNx7ELYfHNA7b4CrfdPexzmIf2rUloFtOZ9zOxrcEuXq9Nr8cAdc1kP5DWdKx-DdpkffT5hoGfKYfh0Jm8VlJztxP7elRZBQe5FqkP58YxifFUwdqGzQnJPfhGupHYBjoq5I5zRHXPrEeuJk6lZPblpsrYQTO1aDBDb8UcDpW8F82ROTRSaXpL-T0gnE3GyKCzqqN0x99CSBp1lCZQj8291oXhMoeESvV__sBVqPWiELtFIWvZFioWhqpoAe_Em15uPs4EZgWgQmQ-LfgOMAOUG0TOb6wDVO75_PyQ4b8uTdDWVSEbMPTCglXWn5PJzqqN4iQzyEKVe8sk708ldiDug7SlNS7Bx0LknC7p_ihIfVQqWLQpLYK6h4JWZle-ugySqzonCzb6ay09yrsvupxPUGp-EDKhjyEURONdtNuP-Fl3Oi1emIy61-rqISLQc-jp3vzvnIIk7r_oA1MKT065zyX-syapAs-4xnA_12Un5wQAgwu5sP9UmJ8ycf4h1xBPGDmC4ZkaMWR_moqpx1k2Wy4IbdcHNMvGbkkqu12sgHWWznxVfZzrzonXKLPBVW9Y3tlQImU9KBheHGL_ADG_8D-zj2S9JG2y7OnxiZNVAUb1yGrVVrJFnsWNPISRJJMZEKiYXgTaHVbZBX6CdCrA7gO25-fFBvVfxp2Do3M_YKDc5TtqBeiZgPCKogeTkSQt1B67Kq7FTpBYJ05uEWLpHpk1jYLH8ppQQpSEasmmKKYj9dg7PqbHPMUkeyBtL69_HkdxtVhDgkNzh1JerLPokIkdGkUv0RALcahWQK4nR8RRU2IAFMQEp-FsNk_VKs_mTnZQmlmSnzPDymkbGLc0S1hIlm9FdBTQ59--zU4cJdOGnECzfZq4B5YKxqxs0ijrcY6T-AOn4_UuwioY"],"session_id":"'+str(data['session_id'])+'","actor_id":"'+data['user_id']+'","client_mutation_id":"1"},"useDefaultActor":false,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false}',
        'server_timestamps': 'true', 'doc_id': '24034997962776771',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=json_data, timeout=15)
        response.raise_for_status()
        return _parse_graphql_response(response)
    except requests.exceptions.RequestException as e:
        return {'status': 'action_failed', 'message': f'Lỗi kết nối: {e}'}

def react_stories(data,object_id, proxy=None):
    prints(255,255,0,f'Đang tim story {object_id[:20]}      ',end='\r')
    headers = {
        'accept': '*/*', 'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.facebook.com',
        'priority': 'u=1, i', 'referer': 'https://www.facebook.com/',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'x-fb-friendly-name': 'useStoriesSendReplyMutation', 'x-fb-lsd': data['lsd'], 'cookie': data['cookie']
    }
    json_data = {
        'av': str(data['user_id']), '__user': str(data['user_id']), 'fb_dtsg': data['fb_dtsg'],
        'jazoest': str(data['jazoest']), 'lsd': data['lsd'], 'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'useStoriesSendReplyMutation',
        'variables': '{"input":{"attribution_id_v2":"StoriesCometSuspenseRoot.react,comet.stories.viewer,via_cold_start,'+str(int(time.time()*1000))+',33592,,,","lightweight_reaction_actions":{"offsets":[0],"reaction":"❤️"},"message":"❤️","story_id":"'+str(object_id)+'","story_reply_type":"LIGHT_WEIGHT","actor_id":"'+str(data['user_id'])+'","client_mutation_id":"2"}}',
        'server_timestamps': 'true', 'doc_id': '9697491553691692',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response = data['session'].post('https://www.facebook.com/api/graphql/',  headers=headers, data=json_data, timeout=15)
        response.raise_for_status()
        return _parse_graphql_response(response)
    except requests.exceptions.RequestException as e:
        return {'status': 'action_failed', 'message': f'Lỗi kết nối: {e}'}

def react_post(data,link,type_react, proxy=None):
    res_object_id=get_post_id(data['session'],data['cookie'],link)
    if not res_object_id.get('success'):
        return {'status': 'action_failed', 'message': 'Lỗi: Không lấy được ID bài viết.'}
        
    if res_object_id.get('stories_id'):
        return react_stories(data,res_object_id['stories_id'], proxy)
    elif res_object_id.get('permalink_id'):
        return react_post_perm(data,res_object_id['permalink_id'],type_react, proxy)
    elif res_object_id.get('post_id'):
        return react_post_defaul(data,res_object_id['post_id'],type_react, proxy)
    
    return {'status': 'action_failed', 'message': 'Không tìm thấy đối tượng hợp lệ.'}

def comment_fb(data, object_id, msg, proxy=None):
    prints(255, 255, 0, f'Đang bình luận vào {object_id[:20]}', end='\r')
    headers = {
        'accept': '*/*', 'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.facebook.com',
        'priority': 'u=1, i', 'referer': 'https://www.facebook.com/',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'x-fb-friendly-name': 'useCometUFICreateCommentMutation', 'x-fb-lsd': data['lsd'], 'cookie': data['cookie'],
    }
    json_data = {
        'av': data['user_id'], '__user': str(data['user_id']), 'fb_dtsg': data['fb_dtsg'],
        'jazoest': data['jazoest'], 'lsd': data['lsd'], 'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'useCometUFICreateCommentMutation',
        'variables': '{"feedLocation":"DEDICATED_COMMENTING_SURFACE","feedbackSource":110,"groupID":null,"input":{"client_mutation_id":"4","actor_id":"'+str(data['user_id'])+'","attachments":null,"feedback_id":"'+str(encode_to_base64('feedback:'+str(object_id)))+'","formatting_style":null,"message":{"ranges":[],"text":"'+msg+'"},"attribution_id_v2":"CometHomeRoot.react,comet.home,via_cold_start,'+str(int(time.time()*1000))+',521928,4748854339,,","is_tracking_encrypted":true,"tracking":["AZX3K9tlBCG5xFInZx-hvHkdaGUGeTF2WOy5smtuctk2uhOd_YMY0HaF_dyAE8WU5PjpyFvAAM8x4Va39jb7YmcxubK8j4k8_16X1jtlc_TqtbWFukq-FUR93cTOBLEldliV6RILPNqYHH_a88DnwflDtg8NvluALzkLO-h8N8cxTQoSUQDPh206jaottUIfOxdZheWcqroL_1IaoZq9QuhwAUY4qu551-q7loObYLWHMcqA7XZFpDm6SPQ8Ne86YC3-sDPo093bfUGHae70FqOts742gWgnFy_t4t7TgRTmv1zsx0CXPdEh-xUx3bXPC6NEutzyNyku7Kdqgg1qTSabXknlJ7KZ_u9brQtmzs7BE_x4HOEwSBuo07hcm-UdqjaujBd2cPwf-Via-oMAsCsTywY-riGnW49EJhhycbj4HvshcHRDqk4iUTOaULV2CAOL7nGo5ACkUMoKbuWFl34uLoHhFJnpWaxPUef3ceL0ed19EChlYsnFl122VMJzRf6ymNtBQKbSfLkDF_1QYIofGvcRktaZOrrhnHdwihCPjBbHm17a3Cc3ax2KNJ6ViUjdj--KFE704jEjkJ9RXdZw3UIO-JjkvbCCeJ3Y-viGeank-vputYKtK1L05t2q5_6ool7PCIOufjNUrACbyeuOiLTyicyVvT013_jbYefSkhJ55PAtIqKn3JVbUpEWBYTWO8mkbU_UyjOnnhCZcagjWXYHKQ_Ne2gfLZN_WrpbEcLKdOtEm-l8J1RdnvYSTc13XVd85eL-k3da2OTamH7cJ_7bS6eJhQ0oSsrlGSJahq_JT9TV5IOffVeZWJ_SpcBwdPvzCRlMJIRljjSmgrCtfJrak8OgGtZM6jIZp6iZluUDlPEv1c_apazECx9CPC3pM1iu4QVdSdEzyBXbhul5hMDkSon4ahxJbWQ5ALpj-QAjfiCyz-aM0L5BqZLRug8_MdPk_ZWO3e70OX2LGHWKsd0ZGWP5kzpMqSMnkgTN5fGQ4A1QJ6EdEisqjclnSrD258ghVgKVEK9_PcIpGmmseB7fzrL1c5R65D4UZQq-kEpsuM42EhkAgfEEzrCTosmpRd7xibmd6aoVsOqCvJrvy_83bLE3-YTkhotHJeQxuLPWF1uvDSkhc_cs3ApJ1xFxHDZc5dikuMXne1azhKp5","{\\"assistant_caller\\":\\"comet_above_composer\\",\\"conversation_guide_session_id\\":\\"'+data['session_id']+'\\",\\"conversation_guide_shown\\":null}"],"feedback_source":"DEDICATED_COMMENTING_SURFACE","idempotence_token":"client:'+str(uuid.uuid4())+'","session_id":"'+data['session_id']+'"},"inviteShortLinkKey":null,"renderLocation":null,"scale":1,"useDefaultActor":false,"focusCommentID":null,"__relay_internal__pv__CometUFICommentAvatarStickerAnimatedImagerelayprovider":false,"__relay_internal__pv__IsWorkUserrelayprovider":false}',
        'server_timestamps': 'true', 'doc_id': '9379407235517228',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=json_data, timeout=15)
        response.raise_for_status()
        
        parsed_result = _parse_graphql_response(response)
        if parsed_result['status'] == 'success':
            try:
                comment_node = parsed_result.get('data', {}).get('comment_create', {}).get('feedback_comment_edge', {}).get('node', {})
                if comment_node:
                    comment_text = comment_node.get('preferred_body', {}).get('text', '')
                    prints(5, 255, 0, f'Đã bình luận: "{comment_text[:30]}..."', end='\r')
                    parsed_result['payload'] = comment_text
                    return parsed_result
                else:
                    return {'status': 'action_failed', 'message': 'Bình luận OK nhưng không có data.'}
            except (KeyError, TypeError):
                return {'status': 'action_failed', 'message': 'Lỗi cấu trúc phản hồi comment.'}
        return parsed_result
    except requests.exceptions.RequestException:
        return {'status': 'action_failed', 'message': 'Lỗi kết nối khi bình luận.'}

def dexuat_fb(data,object_id,msg, proxy=None):
    prints(255,255,0,f'Đang đề xuất Fanpage {object_id[:20]}        ',end='\r')
    if len(msg)<=25:
        msg+=' '*(26-len(msg))
    headers = {
        'accept': '*/*', 'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.facebook.com',
        'priority': 'u=1, i', 'referer': 'https://www.facebook.com/'+object_id,
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'x-fb-friendly-name': 'ComposerStoryCreateMutation', 'x-fb-lsd': data['lsd'], 'cookie': data['cookie']
    }
    json_data = {
        'av': str(data['user_id']), '__user': str(data['user_id']), 'fb_dtsg': data['fb_dtsg'],
        'jazoest': data['jazoest'], 'lsd': data['lsd'], 'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'ComposerStoryCreateMutation',
        'variables': '{"input":{"composer_entry_point":"inline_composer","composer_source_surface":"page_recommendation_tab","idempotence_token":"'+str(uuid.uuid4()) + "_FEED"+'","source":"WWW","audience":{"privacy":{"allow":[],"base_state":"EVERYONE","deny":[],"tag_expansion_state":"UNSPECIFIED"}},"message":{"ranges":[],"text":"'+str(msg)+'"},"page_recommendation":{"page_id":"'+str(object_id)+'","rec_type":"POSITIVE"},"logging":{"composer_session_id":"'+data['session_id']+'"},"navigation_data":{"attribution_id_v2":"ProfileCometReviewsTabRoot.react,comet.profile.reviews,unexpected,'+str(int(time.time()*1000))+','+str(random.randint(111111,999999))+',250100865708545,,;ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,via_cold_start,'+str(int(time.time()*1000))+','+str(random.randint(111111,999999))+',250100865708545,,"},"tracking":[null],"event_share_metadata":{"surface":"newsfeed"},"actor_id":"'+str(data['user_id'])+'","client_mutation_id":"1"},"feedLocation":"PAGE_SURFACE_RECOMMENDATIONS","feedbackSource":0,"focusCommentID":null,"scale":1,"renderLocation":"timeline","useDefaultActor":false,"isTimeline":true,"isProfileReviews":true,"__relay_internal__pv__CometUFIShareActionMigrationrelayprovider":true,"__relay_internal__pv__FBReels_deprecate_short_form_video_context_gkrelayprovider":true,"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider":true,"__relay_internal__pv__FBReelsIFUTileContent_reelsIFUPlayOnHoverrelayprovider":true}',
        'server_timestamps': 'true', 'doc_id': '24952395477729516',
    }
    try:
        if proxy:
            data['session'].proxies = to_requests_proxies(proxy)
        response = data['session'].post('https://www.facebook.com/api/graphql/', headers=headers, data=json_data, timeout=15)
        response.raise_for_status()
        
        parsed_result = _parse_graphql_response(response)
        if parsed_result['status'] == 'success':
            try:
                post_id = parsed_result['data']['story_create']['profile_review_edge']['node']['post_id']
                my_id = parsed_result['data']['story_create']['profile_review_edge']['node']['feedback']['owning_profile']['id']
                link_post = f'https://www.facebook.com/{my_id}/posts/{post_id}'
                link_p = get_lin_share(data, link_post, proxy)
                if link_p:
                    parsed_result['payload'] = link_p
                    return parsed_result
                else:
                    return {'status': 'action_failed', 'message': 'Đánh giá OK nhưng không lấy được link share.'}
            except (KeyError, TypeError):
                return {'status': 'action_failed', 'message': 'Lỗi cấu trúc phản hồi đánh giá.'}
        return parsed_result
    except requests.exceptions.RequestException as e:
        return {'status': 'action_failed', 'message': f'Lỗi kết nối khi đánh giá: {e}'}

def wallet(authorization):
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)', 'Content-Type': 'application/json',
        'lang': 'en', 'version': '37', 'origin': 'app', 'authorization': authorization,
    }
    try:
        response = requests.get('https://api-v2.bumx.vn/api/business/wallet', headers=headers, timeout=10).json()
        return response.get('data', {}).get('balance', 'N/A')
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
    except json.JSONDecodeError:
        return "Lỗi giải mã response"

def load(session,authorization,job):
    prints(255,255,0,f'Đang mở nhiệm vụ...',end='\r')
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)', 'Content-Type': 'application/json',
        'lang': 'en', 'version': '37', 'origin': 'app', 'authorization': authorization,
    }
    json_data = {'buff_id': job['buff_id']}
    try:
        response = session.post('https://api-v2.bumx.vn/api/buff/load-mission', headers=headers, json=json_data, timeout=10).json()
        return response
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        prints(255,0,0,f'Lỗi khi tải thông tin NV')
        return None

def get_job(session, authorization, type_job=None):
    if type_job:
        prints(255,255,0,f'Đang lấy nhiệm vụ {type_job}...',end='\r')
    else:
        prints(255,255,0,f'Đang lấy tất cả nhiệm vụ...',end='\r')
        
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)', 'lang': 'en', 'version': '37',
        'origin': 'app', 'authorization': authorization,
    }
    params = {'is_from_mobile': 'true'}
    
    if type_job:
        params['type'] = type_job
        
    try:
        response = session.get('https://api-v2.bumx.vn/api/buff/mission', params=params, headers=headers, timeout=10)
        response.raise_for_status()
        response_json = response.json()
    except requests.exceptions.RequestException:
        prints(255,0,0,f'Lỗi khi lấy NV')
        return []
    except json.JSONDecodeError:
        prints(255,0,0,f'Lỗi giải mã JSON khi lấy NV.')
        return []
    
    job_count = response_json.get('count', 0)
    if type_job:
        prints(255,255,255,f"Đã tìm thấy {job_count} NV {type_job}",end='\r')
    else:
        prints(255,255,255,f"Đã tìm thấy {job_count} NV (tổng)",end='\r')
        
    JOB=[]
    for i in response_json.get('data', []):
        json_job={
            "_id":i['_id'], "buff_id":i['buff_id'], "type":i['type'], "name":i['name'],
            "status":i['status'], "object_id":i['object_id'], "business_id":i['business_id'],
            "mission_id":i['mission_id'], "create_date":i['create_date'], "note":i['note'],
            "require":i['require'],
        }
        JOB.insert(0,json_job)
    return JOB

def reload(session, authorization, type_job, retries=3):
    prints(255, 255, 0, f'Đang tải danh sách NV {type_job}...', end='\r')
    if retries == 0:
        prints(255, 0, 0, f'Tải danh sách NV {type_job} thất bại.')
        return
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)', 'Content-Type': 'application/json',
        'lang': 'en', 'version': '37', 'origin': 'app', 'authorization': authorization,
    }
    json_data = {'type': type_job}
    try:
        response = session.post('https://api-v2.bumx.vn/api/buff/get-new-mission', headers=headers, json=json_data, timeout=10).json()
    except Exception:
        prints(255, 0, 0, f'Lỗi tải lại NV. Thử lại...')
        time.sleep(2)
        return reload(session, authorization, type_job, retries - 1)

def submit(session,authorization,job,reslamjob,res_load):
    prints(255,255,0,f'Đang hoàn thành nhiệm vụ',end='\r')
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)', 'Content-Type': 'application/json',
        'lang': 'en', 'version': '37', 'origin': 'app', 'authorization': authorization,
    }
    json_data = {
        'buff_id': job['buff_id'], 'comment': None, 'comment_id': None, 'code_submit': None,
        'attachments': [], 'link_share': '', 'code': '', 'is_from_mobile': True, 
        'type': job['type'], 'sub_id': None, 'data': None,
    }
    if job['type']=='like_facebook':
        json_data['comment'] = 'tt nha'
    elif job['type']=='like_poster':
        json_data['comment'] = res_load.get('data')
        json_data['comment_id'] = res_load.get('comment_id')
    elif job['type']=='review_facebook':
        json_data['comment'] = 'Helo Bạn chúc Bạn sức khỏe '
        json_data['link_share'] = reslamjob
    
    try:
        response = session.post('https://api-v2.bumx.vn/api/buff/submit-mission', headers=headers, json=json_data, timeout=10).json()
        if response.get('success') == True:
            message = response.get('message', '')
            _xu = '0'
            sonvdalam = '0'
            try:
                _xu = message.split('cộng ')[1].split(',')[0]
                sonvdalam = message.split('làm: ')[1]
            except IndexError:
                pass
            return [True,_xu,sonvdalam]
        return [False,'0','0']
    except Exception:
        prints(255,0,0,f'Lỗi khi submit')
        return [False,'0','0']
    
def report(session, authorization, job, retries=3):
    prints(255, 255, 0, f'Đang báo lỗi...', end='\r')
    if retries == 0:
        prints(255, 0, 0, f'Báo lỗi thất bại. Bỏ qua...')
        return
    headers = {
        'User-Agent': 'Dart/3.3 (dart:io)', 'Content-Type': 'application/json',
        'lang': 'en', 'version': '37', 'origin': 'app', 'authorization': authorization,
    }
    json_data = {'buff_id': job['buff_id']}
    try:
        response = session.post('https://api-v2.bumx.vn/api/buff/report-buff', headers=headers, json=json_data, timeout=10).json()
        prints(255, 165, 0, 'Đã báo lỗi thành công.')
    except Exception:
        prints(255, 165, 0, f'Báo lỗi không thành công, thử lại... ({retries-1})')
        time.sleep(2)
        return report(session, authorization, job, retries - 1)

def is_comment_sensitive(comment_text):
    text_lower = comment_text.lower()
    for keyword in SENSITIVE_KEYWORDS_VI:
        if keyword in text_lower:
            prints(255, 165, 0, f'Phát hiện từ nhạy cảm "{keyword}".')
            return True
    return False

def lam_job(data, jobs, type_job_doing, current_proxy=None):
    prints(255, 255, 0, f'Đang làm NV...', end='\r')
    link = 'https://www.facebook.com/' + jobs['object_id']
    
    result = {'status': 'action_failed', 'message': 'Hành động không xác định'}

    if type_job_doing == 'review_facebook':
        res_get_post_id = get_post_id(data['session'], data['cookie'], link)
        if res_get_post_id.get('page_id'):
            return dexuat_fb(data, res_get_post_id['page_id'], jobs['data'], current_proxy)
        else:
            result['message'] = 'Lỗi: Không lấy được Page ID.'
    
    elif type_job_doing == 'like_facebook':
        react_type = 'LIKE'
        icon = jobs.get('icon', '').lower()
        if 'love' in icon or 'thuongthuong' in icon: react_type = 'LOVE'
        elif 'care' in icon: react_type = 'CARE'
        elif 'wow' in icon: react_type = 'WOW'
        elif 'sad' in icon: react_type = 'SAD'
        elif 'angry' in icon: react_type = 'ANGRY'
        elif 'haha' in icon: react_type = 'HAHA'
        
        react_result = react_post(data, link, react_type.upper(), current_proxy)
        if react_result['status'] == 'success':
            prints(255, 255, 0, f'Đã thả {react_type}, chờ 10 giây...')
            time.sleep(10)
        return react_result

    elif type_job_doing == 'like_poster':
        res_get_post_id = get_post_id(data['session'], data['cookie'], link)
        post_id_to_comment = res_get_post_id.get('post_id') or res_get_post_id.get('permalink_id')
        if post_id_to_comment:
            
            comment_text_to_post = jobs.get('data') 
            if not comment_text_to_post:
                return {'status': 'action_failed', 'message': 'Lỗi: Không có nội dung comment.'}

            comment_result = comment_fb(data, post_id_to_comment, comment_text_to_post, current_proxy)
            
            if comment_result['status'] == 'success':
                comment_text = comment_result.get('payload', comment_text_to_post) 
                prints(255, 255, 0, f'Bình luận thành công: "{comment_text[:30]}...", chờ 10 giây...')
                time.sleep(10)
                
                return comment_result
            else:
                return comment_result
        else:
             result['message'] = 'Lỗi: Không lấy được Post ID.'

    return result

def countdown(seconds):
    seconds = int(seconds)
    if seconds < 1: return
    for i in range(seconds, 0, -1):
        prints(147, 112, 219, '[', end='')
        prints(0, 255, 127, "TDK", end='')
        prints(147, 112, 219, ']', end='')
        prints(255, 255, 255, '[', end='')
        prints(255, 215, 0, "WAIT", end='')
        prints(255, 255, 255, ']', end='')
        prints(255, 20, 147, ' ➤ ', end='')
        prints(0, 191, 255, f"⏳ {i}s...", end='\r')
        time.sleep(1)
    prints(' ' * 50, end='\r')

def get_lin_share(data,link, proxy=None):
    headers = {
        'accept': '*/*', 'accept-language': 'vi,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.facebook.com',
        'priority': 'u=1, i', 'referer': link,
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'x-fb-friendly-name': 'useLinkSharingCreateWrappedUrlMutation', 'x-fb-lsd': data['lsd'], 'cookie': data['cookie'],
    }
    payload = {
        'av': data['user_id'], '__user': data['user_id'], 'fb_dtsg': data['fb_dtsg'],
        'jazoest': data['jazoest'], 'lsd': data['lsd'], 'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'useLinkSharingCreateWrappedUrlMutation',
        'variables': '{"input":{"client_mutation_id":"3","actor_id":"'+str(data['user_id'])+'","original_content_url":"'+link+'","product_type":"UNKNOWN_FROM_DEEP_LINK"}}',
        'server_timestamps': 'true', 'doc_id': '30568280579452205',
    }
    try:
        proxies = to_requests_proxies(proxy) if proxy else None
        response = requests.post('https://www.facebook.com/api/graphql/',  headers=headers, data=payload, proxies=proxies, timeout=15).json()
        return response['data']['xfb_create_share_url_wrapper']['share_url_wrapper']['wrapped_url']
    except Exception as e:
        prints(255,0,0,f'Lỗi lấy link share: {e}')
        return ''

def add_account_fb(session,authorization,user_id):
    headers = {
        'Content-Type': 'application/json', 'lang': 'en', 'version': '37',
        'origin': 'app', 'authorization': authorization,
    }
    json_data = {'link': f'https://www.facebook.com/profile.php?id={str(user_id)}'}
    try:
        response = session.post('https://api-v2.bumx.vn/api/account-facebook/connect-link', headers=headers, json=json_data, timeout=10).json()
        prints(255,255,0,f"Khai báo FB: {response.get('message', 'No message')}")
    except Exception as e:
        prints(255,0,0,f"Lỗi khai báo FB: {e}")

def rgb(r, g, b, text):
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

def print_state(thread_id, status_job, _xu, jobdalam, dahoanthanh, tongcanhoanthanh, type_job, name_acc, bumx_acc_num):
    hanoi_tz = timezone(timedelta(hours=7))
    now = datetime.now(hanoi_tz).strftime("%H:%M")
    
    type_NV = {'like_facebook':'CX', 'like_poster':'CMT', 'review_facebook':'PAGE'}
    
    status_job_short = status_job.lower()
    if status_job_short == 'complete':
        status_color = rgb(0, 255, 0, 'OK')
    else:
        status_color = rgb(255, 255, 0, 'FAIL')

    thread_colors = [
        (0, 255, 255), (255, 0, 255), (0, 255, 0), (255, 255, 0),
        (255, 165, 0), (0, 191, 255), (255, 20, 147), (138, 43, 226),
        (240, 230, 140), (127, 255, 0)
    ]
    color = thread_colors[thread_id % len(thread_colors)]
    thread_color = rgb(color[0], color[1], color[2], f'L{thread_id}')
    
    name_acc_short = name_acc[:10]

    with print_lock:
        print(f"{rgb(255, 255, 255, '| ')}"
              f"[{thread_color}]"
              f"[{rgb(255, 165, 0, f'BUMX-{bumx_acc_num}')}]"
              f"[{rgb(255, 255, 255, name_acc_short)}]"
              f"[{Fore.LIGHTWHITE_EX}{now}{Style.RESET_ALL}]"
              f"[{Fore.LIGHTWHITE_EX}{dahoanthanh}/{tongcanhoanthanh}{Style.RESET_ALL}]"
              f"[{rgb(3, 252, 252, type_NV.get(type_job, '???'))}{Style.RESET_ALL}]"
              f"[{status_color}{Style.RESET_ALL}]"
              f"[{Fore.LIGHTWHITE_EX}+{_xu.strip()}{Style.RESET_ALL}]"
              f"[{Fore.LIGHTWHITE_EX}Làm:{jobdalam.strip()}{Style.RESET_ALL}]"
              f"{rgb(255, 255, 255, ' |')}")

def switch_facebook_account(cookie, authorization, bumx_session, proxy=None):
    prints(0, 255, 255, "\n--- Chuyển đổi tài khoản Facebook ---")
    data = facebook_info(cookie, proxy)
    if not data or not data.get('success'):
        prints(255, 0, 0, 'Cookie không hợp lệ. Bỏ qua.')
        return None
    
    prints(5, 255, 0, f"Đang dùng: {data['name']} ({data['user_id']})")
    add_account_fb(bumx_session, authorization, data['user_id'])
    return data

def worker_thread(thread_id, authorization, thread_cookies, list_type_job, proxy_rotator_ref, job_history_ref, bumx_acc_num):
    global total_completed_tasks_count, demsk_count, SO_NV

    tasks_on_current_cookie = 0
    consecutive_failures = 0
    current_cookie_index = 0
    bumx_session = requests.Session()
    all_available_jobs = []
    
    valid_cookies = thread_cookies[:] 

    if not valid_cookies:
        prints(255, 255, 0, f"[LUỒNG {thread_id}] Không có cookie nào được giao, luồng kết thúc.")
        return

    current_proxy = proxy_rotator_ref.current() if proxy_rotator_ref else None

    if current_proxy and not check_proxy_fast(current_proxy):
        prints(255,255,0,f'[L{thread_id}] ❌ Proxy lỗi, đang tìm proxy khác...')
        current_proxy = rotate_proxy()

    if current_proxy:
        proxy_ip = get_proxy_info(current_proxy)
        prints(0,255,255,f'[L{thread_id}] 🔗 Dùng proxy: {current_proxy} (IP: {proxy_ip})')
    else:
        prints(255,255,0,f'[L{thread_id}] ⚠️  Không sử dụng proxy')

    data = switch_facebook_account(valid_cookies[current_cookie_index], authorization, bumx_session, current_proxy)
    
    while not data:
        prints(255,0,0,f"[L{thread_id}] Cookie đầu tiên lỗi khi chuyển đổi. Loại bỏ.")
        valid_cookies.pop(current_cookie_index)
        
        if not valid_cookies:
            prints(255,0,0,f"[L{thread_id}] Không còn cookie nào. Dừng luồng.")
            return
            
        prints(255, 255, 0, f"[L{thread_id}] Thử cookie tiếp theo...")
        data = switch_facebook_account(valid_cookies[current_cookie_index], authorization, bumx_session, current_proxy)

    while True:
        try:
            with stats_lock:
                if total_completed_tasks_count >= SO_NV:
                    prints(0, 255, 0, f"[L{thread_id}] Đã đạt tổng số nhiệm vụ. Dừng luồng.")
                    break
            
            if current_proxy and not check_proxy_fast(current_proxy):
                prints(255,255,0,f'[L{thread_id}] ❌ Proxy chết, đang xoay proxy...')
                current_proxy = rotate_proxy()
                if current_proxy:
                    proxy_ip = get_proxy_info(current_proxy)
                    prints(0,255,255,f'[L{thread_id}] ✅ Proxy mới: {current_proxy} (IP: {proxy_ip})')
                else:
                    prints(255,0,0,f'[L{thread_id}] ❌ Không còn proxy live, chạy không proxy.')
                    current_proxy = None
            
            if consecutive_failures >= CONSECUTIVE_FAILURE_LIMIT and len(valid_cookies) > 1:
                prints(255, 0, 0, f"[L{thread_id}] Đã đạt {CONSECUTIVE_FAILURE_LIMIT} lỗi liên tiếp. Kiểm tra lại cookie...")
                
                check_data = facebook_info(data['cookie'], current_proxy)
                cookie_is_dead = not (check_data and check_data.get('success'))

                if cookie_is_dead:
                    prints(255, 0, 0, f"[L{thread_id}] Cookie đã DIE. Loại bỏ khỏi danh sách.")
                    valid_cookies.pop(current_cookie_index)
                else:
                    prints(0, 255, 0, f"[L{thread_id}] Cookie vẫn SỐNG. Lỗi có thể do proxy/FB quét. Tạm chuyển cookie khác.")
                    current_cookie_index = (current_cookie_index + 1) % len(valid_cookies)

                if not valid_cookies:
                    prints(255,0,0,f"[L{thread_id}] Tất cả cookie đều lỗi. Dừng luồng.")
                    break 

                current_cookie_index = current_cookie_index % len(valid_cookies)
                new_data = switch_facebook_account(valid_cookies[current_cookie_index], authorization, bumx_session, current_proxy)

                if new_data:
                    data = new_data
                    tasks_on_current_cookie = 0
                    consecutive_failures = 0
                else:
                    prints(255, 0, 0, f"[L{thread_id}] Cookie ...{valid_cookies[current_cookie_index][-20:]} khi chuyển cũng lỗi. Dừng luồng.")
                    break
                
                continue
            
            if tasks_on_current_cookie >= COOKIE_JOB_LIMIT and len(valid_cookies) > 1:
                prints(255, 255, 0, f"[L{thread_id}] Đã đạt {COOKIE_JOB_LIMIT} jobs. Chuyển cookie...")
                current_cookie_index = (current_cookie_index + 1) % len(valid_cookies)
                
                new_data = switch_facebook_account(valid_cookies[current_cookie_index], authorization, bumx_session, current_proxy)

                if new_data:
                    data = new_data
                    tasks_on_current_cookie = 0
                    consecutive_failures = 0
                else:
                    prints(255, 0, 0, f"[L{thread_id}] Cookie ...{valid_cookies[current_cookie_index][-20:]} khi chuyển lỗi. Loại bỏ.")
                    valid_cookies.pop(current_cookie_index)
                    
                    if not valid_cookies:
                        prints(255,0,0,f"[L{thread_id}] Tất cả cookie đều lỗi. Dừng luồng.")
                        break 

                    current_cookie_index = current_cookie_index % len(valid_cookies)
                    new_data = switch_facebook_account(valid_cookies[current_cookie_index], authorization, bumx_session, current_proxy)

                    if not new_data:
                        prints(255, 0, 0, f"[L{thread_id}] Cookie tiếp theo ...{valid_cookies[current_cookie_index][-20:]} cũng lỗi. Dừng luồng.")
                        break 
                    
                    data = new_data
                    tasks_on_current_cookie = 0
                    consecutive_failures = 0
                
                continue
            
            if not all_available_jobs:
                prints(0, 255, 255, f"\n[L{thread_id}] --- Hết nhiệm vụ, tải danh sách mới ---")
                for type_job in list_type_job:
                    reload(bumx_session, authorization, type_job)
                    time.sleep(2)
                    new_jobs = get_job(bumx_session, authorization, type_job)
                    if new_jobs:
                        prints(0, 255, 0, f"[L{thread_id}] Đã tìm thấy {len(new_jobs)} NV {type_job}.")
                        all_available_jobs.extend(new_jobs)
                    else:
                        prints(255, 255, 0, f"[L{thread_id}] Không có NV mới cho {type_job}.")
                
                if not all_available_jobs:
                    prints(255, 0, 0, f"[L{thread_id}] Không tìm thấy nhiệm vụ nào. Chờ 60 giây...")
                    countdown(60)
                    continue 
            
            job = all_available_jobs.pop(0)

            if has_job_been_done(job_history_ref, data['user_id'], job['buff_id']):
                prints(128, 128, 128, f"[L{thread_id}] Nhiệm vụ {job['buff_id']} đã làm, báo lỗi và bỏ qua.")
                report(bumx_session, authorization, job)
                time.sleep(2)
                continue
            
            try:
                res_load = load(bumx_session, authorization, job)
                time.sleep(random.randint(2, 4))
                
                if not (res_load and res_load.get('success')):
                    raise Exception("Load nhiệm vụ thất bại")
                
                if job['type'] == 'like_poster':
                    comment_content = res_load.get('data', '')
                    if is_comment_sensitive(comment_content):
                        prints(255, 165, 0, f"[L{thread_id}] Comment nhạy cảm. Báo lỗi.")
                        report(bumx_session, authorization, job)
                        with stats_lock:
                            demsk_count += 1
                        time.sleep(3)
                        continue 

                job_result = lam_job(data, res_load, job['type'], current_proxy)
                
                if job_result['status'] == 'success':
                    res_submit = submit(bumx_session, authorization, job, job_result.get('payload'), res_load)
                    if res_submit[0]:
                        with stats_lock:
                            total_completed_tasks_count += 1
                            current_total = total_completed_tasks_count
                        
                        tasks_on_current_cookie += 1
                        consecutive_failures = 0
                        
                        record_job_done(job_history_ref, data['user_id'], job['buff_id'])
                        save_job_history(job_history_ref)
                        
                        print_state(thread_id, 'complete', res_submit[1], res_submit[2], current_total, SO_NV, job['type'], data['name'], bumx_acc_num)
                        
                        post_submit_delay = random.randint(5, 15)
                        countdown(post_submit_delay)
                    else:
                        raise Exception("Submit nhiệm vụ thất bại")
                
                elif job_result['status'] == 'cookie_dead':
                    prints(255, 0, 0, f"[L{thread_id}] COOKIE DIE: {job_result.get('message', '')}, báo lỗi, chuyển cookie.")
                    report(bumx_session, authorization, job)
                    with stats_lock:
                        demsk_count += 1
                    consecutive_failures = CONSECUTIVE_FAILURE_LIMIT
                else:
                    prints(255, 165, 0, f"[L{thread_id}] Thất bại: {job_result.get('message', '')}, báo lỗi.")
                    report(bumx_session, authorization, job)
                    with stats_lock:
                        demsk_count += 1
                    consecutive_failures += 1
                    time.sleep(3)
                    
            except Exception as e:
                prints(255, 165, 0, f"[L{thread_id}] Lỗi NV: {e}, báo lỗi.")
                report(bumx_session, authorization, job)
                with stats_lock:
                    demsk_count += 1
                consecutive_failures += 1
                time.sleep(4)

        except KeyboardInterrupt:
            prints(255,255,0, f"\n[L{thread_id}] Đã dừng bởi người dùng.")
            break
        except Exception as e:
            prints(255,0,0,f'[L{thread_id}] Lỗi vòng lặp chính: {e}')
            time.sleep(10)

def main_bumx_free():
    global proxy_list, proxy_rotator, SO_NV, job_history
    
    clear_caches_if_needed()
    banner()
    
    def ask_job_list(thread_num):
        prints(66, 245, 245, f'''
Các loại nhiệm vụ cho Luồng {thread_num}:
 1. Thả cảm xúc
 2. Comment
 3. Đánh giá Fanpage
Nhập STT các loại NV cần làm (ví dụ: 12): ''',end='')
        
        x = input().strip()
        job_map = {'1': 'like_facebook', '2': 'like_poster', '3': 'review_facebook'}
        job_list = []
        for i in x:
            job_type = job_map.get(i)
            if job_type and job_type not in job_list:
                job_list.append(job_type)
        
        if not job_list:
             prints(255,0,0,f'Luồng {thread_num} không có nhiệm vụ nào được chọn.')
             return []
        
        prints(0, 255, 0, f"  > Luồng {thread_num} sẽ làm: {', '.join(job_list)}")
        return job_list

    proxy_list = []
    proxy_rotator = None
    
    if os.path.exists('tdk-proxy-vip.json'):
        prints(66, 245, 245,'Phát hiện file proxy đã lưu.')
        x=input(Fore.LIGHTWHITE_EX+'Dùng proxy đã lưu? (y/n): ')
        if x.lower()=='y':
            try:
                with open('tdk-proxy-vip.json', 'r') as f:
                    proxy_list = json.load(f)
                proxy_rotator = ProxyRotator(proxy_list)
                prints(0,255,0,f'Đã tải {len(proxy_list)} proxy.')
            except:
                prints(255,0,0,'Lỗi đọc file, nhập mới.')
                proxy_list = add_proxy()
                proxy_rotator = ProxyRotator(proxy_list)
                if proxy_list:
                    with open('tdk-proxy-vip.json', 'w') as f:
                        json.dump(proxy_list, f)
        else:
            proxy_list = add_proxy()
            proxy_rotator = ProxyRotator(proxy_list)
            if proxy_list:
                with open('tdk-proxy-vip.json', 'w') as f:
                    json.dump(proxy_list, f)
    else:
        prints(66, 245, 245,'Chưa có file proxy, nhập mới.')
        proxy_list = add_proxy()
        proxy_rotator = ProxyRotator(proxy_list)
        if proxy_list:
            with open('tdk-proxy-vip.json', 'w') as f:
                json.dump(proxy_list, f)

    num_bumx_accounts = 1
    prints(66, 245, 245, "Tool này được giới hạn 1 tài khoản BUMX.")

    authorizations_list = []
    for i in range(num_bumx_accounts):
        auth_file = f'tdk-auth-bumx-{i+1}.txt'
        authorization = ''
        if os.path.exists(auth_file):
            x = input(Fore.LIGHTCYAN_EX + f'Dùng auth Bumx đã lưu ({auth_file})? (y/n): ').lower()
            if x == 'y':
                with open(auth_file, 'r', encoding='utf-8') as f:
                    authorization = f.read().strip()
            else:
                authorization = input(Fore.LIGHTWHITE_EX + f'Nhập authorization Bumx thứ {i+1}: ').strip()
                with open(auth_file, 'w', encoding='utf-8') as f:
                    f.write(authorization)
                prints(5, 255, 0, f'Đã lưu vào {auth_file}')
        else:
            authorization = input(Fore.LIGHTWHITE_EX + f'Nhập authorization Bumx thứ {i+1}: ').strip()
            with open(auth_file, 'w', encoding='utf-8') as f:
                f.write(authorization)
            prints(5, 255, 0, f'Đã lưu vào {auth_file}')
        
        if authorization:
            prints(5,255,0,f'Kiểm tra số dư BUMX-{i+1}: {wallet(authorization)}')
            authorizations_list.append({'token': authorization, 'num': i+1})

    if not authorizations_list:
        prints(255,0,0, "Không có authorization. Dừng tool.")
        sys.exit(1)
    
    num_cookies = 0
    while num_cookies <= 0:
        try:
            num_cookies = int(input(Fore.LIGHTCYAN_EX + '\nNhập tổng số lượng cookie Facebook: '))
        except ValueError:
             prints(255, 0, 0, "Vui lòng nhập một số.")
             
    all_cookies = []
    for i in range(num_cookies):
        cookie_file = f'tdk-cookie-fb-bumx-{i+1}.txt'
        cookie = ''
        if os.path.exists(cookie_file):
            x = input(Fore.LIGHTCYAN_EX + f'Dùng cookie FB đã lưu ({cookie_file})? (y/n): ').lower()
            if x == 'y':
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookie = f.read().strip()
            else:
                cookie = input(Fore.LIGHTCYAN_EX + f'Nhập cookie FB thứ {i+1}: ').strip()
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    f.write(cookie)
                prints(5, 255, 0, f'Đã lưu vào {cookie_file}')
        else:
            cookie = input(Fore.LIGHTCYAN_EX + f'Nhập cookie FB thứ {i+1}: ').strip()
            with open(cookie_file, 'w', encoding='utf-8') as f:
                f.write(cookie)
            prints(5, 255, 0, f'Đã lưu vào {cookie_file}')
        if cookie:
            all_cookies.append({'cookie': cookie, 'file_num': i+1})

    if not all_cookies:
        prints(255,0,0, "Không có cookie. Dừng tool.")
        sys.exit(1)

    prints(255, 255, 0, f"\nĐổi cookie FB: sau {COOKIE_JOB_LIMIT} jobs hoặc {CONSECUTIVE_FAILURE_LIMIT} lỗi liên tiếp.")
    
    prints(0, 255, 255, "\nĐang kiểm tra và lọc cookie hợp lệ...")
    valid_cookies_info = []
    check_proxy_ip = proxy_rotator.current() if proxy_rotator else None
    
    for i, ck_info in enumerate(all_cookies):
        ck = ck_info['cookie']
        file_num = ck_info['file_num']
        prints(255, 255, 0, f"Kiểm tra cookie {i+1}/{len(all_cookies)} (từ file {file_num})...")
        info = facebook_info(ck, check_proxy_ip)
        if info and info.get('success'):
            prints(0, 255, 0, f"✅ Cookie hợp lệ: {info['name']} ({info['user_id']})")
            valid_cookies_info.append({
                'cookie': ck, 
                'name': info['name'], 
                'user_id': info['user_id'], 
                'file_num': file_num
            })
        else:
            prints(255, 165, 0, f"❌ Cookie từ file {file_num} không hợp lệ, bỏ qua.")
    
    if not valid_cookies_info:
        prints(255,0,0,"Không có cookie nào hợp lệ. Dừng tool.")
        sys.exit(1)
        
    print(Fore.LIGHTGREEN_EX + "\n--- DANH SÁCH COOKIE HỢP LỆ ---")
    for i, info in enumerate(valid_cookies_info):
        print(f"  {Fore.LIGHTWHITE_EX}[{i+1}] {info['name']} (File: tdk-cookie-fb-bumx-{info['file_num']}.txt)")
    print(Fore.LIGHTGREEN_EX + "---------------------------------")
    
    num_threads = 0
    while not (1 <= num_threads <= 2):
        try:
            num_threads = int(input(Fore.LIGHTCYAN_EX + f'\nNhập số luồng muốn chạy (tối đa 2): '))
            if not (1 <= num_threads <= 2):
                prints(255, 0, 0, "Vui lòng nhập 1 hoặc 2.")
        except ValueError:
            prints(255, 0, 0, "Vui lòng nhập một số.")

    thread_configs = []
    for i in range(1, num_threads + 1):
        prints(255, 255, 0, f"\n--- CẤU HÌNH CHO LUỒNG {i} ---")
        
        bumx_choice = 0
        while bumx_choice not in range(1, len(authorizations_list) + 1):
            try:
                bumx_choice_str = input(Fore.LIGHTWHITE_EX + f"  Dùng tài khoản Bumx số mấy (1-{len(authorizations_list)}): ")
                bumx_choice = int(bumx_choice_str)
            except ValueError:
                prints(255, 0, 0, "  Vui lòng nhập một số.")
        selected_auth = authorizations_list[bumx_choice-1]['token']
        selected_bumx_num = authorizations_list[bumx_choice-1]['num']

        selected_cookie_indices = []
        while not selected_cookie_indices:
            try:
                indices_str = input(Fore.LIGHTWHITE_EX + f"  Dùng các cookie SỐ MẤY (từ danh sách trên, ví dụ: 1,3,4): ")
                indices_parts = indices_str.split(',')
                temp_indices = []
                for part in indices_parts:
                    part = part.strip()
                    if not part: continue
                    idx = int(part)
                    if 1 <= idx <= len(valid_cookies_info):
                        if (idx-1) not in temp_indices:
                            temp_indices.append(idx-1)
                    else:
                        raise ValueError(f"Số {idx} không hợp lệ.")
                if not temp_indices:
                    prints(255,0,0, "  Vui lòng chọn ít nhất 1 cookie.")
                else:
                    selected_cookie_indices = temp_indices
            except Exception as e:
                prints(255,0,0, f"  Đầu vào không hợp lệ: {e}. Thử lại.")
                selected_cookie_indices = []
        
        thread_cookie_list = [valid_cookies_info[idx]['cookie'] for idx in selected_cookie_indices]
        prints(0, 255, 0, f"  > Luồng {i} sẽ dùng {len(thread_cookie_list)} cookies.")

        thread_job_list = ask_job_list(i)
        if not thread_job_list:
            prints(255, 165, 0, f"  Luồng {i} không có nhiệm vụ, sẽ không được khởi chạy.")
            continue

        thread_configs.append({
            'thread_id': i,
            'authorization': selected_auth,
            'cookies': thread_cookie_list,
            'jobs': thread_job_list,
            'bumx_acc_num': selected_bumx_num
        })

    if not thread_configs:
        prints(255,0,0, "Không có luồng nào được cấu hình hợp lệ. Dừng tool.")
        sys.exit(1)

    SO_NV=int(input(f'\n{Fore.LIGHTCYAN_EX}Làm tổng cộng bao nhiêu NV (cho tất cả {len(thread_configs)} luồng) thì dừng: '))
    job_history = load_job_history()
    
    time.sleep(2)
    clear_screen()
    banner()

    threads = []
    prints(0, 255, 0, f"--- BẮT ĐẦU {len(thread_configs)} LUỒNG ---")
    
    for config in thread_configs:
        t = threading.Thread(target=worker_thread, 
                             args=(config['thread_id'], 
                                   config['authorization'], 
                                   config['cookies'], 
                                   config['jobs'], 
                                   proxy_rotator, 
                                   job_history, 
                                   config['bumx_acc_num']),
                             daemon=True)
        threads.append(t)
        t.start()
        prints(0, 255, 0, f"Đã khởi chạy Luồng {config['thread_id']}...")
        time.sleep(0.5)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        prints(255,255,0, "\nĐã nhận lệnh dừng... Chờ các luồng kết thúc.")
        
    prints(5,255,0,f'\n--- TẤT CẢ ĐÃ HOÀN THÀNH ---')
    prints(5,255,0,f'Số nhiệm vụ đã hoàn thành: {total_completed_tasks_count}')
    prints(5,255,0,f'Số nhiệm vụ đã bỏ qua/lỗi: {demsk_count}')
    prints(5,255,0,f'Tổng: {demsk_count+total_completed_tasks_count}')


if __name__ == "__main__":
    try:
        is_authenticated = main_authentication()
        if is_authenticated:
            print(f"\n{luc}Xác thực thành công. Bắt đầu chạy tool...{trang}")
            time.sleep(2)
            main_bumx_free()
        else:
            print(f"\n{do}Xác thực không thành công. Dừng.{trang}")
            sys.exit()
    except Exception as e:
        print(f"\n{do}Tool đang bị lỗi: {e}{trang}")
        with open("error_log.txt", "a", encoding='utf-8') as f:
            f.write(f"{datetime.now()}: {str(e)}\n")
        time.sleep(3)
        sys.exit()
