# 표준 라이브러리
import os
import sys
import subprocess
import csv
import time
import re
import configparser
import argparse

# 서드파티 라이브러리
import requests

CONFIG_FILE = "settings.cfg"

# ⚙️ 설정 로드 및 관리(기본 설정 파일(settings.cfg)을 생성합니다.)
def create_default_config():
    config = configparser.ConfigParser()
    config['RA_ACCOUNT'] = {
        '# RetroAchievements 사용자 이름과 API 키를 입력하세요.': '',
        '# API 키는 https://retroachievements.org/controlpanel.php 에서 발급받을 수 있습니다.': '',
        'username': 'your_username_here',
        'api_key': 'your_api_key_here'
    }
    config['PATHS'] = {
        'rahasher_path': './RAHasher.exe',
        'hash_output_path': './hashreports'
    }
    config['FILTERING'] = {
        '# 쉼표(,)로 구분하여 해시 비교에서 제외할 파일 확장자를 입력하세요.': '',
        'skip_extensions': '.txt, .srm, .state, .nfo, .bak, .doc, .pdf, .ini, .cfg, .log, .db, .xml, .json, .png, .jpg, .jpeg, .gif, .mp4, .bmp'
    }
    # 시스템 맵: 가독성을 위해 제조사별로 그룹화하고 주석을 추가합니다.
    config['SYSTEM_MAP'] = {
        '# RetroAchievements 시스템 이름': '로컬 ROM 폴더 이름',
        '# --- Nintendo ---': '',
        'Game Boy': 'gb',
        'Game Boy Advance': 'gba',
        'Game Boy Color': 'gbc',
        'NES/Famicom': 'nes',
        'Nintendo 64': 'n64',
        'Nintendo DS': 'nds',
        'Nintendo DSi': 'dsi',
        'SNES/Super Famicom': 'snes',
        'Virtual Boy': 'virtualboy',
        'Pokemon Mini': 'pokemonmini',
        'GameCube': 'gamecube',
        '# --- Sega ---': '',
        'Master System': 'mastersystem',
        'Genesis/Mega Drive': 'megadrive',
        '32X': 'sega32x',
        'Sega CD': 'segacd',
        'SG-1000': 'sg1000',
        'Saturn': 'saturn',
        'Dreamcast': 'dreamcast',
        'Game Gear': 'gamegear',
        '# --- Sony ---': '',
        'PlayStation': 'psx',
        'PlayStation 2': 'ps2',
        'PlayStation Portable': 'psp',
        '# --- NEC ---': '',
        'PC Engine/TurboGrafx-16': 'pcengine',
        'PC Engine CD/TurboGrafx-CD': 'pcenginecd',
        'PC-FX': 'pcfx',
        '# --- SNK ---': '',
        'Neo Geo Pocket': 'ngp',
        'Neo Geo CD': 'neogeocd',
        '# --- Other Consoles ---': '',
        '3DO Interactive Multiplayer': '3do',
        'Amstrad CPC': 'amstradcpc',
        'Apple II': 'apple2',
        'Arcadia 2001': 'arcadia',
        'Arduboy': 'arduboy',
        'Atari 2600': 'atari2600',
        'Atari 7800': 'atari7800',
        'Atari Jaguar': 'jaguar',
        'Atari Jaguar CD': 'jaguarcd',
        'Atari Lynx': 'lynx',
        'ColecoVision': 'colecovision',
        'Fairchild Channel F': 'channelf',
        'Intellivision': 'intellivision',
        'Interton VC 4000': 'vc4000',
        'Magnavox Odyssey 2': 'o2em',
        'Mega Duck': 'megaduck',
        'MSX': 'msx',
        'PC-8000/8800': 'pc8800',
        'Uzebox': 'uzebox',
        'Vectrex': 'vectrex',
        'Watara Supervision': 'supervision',
        'WonderSwan': 'wswan',
        'WASM-4': 'wasm4',
        'Standalone': 'standalone',
        'Elektor TV Games Computer': 'eletv',
        'Arcade': 'arcade'
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
        config.write(configfile)
    print(f"✅ '{CONFIG_FILE}' 파일이 생성되었습니다. '{CONFIG_FILE}'을 편집기로 열어서 사용자 이름과 API 키를 입력한 후 다시 실행해주세요.")
    sys.exit(0)

# settings.cfg 로드(settings.cfg 파일에서 설정을 로드합니다.)
def load_config():
    if not os.path.exists(CONFIG_FILE):
        create_default_config()

    config = configparser.ConfigParser(comment_prefixes=('#', ';'), allow_no_value=True)
    config.read(CONFIG_FILE, encoding='utf-8')

    settings = {}
    settings['RA_USERNAME'] = config.get('RA_ACCOUNT', 'username')
    settings['RA_API_KEY'] = config.get('RA_ACCOUNT', 'api_key')
    settings['RAHASHER_PATH'] = config.get('PATHS', 'rahasher_path')
    settings['HASH_OUTPUT_PATH'] = config.get('PATHS', 'hash_output_path')
    
    skip_ext_str = config.get('FILTERING', 'skip_extensions', fallback='')
    settings['SKIP_EXTENSIONS'] = [ext.strip() for ext in skip_ext_str.split(',') if ext.strip()]
    
    # 주석을 제외하고 실제 시스템 매핑만 로드합니다.
    system_map_items = config.items('SYSTEM_MAP')
    settings['SYSTEM_TO_FOLDER_MAP'] = {
        k.replace('_', ' '): v for k, v in system_map_items
        if v is not None and not k.startswith(config.comment_prefixes)
    }
    if settings['RA_USERNAME'] == 'your_username_here' or settings['RA_API_KEY'] == 'your_api_key_here':
        print(f"❌ '{CONFIG_FILE}' 파일에 RetroAchievements 계정 정보를 입력해주세요.")
        sys.exit(1)

    return settings

# 파일 확장자 확인(정규식을 사용하여 파일 확장자를 확인합니다.)
def should_skip(filename, skip_patterns):
    for pattern in skip_patterns:
        if pattern.search(filename):
            return True
    return False

# 콘솔 ID 조회(RA에서 모든 콘솔 ID를 가져와 이름-ID 맵을 생성합니다.)
def get_console_id_map(username, api_key):
    url = f"https://retroachievements.org/API/API_GetConsoleIDs.php?z={username}&y={api_key}&a=1&g=1"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        consoles = response.json()
        return {c["Name"].strip().lower(): c["ID"] for c in consoles}
    except requests.RequestException as e:
        print(f"❌ API 오류: 콘솔 목록을 가져올 수 없습니다. ({e})")
        return {}

# 게임 목록 조회
def get_ra_game_list(system_id, username, api_key):
    """특정 시스템 ID에 대한 RA 게임 목록을 가져옵니다."""
    url = f"https://retroachievements.org/API/API_GetGameList.php?z={username}&y={api_key}&i={system_id}&h=1"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ API 오류: 게임 목록을 가져올 수 없습니다 (System ID: {system_id}). ({e})")
        return []

# 해시 계산(RAHasher.exe를 사용하여 ROM 파일의 해시를 계산합니다.)
def get_rom_hash(system_id, rom_path, rahasher_path):
    try:
        result = subprocess.run(
            [rahasher_path, str(system_id), rom_path],
            capture_output=True, text=True, timeout=10
        )
        hash_val = result.stdout.strip()
        return hash_val if len(hash_val) == 32 else None
    except Exception as e:
        print(f"⚠️ 해시 실패: {os.path.basename(rom_path)} → {e}")
        return None

# 시스템 처리(지정된 시스템의 모든 ROM을 처리하고, 해시를 비교하여 결과를 분류합니다.)
def process_system(system_name, folder_name, settings, console_id_map, args):

    ## 시스템 경로 및 RA 데이터 준비
    system_path = os.path.join(args.dir, folder_name)
    if not os.path.exists(system_path):
        print(f"❌ 경로 없음: {system_path}")
        return [], []

    system_id = console_id_map.get(system_name.strip().lower())
    if not system_id:
        print(f"❌ 시스템 ID 없음: {system_name}")
        return [], []

    ra_games = get_ra_game_list(system_id, settings['RA_USERNAME'], settings['RA_API_KEY'])
    known_hashes = {h: g for g in ra_games for h in g.get("Hashes", [])}

    matched, unmatched = [], []

    ## ROM 파일 목록 수집
    if args.recursive:
        file_iter = (
            os.path.join(root, filename)
            for root, _, files in os.walk(system_path)
            for filename in files
        )
    else:
        file_iter = (os.path.join(system_path, f) for f in os.listdir(system_path))

    ## ROM 파일 순회 처리
    skip_patterns = [re.compile(re.escape(ext) + r'\d*$', re.IGNORECASE) for ext in settings['SKIP_EXTENSIONS']]
    for rom_path in file_iter:
        filename = os.path.basename(rom_path)

        ### 파일 유효성 검사
        if not os.path.isfile(rom_path):
            continue
        if should_skip(filename, skip_patterns):
            continue

        ### DRY-RUN 출력
        if args.dry_run:
            print(f"📝 [DRY-RUN] 처리 예정: {rom_path}")
            if args.verbose:
                try:
                    size = os.path.getsize(rom_path)
                    ext = os.path.splitext(rom_path)[1]
                    hash_val = get_rom_hash(system_id, rom_path, settings['RAHASHER_PATH'])
                    print(f"   └ 파일 크기: {size:,} bytes")
                    print(f"   └ 확장자: {ext}")
                    print(f"   └ 해시 값: {hash_val or '❌ 해시 실패'}")
                    print(f"   └ 파일 위치: {rom_path}")
                except Exception as e:
                    print(f"   └ 파일 정보 조회 실패: {e}")
            continue

        ### 해시 계산 및 비교
        hash_val = get_rom_hash(system_id, rom_path, settings['RAHASHER_PATH'])

        #### VERBOSE 출력
        if args.verbose:
            print(f"🔍 {filename} → Rom File 해시: {hash_val or '❌ 해시 실패'}")
            try:
                size = os.path.getsize(rom_path)
                ext = os.path.splitext(rom_path)[1]
                print(f"   └ 파일 크기: {size:,} bytes")
                print(f"   └ 확장자: {ext}")
                print(f"   └ 파일 위치: {rom_path}")
            except Exception as e:
                print(f"   └ 파일 정보 조회 실패: {e}")

        ### 결과 분류 및 일치 여부 출력
        if not hash_val:
            unmatched.append([rom_path, "Invalid hash"])
            if args.verbose:
                print(f"   ❌ 해시 계산 실패 → 비교 불가")
            continue

        if hash_val in known_hashes:
            game = known_hashes[hash_val]
            matched.append([
                rom_path,
                hash_val,
                game["Title"],
                game["ID"],
                game["NumAchievements"]
            ])
            if args.verbose:
                print(f"   ✅ 일치: {game['Title']} (ID: {game['ID']}, 업적: {game['NumAchievements']})")
        else:
            unmatched.append([rom_path, hash_val])
            if args.verbose:
                print(f"   ❌ 불일치: RA 데이터에 등록되지 않은 해시")

    ## 결과 반환
    return matched, unmatched

# 결과 저장
def save_results(matched, unmatched, system_name, system_id, hash_output_path):
    """해시 비교 결과를 CSV 파일로 저장합니다."""
    os.makedirs(hash_output_path, exist_ok=True)
    safe_name = system_name.replace("/", "_")
    output_path = os.path.join(hash_output_path, f"{safe_name}_{system_id}.csv")

    with open(output_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Status", "Game Title", "ROM Path", "Game ID", "Achievements", "MD5 Hash"])

        for row in matched:
            rom_path, hash_val, title, game_id, achievements = row
            writer.writerow(["Matched", title, rom_path, game_id, achievements, hash_val])

        for row in unmatched:
            rom_path, hash_val = row
            writer.writerow(["Unmatched", "", rom_path, "", "", hash_val])

# 자동 시스템 감지(지정된 ROM 경로에 존재하는 폴더를 기반으로 처리할 시스템을 자동으로 감지합니다.)
def auto_detect_systems(rom_base_path, system_to_folder_map):
    detected = []
    for system_name, folder_name in system_to_folder_map.items():
        system_path = os.path.join(rom_base_path, folder_name)
        if os.path.exists(system_path):
            detected.append(system_name)
    return detected

# RA API 기준 콘솔 목록 출력 (이름 기준 정렬-RA API에서 지원하는 콘솔 목록을 가져와 출력합니다.)
def print_available_consoles(username, api_key, system_to_folder_map):
    url = f"https://retroachievements.org/API/API_GetConsoleIDs.php?z={username}&y={api_key}&a=1&g=1"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        consoles = response.json()
    except requests.RequestException as e:
        print(f"❌ API 오류: 콘솔 목록을 가져올 수 없습니다. ({e})")
        return

    print("\n📋 RA에서 지원하는 콘솔 목록 (이름순 정렬):")
    for c in sorted(consoles, key=lambda x: x["Name"].lower()):
        name = c["Name"]
        folder = system_to_folder_map.get(name, "(매핑 없음)")
        print(f"- {name} → 폴더 이름: {folder}")

# 도움말 출력(명령줄 인자 파서를 생성합니다.)
def create_arg_parser():
    parser = argparse.ArgumentParser(
        description="RAHashComparer - RetroAchievements ROM 해시 비교 도구",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  py RAHashComparer.py snes
      → 현재 폴더에서 SNES ROM 처리

  py RAHashComparer.py snes gba -r
      → 하위 폴더 포함하여 SNES, GBA 처리

  py RAHashComparer.py psx --dir D:/RetroROMs
      → D:/RetroROMs 경로에서 PSX 처리

  py RAHashComparer.py -r
      → 현재 폴더에서 자동 감지된 콘솔 처리 (하위 폴더 포함)

  py RAHashComparer.py --dir E:/roms -r
      → E:/roms 경로에서 자동 감지된 콘솔 처리 (하위 폴더 포함)

Note:
  시스템 이름을 생략하면 지정된 ROM 경로에서 자동으로 감지된 콘솔만 처리됩니다.
  예: 'gba', 'snes' 폴더가 있으면 해당 콘솔만 자동 처리됩니다.
"""
    )
    parser.add_argument(
        'systems', nargs='*',
        help="처리할 시스템의 폴더 이름 (예: snes, gba). 생략 시 자동 감지"
    )
    parser.add_argument(
        '-r', '--recursive', action='store_true',
        help="하위 폴더까지 탐색"
    )
    parser.add_argument(
        '--dir', default=os.getcwd(),
        help="ROM 폴더 경로 지정 (기본값: 현재 폴더)"
    )
    parser.add_argument(
        '--list', action='store_true',
        help="지원 콘솔 목록 출력"
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help="해시 계산 없이 ROM 목록만 출력"
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help="처리 중인 ROM과 해시 정보를 실시간 출력"
    )
    return parser

# 메인 실행 함수
def main():
    settings = load_config()
    parser = create_arg_parser()
    args = parser.parse_args()

    if not os.path.exists(settings['RAHASHER_PATH']):
        print("❌ 필수 파일 없음: RAHasher.exe")
        print(f"'{settings['RAHASHER_PATH']}' 경로에 RAHasher.exe 파일이 없습니다.")
        sys.exit(1)

    if args.list:
        print_available_consoles(settings['RA_USERNAME'], settings['RA_API_KEY'], settings['SYSTEM_TO_FOLDER_MAP'])
        sys.exit(0)

    console_id_map = get_console_id_map(settings['RA_USERNAME'], settings['RA_API_KEY'])
    if not console_id_map:
        sys.exit(1)

    folder_to_system_map = {v.lower(): k for k, v in settings['SYSTEM_TO_FOLDER_MAP'].items()}
    
    if args.systems:
        systems_to_process = [folder_to_system_map[s.lower()] for s in args.systems if s.lower() in folder_to_system_map]
    else:
        systems_to_process = auto_detect_systems(args.dir, settings['SYSTEM_TO_FOLDER_MAP'])

    if not systems_to_process:
        print("❌ 처리할 시스템을 찾을 수 없습니다. 폴더가 존재하거나, 시스템 이름을 올바르게 입력했는지 확인하세요.")
        sys.exit(1)

    summary = []
    for system_name in systems_to_process:
        folder_name = settings['SYSTEM_TO_FOLDER_MAP'][system_name]

        print("\n" + "━" * 50)
        print(f"🎮 {system_name}")
        print("━" * 50)

        print(f"🔍 해시 비교 시작: {system_name}")
        matched, unmatched = process_system(system_name, folder_name, settings, console_id_map, args)

        if not matched and not unmatched:
            print(f"⚠️ 처리할 파일 없음: {system_name} → 결과 파일 생략")
            summary.append((system_name, 0, 0))
            continue

        system_id = console_id_map.get(system_name.strip().lower())
        save_results(matched, unmatched, system_name, system_id, settings['HASH_OUTPUT_PATH'])

        print(f"✅ 완료: {len(matched)}개 일치 / {len(unmatched)}개 불일치")
        print("📁 결과 저장 완료")
        print()
        summary.append((system_name, len(matched), len(unmatched)))

    # 전체 처리 결과 요약 (2개 이상 처리한 경우에만 출력)
    if len(systems_to_process) > 1:
        print("\n📊 전체 처리 결과 요약:")
        for s, m, u in summary:
            print(f"- {s}: {m}개 일치 / {u}개 불일치")

# ⏯️ 프로그램 진입점
if __name__ == "__main__":
    main()