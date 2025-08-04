import streamlit as st
import pandas as pd
import random
import os
from PIL import Image, ImageDraw
import geopandas as gpd
import matplotlib.pyplot as plt
from io import BytesIO


# CSV読み込み
df = pd.read_csv("cities.csv")
gdf = gpd.read_file('./N03-20230101_01_GML/N03-23_01_230101.geojson')
hokkaido = gdf[gdf['N03_001'] == '北海道']

# 有効な都市番号だけ抽出
valid_numbers = df["Number"].dropna().astype(int).tolist()

st.set_page_config(page_title='北海道179市町村カントリーサイン', layout='wide', initial_sidebar_state='auto')

# セッションステート初期化
if "history" not in st.session_state:
    st.session_state.history = []

if "show_full_image" not in st.session_state:
    st.session_state.show_full_image = False

def get_masked_image(image_path):
    img = Image.open(img_path).convert('RGBA')
    width, height = img.size

    mask = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(mask)
    draw.rectangle([3, height*3//4-5, width-3, height-2], fill=(255, 255, 150, 255))
    masked_img = Image.alpha_composite(img, mask)
    return masked_img


fig, ax = plt.subplots(figsize=(6, 6))

# ボタンが押されたときに処理を実行
if st.button("次の街へ"):
    selected_number = random.choice(valid_numbers)
    st.session_state.history.append(selected_number)
    st.session_state.show_full_image = False

# 最後に選ばれた都市のみ表示
if st.session_state.history:
    current_number = st.session_state.history[-1]
    city = df[df["Number"] == current_number].iloc[0]

    # レイアウト
    col1, _, col2 = st.columns([1.5, 1.2, 5])
    with col1:
        img_path = f"images/{current_number:03}.gif"
        if os.path.exists(img_path):
            if st.session_state.show_full_image:
                img = Image.open(img_path)
                st.image(img_path, caption=city["Name"], use_container_width=True)
            else:
                masked_img = get_masked_image(img_path)
                st.image(masked_img, use_container_width=True)
            if not st.session_state.show_full_image:
                if st.button('画像を全表示'):
                    st.session_state.show_full_image = True
                    st.rerun()
        else:
            st.warning("画像が見つかりません")

        st.markdown("##### 特産品")
        for item in city["Points"].split("/"):
            st.markdown(f"###### \t- {item}")
        st.markdown(f"**紹介:** {city['Info']}")
        st.write(f"人口: {city['Population']}人 / 面積: {city['Area']} km²")

    with col2:
        hokkaido.boundary.plot(ax=ax, linewidth=0.2, color='gray')
        hokkaido.plot(ax=ax, color='#FFFF99', edgecolor='black', linewidth=0.3)
        current_city_name = city['Name'].strip()
        target_geom = hokkaido[hokkaido["N03_004"] == current_city_name]

        if not target_geom.empty:
            target_geom.plot(ax=ax, color='red')
        else:
            print(f"Warning: {current_city_name} に一致する地物が見つかりませんでした")

        history_names = [df[df["Number"] == num].iloc[0]["Name"] for num in st.session_state.history[:-1]]

        for h in history_names:
            history_geom = hokkaido[hokkaido["N03_004"] == h.strip()]
            history_geom.plot(ax=ax, color='orange')

        ax.axis('off') 
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=200)
        buf.seek(0)
        map_img = Image.open(buf)
        st.image(map_img, use_container_width=True)

# 履歴の表示
if st.session_state.history:
    st.markdown("---")
    st.markdown("##### 📝 これまでに表示した都市の履歴")
    history_names = [df[df["Number"] == num].iloc[0]["Name"] for num in st.session_state.history[:-1]]
    st.markdown(" -> ".join(history_names))
    st.markdown("---")

    # 確認チェックボックスと削除ボタン
    st.markdown("##### ⚠️ 履歴を削除しますか？")
    if st.checkbox("削除"):
        if st.button("履歴を消去"):
            st.session_state.history = []
            st.success("履歴を消去しました。")
