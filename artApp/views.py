# myapp/views.py

import os
import datetime
import time

import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse

from lumaai import LumaAI

# ----------------------------------------------------------------
# 1) インデックスページ (フォーム) を表示するビュー
# ----------------------------------------------------------------
def index(request):
    # シンプルにフォームを表示するだけの例
    return render(request, 'artApp/index.html')


# ----------------------------------------------------------------
# 2) フォーム送信時に動画生成 → ダウンロード → 表示するビュー
# ----------------------------------------------------------------
def generate_video(request):
    if request.method == 'POST':
        prompt = request.POST.get('prompt', '')
        aspect_ratio = request.POST.get('aspect_ratio', '16:9')
        loop_option = request.POST.get('loop', 'off')

        # チェックボックス(loop_option)は 'on'/'off' で渡ってくる想定
        # True/False に変換
        loop_flag = True if loop_option == 'on' else False

        # ----------------------------------------------------------------
        # 2-1) LumaAIクライアントの初期化
        # ----------------------------------------------------------------
        client = LumaAI(
    auth_token="LumaAPI"
)


        # ----------------------------------------------------------------
        # 2-2) ジェネレーションの作成
        # ----------------------------------------------------------------
        generation = client.generations.create(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            loop=loop_flag
        )

        # ----------------------------------------------------------------
        # 2-3) ステータスが "completed" になるまでポーリング
        # ----------------------------------------------------------------
        while generation.state not in ("completed", "failed"):
            # 連続でAPIを叩きすぎないよう 1秒スリープを挟む
            time.sleep(1)
            # 最新情報を取得
            generation = client.generations.get(generation.id)

        if generation.state == "failed":
            # 失敗したらメッセージを表示するなどの対応
            return HttpResponse("Generation failed. Please try again.", status=400)

        # ----------------------------------------------------------------
        # 2-4) 動画が完成した場合のダウンロード処理
        # ----------------------------------------------------------------
        # アセット(生成された動画のURL)を取得
        video_url = generation.assets.video

        # ファイル命名に日時・プロンプトを組み込み
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        sanitized_prompt = prompt.replace(" ", "_") or "video"

        # ここではIDを短く使いたい場合などに備え、[:8] を例示
        file_name = f"{timestamp}_{generation.id[:8]}_{sanitized_prompt}.mp4"

        # 保存先： media/ 以下に myapp_videos フォルダを用意すると良い
        output_dir = os.path.join(settings.MEDIA_ROOT, 'artApp_videos')
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, file_name)

        # 実際のダウンロード
        response = requests.get(video_url)
        with open(file_path, 'wb') as f:
            f.write(response.content)

        # ----------------------------------------------------------------
        # 2-5) 結果ページへ返却 or HTMLテンプレートに渡す
        # ----------------------------------------------------------------
        # 動画ファイルの相対URLを作り、テンプレートで再生できるようにする
        # 例: /media/myapp_videos/<filename>.mp4
        relative_path = os.path.join('artApp_videos', file_name)
        video_url_for_template = settings.MEDIA_URL + relative_path

        # テンプレートに生成済み動画URLやプロンプトを渡して、結果表示
        context = {
            "prompt": prompt,
            "video_path": video_url_for_template,
        }
        return render(request, 'artApp/result.html', context)

    # GETでアクセスされた場合など、適宜リダイレクト
    return redirect('index')
