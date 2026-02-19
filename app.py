import streamlit as st
import pandas as pd
from urllib.parse import quote
import io
import requests
import re

# ==========================================
# 🔗 CSV 發布連結
# ==========================================
URL_HERO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnMztwr71mxuf6pFYoSLlwBeEcxmNrQp0bfA84u3IJPp5DpBmjUwy4ndnL2Zf8mO6hhL1AzHPAXUx3/pub?gid=1879612607&single=true&output=csv"
URL_TYPE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnMztwr71mxuf6pFYoSLlwBeEcxmNrQp0bfA84u3IJPp5DpBmjUwy4ndnL2Zf8mO6hhL1AzHPAXUx3/pub?gid=384260746&single=true&output=csv"
URL_STRATEGY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRnMztwr71mxuf6pFYoSLlwBeEcxmNrQp0bfA84u3IJPp5DpBmjUwy4ndnL2Zf8mO6hhL1AzHPAXUx3/pub?gid=569984786&single=true&output=csv"

st.set_page_config(page_title="AI 全數據護膚系統", layout="wide")

def convert_google_drive_url(url):
    """將 Google Drive 分享網址轉換為直連網址"""
    if 'drive.google.com' in str(url) and '/file/d/' in str(url):
        try:
            file_id = url.split('/file/d/')[1].split('/')[0]
            return f"https://drive.google.com/uc?export=view&id={file_id}"
        except IndexError:
            return url
    return url

def safe_read_csv(url):
    try:
        safe_url = quote(url, safe=':/?&=')
        response = requests.get(safe_url)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
        return pd.DataFrame()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_all_data():
    df_hero = safe_read_csv(URL_HERO)
    df_type = safe_read_csv(URL_TYPE)
    df_strategy = safe_read_csv(URL_STRATEGY)

    for df in [df_hero, df_type, df_strategy]:
        if not df.empty:
            df.columns = df.columns.str.strip()
            for col in df.select_dtypes(include=['object']):
                df[col] = df[col].astype(str).str.strip().replace('nan', pd.NA).str.replace('，', ',').str.replace('、', ',')
    
    return df_hero, df_type, df_strategy

def main():
    st.markdown("# 🧪 AI 專業護膚成分推薦系統")
    df_hero, df_profile, df_strategy = load_all_data()

    # --- 1. 側邊欄 ---
    options = df_profile.iloc[:, 0].unique().tolist() if not df_profile.empty else ["油性肌", "乾性肌"]
    with st.sidebar:
        st.header("👤 您的膚質鑑定")
        selected_skin = st.selectbox("請選取您的肌膚類型", options)

    # --- 2. 階段一：膚質解析 ---
    if not df_profile.empty:
        profile_row = df_profile[df_profile.iloc[:, 0] == selected_skin]
        if not profile_row.empty:
            user_profile = profile_row.iloc[0]
            icon = user_profile.get('Icon') if pd.notna(user_profile.get('Icon')) else '✨'
            title = user_profile.get('標題') if pd.notna(user_profile.get('標題')) else ''
            feel = user_profile.get('自我感受') if pd.notna(user_profile.get('自我感受')) else '暫無資料'
            visual = user_profile.get('視覺特徵') if pd.notna(user_profile.get('視覺特徵')) else '暫無資料'

            st.markdown(f"## {icon} 您是 **{selected_skin}** — **「{title}」**")
            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    st.markdown("#### 💬 自我感受")
                    st.info(str(feel).replace('\n', '  \n'))
            with col2:
                with st.container(border=True):
                    st.markdown("#### 👁️ 視覺特徵")
                    st.warning(str(visual).replace('\n', '  \n'))

    st.markdown("---")

    # --- 3. 階段二：應對策略及成分推薦 ---
    st.subheader(f"🛡️ {selected_skin}：應對策略及成分推薦")

    current_strategies = []
    if not df_profile.empty and not profile_row.empty:
        strategy_col = next((c for c in df_profile.columns if '策略' in c), None)
        if strategy_col and pd.notna(profile_row.iloc[0][strategy_col]):
            raw_strategy = profile_row.iloc[0][strategy_col]
            current_strategies = [s.strip() for s in str(raw_strategy).split(',') if s.strip()]

    if not df_hero.empty and current_strategies:
        col_cat = next((c for c in df_hero.columns if '分類' in c), df_hero.columns[1] if len(df_hero.columns) > 1 else None)
        col_score = next((c for c in df_hero.columns if '分數' in c or 'Score' in c), df_hero.columns[4] if len(df_hero.columns) > 4 else None)
        col_name = next((c for c in df_hero.columns if '中文' in c), df_hero.columns[0])
        col_inci = next((c for c in df_hero.columns if 'INCI' in c), df_hero.columns[2] if len(df_hero.columns) > 2 else None)
        col_desc = next((c for c in df_hero.columns if '功效' in c or '描述' in c), df_hero.columns[3] if len(df_hero.columns) > 3 else None)

        for strategy in current_strategies:
            st.markdown(f"### 🎯 策略：{strategy}")
            
            strat_info = pd.DataFrame()
            if not df_strategy.empty:
                strat_info = df_strategy[df_strategy.iloc[:, 0] == strategy]
                if not strat_info.empty:
                    info_text_raw = strat_info.iloc[0, 1] if len(strat_info.columns) > 1 else ""
                    info_text = str(info_text_raw).replace('\n', '  \n') if pd.notna(info_text_raw) else "暫無詳細說明"
                    
                    # --- 圖片處理 ---
                    image_urls = []
                    for col_idx in [2, 3, 4]: # C, D, E 欄
                        if len(strat_info.columns) > col_idx:
                            raw_url = strat_info.iloc[0, col_idx]
                            if pd.notna(raw_url) and str(raw_url).strip().startswith('http'):
                                img_url = convert_google_drive_url(raw_url)
                                image_urls.append(img_url)

                    if image_urls:
                        cols = st.columns(len(image_urls))
                        for idx, img_url in enumerate(image_urls):
                            with cols[idx]:
                                st.image(img_url, use_container_width=True)
                    
                    with st.expander("💡 想知道更多", expanded=False):
                        st.markdown(info_text)

            # ==========================================
            # 👉 1. 顯示英雄成分推薦
            # ==========================================
            mask = df_hero[col_cat].str.contains(strategy, na=False)
            df_hero[col_score] = pd.to_numeric(df_hero[col_score], errors='coerce').fillna(0)
            top_ingredients = df_hero[mask].sort_values(by=col_score, ascending=False).head(5)

            st.markdown("#### ✨ 推薦成分")
            if not top_ingredients.empty:
                cols = st.columns(2)
                for idx, (_, row) in enumerate(top_ingredients.iterrows()):
                    with cols[idx % 2]:
                        ingredient_name = row[col_name] if pd.notna(row[col_name]) else "未知成分"
                        with st.expander(f"🏆 **{ingredient_name}**"):
                            inci = row[col_inci] if col_inci and pd.notna(row[col_inci]) else "N/A"
                            desc = row[col_desc] if col_desc and pd.notna(row[col_desc]) else "暫無描述"
                            
                            st.caption(f"INCI: {inci}")
                            score = int(row[col_score])
                            st.write(f"推薦指數：{'★' * score}")
                            st.progress(score * 20)
                            st.markdown(f"**功效**：\n{desc}")
            else:
                 st.caption(f"目前沒有針對「{strategy}」的特定成分推薦。")

            # ==========================================
            # 👉 2. 影片處理
            # ==========================================
            if not strat_info.empty:
                video_data = []
                for col_idx in [5, 6, 7]: # F, G, H 欄
                    if len(strat_info.columns) > col_idx:
                        raw_cell_value = strat_info.iloc[0, col_idx]
                        if pd.notna(raw_cell_value) and str(raw_cell_value).strip():
                            cell_str = str(raw_cell_value).strip()
                            
                            # 預防性修正：將中文全形的「｜」替換成半形的「|」
                            cell_str = cell_str.replace('｜', '|')
                            
                            # 解析標題與網址
                            if '|' in cell_str:
                                parts = cell_str.split('|', 1)
                                video_title = parts[0].strip()
                                vid_url = parts[1].strip()
                            else:
                                video_title = None 
                                vid_url = cell_str
                            
                            # 確保網址部分真的是網址
                            if vid_url.startswith('http'):
                                video_data.append({"title": video_title, "url": vid_url})
                
                if video_data:
                    st.markdown("#### 🎬 相關影音")
                    
                    # 定義一個外層容器，開啟 overflow-x 來實現左右滑動
                    html_content = '''
                    <div style="display: flex; overflow-x: auto; gap: 16px; padding-bottom: 12px; width: 100%; font-family: sans-serif;">
                    '''
                    
                    for idx, item in enumerate(video_data):
                        display_title = item["title"] if item["title"] else f"🎬 推薦影片 {idx + 1}"
                        vid_url = item["url"]
                        
                        # 如果是 Bilibili 連結
                        if 'bilibili.com' in vid_url or 'b23.tv' in vid_url:
                            match = re.search(r'(BV[a-zA-Z0-9]+)', vid_url)
                            if match:
                                bvid = match.group(1)
                                html_content += f'''
                                <div style="flex: 0 0 320px; display: flex; flex-direction: column;">
                                    <div style="font-size: 15px; font-weight: bold; margin-bottom: 8px; color: #555; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{display_title}">{display_title}</div>
                                    <iframe src="https://player.bilibili.com/player.html?bvid={bvid}&page=1&high_quality=1&danmaku=0&autoplay=0" 
                                            scrolling="no" border="0" frameborder="no" framespacing="0" 
                                            allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"
                                            style="width: 100%; height: 200px; border-radius: 8px; background-color: #000;">
                                    </iframe>
                                    <a href="{vid_url}" target="_blank" style="font-size: 13px; color: #0078D7; text-decoration: none; margin-top: 6px; text-align: center;">
                                        🔗 若無法播放，點擊前往 Bilibili 觀看
                                    </a>
                                </div>
                                '''
                        else:
                            # 預防性支援一般 MP4 影片
                            html_content += f'''
                            <div style="flex: 0 0 320px; display: flex; flex-direction: column;">
                                <div style="font-size: 15px; font-weight: bold; margin-bottom: 8px; color: #555; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{display_title}">{display_title}</div>
                                <video controls preload="metadata" style="width: 100%; height: 200px; border-radius: 8px; background-color: #000; object-fit: cover;">
                                    <source src="{vid_url}" type="video/mp4">
                                    您的瀏覽器不支援影片播放。
                                </video>
                                <a href="{vid_url}" target="_blank" style="font-size: 13px; color: #0078D7; text-decoration: none; margin-top: 6px; text-align: center;">
                                    🔗 點擊開啟影片連結
                                </a>
                            </div>
                            '''
                            
                    html_content += '</div>'
                    
                    # 💡 終極修正：把所有換行跟多餘的排版空格壓縮掉，徹底破除 Markdown 的程式碼區塊魔咒！
                    clean_html = re.sub(r'\s+', ' ', html_content).strip()
                    st.markdown(clean_html, unsafe_allow_html=True)

            st.markdown("---")

if __name__ == "__main__":
    main()