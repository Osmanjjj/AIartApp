# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),          # フォーム表示や結果をまとめて扱うView
    path('generate/', views.generate_video, name='generate_video'),  # 生成処理
]
