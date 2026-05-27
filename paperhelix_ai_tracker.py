import customtkinter as ctk
from tkinter import messagebox
import json
import os
import platform
from google import genai
from google.genai import types
import pydantic

# 系統字型判定
if platform.system() == "Windows":
    main_font_family = "StayHomeWriting"  # 優先套用你的宅在家字動筆
elif platform.system() == "Darwin":
    main_font_family = "PingFang TC"
else:
    main_font_family = "Arial"

ctk.set_appearance_mode("light")

class PaperHelixAITracker(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 多巴胺視覺配色設定（時序脈絡字卡採用漸進多巴胺色系）
        self.bg_purple = "#C69FD5"      # 粉紫背景
        self.text_yellow = "#FDFDC9"    # 奶油黃字
        self.dark_purple = "#4A2E80"    # 深紫容器
        self.macaron_green = "#BAFFC9"  # 成功追蹤時的綠燈
        self.error_red = "#E74C3C"      # 錯誤紅

        # 時序演進的三波浪馬卡龍色卡
        self.timeline_colors = ["#FFB3BA", "#BAE1FF", "#BAFFC9"] # 櫻花粉(源頭) -> 天空藍(演進) -> 薄荷綠(現狀)

        self.title("PaperHelix AI Tracker - Academic Genealogy Canvas 📊💜")
        self.geometry("1060x650") # 黃金寬螢幕科研畫布
        self.resizable(False, False)
        self.configure(fg_color=self.bg_purple)

        # 🔑 直接植入你的 Gemini API Key
        MY_GEMINI_KEY = "YOUR_GEMINI_API_KEY_HERE"

        # 初始化 Gemini 客戶端
        try:
            self.ai_client = genai.Client(api_key=MY_GEMINI_KEY)
        except:
            self.ai_client = None

        self.title_font = ctk.CTkFont(family=main_font_family, size=18, weight="bold")
        self.body_font = ctk.CTkFont(family=main_font_family, size=13)
        self.card_title_font = ctk.CTkFont(family=main_font_family, size=15, weight="bold")

        self.setup_ui()

    def setup_ui(self):
        # 主雙欄配置外框
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=(15, 10))
        main_frame.grid_columnconfigure(0, weight=40) # 左欄：References 原始文本貼上區
        main_frame.grid_columnconfigure(1, weight=60) # 右欄：AI 學術流向時序牆
        main_frame.grid_rowconfigure(0, weight=1)

        # =====================================================================
        # 📝 【左欄】：文獻原始文本輸入區
        # =====================================================================
        left_column = ctk.CTkFrame(main_frame, fg_color=self.dark_purple, corner_radius=12)
        left_column.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        ctk.CTkLabel(left_column, text="📋 Paste References / Intro Text", font=self.title_font, text_color=self.text_yellow).pack(pady=(12, 2))
        
        # 大文本輸入框
        self.txt_input = ctk.CTkTextbox(left_column, fg_color="#FFFFFF", text_color="#000000", font=self.body_font, corner_radius=8)
        self.txt_input.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 預置一組醫學影像與 dMRI / GAN 領域的精美測試引言段落
        default_refs = """Recent clinical studies on ischemic stroke heavily rely on Diffusion Tensor Imaging (DTI) metrics like Fractional Anisotropy (FA) to evaluate white matter damage, a methodology standardized by Smith et al. (2021). However, raw dMRI scans often suffer from low resolution and severe noise constraints. To overcome this image degradation, Wang & Liu (2023) introduced a novel Generative Adversarial Network (GAN) architecture utilizing residual learning to enhance tensor metrics. Building upon these algorithmic foundations, the current framework (2025) optimizes the loss function specifically for acute stroke prognosis models."""
        self.txt_input.insert("1.0", default_refs)

        # =====================================================================
        # 📊 【右欄】：AI 學術流向時序牆
        # =====================================================================
        self.right_column = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.right_column.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        ctk.CTkLabel(self.right_column, text="🧬 Academic Evolution Genealogy", font=self.title_font, text_color=self.dark_purple).pack(anchor="w", padx=5, pady=(2, 5))

        # 可滾動的時序卡片面板
        self.scroll_canvas = ctk.CTkScrollableFrame(self.right_column, fg_color=self.dark_purple, corner_radius=12)
        self.scroll_canvas.pack(fill="both", expand=True)
        self.scroll_canvas._scrollbar.configure(width=0) # 隱藏滾動條，但仍保留滾動功能
        self.scroll_canvas._scrollbar.pack_forget()

        self.lbl_init_tips = ctk.CTkLabel(self.scroll_canvas, text="準備解構文脈基因鏈... 🧬\n請在左側貼上內文，並在下方盲打 /trace 啟動。", font=self.body_font, text_color="gray")
        self.lbl_init_tips.pack(pady=200)

        # =====================================================================
        # ⌨️ 【底部】：極客盲打核心命令列
        # =====================================================================
        self.ent_cmd = ctk.CTkEntry(
            self, 
            placeholder_text=" ⚡ 盲打指令：輸入 /trace 進行學術文脈追蹤與時序圖譜繪製... ", 
            font=self.body_font,
            fg_color=self.dark_purple, 
            text_color=self.text_yellow,
            placeholder_text_color="gray",
            height=40,
            corner_radius=8
        )
        self.ent_cmd.pack(fill="x", padx=20, pady=(10, 15))
        self.ent_cmd.bind("<Return>", self.parse_tracker_command)

    # --- ⌨️ 核心盲打解析分配器 ---
    def parse_tracker_command(self, event):
        raw_cmd = self.ent_cmd.get().strip()
        self.ent_cmd.delete(0, "end")

        if not raw_cmd: return

        if raw_cmd.lower() == "/trace":
            self.execute_academic_trace()
            return

        self.flash_ui_status(self.error_red, " 未知指令！請使用 /trace 啟動追蹤 ")

    # --- 🤖 Gemini 2.5 結構化語義演進解構核心 ---
    def execute_academic_trace(self):
        raw_text = self.txt_input.get("1.0", "end").strip()
        if not raw_text or raw_text == "Paste References / Intro Text":
            self.flash_ui_status(self.error_red, " ❌ 請先在左側貼上任何論文文獻文本！ ")
            return
        if not self.ai_client:
            self.flash_ui_status(self.error_red, " ❌ Gemini API Key 未正確植入！ ")
            return

        self.ent_cmd.configure(state="disabled", placeholder_text=" Gemini Decoding Academic Genealogy... 🧬 ")
        self.update()

        # 💡 定義精準的演進階段 Schema 類別
        class MilestoneNode(pydantic.BaseModel):
            年份或時序: str    # 例如: "2021年" 或 "階段一"
            核心貢獻科學家: str # 例如: "Smith et al."
            學術里程碑里程: str # 具體改進了什麼技術、提出什麼模型
            核心指標或專有名詞: list[str] # 例如: ["dMRI", "FA", "Residual Learning"]

        class PaperHelixSchema(pydantic.BaseModel):
            學術流派總結: str
            歷史演進時序鏈: list[MilestoneNode] # 按時間由遠到近排列的陣列

        try:
            # 呼叫 Gemini 2.5 Flash 進行高度學術抽象化提煉
            response = self.ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    """你是一位精通神經影像學 (dMRI/MRI) 與深度學習演算法領域的首席科學家。
                    請仔細閱讀左側這段學術引言或參考文獻文本，理清這些科學家之間共同推動技術演進的『歷史脈絡』。
                    請將他們按照時間由遠到近、承先啟後的邏輯進行解構。
                    必須一律使用繁體中文回傳指定的結構化 JSON。""",
                    raw_text
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PaperHelixSchema,
                    temperature=0.2
                )
            )

            result_json = json.loads(response.text)
            self.render_helix_timeline(result_json)

        except Exception as e:
            self.flash_ui_status(self.error_red, f" 💥 追蹤失敗：{str(e)[:25]} ")
        finally:
            self.ent_cmd.configure(state="normal", placeholder_text=" ⚡ 盲打指令：輸入 /trace 進行學術文脈追蹤與時序圖譜繪製... ")
            self.ent_cmd.focus()

    # --- 🎨 渲染多巴胺時序脈絡字卡牆 ---
    def render_helix_timeline(self, data):
        # 清空右側畫布
        for widget in self.scroll_canvas.winfo_children(): 
            widget.destroy()

        # 1. 頂部：學術流派一秒總結卡片（深容器奶油黃字）
        summary_card = ctk.CTkFrame(self.scroll_canvas, fg_color="#361B66", corner_radius=10)
        summary_card.pack(fill="x", padx=12, pady=(5, 10))
        
        lbl_s_title = ctk.CTkLabel(summary_card, text="💡 全局學術流派精髓速讀  ", font=self.card_title_font, text_color=self.text_yellow)
        lbl_s_title.pack(anchor="w", padx=15, pady=(10, 2))
        
        # ✨ 終極修正：將原本的 CTkLabel 拋棄，改用透明、唯讀的 CTkTextbox！
        # 設定 wrap="char" (字元層級自動換行) 與固定高度，留足 padx 避震緩衝區，手寫體絕對不頂牆！
        lbl_s_content = ctk.CTkTextbox(
            summary_card, 
            height=85,                  # 給它足夠容納長篇大總結的舒適高度
            fg_color="transparent",     # 隱藏文字框底色，完美融入深紫卡片
            text_color="#E8D7FF",       # 標籤字體顏色
            font=self.body_font, 
            wrap="char"                 # ✨ 右側撞牆時自動換行
        )
        # 左右 padx 刻意墊厚 (10, 20)，留出右側安全走廊
        lbl_s_content.pack(fill="x", padx=(10, 20), pady=(0, 10))
        
        # 把 AI 吐出來的長文本塞進去
        lbl_s_content.insert("1.0", data.get("學術流派總結", "未明學術流派"))
        # 💡 設定為唯讀狀態，防止滑鼠誤觸修改
        lbl_s_content.configure(state="disabled")

        # 2. 遍歷渲染歷史演進時序鏈陣列
        nodes = data.get("歷史演進時序鏈", [])
        for index, node in enumerate(nodes):
            # 智慧色卡指派：利用餘數在粉、藍、黃馬卡龍色系中平滑循環，視覺效果極佳！
            card_color = self.timeline_colors[index % len(self.timeline_colors)]
            
            # 里程碑字卡載體
            card = ctk.CTkFrame(self.scroll_canvas, fg_color=card_color, corner_radius=12)
            card.pack(fill="x", padx=12, pady=6)

            # 標題欄：結合年份、科學家姓名
            year = node.get("年份或時序", "未知時間")
            author = node.get("核心貢獻科學家", "未知學者")
            lbl_node_title = ctk.CTkLabel(card, text=f"⏱️ [{year}]  {author}  ", font=self.card_title_font, text_color=self.dark_purple)
            lbl_node_title.pack(anchor="w", padx=15, pady=(10, 2))

            # 核心科學突破描述（使用唯讀 Textbox 完美換行，且支援宅在家字動筆複製！）
            content_box = ctk.CTkTextbox(card, height=55, fg_color="transparent", text_color="#1A1A24", font=self.body_font, wrap="char")
            content_box.pack(fill="x", padx=10, pady=0)
            content_box.insert("1.0", node.get("學術里程碑里程", ""))
            content_box.configure(state="disabled")

            # 字卡內附帶的學術專有名詞標籤牆 (Keywords inside card)
            tags = node.get("核心指標或專有名詞", [])
            if tags:
                tag_str = "標籤：" + "  ".join([f"#{t}" for t in tags]) + "  "
                lbl_tags = ctk.CTkLabel(card, text=tag_str, font=ctk.CTkFont(family=main_font_family, size=11), text_color=self.dark_purple)
                lbl_tags.pack(anchor="w", padx=15, pady=(0, 10))

            # 3. 繪製精美的手寫體向下演進箭頭（最後一個節點不需要箭頭）
            if index < len(nodes) - 1:
                lbl_arrow = ctk.CTkLabel(self.scroll_canvas, text="     ⬇️ 承前啟後，技術演進...  ", font=ctk.CTkFont(family=main_font_family, size=12, weight="bold"), text_color=self.text_yellow)
                lbl_arrow.pack(anchor="w", padx=40, pady=2)

        # 成功刷新亮燈
        self.flash_ui_status(self.macaron_green, " 成功！學術脈絡時序基因鏈已全數解構完成！🎉 ", text_color=self.dark_purple)

    # --- 🎨 馬卡龍狀態即時閃爍反饋技術 ---
    def flash_ui_status(self, bg_color, placeholder_msg, text_color="#FDFDC9"):
        self.ent_cmd.configure(fg_color=bg_color, text_color=text_color, placeholder_text=placeholder_msg)
        self.update()
        self.after(2200, self.reset_entry_theme)

    def reset_entry_theme(self):
        self.ent_cmd.configure(fg_color=self.dark_purple, text_color=self.text_yellow, placeholder_text=" ⚡ 盲打指令：輸入 /trace 進行學術文脈追蹤與時序圖譜繪製... ")


if __name__ == "__main__":
    app = PaperHelixAITracker()
    app.mainloop()