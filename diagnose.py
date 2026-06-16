import os
import sys
import shutil

print("=== 🔍 가상 환경 상태 진단 결과 ===\n")

# 1. 실행 중인 Python 및 pip 경로 확인
print("[1] 실행 경로 확인")
print(f"- 현재 Python 경로: {sys.executable}")
pip_path = shutil.which('pip')
print(f"- 현재 pip 경로: {pip_path if pip_path else '찾을 수 없음'}\n")

# 2. VIRTUAL_ENV 환경 변수 확인
venv_env = os.environ.get('VIRTUAL_ENV')
print("[2] 가상 환경 활성화 상태 (VIRTUAL_ENV 변수)")
print(f"- {venv_env if venv_env else '활성화되지 않음 (또는 인식 불가)'}\n")

# 3. pyvenv.cfg 설정 확인
print("[3] pyvenv.cfg (시스템 패키지 포함 여부) 확인")
if venv_env:
    cfg_path = os.path.join(venv_env, 'pyvenv.cfg')
    if os.path.exists(cfg_path):
        found = False
        with open(cfg_path, 'r', encoding='utf-8') as f:
            for line in f:
                if 'include-system-site-packages' in line.lower():
                    print(f"- 설정값: {line.strip()}")
                    found = True
        if not found:
            print("- include-system-site-packages 설정이 파일에 없습니다.")
    else:
        print(f"- {cfg_path} 파일을 찾을 수 없습니다.")
else:
    print("- 가상 환경 변수가 없어 pyvenv.cfg 위치를 추적할 수 없습니다.")
print("")

# 4. PYTHONPATH 환경 변수 확인
print("[4] PYTHONPATH 환경 변수 확인")
python_path = os.environ.get('PYTHONPATH')
print(f"- {python_path if python_path else '설정되지 않음 (정상)'}\n")

# 5. sys.path (실제 패키지 탐색 경로) 확인
print("[5] Python 패키지 탐색 경로 (sys.path 중 site-packages만 출력)")
site_packages = [p for p in sys.path if 'site-packages' in p.lower()]
if site_packages:
    for path in site_packages:
        print(f"-> {path}")
else:
    print("- site-packages 경로를 찾을 수 없습니다.")
print("\n===================================")