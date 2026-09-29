"""
Download Official Indian Railways 'Trains at a Glance' 2026 Data
===============================================================
Downloads:
1. Passengers Information: 19 official guideline PDFs
2. Content: 21 train classification and route index PDFs
3. Content/T: All 97 train timetable table PDFs (1.pdf to 97.pdf)
Stores data in both:
  - d:\\Yue\\Ura\\Sih 58\\NishkarshFoundData
  - D:\\Sih58\\NishkarshFoundData
"""

import os
import sys
import ssl
import time
import shutil
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# SSL Context to prevent certificate issues on government portals
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# 1. Passengers Information PDF links
PASSENGER_INFO_FILES = [
    ("Railway_and_Tourism.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Railways_Tourism.pdf"),
    ("Menu_for_Meals.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Menu_Meals.pdf"),
    ("Advance_Reservation.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Advance_Reservation.pdf"),
    ("Boarding_the_Train.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Boarding_Train.pdf"),
    ("Railway_Train_Enquiry.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Railway_Train_Enquiry.pdf"),
    ("Tatkal_Reservation.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Tatkal_Reservation.pdf"),
    ("Upgradation.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Upgradation.pdf"),
    ("Special_Facilities_for_Foreigners.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Special_Facilities_Foreighners.pdf"),
    ("Change_in_travel_plan.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Change_travel_plan.pdf"),
    ("Circular_Journey_Tickets.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Circular_Journey_Tickets.pdf"),
    ("Reserving_Special_Carriages.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Reservations_Special_Carriages.pdf"),
    ("Booking_of_Luggage.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Booking_Luggage.pdf"),
    ("Advance_Reservation_Through_Internet.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Advance_Reservation_Internet.pdf"),
    ("Refund_Rules.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Refund_Rules.pdf"),
    ("Passenger_Amenities.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Passenger_Amenities.pdf"),
    ("Vigilance_Organisation.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Vigilance_Organisation.pdf"),
    ("Citizens_Charter.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Citizen_Charter.pdf"),
    ("Fares.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Fares.pdf"),
    ("Railway_Protection_Force.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Railway_Protection_Force.pdf"),
]

# 2. Content PDF links
CONTENT_FILES = [
    ("How_to_use_the_Timetable.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/How_use.pdf"),
    ("How_to_Read_the_Table.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/How2Read.pdf"),
    ("Route_Map_with_Table_Numbers.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/RoutMap_Table_Index.pdf"),
    ("Station_Code_Index.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Station_Code_Index.pdf"),
    ("Trains_Number_Index.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/TableNumberIndex.pdf"),
    ("Train_Name_Index.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Train_Name_Index.pdf"),
    ("Vande_Bharat_Trains.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/VandeBharatTrains.pdf"),
    ("Rajdhani_Trains.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Rajdhani_Exp.pdf"),
    ("Duronto_Trains.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Duronto_Exp.pdf"),
    ("Shatabdi_Trains.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Shatabdi_Exp.pdf"),
    ("Humsafar_Trains.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Humsafar_Exp.pdf"),
    ("Antyodaya_Trains.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/AntyodayTrains.pdf"),
    ("Yuva_Tejas_Uday_Gatiman_Trains.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/YuvaTejas_Uday_GatimanTrains.pdf"),
    ("Sampark_Kranti_Trains.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Sampark_Kranti_Exp.pdf"),
    ("Double_Decker_Trains.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/DD.pdf"),
    ("Jan_Shatabdi_Trains.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Janshatabdi_Exp.pdf"),
    ("Amrit_Bharat_Trains.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Amrit_Bharat_Trains.pdf"),
    ("TOD_Special_Trains.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/TOD_Special_Trains.pdf"),
    ("Namo_Bharat_Rapid_Rail.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/NamoBharatRapidRail.pdf"),
    ("Table_Number_Index.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/TableNumberIndex.pdf"),
    ("Indian_Railways_Map.pdf", "https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/Map.pdf"),
]

# 3. Content/T: All 97 Table PDFs
TABLE_T_FILES = [
    (f"Table_{i:02d}.pdf", f"https://indianrailways.gov.in/railwayboard/uploads/directorate/coaching/TAG_2026/{i}.pdf")
    for i in range(1, 98)
]


def download_file(target_path: Path, url: str, retries: int = 3) -> tuple[str, bool, int, str]:
    """Downloads a single file with retries and verifies non-zero byte size."""
    if target_path.exists() and target_path.stat().st_size > 1024:
        return (target_path.name, True, target_path.stat().st_size, "Already exists")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target_path.with_suffix(".tmp")

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=CTX, timeout=30) as resp:
                if resp.status != 200:
                    raise Exception(f"HTTP Status {resp.status}")
                with open(tmp_path, "wb") as f:
                    shutil.copyfileobj(resp, f)

            if tmp_path.exists() and tmp_path.stat().st_size > 500:
                tmp_path.replace(target_path)
                return (target_path.name, True, target_path.stat().st_size, "Downloaded")
            else:
                if tmp_path.exists():
                    tmp_path.unlink()
                raise Exception("Downloaded file too small or empty")
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink()
            if attempt == retries - 1:
                return (target_path.name, False, 0, str(e))
            time.sleep(1.0)

    return (target_path.name, False, 0, "Failed all retries")


def run_batch_download(tasks: list[tuple[Path, str]], section_name: str, max_workers: int = 8):
    """Executes a pool of download tasks with real-time progress logging."""
    print(f"\n[{section_name}] Starting download of {len(tasks)} files with {max_workers} threads...")
    completed = 0
    failed = 0
    total_bytes = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(download_file, target_path, url): (target_path, url)
            for target_path, url in tasks
        }

        for future in as_completed(future_to_task):
            target_path, url = future_to_task[future]
            try:
                name, success, size, msg = future.result()
                if success:
                    completed += 1
                    total_bytes += size
                    print(f"  [OK {completed}/{len(tasks)}] {name} ({size / 1024:.1f} KB) - {msg}")
                else:
                    failed += 1
                    print(f"  [FAIL] {name}: {msg}")
            except Exception as exc:
                failed += 1
                print(f"  [ERROR] {target_path.name}: {exc}")

    print(f"[{section_name} COMPLETE] Success: {completed}/{len(tasks)}, Failed: {failed}, Total Size: {total_bytes / (1024*1024):.2f} MB")
    return completed, failed


def sync_to_mirror(source_dir: Path, target_dir: Path):
    """Copies or synchronizes files to the secondary workspace directory."""
    print(f"\n[SYNC] Mirroring {source_dir} -> {target_dir}...")
    if not source_dir.exists():
        return
    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
    print(f"[SYNC COMPLETE] Mirror synchronized successfully.")


def main():
    base_dir_primary = Path("D:/Sih58/NishkarshFoundData")
    base_dir_secondary = Path("d:/Yue/Ura/Sih 58/NishkarshFoundData")

    passengers_dir = base_dir_primary / "Passengers Information"
    content_dir = base_dir_primary / "Content"
    table_t_dir = content_dir / "T"

    passengers_dir.mkdir(parents=True, exist_ok=True)
    content_dir.mkdir(parents=True, exist_ok=True)
    table_t_dir.mkdir(parents=True, exist_ok=True)

    print("===================================================================")
    print("  DOWNLOADING INDIAN RAILWAYS 'TRAINS AT A GLANCE' (TAG) DATA")
    print(f"  Destination Primary  : {base_dir_primary}")
    print(f"  Destination Secondary: {base_dir_secondary}")
    print("===================================================================")

    # 1. Passengers Information
    p_tasks = [(passengers_dir / fname, url) for fname, url in PASSENGER_INFO_FILES]
    run_batch_download(p_tasks, "1. PASSENGERS INFORMATION", max_workers=6)

    # 2. Content
    c_tasks = [(content_dir / fname, url) for fname, url in CONTENT_FILES]
    run_batch_download(c_tasks, "2. CONTENT", max_workers=6)

    # 3. Content/T (All 97 Timetable PDFs)
    t_tasks = [(table_t_dir / fname, url) for fname, url in TABLE_T_FILES]
    run_batch_download(t_tasks, "3. CONTENT / T (97 TIMETABLES)", max_workers=10)

    # Mirror to workspace path
    sync_to_mirror(base_dir_primary, base_dir_secondary)

    print("\n===================================================================")
    print("  ALL DOWNLOADS AND DIRECTORY SYNC COMPLETED SUCCESSFULLY!")
    print("===================================================================")


if __name__ == "__main__":
    main()
