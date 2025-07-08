
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.http import FileResponse
import os
import time
import pandas as pd
import shutil
from pathlib import Path
import shutil

from scraper.scripts.playwright_yahoo_deliverable1 import generate_yahoo_dv1
from scraper.scripts.playwright_yahoo_deliverable2 import generate_yahoo_dv2
from scraper.scripts.wi_cloudflare_deliverable3 import generate_wi_dv3
from scraper.scripts.bigchart_graph_1day_deliverable4 import generate_bigchart_1day
from scraper.scripts.bigchart_graph_5days_deliverable4 import generate_bigchart_5day

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(BASE_DIR, 'scraper', 'final_output.zip')

def dashboard(request):

    zip_ready = os.path.exists(ZIP_PATH)
    if request.method == 'POST' and request.FILES.get('input_file'):
        try:
            shutil.rmtree(os.path.join(BASE_DIR, 'scraper', 'output'))
        except Exception:
            pass

        try:
            os.remove(os.path.join(BASE_DIR, 'scraper', 'final_output.zip'))
        except Exception:
            pass

        try:
            os.remove(os.path.join(BASE_DIR, 'scraper', 'input_file.xlsx'))
        except Exception:
            pass

        input_file = request.FILES['input_file']
        input_path = os.path.join(BASE_DIR, 'scraper', 'input_file.xlsx')
        output_dir = os.path.join(BASE_DIR, 'scraper', 'output')

        # Save uploaded file
        with default_storage.open(input_path, 'wb+') as destination:
            for chunk in input_file.chunks():
                destination.write(chunk)

        # Cleanup previous output
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        # Begin script logic
        gmt_ts = int(time.time())
        df = pd.read_excel(input_path)
        df.columns = [col.strip().replace(' ', '_').replace('-', '_') for col in df.columns]
        names = []

        for idx, row in df.iterrows():
            WI_Symbol = row['WI_Symbol']
            WI_Name = row['WI_Name']
            WI_Link = row['WI_Link']
            WI_Hyperlink = row['WI_Hyperlink']
            YH_Symbol = row['YH_Symbol']
            YH_Name = row['YH_Name']
            Matching = row['Matching']
            YH_Hyperlink = row['YH_Hyperlink']

            name = f"{YH_Symbol}_{gmt_ts}"
            symbol_name = YH_Symbol.replace("=X", "") if isinstance(YH_Symbol, str) else str(YH_Symbol)

            names.append(name)
            entry_dir = os.path.join(output_dir, name)
            os.makedirs(entry_dir, exist_ok=True)

            generate_yahoo_dv1([Matching], os.path.join(entry_dir, f"yahoo_{symbol_name}_90days.json"), None)
            generate_yahoo_dv2([Matching], os.path.join(entry_dir, f"yahoo_{symbol_name}_1day.json"), None)
            generate_wi_dv3([WI_Link], os.path.join(entry_dir, f"walletinvestor_{symbol_name}_forecast.json"), None)

            onedaychart = generate_bigchart_1day(symbol_name, None)
            fivedaychart = generate_bigchart_5day(symbol_name, None)

            shutil.move(onedaychart, os.path.join(entry_dir, os.path.basename(onedaychart)))
            shutil.move(fivedaychart, os.path.join(entry_dir, os.path.basename(fivedaychart)))

        # Zip the final output
        if os.path.exists(ZIP_PATH):
            os.remove(ZIP_PATH)
        shutil.make_archive(ZIP_PATH.replace('.zip', ''), 'zip', output_dir)

        return redirect('dashboard')

    return render(request, 'scraper/dashboard.html', {'zip_ready': zip_ready})

def download_zip(request):
    if os.path.exists(ZIP_PATH):
        return FileResponse(open(ZIP_PATH, 'rb'), as_attachment=True, filename='final_output.zip')
    return redirect('dashboard')
